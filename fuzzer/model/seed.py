from os.path import exists
from struct import unpack
from technique.arithmetic import *
from technique.bitflip import *
from technique.havoc import *
from technique.interesting_values import *


def mutate_gen(payload):
    # for res in mutate_seq_walking_bits_array(payload):
    #     yield res
    # for res in mutate_seq_two_walking_bits_array(payload):
    #     yield res
    # for res in mutate_seq_four_walking_bits_array(payload):
    #     yield res
    for res in mutate_seq_walking_byte_array(payload, None):
        yield res
    # for res in mutate_seq_two_walking_bytes_array(payload):
    #     yield res
    # for res in mutate_seq_four_walking_bytes_array(payload):
    #     yield res
    
class Seed(object):

    seed_fn:str = ''
    payload = None
    cur = 0

    def __init__(self, fn):
        self.seed_fn = fn
        if exists(fn):
            self.payload = bytearray(open(fn, 'rb').read())
        self.cur = 0
        self.payload_len = len(self.payload)
        self.save_cnt = 0
        self.gen = mutate_gen(self.payload)
    
    def save(self):
        pass

    def get_data(self, size):
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
    
    def mutate(self):
        # TODO
        self.cur = 0
        self.payload = next(self.gen)
        print("mutating")

    def reset(self):
        self.payload = bytearray(open(self.seed_fn, 'rb').read())
        self.cur = 0
        self.payload_len = len(self.payload)
