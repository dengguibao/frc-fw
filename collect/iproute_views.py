import os.path

from pyroute2 import IPDB
from config.models import PolicyRoute
from .serializer import PolicyRouteSerialize
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ParseError

from common.functions import prefix2NetMask, get_ifindex_pair, ifindex2ifname


@api_view(['GET', ])
def get_arp_tables_endpoints(request):
    if not os.path.exists('/proc/net/arp'):
        raise ParseError('not found /proc/net/arp')

    first_line = True
    data = []
    with open('/proc/net/arp', 'r') as fp:
        content = fp.read().splitlines()

    n = 1
    for line in content:
        if first_line:
            first_line = False
            continue

        x = line.split()
        data.append({
            'id': n,
            'ip_addr': x[0],
            'hw_addr': x[3],
            'device': x[5]
        })
        n += 1
    return Response({
        'msg': 'success',
        'data': data,
        'total': len(data)
    })


@api_view(['GET'])
def get_static_route_table_endpoint(request):
    ipdb = IPDB()
    if_name_list = get_ifindex_pair()
    route_table = []
    n = 0
    for i in ipdb.routes:
        # print(i)
        if i.family != 2:
            continue

        route_table.append({
            'dst': '0.0.0.0' if i.dst == 'default' else i.dst,
            'dst_len': i.dst_len,
            'dst_mask': prefix2NetMask(i.dst_len),
            'gateway': i.gateway,
            'oif_index': i.oif,
            'oif': ifindex2ifname(if_name_list, i.oif),
            'priority': i.priority,
            'table': i.table,
            'family': 'Ipv4' if i.family == 2 else 'Ipv6',
            'idx': n
        })
        n += 1
    ipdb.release()
    return Response({
        "code": 0,
        "msg": "success",
        "data": route_table
    })


@api_view(('GET',))
def get_all_ip_rule_endpoint(request):

    res = PolicyRoute.objects.all()
    ser = PolicyRouteSerialize(res, many=True)

    return Response({
        'code': 0,
        'msg': 'success',
        'data': ser.data
    })
