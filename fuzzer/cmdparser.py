
from enum import IntEnum

class Command(IntEnum):
    WRITE = 1
    READ = 2
    EXEC_INIT = 3
    EXEC_EXIT = 4
    READY = 5
    VM_KASAN = 6
    REQ_RESET = 7

opts = {
    Command.WRITE: {
        'func': 'write',
        'argbytes': 32,
        'argfmt': '<QQQQ',
        'retfmt': ''
    },
    Command.READ: {
        'func': 'read',
        'argbytes': 24,
        'argfmt': '<QQQ',
        'retfmt': '<Q'
    },
    Command.EXEC_INIT: {
        'func': 'exec_init',
        'argbytes': 0,
        'argfmt': '',
        'retfmt': '<Q'
    },
    Command.EXEC_EXIT: {
        'func': 'exec_exit',
        'argbytes': 0,
        'argfmt': '',
        'retfmt': '<Q'
    },
    Command.READY: {
        'func': 'vm_ready',
        'argbytes': 0,
        'argfmt': '',
        'retfmt': '<Q'
    },
    Command.VM_KASAN: {
        'func': 'vm_kasan',
        'argbytes': 0,
        'argfmt': '',
        'retfmt': ''
    },
    Command.REQ_RESET: {
        'func': 'req_reset',
        'argbytes': 0,
        'argfmt': '',
        'retfmt': ''
    }
}