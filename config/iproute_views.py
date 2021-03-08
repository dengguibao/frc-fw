import json
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from pyroute2 import IPRoute
from pyroute2 import IPDB
from common.functions import (
    verify_netmask,
    ip2MaskPrefix,
    verify_ip,
    verify_necessary_field,
    verify_prefix_mode_net
)


@api_view(['POST', 'DELETE'])
def set_ip_address_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'request body error!'
        }, status=status.HTTP_400_BAD_REQUEST)

    data = verify_necessary_field(j, ['ip', 'netmask', 'ifname'])

    # if j['command'] not in ('add', 'replace', 'delete'):
    #     return Response({
    #         'code': 1,
    #         'msg': 'command error'
    #     }, status=status.HTTP_400_BAD_REQUEST)

    if not data:
        return Response({
            'code': 1,
            'msg': 'Some required fields are missing'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not verify_ip(j['ip']):
        return Response({
            'code': 1,
            'msg': 'ip format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        prefix = int(j['netmask'])
    except:
        if not verify_netmask(j['netmask']):
            return Response({
                'code': 1,
                'msg': 'mask format error'
            }, status=status.HTTP_400_BAD_REQUEST)
        prefix = ip2MaskPrefix(j['netmask'].strip())

    if not prefix or prefix > 32:
        return Response({
            'code': 1,
            'msg': 'mask format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    ipdb = IPDB()
    ifname_list = ipdb.by_name

    if j['ifname'] not in ifname_list:
        return Response({
            'code': 1,
            'msg': 'error interface name'
        }, status=status.HTTP_400_BAD_REQUEST)

    ipr = IPRoute()
    ifidx = ipr.link_lookup(ifname=j['ifname'].strip())[0]
    # if j['command'] == 'replace':
    #     old_ip = ipr.get_addr(label=j['ifname'].strip())[0].get_attr('IFA_ADDRESS')
    #     ipr.addr('delete', index=ifidx, address=old_ip, mask=prefix)
    json_success = {
        'code': 0,
        'msg': 'success'
    }
    if request.method == 'POST':
        command = 'add'
        status_code = status.HTTP_201_CREATED

    if request.method == 'DELETE':
        command = 'delete'
        status_code = status.HTTP_200_OK
    try:
        ipr.addr(command, index=ifidx, address=j['ip'].strip(), mask=prefix)
    except Exception as e:
        json_success['code'] = 1
        json_success['msg'] = e.args[1] if len(e.args) >= 2 else str(e.args)
    finally:
        ipr.close()
    return Response(json_success, status_code)


@api_view(['POST', 'DELETE'])
def set_route_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'request body error!'
        }, status=status.HTTP_400_BAD_REQUEST)

    data = verify_necessary_field(j, ['dst', 'gateway', 'ifname'])

    if not data or not verify_ip(j['gateway']):
        return Response({
            'code': 1,
            'msg': 'field format error, or some required field mission!'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not verify_prefix_mode_net(j['dst']):
        if not verify_ip(j['dst']) or 'netmask' not in j or not verify_netmask(j['netmask']):
            return Response({
                'code': 1,
                'msg': 'dest net format error!'
            }, status=status.HTTP_400_BAD_REQUEST)
        if verify_netmask(j['netmask']):
            dst = '%s/%s' % (j['dst'], ip2MaskPrefix(j['netmask']))
        else:
            dst = '%s/%s' % (j['dst'], j['netmask'])
    else:
        dst = j['dst']

    ipdb = IPDB()
    ifname_list = ipdb.by_name
    ipr = IPRoute()

    if j['ifname'] not in ifname_list:
        return Response({
            'code': 1,
            'msg': 'error interface name'
        }, status=status.HTTP_400_BAD_REQUEST)

    if 'table' in j and j['table'] != 'main':
        j['table'] = ipr.link_lookup(label=j['ifname'].strip())[0]
    else:
        j['table'] = 254

    success_json = {
        'code': 0,
        'msg': 'success'
    }

    if request.method == 'POST':
        status_code = status.HTTP_201_CREATED
        command = 'add'

    if request.method == 'DELETE':
        status_code = status.HTTP_200_OK
        command = 'delete'

    # print(dst, j['gateway'])

    try:
        ipr.route(command, dst=dst, gateway=j['gateway'], table=j['table'], dev=j['ifname'])
    except Exception as e:
        success_json['code'] = 1
        success_json['msg'] = e.args[1] if len(e.args) >= 2 else str(e.args)
    finally:
        ipr.close()
    return Response(success_json, status_code)
