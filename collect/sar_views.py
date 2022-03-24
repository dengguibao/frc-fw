import time
import json
import shutil

from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from common.common import RESOURCE_MODELS
from common.functions import get_client_ip
from collect.models import IptablesEvent
from common.functions import timeRange2Seconds

ALLOW_POST_HOSTS = (
    '127.0.0.1', '10.10.4.3'
)


@api_view(['GET', 'POST'])
def get_disk_usage_endpoint(request):
    usage = shutil.disk_usage('/')
    return Response({
        'code': 0,
        'msg': 'success',
        'data': {
            'total': usage[0],
            'used': usage[1],
            'free': usage[2],
            'util': round(usage[1]/usage[0], 2)
        }
    })


@api_view(['GET', 'POST'])
def sar_info_endpoint(request, name):
    """
    list collect resources
    :param request:
    :param name: resource name
    :return:
    """
    if name not in RESOURCE_MODELS:
        raise ParseError("invalid resource")

    model = RESOURCE_MODELS[name]['model']
    serialize = RESOURCE_MODELS[name]['serialize']

    if request.method == 'GET':
        time_range = request.GET.get('time_range', None)
        if time_range:
            time_range_seconds = timeRange2Seconds(time_range)
            if time_range_seconds:
                start_time = int(time.time()) - time_range_seconds
                data = model.objects.filter(time__gt=start_time).all()
            else:
                raise ParseError('date format error')
        else:
            data = model.objects.all()[0:1]

        response_data = serialize(data, many=True)
        return_data = {
            'code': 0,
            'msg': 'success',
            'data': response_data.data
        }
        return Response(return_data)

    elif request.method == 'POST':
        client_ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT')
        if client_ip not in ALLOW_POST_HOSTS or 'python-urllib' not in ua.lower():
            raise ParseError('illegal request')

        post_content = request.body.decode()
        # print(post_content)
        post_data = serialize(data=json.loads(post_content))
        if post_data.is_valid():
            post_data.save()
            # print(post_data.data)
            return Response({
                'code': 0,
                'name': name,
                'msg': 'success'
            }, status=HTTP_201_CREATED)

        raise ParseError('post data stract error!')


@api_view(['GET'])
def clean_sar_data_endpoint(request):
    yesterday = int(time.time() - 86400)
    # ua = request.META.get('HTTP_USER_AGENT')
    for k in RESOURCE_MODELS:
        if RESOURCE_MODELS[k]['type'] == 'sar':
            RESOURCE_MODELS[k]['model'].objects.all().delete()

    return Response({
        'code': 0,
        'msg': 'success'
    })


@api_view(['GET'])
def clear_iptables_event(request):
    end_ts = int(time.time() - (86400*15))

    client_ip = get_client_ip(request)
    # ua = request.META.get('HTTP_USER_AGENT')
    if client_ip not in ALLOW_POST_HOSTS:
        raise ParseError('illegal request!')

    IptablesEvent.objects.filter(ts__lt=end_ts).delete()
    return Response({
        'code': 0,
        'msg': 'success'
    }, status=HTTP_201_CREATED)
