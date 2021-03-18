from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.contrib.auth.models import User
import json
from django.contrib.auth import authenticate
import time
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


from common.verify import (
    verify_field,
    verify_username,
    verify_mail,
    verify_true_false
)


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

    token, create = Token.objects.get_or_create(user=user)

    if not create:
        token_create_ts = token.created.timestamp()
        if time.time() - token_create_ts > 86400:
            token.delete()
            token = Token.objects.create(user=user)

    return Response({
        'code': 0,
        'msg': 'success',
        'data': {
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
        }
    })


@api_view(('POST',))
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
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
        try:
            user = User.objects.get(username=data['username'])
        except:
            pass
    else:
        user = request.user
        # user = User.objects.get(username='te2st')

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


@api_view(('POST', 'DELETE'))
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

    # if not request.user.is_superuser:
    #     return Response({
    #         'code': 0,
    #         'msg': 'illegal request'
    #     }, status=status.HTTP_400_BAD_REQUEST)

    try:
        tmp = User.objects.get(username=data['username'])
    except:
        tmp = None

    if request.method == 'POST':
        if not tmp:
            user = User.objects.create_user(**data)
            status_code = status.HTTP_201_CREATED
            # new add user, create token
            Token.objects.create(user=user)
        else:
            User.objects.update(**data)
            status_code = status.HTTP_200_OK

    if request.method == 'DELETE':
        if not tmp:
            status_code = status.HTTP_400_BAD_REQUEST
            return Response({
                'code': 1,
                'msg': 'user not exist'
            }, status=status_code)

        status_code = status.HTTP_200_OK
        t = Token.objects.filter(user_id=tmp.id)
        if t:
            t.delete()
        tmp.delete()

    return Response({
        'code': 0,
        'msg': 'success'
    }, status=status_code)
