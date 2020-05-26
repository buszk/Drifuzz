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

def main():
    config = FuzzerConfiguration()
    num_processes = 1

    prepare_working_dir(config.argument_values['work_dir'], purge=True)

    comm = Communicator(num_processes = num_processes)
    master = MasterProcess(comm)
    mapserver_process = multiprocessing.Process(name='MAPSERVER', target=mapserver_loader, args=(comm,))
    if USE_UI:
        update_process = multiprocessing.Process(name='UPDATE', target=update_loader, args=(comm,))

    slaves = []
    for i in range(num_processes):
        slave = SlaveThread(comm, i)
        slaves.append(slave)
    
    comm.start()
    comm.create_shm()
    for slave in slaves:
        slave.start()
    mapserver_process.start()
    time.sleep(.01)
    if USE_UI:
        update_process.start()
    
    print('Starting master loop')
    try: 
        master.loop()
    except KeyboardInterrupt:
        comm.stop()
        for slave in slaves:
            slave.stop()
        mapserver_process.terminate()
        if USE_UI:
            update_process.terminate()


if __name__ == "__main__":
    main()