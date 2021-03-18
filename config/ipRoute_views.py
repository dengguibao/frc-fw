import json
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from pyroute2 import IPRoute
from pyroute2 import IPDB
from common.verify import (
    verify_netmask,
    verify_ip,
    verify_ip_subnet,
    verify_ip_addr,
    verify_field,
    verify_interface_name,
    verify_prefix,
    verify_interface_state,
)
from common.functions import ip2MaskPrefix


@api_view(['POST', 'DELETE'])
def set_ip_address_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error!'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*ip', str, verify_ip_addr),
        ('*netmask', str, verify_netmask),
        ('*ifname', str, verify_interface_name)
    )

    data = verify_field(j, fields)
    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data
        })

    ipr = IPRoute()
    ifidx = ipr.link_lookup(ifname=data['ifname'].strip())[0]

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
        ipr.addr(command, index=ifidx, address=j['ip'], mask=ip2MaskPrefix(data['netmask']))
    except Exception as e:
        json_success['code'] = 1
        json_success['msg'] = e.args[1] if len(e.args) >= 2 else str(e.args)
    finally:
        ipr.close()
    return Response(json_success, status_code)


@api_view(['POST', 'DELETE'])
def set_ip_route_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*dst', str, verify_ip_subnet),
        ('*gateway', str, verify_ip_addr),
        ('*ifname', str, verify_interface_name),
        ('table', str, None)
    )
    data = verify_field(j, fields)

    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data
        }, status=status.HTTP_400_BAD_REQUEST)

    ipr = IPRoute()
    if 'table' in data and data['table'] != 'main':
        data['table'] = ipr.link_lookup(ifname=j['ifname'].strip())[0]
    else:
        data['table'] = 254

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

    try:
        ipr.route(command, dst=data['dst'], gateway=data['gateway'], table=data['table'], dev=data['ifname'])
    except Exception as e:
        success_json['code'] = 1
        success_json['msg'] = e.args[1] if len(e.args) >= 2 else str(e.args)
        status_code = status.HTTP_400_BAD_REQUEST
    finally:
        ipr.close()
    return Response(success_json, status_code)


@api_view(['POST', 'DELETE'])
def set_ip_rule_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*ifname', str, verify_interface_name),
        ('dst', str, verify_ip),
        ('*src', str, verify_ip),
        ('src_len', int, verify_prefix),
        ('dst_len', int, verify_prefix),
        ('priority', int, None),
        ('tos', str, None)
    )

    data = verify_field(j, fields)

    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data
        }, status=status.HTTP_400_BAD_REQUEST)

    ipr = IPRoute()

    return_json = {}

    if request.method == 'POST':
        command = 'add'
        status_code = status.HTTP_201_CREATED

    if request.method == 'DELETE':
        command = 'del'
        status_code = status.HTTP_200_OK

    try:

        if_idx = ipr.link_lookup(ifname=j['ifname'])
        data['table'] = if_idx[0]
        ipr.rule(command, **data)
    except Exception as e:
        return_json['code'] = 1
        return_json['msg'] = e.args[1] if len(e.args) > 2 else str(e)
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        return_json['code'] = 0
        return_json['msg'] = 'success'
    finally:
        ipr.close()

    return Response(return_json, status_code)


@api_view(['POST'])
def set_interface_state_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*ifname', str, verify_interface_name),
        ('*state', str, verify_interface_state),
    )

    data = verify_field(j, fields)

    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data
        }, status=status.HTTP_400_BAD_REQUEST)

    ipdb = IPDB()
    ifdb = ipdb.interfaces
    ifname = data['ifname']

    if ifdb[ifname]['state'] == data['state']:
        return Response({
            'code': 1,
            'msg': 'interface %s state is already %s' % (ifname, data['state'])
        }, status=status.HTTP_400_BAD_REQUEST)

    try:

        ifdb[ifname].freeze()
        if data['state'].lower() == 'up':
            ifdb[ifname].up().commit()
        if data['state'].lower() == 'down':
            ifdb[ifname].down().commit()
        ifdb[ifname].unfreeze()

    except Exception as e:
        return Response({
            'code': 1,
            'msg': e.args[1] if len(e.args) > 2 else str(e.args)
        }, status=status.HTTP_400_BAD_REQUEST)

    finally:
        ipdb.release()

    return Response({
        'code': 0,
        'msg': 'success'
    }, status=status.HTTP_200_OK)
