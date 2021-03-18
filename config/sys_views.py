from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
import json
from common.verify import verify_field, verify_true_false


@api_view(('POST',))
def set_forward_state_endpoint(request):
    try:
        j = json.loads(request.body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*state', str, verify_true_false),
    )
    data = verify_field(j, fields)

    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data
        }, status=status.HTTP_400_BAD_REQUEST)

    with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
        f.write(data['state'])

    return Response({
        'code': 0,
        'msg': 'success',
    }, status=status.HTTP_200_OK)
