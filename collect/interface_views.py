from socket import AF_INET
from pyroute2 import IPRoute

from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response


@api_view(['GET'])
def get_interface_list_endpoint(request):
    buffer = []
    # ret = execShell("nmcli device status")
    # if ret['code'] == 0:
    #     is_title = True
    #     for line in ret['return'].splitlines():
    #         if is_title:
    #             is_title = False
    #             continue
    #         line_field = line.split()
    #         buffer.append({
    #             'device': line_field[0],
    #             'type': line_field[1],
    #             'state': line_field[2],
    #             'connection': line_field[3],
    #         })
    # else:
    #     return Response(ret, status=status.HTTP_400_BAD_REQUEST)
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
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_interface_detail_endpoint(request):
    buffer = []
    if_name = request.GET.get('ifname', None)
    ipr = IPRoute()
    if if_name:
        detail = ipr.get_addr(label=if_name)
        # ret = execShell(f'nmcli device show {if_name}')
        #
        # if ret['code'] == 0:
        #     for line in ret['return'].splitlines():
        #         line_field = line.split()
        #         k = line_field[0].split(':')[0]
        #         v = line_field[1].strip()
        #         buffer[k] = v
        #     return Response({
        #         'code': 0,
        #         'msg': 'success',
        #         'data': buffer
        #     })
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
    }, status=status.HTTP_200_OK)