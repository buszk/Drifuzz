import os
import signal
import threading
import subprocess
from model.globalmodel import GlobalModel
from model.model import Model
from communicator import send_msg, recv_msg, Communicator
from common.debug import log_concolicserver
from common.config import FuzzerConfiguration
from protocol import *
import shutil
from os.path import dirname, realpath, join

class ConcolicWorker(threading.Thread):
    def __init__(self, comm, target, usb, payload, model, concolic_id, nproc, log, work_dir):
        threading.Thread.__init__(self)
        self.comm = comm
        self.model = model
        self.target = target
        self.usb = usb
        self.concolic_id = concolic_id
        self.slave_id = nproc + concolic_id
        self._stop_event = threading.Event()
        self.log = log
        self.payload = payload
        self.work_dir = work_dir

    def run(self):
        while not self.stopped():
            if self.comm.concolic_locks[self.concolic_id].acquire(timeout=0.1):
                break

        if self.stopped():
            return

        self.model.payload = self.payload
        self.model.payload_len = len(self.payload)
        self.model.read_cnt = {}
        self.model.dma_cnt = {}
        log_concolicserver("concolic locked " + str(self.concolic_id))
        fname = join(self.work_dir, f'tmp_conc_payload_{self.concolic_id}')
        outdir = join(self.work_dir, f'tmp_conc_out_{self.concolic_id}')
        drifuzz_path = dirname(dirname(dirname(realpath(__file__))))
        
        # Preparation
        if os.path.exists(outdir):
            shutil.rmtree(outdir)

        with open(fname, 'wb') as f:
            f.write(self.payload)

        # Run concolic script
        cmd = [
                'taskset', '-c', f'{2*self.concolic_id},{2*self.concolic_id+1}',
                'python3', '-u',
                f'{drifuzz_path}/../drifuzz-concolic/concolic.py',
                self.target, fname,
                '--outdir', outdir,
                '--tempdir',
                '--id', str(self.concolic_id),
                # '--pincpu', f'{2*self.concolic_id},{2*self.concolic_id+1}',
                '--socket', self.comm.qemu_socket_prefix + str(self.slave_id)
                ]
        if self.usb:
            cmd += ['--usb']
        p = subprocess.Popen(cmd,
                            stdin=subprocess.DEVNULL,
                            stdout=self.log,
                            stderr=self.log)
        total_timeout = 500
        while not self.stopped():
            try:
                p.wait(timeout=1)
            except subprocess.TimeoutExpired:
                total_timeout -= 1
                if total_timeout == 0:
                    # Concolic timedout
                    p.kill()
                    log_concolicserver("thread timedout. Killing concolic process")
                    self.comm.concolic_locks[self.concolic_id].release()
                    return
                continue
            break
        else:
            log_concolicserver("thread stopped. Killing concolic process")
            p.kill()

        # Postprocessing
        payloads = []
        if os.path.exists(outdir):
            for filename in os.listdir(outdir):
                file_path = os.path.join(outdir, filename)
                with open(file_path, 'rb') as f:
                    payloads.append(f.read())
        log_concolicserver(f"Concolic generate {len(payloads)} inputs " + str(self.concolic_id))

        # If no inputs were generated, redo the analysis
        if len(payloads) <= 1:
            send_msg(DRIFUZZ_NEW_INPUT, self.payload, self.comm.to_concolicserver_queue)

        # Send to master
        for pl in payloads:
            send_msg(DRIFUZZ_NEW_INPUT, pl, self.comm.to_master_queue)
        self.comm.concolic_locks[self.concolic_id].release()
        log_concolicserver("concolic unlocked " + str(self.concolic_id))

    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()

class ConcolicController(threading.Thread):
    def __init__(self, comm, nproc, concolic_id):
        threading.Thread.__init__(self)
        self.comm = comm
        self.idx_sem = threading.BoundedSemaphore(value=1)
        self.idx_sem.acquire()
        self.model = Model(self)
        self.comm.register_model(nproc + concolic_id, self.model)
        self.slave_id = nproc + concolic_id
        self._stop_event = threading.Event()

    def req_read_idx(self, key, size, cnt):
        send_msg(DRIFUZZ_REQ_READ_IDX, (key, size, cnt), \
            self.comm.to_modelserver_queue,  source=self.slave_id)
        # response = recv_tagged_msg(self.comm.to_slave_queues[self.slave_id], DRIFUZZ_REQ_READ_IDX)
        # print("requesting")

        if self.idx_sem.acquire(timeout=5):
            # print("requested")
            return self.idx
        else:
            log_concolicserver('Req read index: timeout')
            print(key, " ", size, " ", cnt)
            # self.stop()
            return 0
    
    def req_dma_idx(self, key, size, cnt):
        send_msg(DRIFUZZ_REQ_DMA_IDX, (key, size, cnt), \
            self.comm.to_modelserver_queue,  source=self.slave_id)
        # response = recv_tagged_msg(self.comm.to_slave_queues[self.slave_id], DRIFUZZ_REQ_READ_IDX)
        # print("requesting")
        if self.idx_sem.acquire(timeout=5):
            # print("requested")
            return self.idx
        else:
            log_concolicserver('Req dma index: timeout')
            # self.stop()
            return 0

    def loop(self):
        while not self.stopped():
            msg = recv_msg(self.comm.to_slave_queues[self.slave_id], timeout=0.1)
            if msg is None:
                continue
            if msg.tag == DRIFUZZ_REQ_READ_IDX or \
                msg.tag == DRIFUZZ_REQ_DMA_IDX:
                key, idx = msg.data
                self.idx = idx
                # log_concolicserver(f"Received index {self.idx}")
                self.idx_sem.release()

    def run(self):
        self.loop()

    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()


class ConcolicServerThread(threading.Thread):

    def __init__(self, comm, nproc, num_concolic, models):
        threading.Thread.__init__(self)
        self.comm = comm
        self.config = FuzzerConfiguration()
        self.nproc = nproc
        self.num_concolic = num_concolic
        self._stop_event = threading.Event()
        self.target = self.config.argument_values['target']
        self.workers = []
        self.work_dir = self.config.argument_values['work_dir']
        self.logs = []
        for i in range(num_concolic):
            self.logs.append(open(join(self.work_dir, f'tmp_conc_log_{i}'), 'w'))
        self.current = 0
        assert len(models) == num_concolic
        self.models = models
    
    def _next(self):
        self.current += 1
        self.current %= self.num_concolic

    def run_concolic(self, payload):
        log_concolicserver(f"Creating concolic worker on queue {self.current}")
        worker_thread = ConcolicWorker(
            self.comm, self.target, self.config.argument_values['usb'], payload,
            self.models[self.current], self.current, self.nproc,
            self.logs[self.current], self.work_dir)
        self.workers.append(worker_thread)
        worker_thread.start()
        self._next()



    def loop(self):
        while not self.stopped():
            msg = recv_msg(self.comm.to_concolicserver_queue, timeout=0.1)
            if msg is None:
                continue
            if msg.tag ==  DRIFUZZ_NEW_INPUT:
                log_concolicserver("Received DRIFUZZ_NEW_INPUT")
                self.run_concolic(msg.data)
        for lf in self.logs:
            lf.close()

    def run(self):
        self.loop()

    def stop(self):
        self._stop_event.set()
        for w in self.workers:
            if w:
                w.stop()
        
    def stopped(self):
        return self._stop_event.is_set()
