import iptc
import json
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from pyroute2 import IPDB

from common.verify import (
    verify_ip,
    verify_port,
    verify_ip_range,
    verify_protocol,
    verify_interface_name,
    verify_ip_addr,
    filter_user_data
)
from common.functions import get_chain_groups


@api_view(['POST', 'DELETE'])
def set_chain_group_endpoint(request):
    fields = (
        ('*chain_name', str, None),
        ('*table_name', str, None),
        ('nat_mode', str, None),
    )

    data = filter_user_data(request.body, fields)

    if data['table_name'] not in ('nat', 'filter'):
        raise ParseError('the table name mast be nat or filter!')

    if data['table_name'] == 'nat' and 'nat_mode' not in data:
        raise ParseError('nat chain must be specific the nat_mode field!')

    if 'nat_mode' in data and data['nat_mode'] not in ('snat', 'dnat'):
        raise ParseError('the nat_mode field value must be snat or dnat!')

    rule = {
        'src': '0.0.0.0/0',
        'target': {
            'goto': data['chain_name']
        }
    }

    root_chain = None
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

        if request.method == 'DELETE':
            iptc.easy.delete_rule(data['table_name'], root_chain, rule_d=rule)
            iptc.easy.delete_chain(data['table_name'], data['chain_name'], flush=True)

    except Exception as e:
        raise ParseError(e.args[1] if len(e.args) >= 2 else str(e.args))

    return Response({
        'code': 0,
        'msg': 'success'
    })


@api_view(('POST', 'DELETE'))
def set_rule_endpoint(request, rule_type):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except json.JSONDecodeError:
        raise ParseError('illegal request, body format error')

    target_list = {
        'snat': ('SNAT', 'MASQUERADE'),
        'dnat': ('DNAT', 'REDIRECT'),
        'filter': ('ACCEPT', 'DROP')
    }

    if rule_type not in target_list:
        raise ParseError('illegal rule type!')

    ret = insert_rule(rule_type, j, request.method, target_list[rule_type])
    return Response({
        'code': 0,
        'msg': 'success',
        'data': ret
    })


def insert_rule(rule_type: str, post_data: dict, action: str, target_action: tuple) -> dict:
    table_field = {
        'snat': {
            'fields': (
                ('*chain_group_name', str, None),
                ('protocol', str, verify_protocol),
                ('src', str, verify_ip),
                ('dst', str, verify_ip),
                ('comment', str, None),
                ('dport', str, verify_port),
                ('sport', str, verify_port),
                ('in_interface', str, verify_interface_name),
                ('*target', str, None),
                ('src_range', str, verify_ip_range),
                ('dst_range', str, verify_ip_range),
                ('to_source', str, verify_ip_addr),
                ('to_port', str, verify_port),
            ),
            'table': 'nat'
        },
        'dnat': {
            'fields': (
                ('*chain_group_name', str, None),
                ('protocol', str, verify_protocol),
                ('src', str, verify_ip),
                ('dst', str, verify_ip),
                ('comment', str, None),
                ('dport', str, verify_port),
                ('sport', str, verify_port),
                ('in_interface', str, verify_interface_name),
                ('*target', str, None),
                ('to_destination', str, verify_ip_addr),
                ('to_port', str, verify_port)
            ),
            'table': 'nat'
        },
        'filter': {
            'fields': (
                ('*chain_group_name', str, None),
                ('protocol', str, verify_protocol),
                ('src', str, verify_ip),
                ('dst', str, verify_ip),
                ('comment', str, None),
                ('dport', str, verify_port),
                ('sport', str, verify_port),
                ('src_range', str, verify_ip_range),
                ('dst_range', str, verify_ip_range),
                ('in_interface', str, verify_interface_name),
                ('*target', str, None),
            ),
            'table': 'filter'
        }
    }
    if rule_type not in table_field:
        return {
            'code': 1,
            'msg': 'inert rule table is not nat or filter'
        }

    data = filter_user_data(post_data, table_field[rule_type]['fields'])
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
            iptc.easy.insert_rule(table_field[rule_type]['table'], data['chain_group_name'], rule_d=r)

        if action.upper() == 'DELETE':
            iptc.easy.delete_rule(table_field[rule_type]['table'], data['chain_group_name'], rule_d=r)

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
            'msg': 'target not in %s' % str(target_action)
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

    if ('dport' in data and 'protocol' not in data) or ('sport' in data and 'protocol' not in data):
        return {
            'code': 1,
            'msg': 'specific source port or destination port, both protocol must be specified'
        }

    if 'src' in data and 'src_range' in data:
        return {
            'code': 1,
            'msg': 'src and src_range field conflict!'
        }

    if 'dst' in data and 'dst_range' in data:
        return {
            'code': 1,
            'msg': 'dst and dst_range field conflict!'
        }

    if 'src_range' in data and 'dst_range' in data:
        return {
            'code': 1,
            'msg': 'dst_range and src_range field conflict!'
        }

    r = {
        'target': data['target'],
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

    if 'src_range' in data:
        r['iprange'] = {
            'src_range': data['src_range']
        }

    if 'dst_range' in data:
        r['iprange'] = {
            'dst_range': data['dst_range']
        }
    return r


def get_all_interfaces_list() -> list:
    ipdb = IPDB()
    d = ipdb.by_name.keys()
    ipdb.release()
    return d
