import iptc
import json
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from common.functions import (
    verify_netmask,
    ip2MaskPrefix,
    verify_ip,
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
    if data['table_name'] not in ('nat', 'filter'):
        return Response({
            'code': 1,
            'msg': 'table type error!'
        }, status=status.HTTP_400_BAD_REQUEST)

    if data['table_name'] == 'nat' and 'nat_mode' not in data and data['nat_mode'] not in ('snat', 'dnat'):
        return Response({
            'code': 1,
            'msg': 'nat need specific mode!'
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
def get_chains_endpoint(request):
    table_name = request.GET.get('table_name', None)
    data = None
    if table_name:
        data = get_chains_by_table(table_name)

    if not data:
        return Response({
            'code': 0,
            'msg': 'table name error',
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'code': 0,
        'msg': 'success',
        'data': data
    }, status=status.HTTP_200_OK)


def insert_rule_to_chain_endpoint(request):
    req_body = request.body
    try:
        j = json.loads(req_body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'request body error!'
        }, status=status.HTTP_400_BAD_REQUEST)

    data = verify_necessary_field(j, ('*chain_name', '*table_name', 'nat_mode'))
    pass


def get_chains_by_table(table_name):
    try:
        d = iptc.easy.dump_table(table_name, ipv6=False)
    except:
        return False
    return d.keys()
