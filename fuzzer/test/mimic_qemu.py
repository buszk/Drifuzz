import socket
import struct
import sys
sys.path.append('..')
from cmdparser import Command

server_address = './uds_socket_0'
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
    sock.connect(server_address)
    print('VM Ready')
    sock.send(struct.pack('<Q', Command.READY))
    res = struct.unpack('<Q', sock.recv(8))
    print(res)

    for i in range(49):
        print('exec init')
        sock.send(struct.pack('<Q', Command.EXEC_INIT))
        res = struct.unpack('<Q', sock.recv(8))
        print(res)
        
        print('write')
        sock.send(struct.pack('<QQQQQ', 0x1, 0x1, 0x11bb, 0x4, 0xaaaa))
        print()

        print('read')
        sock.send(struct.pack('<QQQQ', 0x2, 0x1, 0x11bb, 0x4))
        res = struct.unpack('<Q', sock.recv(8))
        print(res)

        print('exec exit')
        sock.send(struct.pack('<Q', Command.EXEC_EXIT))
        res = struct.unpack('<Q', sock.recv(8))
        print(res)
    
    print('exec init')
    sock.send(struct.pack('<Q', Command.EXEC_INIT))
    res = struct.unpack('<Q', sock.recv(8))
    print(res)

    print('vm kasan')
    sock.send(struct.pack('<Q', Command.VM_KASAN))
    res = struct.unpack('<Q', sock.recv(8))
    print(res)

except socket.error as msg:
    print(msg)
    sys.exit(1)
finally:
    sock.close()
