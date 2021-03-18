from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from common.functions import get_chain_groups


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