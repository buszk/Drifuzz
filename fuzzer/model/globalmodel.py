import json
from common.util import json_dumper

class GlobalModel():
    
    def __init__(self, config):
        self.config = config
        self.next_free_idx = 0
        self.read_idx:dict = {}
        self.dma_idx:dict = {}

    def get_read_idx(self, key, size, cnt):
        if key in self.read_idx.keys():
            if cnt < len(self.read_idx[key]):
                return self.read_idx[key][cnt]
            elif cnt == len(self.read_idx[key]):
                self.read_idx[key].append(self.next_free_idx)
                self.next_free_idx += size
                return self.read_idx[key][cnt]
            else:
                print("Error: read counter too large %d %d" % (cnt, len(self.read_idx[key])))
                return 0
        elif cnt == 0:
            self.read_idx[key] = [self.next_free_idx]
            self.next_free_idx += size
            return self.read_idx[key][cnt]
        else:
            print("Error: non-zero counter for empty read list %d" % cnt)
            return 0
    
    def get_dma_idx(self, key, size, cnt, reuse=True):
        if key in self.dma_idx.keys():
            if reuse:
                return self.read_idx[key][0]
            elif cnt < len(self.dma_idx[key]):
                return self.dma_idx[key][cnt]
            elif cnt == len(self.dma_idx[key]):
                self.dma_idx[key].append(self.next_free_idx)
                self.next_free_idx += size
                return self.dma_idx[key][cnt]
            else:
                print("Error: dma counter too large %d %d" % (cnt, len(self.dma_idx[key])))
                return 0
        elif cnt == 0:
            self.dma_idx[key] = [self.next_free_idx]
            self.next_free_idx += size
            return self.dma_idx[key][cnt]
        else:
            print("Error: non-zero counter for empty dma list %d" % cnt)
            return 0



    def save_data(self):
        dump = {}
        args_to_save = ['next_free_idx', 'read_idx', 'dma_idx']
        for key, value in self.__dict__.items():
            if key == 'next_free_idx':
                dump[key] = value
            elif key == 'read_idx' or key == 'dma_idx':
                dump[key] = [{'key': k, 'value': v} for k, v in value.items()]

        with open(self.config.argument_values['work_dir'] + "/globalmodule.json", \
                        'w') as outfile:
            json.dump(dump, outfile, default=json_dumper)

    def load_data(self):
        """
        Method to load an entire master state from JSON file...
        """
        with open(self.config.argument_values['work_dir'] + "/globalmodule.json", \
                        'r') as infile:
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
                    
