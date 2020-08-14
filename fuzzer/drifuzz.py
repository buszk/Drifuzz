import os
import sys
import time
import signal
import threading
import traceback
import multiprocessing
from communicator import Communicator
from process.master import MasterProcess
from process.slave import SlaveThread
from process.mapserver import mapserver_loader
from process.update import update_loader
from common.debug import log_core, enable_logging
from common.config import FuzzerConfiguration
from common.util import prepare_working_dir, copy_seed_files, print_fail, \
    check_if_old_state_exits, print_exit_msg, check_state_exists, print_pre_exit_msg, ask_for_purge, print_warning

USE_UI = True

def handle_pdb(sig, frame):
    import pdb
    # pdb.set_trace()
    for th in threading.enumerate():
        print(th)
        traceback.print_stack(sys._current_frames()[th.ident])
        print()

def main():
    signal.signal(signal.SIGUSR1, handle_pdb)
    print(os.getpid())
    time.sleep(1)

    config = FuzzerConfiguration()
    num_processes = config.argument_values['p']
    reload = False

    if config.argument_values['Purge'] and check_if_old_state_exits(config.argument_values['work_dir']):
        print_warning("Old workspace found!")
        print_warning("Wiping old workspace...")
        prepare_working_dir(config.argument_values['work_dir'], purge=config.argument_values['Purge'])
        time.sleep(2)

    if not check_if_old_state_exits(config.argument_values['work_dir']):
        if not prepare_working_dir(config.argument_values['work_dir'], purge=config.argument_values['Purge']):
            print_fail("Working directory is weired or corrupted...")
            return 1
        if not copy_seed_files(config.argument_values['work_dir'], config.argument_values['seed_dir']):
            print_fail("Seed directory is empty...")
            return 1
        config.save_data()
    else:
        log_core("Old state exist -> loading...")
        config.load_data()
        reload = True

    comm = Communicator(num_processes = num_processes)
    master = MasterProcess(comm, reload=reload)
    mapserver_process = multiprocessing.Process(name='MAPSERVER', target=mapserver_loader, args=(comm,reload))
    if USE_UI:
        update_process = multiprocessing.Process(name='UPDATE', target=update_loader, args=(comm,))

    slaves = []
    for i in range(num_processes):
        slave = SlaveThread(comm, i, reload=reload)
        slaves.append(slave)

    comm.start()
    comm.create_shm()

    if USE_UI:
        update_process.start()
        time.sleep(.1)

    mapserver_process.start()

    for slave in slaves:
        slave.start()
    

    print('Starting master loop')
    try:
        master.loop()
    except KeyboardInterrupt:
        print('Saving data')
        # Wait for child processes to properly exit
        mapserver_process.join()
        if USE_UI:
            update_process.join()
        
        # Properly stop threads
        for slave in slaves:
            slave.stop()
        # Stop communicator last because Queues may be in used
        comm.stop()
        master.save_data()
        print('Data saved')
        


if __name__ == "__main__":
    main()
