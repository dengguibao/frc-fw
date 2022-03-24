from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .serializer import IptablesEvent, IptablesEventSerialize

from django.db.models import Sum, Count

from config.models import Rule, ChainGroup
from config.serializer import Rules
import time
import json
import iptc

ALLOW_POST_HOSTS = (
    '127.0.0.1'
)


@api_view(('GET',))
def get_iptables_chains_endpoint(request):
    group_type = request.GET.get('group_type', None)
    if group_type not in ('snat', 'dnat', 'filter') or not group_type:
        raise ParseError('group type is wrong!')
    data = get_chain_by_type(group_type)
    return Response({
        'code': 0,
        'msg': 'success',
        'data': data
    })


def get_chain_by_type(t: str):
    gt = {
        'snat': {
            'table': 'nat',
            'root_chain': 'POSTROUTING'
        },
        'dnat': {
            'table': 'nat',
            'root_chain': 'PREROUTING',
        },
        'filter': {
            'table': 'filter',
            'root_chain': 'FORWARD'
        }
    }
    chain_group_list = ChainGroup.objects.filter(group_type=t).values_list('chain_name', flat=True)

    result = iptc.easy.dump_chain(table=gt[t]['table'], chain=gt[t]['root_chain'])
    data = []
    index = 1
    for i in result:
        if 'LOG' in i['target']:
            continue
        in_interface = i['in-interface'] if 'in-interface' in i else None
        src = i['src'] if 'src' in i else '0.0.0.0/0'
        dst = i['dst'] if 'dst' in i else '0.0.0.0/0'
        chain_name = i['target']['goto'] if 'goto' in i['target'] else i['target']

        if chain_name.startswith('__SYS_') and chain_name.endswith('__'):
            continue

        if isinstance(chain_name, dict):
            chain_name = list(chain_name.keys())[0]

        if chain_name in ('ACCEPT', 'DROP', 'LOG', 'REJECT'):
            is_rule = True
        else:
            is_rule = False

        data.append({
            'manual': False if chain_name in chain_group_list else True,
            'id': index,
            'in_interface': in_interface,
            'is_rule': is_rule,
            # 'chain_name': chain_name if isinstance(chain_name, str) else list(chain_name.keys())[0],
            'chain_name': chain_name,
            'src': src,
            'dst': dst,
            'table_name': gt[t]['table'],
            'group_type': t,
            'packets': i['counters'][0],
            'bytes': i['counters'][1]
        })
        index += 1
    return data


@api_view(('GET',))
def get_iptables_rules_endpoint(request):
    chain_name = request.GET.get('chain_name', None)
    table_name = request.GET.get('table_name', None)

    if table_name not in ('nat', 'filter'):
        raise ParseError('table name error!')

    if not chain_name or not table_name:
        raise ParseError('illegal request')

    return Response({
        'code': 0,
        'msg': 'success',
        'data': get_rule_by_table_chain(table_name, chain_name)
    })


def get_rule_by_table_chain(table: str, chain: str) -> list:
    try:
        c = ChainGroup.objects.get(chain_name=chain)
    except ChainGroup.DoesNotExist:
        result = None
    else:
        result = Rule.objects.select_related('chain').filter(chain=c, enable=0).order_by('-id')

    if result:
        data = Rules(result, many=True).data
    else:
        data = []

    index = -1
    rule_seq = 1
    for i in iptc.easy.dump_chain(table=table, chain=chain):

        target = i['target']

        to_ports = to_source = to_destination = None
        if target in ('DROP', 'ACCEPT', 'MASQUERADE', 'RETURN', 'REJECT', 'QUEUE'):
            pass
        else:
            t = list(target.keys())[0]
            target = t
            to_source = i['target'][t]['to-source'] if 'to-source' in i['target'][t] else None
            to_destination = i['target'][t]['to-destination'] if 'to-destination' in i['target'][t] else None
            to_ports = i['target'][t]['to-ports'] if 'to-ports' in i['target'][t] else None

        in_interface = i['in-interface'] if 'in-interface' in i else None
        out_interface = i['out-interface'] if 'out-interface' in i else None

        dst = i['dst'] if 'dst' in i else '0.0.0.0/0'
        src = i['src'] if 'src' in i else '0.0.0.0/0'

        protocol = i['protocol'] if 'protocol' in i else None
        comment = i['comment']['comment'] if 'comment' in i else None
        counters = i['counters']

        sport = dport = None
        if 'multiport' in i:
            if 'sports' in i['multiport']:
                sport = ','.join(i['multiport']['sports'])
            if 'dports' in i['multiport']:
                dport = ','.join(i['multiport']['dports'])

        if protocol and protocol.lower() in ('tcp', 'udp'):
            if protocol in i:
                sport = i[protocol]['sport'] if 'sport' in i[protocol] else None
                dport = i[protocol]['dport'] if 'dport' in i[protocol] else None

        data.append({
            'rule_seq': rule_seq,
            'chain_name': chain,
            'id': index,
            'target': target,
            'protocol': protocol,
            'src': src,
            'dst': dst,
            'sport': sport,
            'dport': dport,
            'in_interface': in_interface,
            'out_interface': out_interface,
            'comment': comment,
            'to_ports': to_ports,
            'to_destination': to_destination,
            'to_source': to_source,
            'enable': 1,
            'packets': counters[0],
            'bytes': counters[1]
        })
        index -= 1
        rule_seq += 1

    return data


@api_view(('GET',))
def iptables_chain_aggregation_endpoint(request):
    rule_aggr = ChainGroup.objects.all().values_list('group_type').annotate(Sum('rule_count'))
    chain_aggr = ChainGroup.objects.all().values_list('group_type').annotate(Count('id'))

    def build_data(d):
        data = []
        for i in d:
            data.append({
                'name': i[0],
                'value': i[1]
            })
        return data

    return Response({
        'code': 0,
        'message': 'success',
        'data': {
            'rule': build_data(rule_aggr),
            'chain': build_data(chain_aggr)
        }
    })


@api_view(('GET', 'POST'))
def iptables_event_endpoint(request):

    if request.method == 'GET':
        size = request.GET.get('size', 10)
        cur_page = request.GET.get('page', 1)

        page = PageNumberPagination()
        page.page_size = size
        page.number = cur_page
        page.max_page_size = 20

        all_record = IptablesEvent.objects.all()
        ret = page.paginate_queryset(
            all_record, request
        )
        ser = IptablesEventSerialize(ret, many=True)
        return Response({
            'code': 0,
            'message': 'success',
            'data': ser.data,
            'page_info': {
                'record_count': len(all_record),
                'page_size': int(size),
                'current_page': page.page.number
            }
        })

    if request.method == 'POST':
        remote_addr = request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT')
        if remote_addr not in ALLOW_POST_HOSTS or 'python-urllib' not in ua.lower():
            return Response({
                'code': 1
            })
        try:
            req_data = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return Response({
                'msg': 'request body is not a json'
            })

        try:
            IptablesEvent.objects.create(**req_data)
        except:
            raise ParseError({
                'msg': 'request body struct error!'
            })

        return Response({
            'code': 0,
            'msg': 'success'
        })


# @api_view(('GET',))
# def iptables_event_aggregation_endpoint(request):
#     result = IptablesEvent.objects.filter(ts__gt=(time.time()-86400*11)).extra(
#         {'ts': 'date(ts, "unixepoch")'}
#     ).values('ts').annotate(session_total=Count('ts'))
#     return Response({
#         'code': 0,
#         'msg': 'success',
#         'data': result
#     })
