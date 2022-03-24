from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from .models import Vip
from pyroute2 import IPDB
from .serializer import VipSerialize

from common.verify import (
    verify_ip_range,
    verify_max_length,
    verify_in_array,
    filter_user_data
)


@api_view(('GET', 'POST', 'PUT', 'DELETE'))
def set_vip_set_endpoints(request):
    fields = (
        ('*name', str, (verify_max_length, 20)),
        ('*isp', str, (verify_max_length, 20)),
        ('*state', str, (verify_in_array, ('e', 'd'))),
        ('*ip_range', str, verify_ip_range),
    )

    if request.method == 'GET':
        res = Vip.objects.all()
        ser = VipSerialize(res, many=True)
        return Response({
            'msg': 'success',
            'data': ser.data
        })

    if request.method == 'POST':
        data = filter_user_data(request.body, fields)
        Vip.objects.create(**data)
        return Response({
            'code': 0,
            'msg': 'success'
        })

    if request.method == 'PUT':
        _id = request.GET.get('id', 0)
        assert _id, ParseError('illegal id')
        try:
            o = Vip.objects.filter(pk=_id)
        except Vip.DoesNotExist:
            raise ParseError('not found that record')
        data = filter_user_data(request.body, fields)
        o.update(**data)
        return Response({'code': 0, 'msg': 'success'})

    if request.method == 'DELETE':
        _id = request.GET.get('id', 0)
        assert _id, ParseError('illegal id')
        try:
            o = Vip.objects.filter(pk=_id)
        except Vip.DoesNotExist:
            raise ParseError('not found that record')
        o.delete()
        return Response({'code': 0, 'msg': 'success'})


@api_view(('GET',))
def get_all_vip_address_endpoint(request):
    data = []
    res = Vip.objects.filter(state='e').values('name', 'ip_range')
    for i in res:
        ip_range = i.get('ip_range').split('-')
        tmp = '.'.join(ip_range[0].split('.')[:-1]) + '.%s'

        try:
            start = int(ip_range[0].split('.')[-1])
            end = int(ip_range[1].split('.')[-1])
        except (IndexError, ValueError):
            break
        data.append({
            'label': i['name'],
            'value': i['name'],
            'children': build_all_ip(tmp, start, end)
        })

    ipdb = IPDB()
    for i in ipdb.by_name.keys():
        x = ipdb.interfaces[i]
        if x['ipaddr']:
            ip_addr = x['ipaddr'][0]['local']
        else:
            ip_addr = None

        data.append(
            {
                'label': x['ifname'],
                'value': x['ifname'],
                'children': [
                    {
                        'value': ip_addr,
                        'label': ip_addr,
                    }
                ]
            }
        )
    ipdb.release()

    return Response({'data': data})


def build_all_ip(tmp: str, s: int, e: int):
    data = [{
        'value': tmp % s + '-' + tmp % e,
        'label': tmp % s + '-' + tmp % e
    }]

    for i in range(s, e + 1):
        data.append({
            'value': tmp % i,
            'label': tmp % i
        })
    return data
