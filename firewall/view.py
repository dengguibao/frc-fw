from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
import json
from django.contrib.auth import authenticate

from common.functions import (
    verify_necessary_field
)


def read_api_ref_endpoint(request):
    """
    open readme on web browser
    """
    fp = open('api_ref.md', 'rb')
    response = FileResponse(fp)
    return response


@api_view(('POST', ))
def user_login_endpoint(request):
    """
    user login
    """
    try:
        j = json.loads(request.body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request body'
        }, status=status.HTTP_400_BAD_REQUEST)

    data = verify_necessary_field(j, ('*username', '*password'))
    if not data:
        return Response({
            'code': 1,
            'msg': 'some require field is mission!'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=data['username'], password=data['password'])
    if not user and not user.is_active:
        return Response({
            'code': 1,
            'msg': 'username or password is wrong!'
        }, status=status.HTTP_400_BAD_REQUEST)

    token, created = Token.objects.get_or_create(user=user)
    return Response({
        'code': 0,
        'msg': 'success',
        'data': {
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
        }
    })
