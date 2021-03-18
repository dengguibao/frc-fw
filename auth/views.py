from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
import json
from django.contrib.auth import authenticate

from common.verify import (
    verify_field,
    verify_username,
    verify_mail,
    verify_true_false
)


# Create your views here.


@api_view(('POST',))
def user_login_endpoint(request):
    """
    user login
    """
    try:
        j = json.loads(request.body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*username', str, verify_username),
        ('*password', str, None)
    )

    data = verify_field(j, fields)
    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data
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


def change_password_endpoint(request):
    """
    if request.user is superuser then change the password of specified user, else change the password is user itself
    """
    try:
        j = json.loads(request.body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*username', str, verify_username),
        ('*password1', str, None),
        ('*password2', str, None)
    )

    data = verify_field(j, fields)

    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data
        }, status=status.HTTP_400_BAD_REQUEST)

    if data['password1'] != data['password2']:
        return Response({
            'code': 1,
            'msg': 'the old and new password is not match!'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = None
    if request.user.is_superuser:
        tmp = User.objects.get(username=data['username'])
        if tmp:
            user = tmp
    else:
        user = request.user

    if user and user.username != data['username']:
        return Response({
            'code': 1,
            'msg': 'error username!'
        }, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(data['password1'])
    user.save()

    return Response({
        'code': 1,
        'msg': 'success'
    }, status=status.HTTP_400_BAD_REQUEST)


def set_user_endpoint(request):
    try:
        j = json.loads(request.body.decode())
    except:
        return Response({
            'code': 1,
            'msg': 'illegal request, body format error'
        }, status=status.HTTP_400_BAD_REQUEST)

    fields = (
        ('*username', str, verify_username),
        ('*email', str, verify_mail),
        ('*first_name', str, verify_username),
        ('*last_name', str, verify_username),
        ('is_superuser', int, verify_true_false),
        ('is_active', int, verify_true_false)
    )

    data = verify_field(j, fields)

    if not isinstance(data, dict):
        return Response({
            'code': 1,
            'msg': data,
        }, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.is_superuser:
        return Response({
            'code': 0,
            'msg': 'illegal request'
        }, status=status.HTTP_400_BAD_REQUEST)

    tmp = User.objects.get(username=data['username'])
    if tmp:
        del data['username']

    if request.method == 'POST':
        user = User.objects.update_or_create(**data)
        if not tmp:
            status_code = status.HTTP_201_CREATED
            # new add user, create token
            Token.objects.create(user=user)
        else:
            status_code = status.HTTP_200_OK

    if request.method == 'DELETE':
        status_code = status.HTTP_200_OK
        if not tmp:
            return Response({
                'code': 0,
                'msg': 'user not exist'
            }, status=status_code)
        Token.objects.filter(user=tmp).delete()
        User.objects.filter(username=data['username']).delete()

    return Response({
        'code': 0,
        'msg': 'success'
    }, status=status_code)
