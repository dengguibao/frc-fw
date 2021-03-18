import time
import json

from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from common.common import RESOURCE_MODELS
from common.functions import timeRange2Seconds

ALLOW_POST_HOSTS = (
    '127.0.0.1'
)


@api_view(['GET', 'POST'])
def sar_info_endpoint(request, name):
    """
    list collect resources
    :param request:
    :param name: resource name
    :return:
    """
    if name not in RESOURCE_MODELS:
        return Response({
            'code': 1,
            'msg': "invalid resource"
        }, status=status.HTTP_400_BAD_REQUEST)

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
                return Response({
                    'code': 1,
                    'msg': 'date format error'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = model.objects.all()[0:1]

        response_data = serialize(data, many=True)
        return_data = {
            'code': 0,
            'msg': 'success',
            'data': response_data.data
        }
        return Response(return_data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        remote_addr = request.META.get('REMOTE_ADDR')
        if remote_addr not in ALLOW_POST_HOSTS:
            return Response({
                'code': 1,
                'msg': 'illegal request'
            }, status=status.HTTP_403_FORBIDDEN)

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
            }, status=status.HTTP_201_CREATED)

        return Response({
            'code': 1,
            'name': name,
            'msg': post_data.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def clean_sar_data_endpoint(request):
    yesterday = int(time.time() - 86400)
    for k in RESOURCE_MODELS:
        if RESOURCE_MODELS[k]['type'] == 'sar':
            RESOURCE_MODELS[k]['model'].objects.filter(time__lt=yesterday).delete()
    return Response({
        'code': 0,
        'msg': 'success'
    }, status=status.HTTP_200_OK)