from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotAuthenticated, ParseError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from common.verify import filter_user_data
from common.verify import (
    verify_username,
    verify_mail,
    verify_true_false
)


@api_view(('POST',))
@permission_classes((AllowAny,))
def user_login_endpoint(request):
    """
    user login
    """
    fields = (
        ('*username', str, verify_username),
        ('*password', str, None)
    )

    data = filter_user_data(request.body, fields)

    user = authenticate(username=data['username'], password=data['password'])
    if not user or not user.is_active:
        raise NotAuthenticated('username or password is wrong!')

    try:
        Token.objects.get(user=user).delete()
    except Token.DoesNotExist:
        pass
    finally:
        t, create = Token.objects.get_or_create(user=user)

    return Response({
        'code': 0,
        'msg': 'success',
        'data': {
            'token': t.key,
            'user_id': user.pk,
            'username': user.username,
        }
    })


@api_view(('POST',))
def change_password_endpoint(request):
    """
    if request.user is superuser then change the password of specified user, else change the password is user itself
    """
    fields = (
        ('*username', str, verify_username),
        ('*password1', str, None),
        ('*password2', str, None)
    )

    data = filter_user_data(request.body, fields)

    if data['password1'] != data['password2']:
        raise ParseError('the old and new password is not match!')

    if request.user.is_superuser or request.user.is_staff:
        try:
            user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            user = None
    else:
        user = request.user

    if user and user.username != data['username']:
        raise ParseError('error username!')

    user.set_password(data['password1'])
    user.save()

    return Response({
        'code': 1,
        'msg': 'success'
    })


@api_view(('POST', 'DELETE'))
@permission_classes((IsAdminUser,))
def set_user_endpoint(request):
    fields = (
        ('*username', str, verify_username),
        ('*email', str, verify_mail),
        ('*first_name', str, verify_username),
        ('*last_name', str, verify_username),
        ('is_staff', int, verify_true_false),
        ('is_active', int, verify_true_false)
    )

    data = filter_user_data(request.body, fields)

    try:
        tmp = User.objects.get(username=data['username'])
        del data['username']
    except User.DoesNotExist:
        tmp = None

    if request.method == 'POST':
        if not tmp:
            user = User.objects.create_user(**data)
            # new add user, create token
            Token.objects.create(user=user)
        else:
            User.objects.update(**data)

    if request.method == 'DELETE':
        if not tmp:
            raise ParseError('user not exist')

        t = Token.objects.filter(user_id=tmp.id)
        if t:
            t.delete()
        tmp.delete()

    return Response({
        'code': 0,
        'msg': 'success'
    })
