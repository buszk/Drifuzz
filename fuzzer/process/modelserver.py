import os
import signal
from model.globalmodel import GlobalModel
from communicator import send_msg, recv_msg, Communicator
from common.debug import log_modelserver
from common.config import FuzzerConfiguration
from protocol import *

def handle_pdb(sig, frame):
    import sys
    import pdb
    import threading
    import traceback
    for th in threading.enumerate():
        print(th)
        traceback.print_stack(sys._current_frames()[th.ident])
        print()

def modelserver_loader(comm):
    signal.signal(signal.SIGUSR1, handle_pdb)

    log_modelserver("PID: " + str(os.getpid()))
    modelserver_process = None
    
    try:
        modelserver_process = ModelServerProcess(comm)
        modelserver_process.loop()
    except KeyboardInterrupt:
        if modelserver_process:
            print('modelserver keyboard interrupt')
            modelserver_process.global_model.save_data()
            

class ModelServerProcess:

    def __init__(self, comm):
        self.comm = comm
        self.config = FuzzerConfiguration()
        self.global_model = GlobalModel(self.config)

    def loop(self):
        while True:
            msg = recv_msg(self.comm.to_modelserver_queue)
            if msg.tag ==  DRIFUZZ_REQ_READ_IDX:
                key, _, _ = msg.data
                res = self.global_model.get_read_idx(*msg.data)
                send_msg(DRIFUZZ_REQ_READ_IDX, (key, res), self.comm.to_slave_queues[msg.source])
            elif msg.tag == DRIFUZZ_REQ_DMA_IDX:
                key, _, _ = msg.data
                res = self.global_model.get_dma_idx(*msg.data)
                send_msg(DRIFUZZ_REQ_DMA_IDX, (key, res), self.comm.to_slave_queues[msg.source])
            else:
                continue
