from rest_framework.decorators import api_view
from rest_framework.response import Response
from common.verify import verify_true_false, filter_user_data


@api_view(('POST',))
def set_forward_state_endpoint(request):
    fields = (
        ('*state', str, verify_true_false),
    )
    data = filter_user_data(request.body, fields)

    with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
        f.write(data['state'])

    return Response({
        'code': 0,
        'msg': 'success',
    })
