from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from pyroute2.netlink.exceptions import NetlinkError
from pyroute2 import IPRoute
import iptc
from .models import PolicyRoute
from common.verify import (
    verify_netmask,
    verify_max_value,
    verify_ip_subnet,
    verify_ip_addr,
    verify_interface_name,
    verify_ip,
    verify_valid_tcp_port,
    verify_max_length,
    filter_user_data,
    verify_in_array,
)
from common.functions import ip2MaskPrefix


@api_view(['POST', ])
def set_ip_address_endpoint(request):
    fields = (
        ('*ip', str, verify_ip_addr),
        ('*netmask', str, verify_netmask),
        ('*ifname', str, verify_interface_name),
        ('*mode', str, (verify_in_array, ('static', 'none'))),
        ('*state', str, (verify_in_array, ('up', 'down'))),
        # ('flag', str, (verify_in_array, ('NULL', 'NOT_CHANGE'))),
    )

    data = filter_user_data(request.body, fields)

    try:
        ipr = IPRoute()
        if_idx = ipr.link_lookup(ifname=data['ifname'].strip())[0]
    except IndexError:
        raise ParseError('interface name error!')

    try:

        ipr.flush_addr(index=if_idx)
        ipr.flush_routes(table=if_idx)

        if data['mode'] == 'static':
            ipr.link('set', index=if_idx, state='up')
            ipr.addr('add', index=if_idx, address=data['ip'], mask=ip2MaskPrefix(data['netmask']))
            ipr.route('add', dst='0.0.0.0/0', gateway=data['ip'], table=if_idx)

        link_state = get_link_state(if_idx)
        if data['state'] != link_state:
            ipr.link('set', index=if_idx, state=data['state'])

    except NetlinkError as e:
        if e.code == 17:
            raise ParseError('The interface already has an IP of the same network segment')
        if e.code == 100:
            raise ParseError('The interface is down, please set it to up and try again')
        else:
            raise ParseError(e.args[1])
    finally:
        ipr.close()

    return Response({
        'code': 0,
        'msg': 'success'
    })


@api_view(['POST', 'DELETE'])
def set_ip_route_endpoint(request):
    fields = (
        ('*dst', str, verify_ip_subnet),
        ('*gateway', str, verify_ip_addr),
        # ('*dev', str, verify_interface_name),
        ('table', str, None)
    )
    data = filter_user_data(request.body, fields)
    ipr = IPRoute()
    if 'table' in data and data['table'] != 'main':
        data['table'] = ipr.link_lookup(ifname=data['dev'].strip())[0]
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

    # print(data)
    # ipr.route(command, **data)
    try:
        ipr.route(command, **data)
    except NetlinkError as e:
        if e.code == 22:
            raise ParseError('Invalid prefix for given prefix length.')

    except Exception as e:
        if isinstance(e.args, tuple):
            raise ParseError(e.args[1])

        # print(e.code, e.args)
        raise ParseError(e.args)
    finally:
        ipr.close()
    return Response(success_json)


@api_view(['POST', 'DELETE'])
def set_ip_rule_endpoint(request):
    fields = (
        # ('*ifname', str, verify_interface_name),
        ('*src', str, verify_ip),
        ('sport', int, verify_valid_tcp_port),

        ('*dst', str, verify_ip),
        ('dport', int, verify_valid_tcp_port),
        ('protocol', str, (verify_max_length, 8)),
        ('*mark', int, (verify_max_value, 99)),
        # ('priority', int,),
        ('*iif', str, verify_interface_name),
        ('*oif', str, verify_interface_name)
    )
    data = filter_user_data(request.body, fields)
    ipr = IPRoute()

    ipr.get_routes(match='default')

    if_idx = ipr.link_lookup(ifname=data['oif'])
    if not if_idx:
        raise ParseError('error output interface')
    data['table'] = if_idx[0]

    return_json = dict()
    command = None
    if request.method == 'POST':
        command = 'add'

    if request.method == 'DELETE':
        command = 'del'

    try:
        rule_d = {
            'src': data['src'],
            'dst': data['dst'],
            # 'protocol': data['protocol'],
            'in-interface': data['iif'],
            'target': {
                'MARK': {
                    'set-xmark': hex(data['mark'])
                }
            }
        }

        if 'protocol' in data:
            rule_d['protocol'] = data['protocol']

            if 'dport' in data or 'sport' in data:
                rule_d[data['protocol']] = {}

            if 'dport' in data:
                rule_d[data['protocol']]['dport'] = str(data['dport'])

            if 'sport' in data:
                rule_d[data['protocol']]['sport'] = str(data['sport'])

        if request.method == 'POST':
            iptc.easy.add_rule('mangle', 'PREROUTING', rule_d=rule_d)
            PolicyRoute.objects.create(**data)

        if request.method == 'DELETE':
            iptc.easy.delete_rule('mangle', 'PREROUTING', rule_d=rule_d)
            PolicyRoute.objects.filter(**data).delete()

        ipr.rule(
            command,
            table=data['table'],
            src=data['src'],
            dst=data['dst'],
            fwmark=data['mark'],
            # sport=data['sport'],
            # dport=data['dport'],
            iifname=data['iif'],
            # oifname=data['oif'],
            # talbe=data['table'],
        )

    except Exception as e:
        if isinstance(e.args, tuple):
            raise ParseError(e.args[1])

        raise ParseError(e.args)

    else:
        return_json['code'] = 0
        return_json['msg'] = 'success'
    finally:
        ipr.close()

    return Response(return_json)


def get_link_state(index: int) -> bool:
    try:
        ipr = IPRoute()
        link = ipr.link('get', index=index)
        ipr.close()
        if not link:
            return False
        return link[0].get('state')
    except NetlinkError:
        return False
