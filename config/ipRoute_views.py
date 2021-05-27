from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from pyroute2 import IPRoute
from pyroute2 import IPDB
from common.verify import (
    verify_netmask,
    verify_ip,
    verify_ip_subnet,
    verify_ip_addr,
    verify_interface_name,
    verify_prefix,
    verify_interface_state,
    filter_user_data,
)
from common.functions import ip2MaskPrefix


@api_view(['POST', 'DELETE'])
def set_ip_address_endpoint(request):

    fields = (
        ('*ip', str, verify_ip_addr),
        ('*netmask', str, verify_netmask),
        ('*ifname', str, verify_interface_name)
    )
    data = filter_user_data(request.body, fields)

    ipr = IPRoute()
    if_idx = ipr.link_lookup(ifname=data['ifname'].strip())[0]

    json_success = {
        'code': 0,
        'msg': 'success'
    }
    command = None
    if request.method == 'POST':
        command = 'add'

    if request.method == 'DELETE':
        command = 'delete'

    try:
        ipr.addr(command, index=if_idx, address=data['ip'], mask=ip2MaskPrefix(data['netmask']))
    except Exception as e:
        json_success['code'] = 1
        json_success['msg'] = e.args[1] if len(e.args) >= 2 else str(e.args)
    finally:
        ipr.close()
    return Response(json_success)


@api_view(['POST', 'DELETE'])
def set_ip_route_endpoint(request):
    fields = (
        ('*dst', str, verify_ip_subnet),
        ('*gateway', str, verify_ip_addr),
        ('*ifname', str, verify_interface_name),
        ('table', str, None)
    )
    data = filter_user_data(request.body, fields)
    ipr = IPRoute()
    if 'table' in data and data['table'] != 'main':
        data['table'] = ipr.link_lookup(ifname=data['ifname'].strip())[0]
    else:
        data['table'] = 254

    success_json = {
        'code': 0,
        'msg': 'success'
    }
    command = None
    if request.method == 'POST':
        command = 'add'

    if request.method == 'DELETE':
        command = 'delete'

    try:
        ipr.route(command, dst=data['dst'], gateway=data['gateway'], table=data['table'], dev=data['ifname'])
    except Exception as e:
        raise ParseError(e.args[1] if len(e.args) >= 2 else str(e.args))
    finally:
        ipr.close()
    return Response(success_json)


@api_view(['POST', 'DELETE'])
def set_ip_rule_endpoint(request):
    fields = (
        ('*ifname', str, verify_interface_name),
        ('dst', str, verify_ip),
        ('*src', str, verify_ip),
        ('src_len', int, verify_prefix),
        ('dst_len', int, verify_prefix),
        ('priority', int, None),
        ('tos', str, None)
    )
    data = filter_user_data(request.body, fields)
    ipr = IPRoute()
    return_json = dict()

    command = None
    if request.method == 'POST':
        command = 'add'

    if request.method == 'DELETE':
        command = 'del'

    try:
        if_idx = ipr.link_lookup(ifname=data['ifname'])
        data['table'] = if_idx[0]
        ipr.rule(
            command,
            **data
        )
    except Exception as e:
        raise ParseError(e.args[1] if len(e.args) > 2 else str(e))
    else:
        return_json['code'] = 0
        return_json['msg'] = 'success'
    finally:
        ipr.close()

    return Response(return_json)


@api_view(['POST'])
def set_interface_state_endpoint(request):
    fields = (
        ('*ifname', str, verify_interface_name),
        ('*state', str, verify_interface_state),
    )

    data = filter_user_data(request.body, fields)
    ipdb = IPDB()
    if_db = ipdb.interfaces
    if_name = data['ifname']

    if if_db[if_name]['state'] == data['state']:
        raise ParseError('interface %s state is already %s' % (if_name, data['state']))

    try:

        if_db[if_name].freeze()
        if data['state'].lower() == 'up':
            if_db[if_name].up().commit()
        if data['state'].lower() == 'down':
            if_db[if_name].down().commit()
        if_db[if_name].unfreeze()

    except Exception as e:
        raise ParseError(e.args[1] if len(e.args) > 2 else str(e.args))

    finally:
        ipdb.release()

    return Response({
        'code': 0,
        'msg': 'success'
    })
