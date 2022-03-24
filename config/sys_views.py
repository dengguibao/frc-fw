from iptc.ip4tc import IPTCError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from common.verify import verify_true_false, filter_user_data, verify_max_length, verify_ip_addr
from django.conf import settings
from .models import SysSetting
import iptc

from ipsetpy import ipset_add_entry, ipset_list, ipset_test_entry, ipset_del_entry

tg = {
    'snat': {
        'table': 'nat',
        'chain': 'POSTROUTING'
    },
    'dnat': {
        'table': 'nat',
        'chain': 'PREROUTING',
    },
    'forward': {
        'table': 'filter',
        'chain': 'FORWARD'
    }
}


def set_ping_func(v: bool) -> bool:
    rule_d = {'protocol': 'icmp', 'icmp': {'icmp-type': '8'}, 'target': 'ACCEPT' if v else 'REJECT'}
    if not iptc.easy.has_rule('filter', '__SYS_DEFAULT_RULE__', rule_d):
        iptc.easy.add_rule('filter', '__SYS_DEFAULT_RULE__', rule_d)
        try:
            n_rule_d = {'protocol': 'icmp', 'icmp': {'icmp-type': '8'}, 'target': 'REJECT' if v else 'ACCEPT'}
            iptc.easy.delete_rule('filter', '__SYS_DEFAULT_RULE__', n_rule_d)
        except:
            pass
    return True


def set_ssh_rule_func(v: bool) -> bool:
    target = 'ACCEPT' if v else 'REJECT'
    input_rule_d = {'protocol': 'tcp', 'tcp': {'dport': '22'}, 'target': target}
    output_rule_d = {'protocol': 'tcp', 'tcp': {'sport': '22'}, 'target': target}

    if not iptc.easy.has_rule('filter', 'INPUT', input_rule_d):
        iptc.easy.insert_rule('filter', 'INPUT', input_rule_d)
        try:
            input_rule_d['target'] = 'REJECT' if v else 'ACCEPT'
            iptc.easy.delete_rule('filter', 'INPUT', input_rule_d)
        except:
            pass

    if not iptc.easy.has_rule('filter', 'OUTPUT', output_rule_d):
        iptc.easy.insert_rule('filter', 'OUTPUT', output_rule_d)
        try:
            output_rule_d['target'] = 'REJECT' if v else 'ACCEPT'
            iptc.easy.delete_rule('filter', 'OUTPUT', output_rule_d)
        except:
            pass

    return True


def set_forward_state(v: bool) -> bool:
    fp = open('/proc/sys/net/ipv4/ip_forward', 'w+')
    try:
        if v:
            fp.write('1')
        else:
            fp.write('0')
    except OSError:
        raise False
    finally:
        fp.close()
    return True


def record_iptables_event(value: bool, t: str) -> bool:
    try:
        log_rule_d = {
            'src': '!127.0.0.1/32',
            'dst': '0.0.0.0/0',
            'target': {
                'LOG': {
                    'log_prefix': '%s%s ' % (settings.IPTABLES_PREFIX, t.upper()),
                    'log_level': '%s' % settings.IPTABLES_LOG_LEVEL
                }
            }
        }
        table_name = tg[t]['table']
        chain_name = tg[t]['chain']

        if value is True and not iptc.easy.has_rule(table_name, chain_name, rule_d=log_rule_d):
            iptc.easy.insert_rule(table_name, chain_name, log_rule_d)

        if value is False and iptc.easy.has_rule(table_name, chain_name, log_rule_d):
            iptc.easy.delete_rule(tg[t]['table'], tg[t]['chain'], log_rule_d)

    except IPTCError:
        return False

    return True


# def query_iptables_log_func(t):
#     try:
#         rule = iptc.easy.get_rule(tg[t]['table'], tg[t]['chain'])
#         first_rule = json.dumps(rule[0]['target'], ensure_ascii=False)
#         log_rule_d = '{"LOG": {"log-prefix": "%s%s ", "log-level": "%s"}}' % (
#             settings.IPTABLES_PREFIX, t.upper(), settings.IPTABLES_LOG_LEVEL
#         )
#         if log_rule_d == first_rule:
#             return True
#         return False
#     except:
#         return False


@api_view(('GET', 'POST'))
def sys_setting_endpoint(request):
    if request.method == 'GET':
        return Response({
            'msg': 'success',
            'data': [i.json for i in SysSetting.objects.all()]
        })

    if request.method == 'POST':
        fields = (
            ('*item', str, (verify_max_length, 20)),
            ('*value', bool, verify_true_false),
        )
        data = filter_user_data(request.body, fields)
        try:
            res = SysSetting.objects.get(item=data['item'])
        except SysSetting.DoesNotExist:
            raise ParseError('not found this config item')

        if data['value'] == res.value:
            raise ParseError('not change')

        update_func_map = (
            ('sys_forward', set_forward_state, data['value'], None),
            ('sys_ping_func', set_ping_func, data['value'], None),
            ('set_ssh_rule_func', set_ssh_rule_func, data['value'], None),
            # ('iptables_snat_log', record_iptables_event, data['value'], 'snat'),
            # ('iptables_dnat_log', record_iptables_event, data['value'], 'dnat'),
            # ('iptables_foward_log', record_iptables_event, data['value'], 'forward'),
        )

        for k, func, arg1, arg2 in update_func_map:
            if res.item == k:
                if not arg2:
                    update_result = func(arg1)
                else:
                    update_result = func(arg1, arg2)
            else:
                continue

            if update_result:
                res.value = data['value']
                res.save()
                break

        return Response({
            'code': 0,
            'msg': 'success'
        })


@api_view(('GET', 'POST', 'PUT', 'DELETE'))
def ip_set_endpoint(request):
    t = request.GET.get('type', None)
    if t not in ('whitelist', 'blacklist'):
        raise ParseError('error type!')

    if request.method == 'GET':
        return Response({
            'msg': 'success',
            'data': get_all_record_form_ipset(t)
        })

    if request.method == 'POST':
        fields = (
            ('*ip', str, verify_ip_addr),
            ('timeout', int, None)
        )
        data = filter_user_data(request.body, fields)
        if ipset_test_entry(t, data['ip']):
            raise ParseError('the ip already exist!')

        ipset_add_entry(t, data['ip'], entry_timeout=data['timeout'] if 'timeout' in data else 0)
        return Response({
            'code': 0,
            'msg': 'success'
        })

    if request.method == 'PUT':
        fields = (
            ('*ip', str, verify_ip_addr),
            ('timeout', int, None)
        )
        data = filter_user_data(request.body, fields)
        if not ipset_test_entry(t, data['ip']):
            raise ParseError('the ip not exist!')

        ipset_add_entry(t, data['ip'], entry_timeout=data['timeout'] if 'timeout' in data else 0, exist=True)
        return Response({
            'code': 0,
            'msg': 'success'
        })

    if request.method == 'DELETE':
        fields = (
            ('*ip', str, verify_ip_addr),
        )
        data = filter_user_data(request.body, fields)
        if not ipset_test_entry(t, data['ip']):
            raise ParseError('the ip not exist!')

        ipset_del_entry(t, data['ip'], exist=True)
        return Response({
            'code': 0,
            'msg': 'success'
        })


def get_all_record_form_ipset(name: str) -> list:
    if name not in ('blacklist', 'whitelist'):
        return []

    data = []
    index = 1
    for i in ipset_list(name).splitlines():
        if ':' in i or i.strip() == '':
            continue
        else:
            result = i.split()
            data.append({
                'id': index,
                'ip': result[0],
                'timeout': result[2] if len(result) >= 2 else None
            })
            index += 1
    return data
