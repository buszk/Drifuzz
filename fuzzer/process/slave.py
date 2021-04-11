import os
import mmap
import time
import signal
import struct
import threading
import multiprocessing
from enum import IntEnum
from .qemu import qemu
from communicator import Communicator
from communicator import send_msg, recv_msg, recv_tagged_msg
from model.model import Model
from protocol import *
from common.config import FuzzerConfiguration
from common.debug import log_slave


class SlaveState(IntEnum):
    PROC_BITMAP = 1
    PROC_TASK = 2
    WAITING = 3

class SlaveThread(threading.Thread):
    comm: Communicator = None
    q:qemu = None
    model:Model = None
    slave_id:int = -1
    payload = None
    payload_sem  = None
    global_bitmap = None
    global_bitmap_fd = None

    reproduce = None
    vm_ready = False

    requested_input = False


    def __init__(self, comm, id, reload=False):
        threading.Thread.__init__(self)
        self.comm = comm
        self.slave_id = id
        self.config = FuzzerConfiguration()
        self.q = qemu(id, config=self.config)
        self.model = Model(self)
        self.comm.register_model(self.slave_id, self.model)
        self.state = SlaveState.WAITING
        self.payload_sem = threading.BoundedSemaphore(value=1)
        self.payload_sem.acquire()
        self.idx_sem = threading.BoundedSemaphore(value=1)
        self.idx_sem.acquire()
        self._stop_event = threading.Event()
        self.bitmap_size = self.config.config_values['BITMAP_SHM_SIZE']
        self.bitmap_filename = '/dev/shm/drifuzz_bitmap_' + str(self.slave_id)
        self.comm.slave_locks_bitmap[self.slave_id].acquire()
    
        self.reproduce = self.config.argument_values['reproduce']
        self.query_key = (0,)
        

    def __del__(self):
        if self.global_bitmap:
            self.global_bitmap.close()

    def exit_if_reproduce(self):
        if self.reproduce and self.reproduce != "":
            print("Reproducing case. Stop here")
            self.stop()
            os.kill(os.getpid(), signal.SIGINT)
            return True
        return False

    
    def restart_vm(self, reuse=False):
        log_slave(f"restarting vm {reuse=}", self.slave_id)
        self.query_key = (0,)
        while True:
            self.q.__del__()
            self.q = qemu(self.slave_id, config=self.config)
            v = False
            g = False
            if self.reproduce and self.reproduce != "":
                v = True
            elif self.config.argument_values['verbose']:
                v = True
                g = True
            if self.q.start(verbose=v, gdb=g):
                break
            else:
                time.sleep(1)
                print('Fail Reload')
        if self.comm.slave_termination.value:
            return False
        # Reuse self.payload
        if reuse:
            log_slave(f"release payload in restart_vm", self.slave_id)
            self.payload_sem.release()
        return True

    def __respond_job_req(self, response):
        # if self.state != SlaveState.WAITING:
        #     print("Error: slave is not waiting for input")
        #     return
        self.affected_bytes = response.data
        shm_fs = self.comm.get_master_payload_shm(self.slave_id)
        shm_fs.seek(0)
        payload_len = struct.unpack('<I', shm_fs.read(4))[0]
        # print('payload len:', payload_len)
        self.payload = shm_fs.read(payload_len) 
        # print(self.state)
        assert(self.state == SlaveState.WAITING)
        self.state = SlaveState.PROC_TASK
        log_slave(f"release payload in __respond_job_req", self.slave_id)
        self.payload_sem.release()
        # Todo one payload each time?

    def __respond_bitmap_req(self, response):
        # if self.state != SlaveState.WAITING:
        #     print("Error: slave is not waiting for input")
        #     return
        self.payload = response.data
        assert(self.state == SlaveState.WAITING)
        self.state = SlaveState.PROC_BITMAP
        log_slave(f"release payload in __respond_bitmap_req", self.slave_id)
        self.payload_sem.release()
            
    def open_global_bitmap(self):
        self.global_bitmap_fd = os.open(self.config.argument_values['work_dir'] + "/bitmap", os.O_RDWR | os.O_SYNC | os.O_CREAT)
        os.ftruncate(self.global_bitmap_fd, self.bitmap_size)
        self.global_bitmap = mmap.mmap(self.global_bitmap_fd, self.bitmap_size, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)
        os.close(self.global_bitmap_fd)

    def check_for_unseen_bits(self, bitmap):
        if not self.global_bitmap:
            self.open_global_bitmap()

        self.check_covered_bytes(bitmap)

        for i in range(self.bitmap_size):
            if bitmap[i] != 255:
                if self.global_bitmap[i] == 0:
                    return True
                if ((bitmap[i] | self.global_bitmap[i]) != self.global_bitmap[i]):
                    return True
        return False
    
    def check_covered_bytes(self, bitmap):
        result = 0
        global_cnt = 0
        for i in range(self.bitmap_size):
            if bitmap[i] != 255:
                result += 1
            if self.global_bitmap[i] != 0:
                global_cnt += 1
            
        log_slave('bitmap covers %d bytes; global bitmap covers %d bytes' % (result, global_cnt), self.slave_id)

    def send_bitmap(self, perf = 10, kasan = False, timeout = False, payload = None):
        if self.exit_if_reproduce():
            return

        if self.state == SlaveState.PROC_BITMAP:
            bitmap_shm = self.comm.get_bitmap_shm(self.slave_id)
            bitmap_shm.seek(0)
            bitmap = bitmap_shm.read(self.bitmap_size)
            # Reply master's BITMAP cmd
            send_msg(KAFL_TAG_REQ_BITMAP, bitmap, self.comm.to_master_queue, source = self.slave_id)
            # Ask master for new payloads once
            #   Transit from PROC_BITMAP to regular fuzzing
            # if not self.requested_input:
            #     self.requested_input = True
            #     send_msg(KAFL_TAG_REQ, str(self.slave_id), self.comm.to_master_queue, source = self.slave_id)
        elif self.state == SlaveState.PROC_TASK:
            bitmap_shm = self.comm.get_bitmap_shm(self.slave_id)
            bitmap_shm.seek(0)
            bitmap = bitmap_shm.read(self.bitmap_size)
            bitmap_shm.flush()

            # Process bitmap results
            hnb = self.check_for_unseen_bits(bitmap)
            if hnb:
                # Update mapserver with the payload
                mapserver_payload_shm = self.comm.get_mapserver_payload_shm(self.slave_id)
                mapserver_payload_shm.seek(0)
                mapserver_payload_shm.write(struct.pack('<I', len(payload)))
                mapserver_payload_shm.write(payload)
            result = FuzzingResult(0, False, timeout, kasan, self.affected_bytes[0],
                    self.slave_id, perf, reloaded=False, new_bits=hnb, qid=self.slave_id)
            # Notify mapserver the result
            send_msg(KAFL_TAG_RESULT, [result], self.comm.to_mapserver_queue, source=self.slave_id)
            # Wait for mapserver to finish
            self.comm.slave_locks_bitmap[self.slave_id].acquire()
            # Ask master for new payloads
            send_msg(KAFL_TAG_REQ, str(self.slave_id), self.comm.to_master_queue, source = self.slave_id)
        else:
            print("Error: slave thread in wrong state")
        self.state = SlaveState.WAITING
        log_slave(f"Execution time: {time.time()-self.start_time}", self.slave_id)

    def fetch_payload(self):
        if self.stopped():
            return None
        
        if not self.vm_ready:
            self.vm_ready = True
            send_msg(KAFL_TAG_START, self.q.qemu_id, self.comm.to_master_queue, source=self.slave_id)
            
        if self.reproduce and self.reproduce != "":
            with open(self.reproduce, 'rb') as infile:
                return infile.read()
        
        self.payload_sem.acquire()
        payload = self.payload
        # print(len(payload))
        assert(self.state != SlaveState.WAITING)
        self.start_time = time.time()
        log_slave("fetch_payload", self.slave_id)
        return payload

    def req_read_idx(self, key, size, cnt):
        self.query_key = key
        send_msg(DRIFUZZ_REQ_READ_IDX, (key, size, cnt), \
            self.comm.to_master_queue,  source=self.slave_id)
        # response = recv_tagged_msg(self.comm.to_slave_queues[self.slave_id], DRIFUZZ_REQ_READ_IDX)
        # print("requesting")
        if self.idx_sem.acquire(timeout=5):
            # print("requested")
            return self.idx
        else:
            print('Req read index: timeout')
            print(key, " ", size, " ", cnt)
            # self.stop()
            return 0
    
    def req_dma_idx(self, key, size, cnt):
        self.query_key = key
        send_msg(DRIFUZZ_REQ_DMA_IDX, (key, size, cnt), \
            self.comm.to_master_queue,  source=self.slave_id)
        # response = recv_tagged_msg(self.comm.to_slave_queues[self.slave_id], DRIFUZZ_REQ_READ_IDX)
        # print("requesting")
        if self.idx_sem.acquire(timeout=5):
            # print("requested")
            return self.idx
        else:
            print('Req dma index: timeout')
            # self.stop()
            return 0
        
    
    def interprocess_proto_handler(self):
        response = recv_msg(self.comm.to_slave_queues[self.slave_id], timeout=0.1)
        if response is None:
            return
        # print('slave got cmd %d' % response.tag)

        if response.tag == KAFL_TAG_JOB:
            self.__respond_job_req(response)

        elif response.tag == KAFL_TAG_REQ_BITMAP:
            self.__respond_bitmap_req(response)

        elif response.tag == KAFL_TAG_REQ_SAMPLING:
            self.__respond_sampling_req(response)

        elif response.tag == KAFL_TAG_REQ_BENCHMARK:
            self.__respond_benchmark_req(response)  

        elif response.tag == DRIFUZZ_REQ_READ_IDX or \
             response.tag == DRIFUZZ_REQ_DMA_IDX:
            # If qemu was restarted and we receive this,
            # it's from last execution before restarting
            # We discard the result
            key, idx = response.data
            if key == self.query_key:
                self.idx = idx
                self.idx_sem.release()

        else:
            log_slave("Received TAG: " + str(response.tag), self.slave_id)


    def loop(self):
        # print('starting qemu')
        # self.comm.reload_semaphore.acquire()
        v = False
        g = False
        if self.reproduce and self.reproduce != "":
            v = True
        elif self.config.argument_values['verbose']:
            v = True
            g = True
        self.q.start(verbose=v, gdb=g)
        # self.comm.reload_semaphore.release()
        # print('started qemu')
        send_msg(KAFL_TAG_REQ, self.q.qemu_id, self.comm.to_master_queue, source=self.slave_id)
        while not self.stopped():
            #try:
            # if self.comm.slave_termination.value:
                # return
            self.interprocess_proto_handler()
            #except:
            #    return
            

    def run(self):
        self.loop()

    def stop(self):
        self.q.__del__()
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()

            