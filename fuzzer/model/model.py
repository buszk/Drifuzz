import time
from .seed import Seed
from .bitmap import Bitmap
from struct import unpack
# from process.slave import SlaveThread

class Model(object):

    # slave:SlaveThread = None
    slave = None
    # seed:Seed = None
    bitmap:Bitmap = None
    log:[str] = []
    cnt = 1
    payload:bytearray = None
    payload_len:int = 0
    cur = 0

    def __init__(self, slave):
        # TODO different seed file
        # self.bitmap = Bitmap()
        self.slave = slave


    def get_data(self, size):
        if self.payload is None:
            return 0
        if (size == 1):
            return unpack('<B', self.get_byte())[0]
        elif (size == 2):
            return unpack('<H', self.get_word())[0]
        elif (size == 4):
            return unpack('<I', self.get_dword())[0]
        elif (size == 8):
            return unpack('<Q', self.get_qword())[0]

    def get_byte(self):
        if self.cur + 1 > self.payload_len:
            self.cur = 0
        res = self.payload[self.cur:self.cur+1]
        self.cur += 1
        return res
            
    def get_word(self):
        if self.cur + 2 > self.payload_len:
            self.cur = 0
        res = self.payload[self.cur:self.cur+2]
        self.cur += 2
        return res
    
    def get_dword(self):
        if self.cur + 4 > self.payload_len:
            self.cur = 0
        res = self.payload[self.cur:self.cur+4]
        self.cur += 4
        return res

    def get_qword(self):
        if self.cur + 8 > self.payload_len:
            self.cur = 0
        res = self.payload[self.cur:self.cur+8]
        self.cur += 8
        return res

    def handle(self, type:str, *args):
        # print(type, *args)
        return getattr(self, f"handle_"+type)(*args)

    def handle_write(self, region, addr, size, val):
        self.log.append("write #%d[%lx][%d] =  %x" % (region, addr, size, val))

    def handle_read(self, region, addr, size):
        ret = self.get_data(size)
        self.log.append("read  #%d[%lx][%d] as %x" % (region, addr, size, ret))
        return (ret,)

    def handle_reset(self):
        # TODO Check coverage
        pass

    def handle_exec_init(self):
        # TODO clear bitmap
        # self.seed.reset()
        # self.seed.mutate()
        self.init_time = time.time()
        self.log = []
        print("requesting payload")
        self.payload:bytearray = self.slave.req_new_payload()
        print(self.payload[0:128])
        self.payload_len = len(self.payload)
        self.cur = 0
        
        return (0,)

    def __submit_case(self, kasan):
        elapsed = time.time() - self.init_time
        print("Time spent:", elapsed)
        self.slave.send_bitmap(time=elapsed, kasan = kasan, payload = self.payload)

    def handle_exec_exit(self):
        # TODO get bitmap
        # print("The run cover bytes: ", self.bitmap.bytes())
        # hnb = self.bitmap.has_new_bits()
        # print("has_new_bits: ",hnb )
        # if (hnb):
        #     with open('rw%d.log' % self.cnt, 'a+') as f:
        #         f.write('\n===== Read/Write Log =====\n')
        #         f.write('\n'.join(self.log))
        #     self.cnt += 1
        self.__submit_case(False)
        return (0,)

    def handle_vm_ready(self):
        return (0,)

    def handle_vm_kasan(self):
        print("VM enters kasan report")
        # print("has_new_bits: ", self.bitmap.has_new_bits())
        self.__submit_case(True)
        return (0,)

    def release(self):
        # if self.bitmap:
            # self.bitmap.release()
        pass