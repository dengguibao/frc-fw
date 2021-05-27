from socket import AF_INET
from pyroute2 import IPRoute

from rest_framework.decorators import api_view
from rest_framework.response import Response


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
    if_name = request.GET.get('ifname', None)
    ipr = IPRoute()
    if if_name:
        detail = ipr.get_addr(label=if_name)
    else:
        detail = ipr.get_addr(family=AF_INET)
    ipr.close()
    for i in detail:
        buffer.append({
            'address': i.get_attr('IFA_ADDRESS'),
            'broadcast': i.get_attr('IFA_BROADCAST'),
            'ifname': i.get_attr('IFA_LABEL'),
            'prefix': i['prefixlen'],
            'index': i['index']
        })
    return Response({
        'code': 1,
        'msg': 'success',
        'data': buffer
    })