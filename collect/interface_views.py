from pyroute2 import IPRoute, IPDB
from common.functions import prefix2NetMask
from rest_framework.decorators import api_view
from rest_framework.response import Response
# from pyroute2.ndb.objects.interface import Interface


@api_view(['GET'])
def get_interface_list_endpoint(request):
    buffer = []
    ipr = IPRoute()
    links = ipr.get_links()
    for i in links:
        buffer.append({
            "ifname": i.get_attr('IFLA_IFNAME'),
            "state": i.get_attr('IFLA_OPERSTATE'),
            "index": i['index'],
        })
    ipr.close()
    return Response({
        'code': 0,
        'msg': 'success',
        'data': buffer
    })


@api_view(['GET'])
def get_interface_detail_endpoint(request):
    buffer = []
    ipdb = IPDB()
    for i in ipdb.by_name.keys():
        x = ipdb.interfaces[i]
        if x['ifname'] == 'lo':
            continue
        # print(x.ipaddr)
        if x['ipaddr']:
            ip_addr = x['ipaddr'][0]['local']
            prefix = x['ipaddr'][0]['prefixlen']
            netmask = prefix2NetMask(prefix)
        else:
            ip_addr = prefix = netmask = None

        buffer.append({
            'address': ip_addr,
            'mac': x['address'],
            'broadcast': x['broadcast'],
            'prefix': prefix,
            'netmask': netmask,
            'state': x['state'],
            'ifname': x['ifname'],
            'mtu': x['mtu'],
            'index': x['index'],
        })
    ipdb.release()

    return Response({
        'code': 1,
        'msg': 'success',
        'data': buffer
    })
