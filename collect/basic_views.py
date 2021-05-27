import time
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def get_basic_info_endpoint(request):
    """
    get server status information
    :param request:
    :return:
    """

    with open('/etc/hostname', 'r') as fp:
        hostname = fp.read()

    with open('/proc/uptime') as fp:
        running_total_time = fp.read().split()[0]
    system_time = time.time()
    return Response({
        'code': 0,
        'msg': 'success',
        'data': {
            'hostname': hostname if hostname else None,
            'running_total_time': running_total_time if running_total_time else None,
            'system_time': system_time
        }
    })


@api_view(('GET',))
def get_sys_forward_state_endpoint(request):
    with open('/proc/sys/net/ipv4/ip_forward', 'r') as f:
        d = f.read()

    return Response({
        'code': 0,
        'msg': 'success',
        'state': 'enable' if d.strip() == '1' else 'disable'
    })

