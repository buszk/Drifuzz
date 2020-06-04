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

    def __init__(self, id, config, req_payload_cb, submit_res_cb, reset_cb,
                    use_model=True):
        self.req_payload_cb = req_payload_cb
        self.submit_res_cb = submit_res_cb
        self.reset_cb = reset_cb
        self.log_file = open('rw.log', 'w')
        self.module_id = id 
        self.config = config
        self.next_free_idx = 0
        # count data access for this run
        self.read_cnt:dict = {}
        # data access to index
        self.read_idx:dict = {}
        self.dma_cnt:dict = {}
        self.dma_idx:dict = {}
        self.use_model = use_model

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
            ret = self.bytes_to_int(self.get_data_by_model(self.read_cnt, \
                    self.read_idx, key, size))
        else:
            ret = self.bytes_to_int(self.get_data_by_size(size))
        return ret

    def get_dma_data(self, size):
        if not self.payload:
            return b'A'*size
        if self.use_model:
            k = (size)
            ret = self.get_data_by_model(self.dma_cnt, self.dma_idx, k, size, reuse=True)
        else:
            ret = self.get_data_by_size(size)
        return ret
    
    def get_data_by_size(self, size, ind = None):
        if ind:
            ii = ind % self.payload_len
        else:
            ii = self.next_free_idx % self.payload_len
        res = b''
        while ii + size >self.payload_len:
            res += self.payload[ii:self.payload_len]
            size -= (self.payload_len - ii)
            ii = 0
        res += self.payload[ii:ii+size]
        if not ind:
            self.next_free_idx += size
        # print(size, res)
        return res

    def get_data_by_model(self, cnt_dict, idx_dict, k, size, reuse=False):
        n = 0
        first_occur = False
        if k not in cnt_dict.keys():
            cnt_dict[k] = 1
            first_occur = True
        else:
            n = cnt_dict[k]
            cnt_dict[k] += 1
        
        if k in idx_dict.keys():
            v = idx_dict[k]
            if not first_occur and reuse:
                idx = idx_dict[k][0]
                ret = self.get_data_by_size(size, ind=idx)
            elif len(v) > n:
                idx = idx_dict[k][n]
                ret = self.get_data_by_size(size, ind=idx)
            else:
                idx_dict[k].append(self.next_free_idx)
                ret = self.get_data_by_size(size)
        else:
            idx = self.next_free_idx
            idx_dict[k] = [self.next_free_idx]
            ret = self.get_data_by_size(size)
        return ret
    def handle(self, type:str, *args):
        return getattr(self, f"handle_"+type)(*args)

    def handle_write(self, region, addr, size, val):
        # self.log.append("write #%d[%lx][%d] =  %x" % (region, addr, size, val))
        self.log_file.write("[%.4f] write #%d[%lx][%d] =  %x\n" % (time.time(), region, addr, size, val))

    def handle_read(self, region, addr, size):
        k = (region, addr, size)
        ret = self.get_read_data(k, size)
        self.log_file.write("[%.4f] read  #%d[%lx][%d] as %x\n" % (time.time(), region, addr, size, ret))
        return (ret,)
    
    def handle_dma_buf(self, size):
        ret = self.get_dma_data(size)
        self.log_file.write("[%.4f] dma_buf [%x]\n" % (time.time(), size))
        return (ret,)

    def handle_reset(self):
        # TODO Check coverage
        pass

    def handle_exec_init(self):
        self.init_time = time.time()
        self.log = []
        self.log_file.truncate(0)
        print("requesting payload")
        self.payload:bytearray = self.req_payload_cb()
        print(self.payload[0:20])
        self.payload_len = len(self.payload)
        self.data_cnt = {}
        self.read_cnt = {}
        
        return (0,)

    def __submit_case(self, kasan):
        elapsed = time.time() - self.init_time
        print("Time spent:", elapsed)
        self.submit_res_cb(time=elapsed, kasan=kasan, payload=self.payload)

    def handle_exec_exit(self):
        self.__submit_case(False)
        return (0,)

    def handle_vm_ready(self):
        print("VM ready")
        return (0,)

    def handle_vm_kasan(self):
        print("VM enters kasan report")
        self.__submit_case(True)
        self.reset_cb()
        return (0,)

    def handle_req_reset(self):
        print("VM req hard reset")
        self.reset_cb()

    def save_data(self):
        dump = {}
        args_to_save = ['next_free_idx', 'read_idx', 'dma_idx']
        for key, value in self.__dict__.items():
            if key == 'next_free_idx':
                dump[key] = value
            elif key == 'read_idx' or key == 'dma_idx':
                dump[key] = [{'key': k, 'value': v} for k, v in value.items()]

        with open(self.config.argument_values['work_dir'] + "/module-%d.json" % \
                    self.module_id, 'w') as outfile:
            json.dump(dump, outfile, default=json_dumper)

    def load_data(self):
        """
        Method to load an entire master state from JSON file...
        """
        with open(self.config.argument_values['work_dir'] + "/module-%d.json" % \
                    self.module_id, 'r') as infile:
            dump = json.load(infile)
            for key, value in dump.items():
                if key == 'next_free_idx':
                    setattr(self, key, value)
                elif key == 'read_idx' or key == 'dma_idx':
                    d = {}
                    for entry in value:
                        if isinstance(entry['key'], list):
                            k = tuple(entry['key'])
                        elif isinstance(entry['key'], int):
                            k = entry['key']
                        d[k] = entry['value']
                    setattr(self, key, d)
                    