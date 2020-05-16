import sys
import signal
import multiprocessing
from communicator import Communicator
from process.master import MasterProcess
from process.slave import SlaveThread
from process.mapserver import mapserver_loader
from common.config import FuzzerConfiguration
from common.util import prepare_working_dir, copy_seed_files, print_fail, \
    check_if_old_state_exits, print_exit_msg, check_state_exists, print_pre_exit_msg, ask_for_purge, print_warning


def main():
    config = FuzzerConfiguration()
    num_processes = 1

    prepare_working_dir(config.argument_values['work_dir'], purge=True)

    comm = Communicator(num_processes = num_processes)
    master = MasterProcess(comm)
    mapserver_process = multiprocessing.Process(name = 'MAPSERVER', target = mapserver_loader, args = (comm,))

    slaves = []
    for i in range(num_processes):
        slave = SlaveThread(comm, i)
        slaves.append(slave)
    
    comm.start()
    comm.create_shm()
    for slave in slaves:
        slave.start()
    
    mapserver_process.start()
    
    print('Starting master loop')
    try: 
        master.loop()
    except KeyboardInterrupt:
        print('trapped keyboard interrupt')
        comm.stop()
        print('comm stopped')
        for slave in slaves:
            slave.stop()
        print('slaves stopped')
        mapserver_process.terminate()
        print('mapserver terminated')


if __name__ == "__main__":
    main()