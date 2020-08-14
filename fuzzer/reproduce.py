import os
import sys
import time
import signal
import multiprocessing
from communicator import Communicator
from process.master import MasterProcess
from process.slave import SlaveThread
from process.mapserver import mapserver_loader
from process.update import update_loader
from common.config import FuzzerConfiguration
from common.util import prepare_working_dir, copy_seed_files, print_fail, \
    check_if_old_state_exits, print_exit_msg, check_state_exists, print_pre_exit_msg, ask_for_purge, print_warning

USE_UI = False

def handle_pdb(sig, frame):
    import threading
    import traceback
    for th in threading.enumerate():
        print(th)
        traceback.print_stack(sys._current_frames()[th.ident])
        print()

# def handle_exit(sig, frame):
#     global comm, slave
#     print('Fuzzer exiting')
#     comm.stop()
#     print('comm to be stopped')
#     slave.stop()
#     print('slave to be stopped')

def main():
    global comm, slave
    signal.signal(signal.SIGUSR1, handle_pdb)
    # signal.signal(signal.SIGINT, handle_exit)
    print(os.getpid())

    config:FuzzerConfiguration = FuzzerConfiguration()
    num_processes = 1

    # prepare_working_dir(config.argument_values['work_dir'], purge=True)

    comm = Communicator(num_processes = num_processes)
    master = MasterProcess(comm, reload=False)
    slave = SlaveThread(comm, 0, reload=True)
    
    comm.start()
    comm.create_shm()

    slave.start()
    try:
        master.reproduce_loop()
    except KeyboardInterrupt:
        print('Received keyboard interrupt')
        comm.stop()
    

if __name__ == "__main__":
    main()