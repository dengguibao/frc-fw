import time
import json

from socket import AF_INET

from pyroute2 import IPRoute
from pyroute2 import IPDB

from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from common.common import RESOURCE_MODELS
from common.functions import (
    timeRange2Seconds, prefix2NetMask
)

ALLOW_POST_HOSTS = (
    '127.0.0.1'
)


@api_view(['GET', 'POST'])
def sar_info_endpoint(request, name):
    """
    list collect resources
    :param request:
    :param name: resource name
    :return:
    """
    if name not in RESOURCE_MODELS:
        return Response({
            'code': 1,
            'msg': "invalid resource"
        }, status=status.HTTP_400_BAD_REQUEST)

    model = RESOURCE_MODELS[name]['model']
    serialize = RESOURCE_MODELS[name]['serialize']

    if request.method == 'GET':
        time_range = request.GET.get('time_range', None)
        if time_range:
            time_range_seconds = timeRange2Seconds(time_range)
            if time_range_seconds:
                start_time = int(time.time()) - time_range_seconds
                data = model.objects.filter(time__gt=start_time).all()
            else:
                return Response({
                    'code': 1,
                    'msg': 'date format error'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = model.objects.all()[0:1]

        response_data = serialize(data, many=True)
        return_data = {
            'code': 0,
            'msg': 'success',
            'data': response_data.data
        }
        return Response(return_data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        remote_addr = request.META.get('REMOTE_ADDR')
        if remote_addr not in ALLOW_POST_HOSTS:
            return Response({
                'code': 1,
                'msg': 'illegal request'
            }, status=status.HTTP_403_FORBIDDEN)

        post_content = request.body.decode()
        # print(post_content)
        post_data = serialize(data=json.loads(post_content))
        if post_data.is_valid():
            post_data.save()
            # print(post_data.data)
            return Response({
                'code': 0,
                'name': name,
                'msg': 'success'
            }, status=status.HTTP_201_CREATED)

        return Response({
            'code': 1,
            'name': name,
            'msg': post_data.errors
        }, status=status.HTTP_400_BAD_REQUEST)


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
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_static_route_table_endpoint(request):
    table = request.GET.get('interface_index', 254)
    try:
        table = int(table)
    except:
        table = 254
    ipdb = IPDB()
    ifname_list = ipdb.by_name.keys()
    ipr = IPRoute()
    x = ipr.route('dump', table=table)
    route_table = []
    for i in x:
        buf = {}
        dst_len = i['dst_len']
        table = i['table']
        dst_addr = i.get_attr('RTA_DST') if i.get_attr('RTA_DST') else '0.0.0.0'
        gw = i.get_attr('RTA_GATEWAY')
        metric = i.get_attr('RTA_PRIORITY')
        if_idx = i.get_attr('RTA_OIF')

        if not if_idx:
            continue

        buf['destination'] = dst_addr
        buf['netmask'] = prefix2NetMask(dst_len)
        if gw:
            buf['gateway'] = gw
        if if_idx:
            buf['iface'] = ifname_list[if_idx - 1]
        if metric:
            buf['metric'] = metric
        buf['table'] = table
        buf['prefix'] = dst_len
        route_table.append(buf)
        del buf
    ipr.close()
    ipdb.release()

    # is_title = True
    # route_table = []
    # with open('/proc/net/route') as fp:
    #     for line in fp:
    #         if is_title:
    #             is_title = False
    #             continue
    #         line_field = line.split()
    #         netmask = hexStr2Ip(line_field[7])
    #         route_table.append({
    #             "iface": line_field[0],
    #             "destination": hexStr2Ip(line_field[1]),
    #             "gateway": hexStr2Ip(line_field[2]),
    #             "netmask": netmask,
    #             "prefix": ip2MaskPrefix(netmask),
    #             "metric": line_field[6]
    #         })
    return Response({
        "code": 0,
        "msg": "success",
        "data": route_table
    }, status=status.HTTP_200_OK)


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


@api_view(['GET'])
def clean_sar_data_endpoint(request):
    yesterday = int(time.time() - 86400)
    for k in RESOURCE_MODELS:
        if RESOURCE_MODELS[k]['type'] == 'sar':
            RESOURCE_MODELS[k]['model'].objects.filter(time__lt=yesterday).delete()
    return Response({
        'code': 0,
        'msg': 'success'
    }, status=status.HTTP_200_OK)
