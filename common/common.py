# from collect.models import *
from collect.serializer import *

RESOURCE_MODELS = {
    'io': {
        'type': 'sar',
        'model': IoInfo,
        'serialize': IoInfoSerialize
    },
    'memory': {
        'type': 'sar',
        'model': MemoryInfo,
        'serialize': MemoryInfoSerialize
    },
    'cpu': {
        'type': 'sar',
        'model': CpuInfo,
        'serialize': CpuInfoSerialize
    },
    'net': {
        'type': 'sar',
        'model': NetInfo,
        'serialize': NetInfoSerialize
    },
    'load': {
        'type': 'sar',
        'model': SysLoad,
        'serialize': SysLoadSerialize
    },
    'tcp': {
        'type': 'sar',
        'model': TcpInfo,
        'serialize': TcpInfoSerialize
    },
}
