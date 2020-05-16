from sysv_ipc import SharedMemory,ftok,IPC_EXCL, IPC_CREAT

bitmap_size = 65536
virgin_bits:bytearray = bytearray(bitmap_size)
for i in range(bitmap_size):
    virgin_bits[i] = 0xff

class Bitmap():

    def __init__(self):
        self.shm = SharedMemory(None, flags = IPC_EXCL|IPC_CREAT, 
                mode= 0o600, size = bitmap_size, init_character = b'\x00')
        print('shm', self.shm)
        # to show we are alive
        self.shm.write('\x01')
        # print(self.bytes())
        # self.shm.attach()
    
    def get_key(self):
        return self.shm.key 
    
    def get_id(self):
        return self.shm.id
    
    def get_size(self):
        return bitmap_size

    def bytes(self):
        buffer = self.shm.read(bitmap_size)
        n = 0
        for i in range(bitmap_size):
            if buffer[i] != 0:
                n += 1
        return n

    def has_new_bits(self):
        ret = 0
        buffer = self.shm.read(bitmap_size)
        for i in range(bitmap_size):
            if buffer[i] and buffer[i] & virgin_bits[i]:
                virgin_bits[i] &= ~buffer[i]
                if virgin_bits[i] == 0xff:
                    ret = 2
                elif ret < 1:
                    ret = 1
        return ret
        

    def release(self):
        self.shm.remove()
