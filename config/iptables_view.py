import iptc
from iptc.ip4tc import IPTCError
import json
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from .models import ChainGroup
from .models import Rule
from django.db.utils import OperationalError
from pyroute2 import IPDB

from common.verify import (
    verify_port_list,
    verify_ip,
    verify_port,
    verify_ip_range,
    verify_protocol,
    verify_interface_name,
    verify_ip_addr,
    filter_user_data,
    verify_ip_subnet,
    verify_ip_or_ip_port,
    verify_port_range,
    verify_ip_or_ip_range,
    verify_iptables_destination,
    verify_max_length,
)


@api_view(['POST', 'DELETE'])
def set_chain_group_endpoint(request):
    fields = (
        ('*chain_name', str, None),
        ('*table_name', str, None),
        ('*src', str, verify_ip_subnet),
        ('*dst', str, verify_ip_subnet),
        ('in_interface', str, verify_interface_name),
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
        'src': data['src'],
        'dst': data['dst'],
        'target': {
            'goto': data['chain_name']
        }
    }

    if data['chain_name'].startswith('__'):
        raise ParseError('chain name not allow starts with __')

    if data['table_name'] == 'filter' and 'in_interface' in data:
        rule['in-interface'] = data['in_interface']

    root_chain = None
    if data['table_name'] == 'filter':
        root_chain = "FORWARD"

    if data['table_name'] == 'nat' and data['nat_mode'] == 'snat':
        root_chain = 'POSTROUTING'

    if data['table_name'] == 'nat' and data['nat_mode'] == 'dnat':
        root_chain = 'PREROUTING'

    try:
        if request.method == 'POST':
            c = ChainGroup.objects.filter(chain_name=data['chain_name'])
            if c:
                raise ParseError('Chain name is already exist!')
            iptc.easy.add_chain(data['table_name'], data['chain_name'])
            iptc.easy.add_rule(data['table_name'], root_chain, rule_d=rule)
            group_type = data['nat_mode'] if data['table_name'] == 'nat' else 'filter'

            # insert default rule to chain
            # deny all

            # default_rule = {
            #     'src': '0.0.0.0/0',
            #     'target': 'DROP',
            # }
            #
            # iptc.easy.insert_rule(data['table_name'], data['chain_name'], default_rule)

            ChainGroup.objects.create(
                chain_name=data['chain_name'],
                group_type=group_type,
                table_name=data['table_name'],
                src=data['src'],
                dst=data['dst'],
                in_interface=data['in_interface'] if 'in_interface' in data else None
            )

        if request.method == 'DELETE':
            iptc.easy.delete_rule(data['table_name'], root_chain, rule_d=rule)
            iptc.easy.delete_chain(data['table_name'], data['chain_name'], flush=True)

            r = ChainGroup.objects.filter(chain_name=data['chain_name'])
            if r:
                r.delete()
    except (IPTCError, Exception) as e:

        if isinstance(e.args, str):
            raise ParseError(e.args)

        if isinstance(e.args, tuple):
            raise ParseError(e.args[0] if len(e.args) == 1 else e.args[1])

    return Response({
        'code': 0,
        'msg': 'success'
    })


@api_view(('PUT',))
def change_rule_seq_endpoint(request):
    fields = (
        ('*chain_name', str, (verify_max_length, 50)),
        ('old_index', int, None),
        ('new_index', int, None)
    )
    data = filter_user_data(request.body, fields)
    try:
        chain = ChainGroup.objects.get(chain_name=data['chain_name'])
    except ChainGroup.DoesNotExist:
        raise ParseError('not found the chain from system db')

    r_obj = Rule.objects.filter(chain=chain, enable=1)
    x = r_obj.filter(rule_seq=data['old_index'])
    y = r_obj.filter(rule_seq=data['new_index'])

    if not x or not y or len(x) != 1 or len(y) != 1:
        raise ParseError('not found the rule or found multiple rule from system db')

    rule_set = iptc.easy.dump_chain(chain.table_name, chain.chain_name)
    old_rule = rule_set[data['old_index']-1]
    # new_rule = rule_set[data['new_index']-1]
    del old_rule['counters']
    # del new_rule['counters']

    # 删除旧的rule，在新位置添加旧的rule
    # print(data['old_index'])
    # print(data['new_index'])
    # print(old_rule)
    iptc.easy.delete_rule(chain.table_name, chain.chain_name, old_rule)
    iptc.easy.add_rule(chain.table_name, chain.chain_name, rule_d=old_rule, position=data['new_index'])
    # 交换新旧rule序号
    x[0].rule_seq = data['new_index']
    y[0].rule_seq = data['old_index']
    x[0].save()
    y[0].save()
    return Response({
        'msg': 'success'
    })


@api_view(('POST', 'DELETE', 'PUT'))
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
        raise ParseError(detail='illegal rule type!')

    ret = insert_rule(rule_type, j, request, target_list[rule_type])

    return Response({
        'code': 0,
        'msg': 'success',
        'data': ret
    })


def insert_rule(rule_type: str, post_data: dict, request, target_action: tuple) -> dict:
    table_field = {
        'snat': {
            'fields': (
                ('*chain_name', str, None),
                ('protocol', str, verify_protocol),
                ('src', str, verify_ip_subnet),
                ('dst', str, verify_ip_subnet),
                ('comment', str, (verify_max_length, 30)),
                ('dport', str, verify_port_list),
                ('sport', str, verify_port_list),
                ('in_interface', str, verify_interface_name),
                ('out_interface', str, verify_interface_name),
                ('*target', str, None),
                ('src_range', str, verify_ip_range),
                ('dst_range', str, verify_ip_range),
                ('to_source', str, verify_ip_or_ip_range),
                # ('to_ports', str, verify_port),
                ('enable', int, None),
                # ('id', int, None),
            ),
            'table': 'nat'
        },
        'dnat': {
            'fields': (
                ('*chain_name', str, None),
                ('protocol', str, verify_protocol),
                ('src', str, verify_ip_subnet),
                ('dst', str, verify_ip_subnet),
                ('comment', str, (verify_max_length, 30)),
                ('dport', str, verify_port_list),
                ('sport', str, verify_port_list),
                ('in_interface', str, verify_interface_name),
                # ('in_interface', str, verify_interface_name),
                ('*target', str, None),
                ('to_destination', str, verify_iptables_destination),
                ('to_ports', str, verify_port_range),
                ('enable', int, None),
                # ('id', int, None),
            ),
            'table': 'nat'
        },
        'filter': {
            'fields': (
                ('*chain_name', str, None),
                ('protocol', str, verify_protocol),
                ('src', str, verify_ip_subnet),
                ('dst', str, verify_ip_subnet),
                ('comment', str, (verify_max_length, 30)),
                ('dport', str, verify_port_list),
                ('sport', str, verify_port_list),
                ('src_range', str, verify_ip_range),
                ('dst_range', str, verify_ip_range),
                ('in_interface', str, verify_interface_name),
                # ('out_interface', str, verify_interface_name),
                ('*target', str, None),
                ('enable', int, None),
                # ('id', int, None),
            ),
            'table': 'filter'
        }
    }

    if rule_type not in table_field:
        raise ParseError('inert rule table is not nat or filter')

    data = filter_user_data(post_data, table_field[rule_type]['fields'])

    if not iptc.easy.has_chain(table_field[rule_type]['table'], data['chain_name']):
        raise ParseError('illegal chain name')

    chain_name = data['chain_name']
    table_name = table_field[rule_type]['table']

    del data['chain_name']

    try:
        c = ChainGroup.objects.get(
            chain_name=chain_name
        )
    except ChainGroup.DoesNotExist:
        raise ParseError('not found this chain on database')

    try:

        if request.method == 'POST':
            r = build_rule(data, target_action=target_action)
            # print(r)

            if 'code' in r and r['code'] == 1:
                raise ParseError('build rule_d has error, %s' % r['msg'])

            if not iptc.easy.has_rule(table=table_name, chain=chain_name, rule_d=r):
                iptc.easy.add_rule(table_name, chain_name, rule_d=r)

            ret, created = Rule.objects.update_or_create(
                chain=c,
                **data
            )

            if created:
                c.incrase_rule()
                ret.rule_seq = c.rule_count
                ret.save()

        if request.method == 'DELETE':
            # r = None
            # if data['id'] > 0:
            #     r = Rule.objects.get(id=data['id'])
            #     rule_d = build_rule(r.json)
            # else:
            rule_d = build_rule(data)
            # print(r.json)
            # print(rule_d)
            if 'code' in rule_d and rule_d['code'] == 1:
                raise ParseError('build rule_d has error, %s' % rule_d['msg'])

            if iptc.easy.has_rule(table_name, chain_name, rule_d):
                iptc.easy.delete_rule(table_name, chain_name, rule_d)

            r = Rule.objects.filter(**data, chain=c)
            if r and len(r) == 1:
                r.delete()
                c.decrase_rule()
            else:
                raise ParseError('not round record or found multiple record!')

        if request.method == 'PUT':
            # r = Rule.objects.get(id=data['id'])
            # rule_json = r.json
            # rule_d = build_rule(rule_json)
            rule_d = build_rule(data)
            # print(r.json)

            if 'code' in rule_d and rule_d['code'] == 1:
                raise ParseError('build rule failed!, %s' % rule_d['msg'])

            if data['enable'] == 1 and not iptc.easy.has_rule(table_name, chain_name, rule_d):
                iptc.easy.add_rule(table_name, chain_name, rule_d=rule_d)
                # delete origin record
                data['chain_id'] = c.chain_name
                # 下面使用kwargs查询，该记录已经被禁用，操作为启用，需要将查询状态改为禁用
                data['enable'] = 0
                r = Rule.objects.filter(**data)
                # r.delete()
                #
                if r and len(r) == 1:
                    c.incrase_rule()
                    r.update(enable=1, rule_seq=c.rule_count)
                else:
                    iptc.easy.delete_rule(table_name, chain_name, rule_d)
                    raise ParseError('not round record or found multiple record!')
                # 操作结束后将状态改为启用，以免进入下个条件
                data['enable'] = 1

            if data['enable'] == 0 and iptc.easy.has_rule(table_name, chain_name, rule_d):
                iptc.easy.delete_rule(table_name, chain_name, rule_d=rule_d)
                data['enable'] = 1
                data['chain_id'] = c.chain_name
                r = Rule.objects.filter(**data)
                if r and len(r) == 1:
                    r.update(enable=0, rule_seq=-1)
                    c.decrase_rule()
                else:
                    iptc.easy.add_rule(table_name, chain_name, rule_d)
                    raise ParseError('not round record or found multiple record!')
    except Rule.DoesNotExist:
        raise ParseError('not found this rule')

    except ChainGroup.DoesNotExist:
        raise ParseError('not found this chain')

    except OperationalError:
        raise ParseError('system is busy, please try again later!')

    except IPTCError as e:
        raise ParseError(e.args)

    return {
        'code': 0,
        'msg': 'success'
    }


def build_rule(
        data: dict,
        target_action: tuple = ('SNAT', 'DNAT', 'REDIRECT', 'MASQUERADE', 'DROP', 'ACCEPT')) -> dict:

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

    if data['target'] == 'DNAT' and 'to_destination' not in data:
        return {
            'code': 1,
            'msg': 'dnat mode mast be specific to_destination field!'
        }

    if data['target'] == 'REDIRECT' and ('to_ports' not in data or 'protocol' not in data):
        return {
            'code': 1,
            'msg': 'redirect mode mast be specific to_ports and protocol field!'
        }

    if ('dport' in data and 'protocol' not in data) or ('sport' in data and 'protocol' not in data):
        return {
            'code': 1,
            'msg': 'specific source port or destination port(dport), both protocol must be specified'
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

    target = data['target']

    r = dict()

    if 'protocol' in data:
        r['protocol'] = data['protocol']

    if 'in_interface' in data:
        r['in-interface'] = data['in_interface']

    if 'out_interface' in data:
        r['out-interface'] = data['out_interface']

    if target in ('DROP', 'ACCEPT', 'MASQUERADE'):
        r['target'] = target
    else:
        r['target'] = {
            target: dict()
        }

    if 'to_source' in data:
        r['target'][target]['to_source'] = data['to_source']

    if 'to_destination' in data:
        r['target'][target]['to_destination'] = data['to_destination']

    if 'to_ports' in data:
        r['target'][target]['to_ports'] = '%s' % data['to_ports']

    # if 'protocol' in data:
    #     prot = data['protocol']
    if 'sport' in data or 'dport' in data:
        prot = data['protocol']
        r[prot] = dict()
        r['multiport'] = dict()

        if 'dport' in data:
            if ',' in data['dport']:
                r['multiport']['dports'] = '%s' % data['dport'].replace(' ', '')
            else:
                r[prot]['dport'] = '%s' % data['dport']

        if 'sport' in data:
            if ',' in data['sport']:
                r['multiport']['sports'] = '%s' % data['sport'].replace(' ', '')
            else:
                r[prot]['sport'] = '%s' % data['sport']

        if not r['multiport']:
            del r['multiport']

        if not r[prot]:
            del r[prot]

    if 'src' in data:
        r['src'] = data['src']

    if 'dst' in data:
        r['dst'] = data['dst']

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

