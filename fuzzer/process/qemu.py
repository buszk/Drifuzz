"""
Copyright (C) 2017 Sergej Schumilo

This file is part of kAFL Fuzzer (kAFL).

QEMU-PT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

QEMU-PT is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with QEMU-PT.  If not, see <http://www.gnu.org/licenses/>.
"""

import mmap
import os
import sys
import random
import resource
import select
import socket
import subprocess
import time
from socket import error as socket_error
import psutil
import mmh3
from os.path import dirname

# from common.debug import log_qemu
# from common.util import atomic_write

# from common.util import Singleton
from multiprocessing import Process, Manager


def to_string_32(value):
    return chr((value >> 24) & 0xff) + \
           chr((value >> 16) & 0xff) + \
           chr((value >> 8) & 0xff) + \
           chr(value & 0xff)


class qemu:
    SC_CLK_TCK = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

    def __init__(self, qid, bitmap_prefix, socket_prefix, config=None):

        self.global_bitmap = None

        # self.lookup = QemuLookupSet()
        self.bitmap_size = 65536
        # self.bitmap_size = config.config_values['BITMAP_SHM_SIZE']
        self.config = config
        self.qemu_id = str(qid)

        self.process = None
        self.bitmap_filename = bitmap_prefix + self.qemu_id
        self.socket_path = socket_prefix + self.qemu_id
        drifuzz_path = dirname(dirname(dirname(os.path.realpath(__file__))))
        target = self.config.argument_values['target']
        self.cmd = [f"{drifuzz_path}/panda-build/x86_64-softmmu/panda-system-x86_64",
                    "-hda", f"{drifuzz_path}/image/buster.img",
                    "-kernel", f"{drifuzz_path}/linux-module-build/arch/x86_64/boot/bzImage",
                    "-append", "console=ttyS0 nokaslr root=/dev/sda earlyprintk=serial net.ifnames=0 modprobe.blacklist=%s" % target,
                    "-snapshot",
                    "-enable-kvm",
                    "-k", "de",
                    "-m", "1G",
                    "-nographic",
                    "-net", "user",
                    "-net", "nic,model=%s" % target,
                    "-machine", "kernel-irqchip=off",
                    "-device", "drifuzz,bitmap=" + self.bitmap_filename + \
                        ",bitmap_size=" + str(self.bitmap_size) + \
                        ",socket=" + self.socket_path + \
                        ",timeout=" + str(self.config.argument_values['timeout']) + \
                        ",target=%s" % target + \
                        ",prog=init"]
        # self.cmd = ["gdb", "-ex", "handle SIGUSR1 nostop noprint", "-ex", "r", "--args"] +\
        #         self.cmd
        self.kafl_shm_f = None
        self.kafl_shm   = None

        self.payload_shm_f   = None
        self.payload_shm     = None

        self.bitmap_shm_f   = None
        self.bitmap_shm     = None

        self.e = select.epoll()
        self.crashed = False
        self.timeout = False
        self.kasan = False
        self.shm_problem = False
        self.initial_mem_usage = 0

        self.stat_fd = None

        self.virgin_bitmap = bytearray(self.bitmap_size)
        for i in range(self.bitmap_size):
            self.virgin_bitmap[i] = 255


    def __del__(self):
        if not self.process:
            return

        try:
            self.kafl_shm.close()
        except:
            pass

        try:
            self.global_bitmap.close()
        except:
            pass

        try:
            self.process.kill()
        except:
            pass

    def start(self, verbose=False, gdb=False):
        cmd = self.cmd
        if gdb:
            cmd = ['gdb', 
                    '-ex', 'handle SIGTTOU noprint',
                    '-ex', 'handle SIGTTIN noprint',
                    '-ex', 'break exit',
                    '-ex', 'r',
                    '-ex', 'bt',
                    '--args'] + self.cmd
        for _ in range(10):
            try:
                if verbose:
                    self.process = subprocess.Popen(cmd,
                                                    stdin=None,
                                                    stdout=None,
                                                    stderr=None)
                else:
                    #TODO: maybe a log file? devnull is fast, PIPE is very slow
                    self.process = subprocess.Popen(cmd,
                                                    stdin=subprocess.DEVNULL,
                                                    stdout=subprocess.DEVNULL,
                                                    stderr=subprocess.DEVNULL)
            except OSError as e:
                log_qemu("OSError in subprocess.Popen", self.qemu_id)
                print("OSError in subprocess.Popen", self.qemu_id)
                try:
                    self.process.kill()
                    self.process = None
                except:
                    pass
                continue
            # No error
            break
            
        if not self.process:
            log_qemu("Cannot create process properly", self.qemu_id)
            return False

        self.init()
        self.initial_mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self.kafl_shm.seek(0x0)
        self.kafl_shm.write(self.virgin_bitmap)
        self.kafl_shm.flush()
        return True

    def init(self):
        self.kafl_shm_f     = os.open(self.bitmap_filename, os.O_RDWR | os.O_SYNC | os.O_CREAT)
        os.ftruncate(self.kafl_shm_f, self.bitmap_size)

        self.kafl_shm       = mmap.mmap(self.kafl_shm_f, self.bitmap_size, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)
        os.close(self.kafl_shm_f)
        return True
