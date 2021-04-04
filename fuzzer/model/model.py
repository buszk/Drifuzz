import time
import os
import mmap
import json
from struct import unpack
from .seed import Seed
from .bitmap import Bitmap
from common.util import json_dumper

class Model(object):

    log:[str] = []
    # cnt = 1
    payload:bytearray = None
    payload_len:int = 0

    log_file = None

    def __init__(self, slave,
                    use_model=True, global_model=True):
        self.slave = slave
        self.log_file = open('rw.log', 'w')
        self.module_id = self.slave.slave_id
        self.next_free_idx = 0
        # count data access for this run
        self.read_cnt:dict = {}
        # data access to index
        self.read_idx:dict = {}
        self.dma_cnt:dict = {}
        self.dma_idx:dict = {}
        self.use_model = use_model
        self.use_global_model = global_model

    def __del__(self):
        self.log_file.close()

    def bytes_to_int(self, bs):
        if (len(bs) == 1):
            return unpack('<B', bs)[0]
        elif (len(bs) == 2):
            return unpack('<H', bs)[0]
        elif (len(bs) == 4):
            return unpack('<I', bs)[0]
        elif (len(bs) == 8):
            return unpack('<Q', bs)[0]

    def get_read_data(self, key, size):
        if self.payload is None:
            return 0
        if self.use_model:
            ret = self.bytes_to_int(self.get_read_data_by_model(key, size))
        else:
            ret = self.bytes_to_int(self.get_data_by_size(size))
        return ret

    def get_dma_data(self, size):
        if not self.payload:
            return b'A'*size
        if self.use_model:
            k = (size)
            ret = self.get_dma_data_by_model(k, size)
        else:
            ret = self.get_data_by_size(size)
        return ret
    
    def get_data_by_size(self, size, ind = None):
        res = b''
        if ind >= self.payload_len:
            res = b'\xaa' * size
        elif ind + size > self.payload_len:
            res += self.payload[ind:self.payload_len]
            res += b'\xaa' * (ind + size - self.payload_len)
        else:
            res += self.payload[ind:ind+size]
        return res

        # if ind:
        #     ii = ind % self.payload_len
        # else:
        #     ii = self.next_free_idx % self.payload_len
        # res = b''
        # # while ii + size >self.payload_len:
        # #     res += self.payload[ii:self.payload_len]
        # #     size -= (self.payload_len - ii)
        # #     ii = 0
        # # res += self.payload[ii:ii+size]
        # if ii + size >self.payload_len:
        #     res += self.payload[ii:self.payload_len]
        #     res += b'\xaa' * (ii + size - self.payload_len)
        # else:
        #     res += self.payload[ii:ii+size]
        # if not ind:
        #     self.next_free_idx += size
        # # print(size, res)
        # return res

    def get_read_data_by_model(self, k, size):
        n = 0
        if k not in self.read_cnt.keys():
            self.read_cnt[k] = 1
        else:
            n = self.read_cnt[k]
            self.read_cnt[k] += 1
        
        if k in self.read_idx.keys():
            v = self.read_idx[k]
            if len(v) > n:
                idx = self.read_idx[k][n]
                ret = self.get_data_by_size(size, ind=idx)
            else:
                idx = self.slave.req_read_idx(k, size, n)
                self.read_idx[k].append(idx)
                ret = self.get_data_by_size(size, ind=idx)
        else:
            idx = self.slave.req_read_idx(k, size, n)
            self.read_idx[k] = [idx]
            ret = self.get_data_by_size(size, ind=idx)
        self.log_file.write("[%.4f] idx %x n %d :%d %d %d\n" % (time.time(), idx, n, k[0], k[1], k[2]))
        return ret
    
    def get_dma_data_by_model(self, k, size, reuse=True):
        n = 0
        if k not in self.dma_cnt.keys():
            self.dma_cnt[k] = 1
        else:
            n = self.dma_cnt[k]
            self.dma_cnt[k] += 1
        
        if k in self.dma_idx.keys():
            v = self.dma_idx[k]
            if reuse:
                idx = self.dma_idx[k][0]
                ret = self.get_data_by_size(size, ind=idx)
            elif len(v) > n:
                idx = self.dma_idx[k][n]
                ret = self.get_data_by_size(size, ind=idx)
            else:
                idx = self.slave.req_dma_idx(k, size, n)
                self.dma_idx[k].append(idx)
                ret = self.get_data_by_size(size, ind=idx)
        else:
            idx = self.slave.req_dma_idx(k, size, n)
            self.dma_idx[k] = [idx]
            ret = self.get_data_by_size(size, ind=idx)
        return ret
    
    def handle(self, type:str, *args):
        return getattr(self, f"handle_"+type)(*args)

    def handle_write(self, region, addr, size, val):
        # self.log.append("write #%d[%lx][%d] =  %x" % (region, addr, size, val))
        self.log_file.write("[%.4f] write #%d[%lx][%d] =  %x\n" % (time.time(), region, addr, size, val))

    def handle_read(self, region, addr, size):
        ind = self.next_free_idx
        k = (region, addr, size)
        ret = self.get_read_data(k, size)
        self.log_file.write("[%.4f] read  #%d[%lx][%d] as %x\n" % (time.time(), region, addr, size, ret))
        return (ret, ind,)
    
    def handle_dma_buf(self, size):
        ret = self.get_dma_data(size)
        self.log_file.write("[%.4f] dma_buf [%x]\n" % (time.time(), size))
        # Pass an empty index 0 here
        # No need to care during fuzzing
        return (ret, 0)

    def handle_reset(self):
        # TODO Check coverage
        pass

    def handle_exec_init(self):
        self.init_time = time.time()
        self.log = []
        # print("requesting payload")
        self.payload:bytearray = self.slave.fetch_payload()
        # print(self.payload[0:20])
        self.payload_len = len(self.payload)
        self.data_cnt = {}
        self.read_cnt = {}
        
        return (0,)

    def __submit_case(self, kasan=False, timeout=False):
        elapsed = time.time() - self.init_time
        # print("Time spent:", elapsed)
        self.slave.send_bitmap(time=elapsed, kasan=kasan, timeout=timeout, payload=self.payload)

    def handle_exec_exit(self):
        self.__submit_case()
        return (0,)

    def handle_vm_ready(self):
        # print("VM ready")
        return (0,)

    def handle_vm_kasan(self):
        print("VM enters kasan report")
        self.__submit_case(kasan=True)
        # self.slave.restart_vm()
        return (0,)

    def handle_req_reset(self):
        print("VM req hard reset")
        self.slave.restart_vm()
    
    def handle_exec_timeout(self):
        print("Execution timed out")
        self.__submit_case(timeout=True)
        self.slave.restart_vm()
        return (0,)
