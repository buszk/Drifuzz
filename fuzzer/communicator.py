import multiprocessing
import socket
import struct
import os
import threading
import queue
import mmap
from model.model import Model
from cmdparser import opts, Command



# qemu_socket_prefix = '/dev/drifuzz_socket_'
qemu_socket_prefix = '/tmp/drifuzz_socket_'
bitmap_size = 65536

class SocketThread (threading.Thread):
    model: Model = None
    
    def __init__(self, addrses):
        threading.Thread.__init__(self)
        self.address = addrses
        self._stop_event = threading.Event()


    def register_model(self, model):
        self.model = model

    def run(self):
        if not self.model:
            print('Error: socket thread has not yet set up model')
            return
        try:
            os.unlink(self.address)
        except OSError:
            if os.path.exists(self.address):
                raise

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.address)
        sock.listen(1)

        while not self.stopped():
            sock.settimeout(0.1)
            try:
                connection, _ = sock.accept()
            except socket.timeout:
                    continue
            try:
                connection.settimeout(0.1)
                while not self.stopped():
                    try:
                        ty: bytearray[8] = connection.recv(8)
                        if ty == b'':
                            break
                        _ty = struct.unpack('<Q', ty)[0]
                        opt = opts[Command(_ty)]
                        args:bytearray[opt['argbytes']] = connection.recv(opt['argbytes'])
                        _args = struct.unpack(opt['argfmt'], args)
                        # print(_args)
                        ret = self.model.handle(opts[Command(_ty)]['func'], *_args)
                        # print(ret)
                        # If VM request reset, we close the connection
                        if Command(_ty) == Command.REQ_RESET:
                            print('REQ_RESET')
                            break            
                        if ret != None and opt['retfmt'] != '':
                            _ret = struct.pack(opt['retfmt'], *ret)
                            connection.send(_ret)        

                    except socket.timeout:
                        pass
                    except ConnectionResetError:
                        break
                
            finally:
                connection.close()
                
    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class Communicator:
    models: [Model] = []
    socks: [SocketThread] = []

    def __init__(self, num_processes=1):
        self.num_processes = num_processes
        self.files = ["/dev/shm/drifuzz_master_", "/dev/shm/drifuzz_mapserver_", "/dev/shm/drifuzz_bitmap_"]
        self.sizes = [(65 << 10), (65 << 10), bitmap_size]
        self.tmp_shm = [{}, {}, {}]
        self.tasks_per_requests = 1
        
        self.to_update_queue = multiprocessing.Queue()
        self.to_master_queue = multiprocessing.Queue()
        self.to_master_from_mapserver_queue = multiprocessing.Queue()
        self.to_master_from_slave_queue = multiprocessing.Queue()
        self.to_mapserver_queue = multiprocessing.Queue()

        # Call cancel_join_thread to ensure processes can exit properly
        #   when received SIGINT
        self.to_update_queue.cancel_join_thread()
        self.to_master_queue.cancel_join_thread()
        self.to_master_from_mapserver_queue.cancel_join_thread()
        self.to_master_from_slave_queue.cancel_join_thread()
        self.to_mapserver_queue.cancel_join_thread()

        self.to_slave_queues = []
        for i in range(num_processes):
            self.to_slave_queues.append(multiprocessing.Queue())
            self.to_slave_queues[i].cancel_join_thread()
            self.socks.append(SocketThread(qemu_socket_prefix + str(i)))

        self.slave_locks_bitmap = []
        self.slave_locks_A = []
        self.slave_locks_B = []
        for i in range(num_processes):
            self.slave_locks_bitmap.append(multiprocessing.Lock())
            self.slave_locks_A.append(multiprocessing.Lock())
            self.slave_locks_B.append(multiprocessing.Lock())
            self.slave_locks_B[i].acquire()

        self.stage_abortion_notifier = multiprocessing.Value('b', False)
        self.slave_termination = multiprocessing.Value('b', False, lock=False)
        self.sampling_failed_notifier = multiprocessing.Value('b', False)
        self.effector_mode = multiprocessing.Value('b', False)



    def get_master_payload_shm(self, slave_id):
        return self.__get_shm(0, slave_id)

    def get_mapserver_payload_shm(self, slave_id):
        return self.__get_shm(1, slave_id)

    def get_bitmap_shm(self, slave_id):
        return self.__get_shm(2, slave_id)

    def get_master_payload_shm_size(self):
        return self.sizes[0]

    def get_mapserver_payload_shm_size(self):
        return self.sizes[1]

    def get_bitmap_shm_size(self):
        return self.sizes[2]

    def create_shm(self):
        for j in range(len(self.files)):
            for i in range(self.num_processes):
                shm_f = os.open(self.files[j]+str(i), os.O_CREAT | os.O_RDWR | os.O_SYNC)
                os.ftruncate(shm_f, self.sizes[j]*self.tasks_per_requests)
                os.close(shm_f)

    def __get_shm(self, type_id, slave_id):
        if slave_id in self.tmp_shm[type_id]:
            shm = self.tmp_shm[type_id][slave_id]
        else:
            shm_fd = os.open(self.files[type_id] + str(slave_id), os.O_RDWR | os.O_SYNC)
            shm = mmap.mmap(shm_fd, self.sizes[type_id]*self.tasks_per_requests, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)
            self.tmp_shm[type_id][slave_id] = shm
        return shm

           

    def register_model(self, id, model:Model):
        self.socks[id].register_model(model)


    def start(self):
        for sock in self.socks:
            sock.start()
    
    def stop(self):
        for sock in self.socks:
            sock.stop()
            sock.join()


class Message():
    def __init__(self, tag, data, source=None):
        self.tag = tag
        self.data = data
        self.source = source

def msg_pending(queue):
    return queue.empty()

def send_msg(tag, data, queue, source=None):
    msg = Message(tag, data, source=source)
    queue.put(msg)

def recv_msg(q, timeout=None):
    if timeout:
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
    return q.get()

def recv_tagged_msg(queue, tag):
    tmp_list = []
    tmp_obj = None

    while True:
        tmp_obj = recv_msg(queue)
        if tmp_obj.tag == tag:
            return tmp_obj
        else:
            queue.put(tmp_obj)


