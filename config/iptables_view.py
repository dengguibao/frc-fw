import iptc
import json
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from pyroute2 import IPDB

from common.functions import (
    verify_ip,
    verify_port,
    verify_necessary_field,
    verify_prefix_mode_net
)


@api_view(['POST', 'DELETE'])
def set_chain_group_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'request body error!'
        }, status=status.HTTP_400_BAD_REQUEST)

    data = verify_necessary_field(j, ('*chain_name', '*table_name', 'nat_mode'))
    if not data:
        return Response({
            'code': 1,
            'msg': 'some necessary field is mission!'
        }, status=status.HTTP_400_BAD_REQUEST)

    if data['table_name'] not in ('nat', 'filter'):
        return Response({
            'code': 1,
            'msg': 'table type error!'
        }, status=status.HTTP_400_BAD_REQUEST)

    if (data['table_name'] == 'nat' and 'nat_mode' not in data) \
            or data['nat_mode'] not in ('snat', 'dnat'):
        return Response({
            'code': 1,
            'msg': 'nat chain must be specific the nat_mode field!'
        }, status=status.HTTP_400_BAD_REQUEST)

    rule = {
        'src': '0.0.0.0/0',
        'target': {
            'goto': data['chain_name']
        }
    }

    if data['table_name'] == 'filter':
        root_chain = "FORWARD"

    if data['table_name'] == 'nat' and data['nat_mode'] == 'snat':
        root_chain = 'POSTROUTING'

    if data['table_name'] == 'nat' and data['nat_mode'] == 'dnat':
        root_chain = 'PREROUTING'

    try:
        if request.method == 'POST':
            iptc.easy.add_chain(data['table_name'], data['chain_name'])
            iptc.easy.add_rule(data['table_name'], root_chain, rule_d=rule)
            status_code = status.HTTP_201_CREATED

        if request.method == 'DELETE':
            iptc.easy.delete_rule(data['table_name'], root_chain, rule_d=rule)
            iptc.easy.delete_chain(data['table_name'], data['chain_name'], flush=True)
            status_code = status.HTTP_200_OK

    except Exception as e:
        return Response({
            'code': 1,
            'msg': e.args[1] if len(e.args) >= 2 else str(e.args)
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'code': 0,
        'msg': 'success'
    }, status=status_code)


@api_view(('GET',))
def get_chain_groups_endpoint(request):
    group_type = request.GET.get('group_type', None)
    data = None
    if group_type:
        data = get_chain_groups(group_type)

    if not isinstance(data, list):
        return Response({
            'code': 0,
            'msg': 'param group_type error',
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'code': 0,
        'msg': 'success',
        'data': data
    }, status=status.HTTP_200_OK)


@api_view(('POST', 'DELETE'))
def set_rule_endpoint(request, rule_type):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'request body error!'
        }, status=status.HTTP_400_BAD_REQUEST)
    target_list = {
        'snat': ('SNAT', 'MASQUERADE'),
        'dnat': ('DNAT', 'REDIRECT'),
        'filter': ('ACCEPT', 'DROP')
    }

    if rule_type not in target_list:
        return Response({
            'code': 1,
            'msg': 'illegal rule type!'
        }, status=status.HTTP_400_BAD_REQUEST)

    ret = insert_rule(rule_type, j, request.method, target_list[rule_type])
    if ret['code'] == 0:
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return Response(ret, status_code)


def insert_rule(rule_type: str, post_data: dict, action: str, target_action: tuple) -> dict:
    necessary_field = {
        'snat': {
            'field': (
                '*chain_group_name', 'protocol',
                'src', 'dst', 'comment',
                'dport', 'sport',
                'in_interface', '*target',
                'to_source', 'to_port'
            ),
            'table': 'nat'
        },
        'dnat': {
            'field': (
                '*chain_group_name', 'protocol',
                'src', 'dst', 'comment',
                'dport', 'sport',
                'in_interface', '*target',
                'to_destination', 'to_port'
            ),
            'table': 'nat'
        },
        'filter': {
            'field': (
                '*chain_group_name', 'protocol',
                'src', 'dst', 'comment',
                'dport', 'sport',
                'in_interface', '*target',
            ),
            'table': 'filter'
        }
    }
    if rule_type not in necessary_field:
        return {
            'code': 1,
            'msg': 'inert rule type is not nat or filter'
        }

    data = verify_necessary_field(post_data, necessary_field[rule_type]['field'])
    if not data:
        return {
            'code': 1,
            'msg': "necessary field verify failed!"
        }

    chain_group_list = get_chain_groups(rule_type)

    if data['chain_group_name'] not in chain_group_list:
        return {
            'code': 1,
            'msg': 'illegal chain group name'
        }

    r = build_rule(data, target_action=target_action)

    if 'code' in r:
        return {
            'code': 1,
            'msg': 'build rule_d has error',
            "data": r,
        }
    try:

        if action.upper() == 'POST':
            iptc.easy.insert_rule(necessary_field[rule_type]['table'], data['chain_group_name'], rule_d=r)

        if action.upper() == 'DELETE':
            iptc.easy.delete_rule(necessary_field[rule_type]['table'], data['chain_group_name'], rule_d=r)

    except Exception as e:
        return {
            'code': 1,
            'msg': e.args[1] if len(e.args) >= 2 else str(e.args)
        }

    return {
        'code': 0,
        'msg': 'success'
    }


def build_rule(data: dict, target_action: tuple) -> dict:
    if 'target' in data and data['target'] not in target_action:
        return {
            'code': 1,
            'msg': 'target error!'
        }

    if data['target'] == 'SNAT' and 'to_source' not in data:
        return {
            'code': 1,
            'msg': 'snat mode mast be specific to_source field!'
        }

    if data['target'] == 'DNAT' and \
            ('to_destination' not in data and 'to_port' not in data):
        return {
            'code': 1,
            'msg': 'dnat mode mast be specific to_destination field!'
        }

    if data['target'] == 'REDIRECT' and 'to_port' not in data:
        return {
            'code': 1,
            'msg': 'redirect mode mast be specific to_port field!'
        }

    if 'to_port' in data and not verify_port(data['to_port']):
        return {
            'code': 1,
            'msg': 'to_port format verify failed!'
        }

    if 'protocol' in data and data['protocol'] not in ('tcp', 'udp','icmp','gre','ah','esp','ospf','sctp'):
        return {
            'code': 1,
            'msg': 'protocol error, only support tcp or udp!'
        }

    if ('src' in data and not verify_prefix_mode_net(data['src'])) \
            or ('dst' in data and not verify_prefix_mode_net(data['dst'])):
        return {
            'code': 1,
            'msg': 'source address or destination address format error!'
        }

    if 'sport' in data and not verify_port(data['sport']):
        return {
            'code': 1,
            'msg': 'source port format error!'
        }

    if 'dport' in data and not verify_port(data['dport']):
        return {
            'code': 1,
            'msg': 'destination port format error!'
        }

    if ('dport' in data and 'protocol' not in data) or ('sport' in data and 'protocol' not in data):
        return {
            'code': 1,
            'msg': 'specific source port or destination port, both protocol must be specified'
        }

    if_list = get_all_interfaces_list()
    if 'in_interface' in data and data['in_interface'] not in if_list:
        return {
            'code': 1,
            'msg': 'in interface error!'
        }

    if 'to_source' in data and not verify_ip(data['to_source']):
        return {
            'code': 1,
            'msg': 'snat to source address error!'
        }

    if 'to_destination' in data and \
            (not verify_prefix_mode_net(data['to_destination']) and not verify_ip(data['to_destination'])):
        return {
            'code': 1,
            'msg': 'to_destination field format error!'
        }

    r = {
        'target': data['target']
    }

    if 'to_source' in data:
        r['target'] = {
            r['target']: {
                'to_source': data['to_source']
            }
        }
    if 'to_destination' in data:
        r['target'] = {
            r['target']: {
                'to_destination': data['to_destination']
            }
        }

    if 'to_port' in data:
        r['target'] = {
            r['target']: {
                'to_port': '%s' % data['to_port']
            }
        }

    if 'protocol' in data:
        r['protocol'] = data['protocol']

    if 'protocol' in data and 'dport' in data:
        prot = r['protocol']
        r[prot] = {
            'dport': '%s' % data['dport']
        }

    if 'protocol' in data and 'sport' in data:
        prot = r['protocol']
        r[prot] = {
            'sport': '%s' % data['sport']
        }

    if 'src' in data:
        r['src'] = data['src']

    if 'dst' in data:
        r['dst'] = data['dst']

    if 'in_interface' in data:
        r['in_interface'] = data['in_interface']

    if 'comment' in data:
        r['comment'] = {
            'comment': data['comment']
        }

    # print(r)
    return r


def get_chain_groups(group_type: str):
    data = []
    g_list = {
        'snat': {
            'table_name': 'nat',
            'chain_name': 'POSTROUTING',
        },
        'dnat': {
            'table_name': 'nat',
            'chain_name': 'PREROUTING',
        },
        'filter': {
            'table_name': 'filter',
            'chain_name': 'FORWARD',
        }
    }
    if group_type not in g_list:
        return False
    try:

        d = iptc.easy.dump_chain(g_list[group_type]['table_name'], g_list[group_type]['chain_name'], ipv6=False)
    except:
        return False
    else:
        for i in d:
            if 'target' in i and 'goto' in i['target']:
                data.append(i['target']['goto'])
    return data


def get_all_interfaces_list() -> list:
    ipdb = IPDB()
    d = ipdb.by_name.keys()
    ipdb.release()
    return d
