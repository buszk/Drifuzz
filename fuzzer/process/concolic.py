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
from os.path import dirname, realpath

class ConcolicThread(threading.Thread):

    def __init__(self, comm, nproc):
        threading.Thread.__init__(self)
        self.comm = comm
        self.config = FuzzerConfiguration()
        self.idx_sem = threading.BoundedSemaphore(value=1)
        self.idx_sem.acquire()
        self.model = Model(self)
        self.comm.register_model(nproc, self.model)
        self._stop_event = threading.Event()
        self.slave_id = nproc

    def run_concolic(self, payload):
        while not self.stopped():
            if self.comm.concolic_lock.acquire(timeout=0.1):
                break
        log_concolicserver("concolic locked")
        fname = 'tmp_conc_payload'
        outdir = 'tmp_conc_out'
        drifuzz_path = dirname(dirname(dirname(realpath(__file__))))
        target = self.config.argument_values['target']
        
        # Preparation
        if os.path.exists(outdir):
            shutil.rmtree(outdir)

        with open(fname, 'wb') as f:
            f.write(payload)

        # Run concolic script
        cmd = [
                f'{drifuzz_path}/../drifuzz-panda/concolic.py',
                target, fname,
                '--outdir', outdir
                ]
        log = open('tmp_conc_log', 'a')
        p = subprocess.Popen(cmd,
                            stdin=None,
                            stdout=log,
                            stderr=log)
        total_timeout = 120
        while not self.stopped():
            try:
                p.wait(timeout=1)
            except subprocess.TimeoutExpired:
                total_timeout -= 1
                if total_timeout == 0:
                    break
                continue
            break
        else:
            log_concolicserver("thread stopped. Killing concolic process")
            p.kill()
        log.close()

        # Postprocessing
        payloads = []
        if os.path.exists(outdir):
            for filename in os.listdir(outdir):
                file_path = os.path.join(outdir, filename)
                with open(file_path, 'rb') as f:
                    payloads.append(f.read())
        log_concolicserver(f"Concolic generate {len(payloads)} inputs")

        # Send to master
        for pl in payloads:
            send_msg(DRIFUZZ_NEW_INPUT, pl, self.comm.to_master_queue)
        self.comm.concolic_lock.release()
        log_concolicserver("concolic unlocked")

    def req_read_idx(self, key, size, cnt):
        send_msg(DRIFUZZ_REQ_READ_IDX, (key, size, cnt), \
            self.comm.to_modelserver_queue,  source=self.slave_id)
        # response = recv_tagged_msg(self.comm.to_slave_queues[self.slave_id], DRIFUZZ_REQ_READ_IDX)
        # print("requesting")

        if self.idx_sem.acquire(timeout=5):
            # print("requested")
            return self.idx
        else:
            log_concolicserver('Req read index: timeout', self.slave_id)
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
            log_concolicserver('Req dma index: timeout', self.slave_id)
            # self.stop()
            return 0

    def loop(self):
        while not self.stopped():
            msg = recv_msg(self.comm.to_concolicserver_queue, timeout=0.1)
            if msg is None:
                continue
            if msg.tag ==  DRIFUZZ_NEW_INPUT:
                log_concolicserver("Received DRIFUZZ_NEW_INPUT")
                self.run_concolic(msg.data)        
            elif response.tag == DRIFUZZ_REQ_READ_IDX or \
                response.tag == DRIFUZZ_REQ_DMA_IDX:
                key, idx = response.data
                self.idx = idx
                self.idx_sem.release()

    def run(self):
        self.loop()

    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()
