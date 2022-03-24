import random

from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotAuthenticated, ParseError, PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from common.functions import get_client_ip
import time

from common.verify import (
    verify_username,
    verify_mail,
    verify_true_false,
    filter_user_data,
    verify_max_length,
    verify_img_verification_code
)


@api_view(('GET',))
def list_all_users_endpoint(request):
    is_admin = False
    username = request.GET.get("username", None)
    if not request.user.is_active:
        raise PermissionDenied('user is state is inactive')

    data = []
    if request.user.is_staff:
        is_admin = True

    if is_admin:
        if username:
            qs = User.objects.filter(username=username)
        else:
            qs = User.objects.all()
    else:
        qs = [request.user]

    i = 1
    for u in qs:
        data.append({
            'id': i,
            'pk': u.id,
            'username': u.username,
            # 'name': u.first_name,
            'state': u.is_active,
            'join_date': u.date_joined,
            'is_staff': u.is_staff,
            'is_superuser': u.is_superuser,
        })
        i += 1

    return Response({
        'code': 0,
        'msg': 'success',
        'data': data
    })


@api_view(('POST',))
@permission_classes((AllowAny,))
def user_login_endpoint(request):
    """
    user login
    """
    fields = (
        ('*username', str, verify_username),
        ('*password', str, (verify_max_length, 30)),
        ('*verify_code', str, verify_img_verification_code)
    )

    data = filter_user_data(request.body, fields)

    user = authenticate(username=data['username'], password=data['password'])
    if not user or not user.is_active:
        raise NotAuthenticated('username or password is wrong!')

    try:
        t = Token.objects.get(user=user)
        tk = t.key
        t.delete()
        cache.delete('token_%s' % tk)
    except Token.DoesNotExist:
        pass
    finally:
        tk, create = Token.objects.update_or_create(user=user)
        cache_request_user_meta_info(tk, request)

    return Response({
        'code': 0,
        'msg': 'success',
        'data': {
            'token': tk.key,
            'user_id': user.pk,
            'username': user.username,
            'first_name': user.username,
        }
    })


@api_view(('POST',))
def change_password_endpoint(request):
    """
    if request.user is superuser then change the password of specified user, else change the password is user itself
    """

    fields = [
        ('*username', str, verify_username),
        ('*pwd1', str, (verify_max_length, 30)),
        ('*pwd2', str, (verify_max_length, 30)),
    ]

    if not request.user.is_superuser:
        fields.append(
            ('*old_pwd', str, (verify_max_length, 30))
        )

    data = filter_user_data(request.body, tuple(fields))

    # 验证两次密码是否一样
    if data['pwd1'] != data['pwd2']:
        raise ParseError(detail='the old and new password is not match!')
    # 超级管理员则查询指定的用户
    if request.user.is_superuser:
        try:
            user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            user = None
    else:
        user = request.user

    if user and user.username != data['username']:
        raise ParseError(detail='error username!')

    if request.user.is_superuser:
        user.set_password(data['pwd1'])
    else:
        if authenticate(username=data['username'], password=data['old_pwd']):
            user.set_password(data['pwd1'])
        else:
            raise ParseError('old password is error!')
    user.save()

    return Response({
        'code': 0,
        'msg': 'success'
    })


@api_view(('PUT', 'POST', 'DELETE'))
@permission_classes((IsAdminUser,))
def set_user_endpoint(request):
    fields = (
        ('*username', str, verify_username),
        ('email', str, verify_mail),
        # ('*first_name', str, verify_username),
        # ('*last_name', str, verify_username),
        ('is_staff', int, verify_true_false),
        ('is_active', int, verify_true_false)
    )

    data = filter_user_data(request.body, fields)

    try:
        tmp = User.objects.get(username=data['username'])
        del data['username']
    except User.DoesNotExist:
        tmp = None

    action_explain = None

    if request.method == 'PUT':
        if tmp:
            raise ParseError('user already exist!')
        char = list('abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        random_pwd = random.sample(char, 6)
        user = User.objects.create_user(
            username=data['username'],
            email= data['email'] if 'email' in data else 'a@b.com',
            password=''.join(random_pwd)
        )
        Token.objects.create(user=user)
        action_explain = 'create user'


    if request.method == 'POST':
        if not tmp:
            raise ParseError('not found this user')

        if tmp.is_superuser:
            raise PermissionDenied('super user can not change!!!')

        if not data:
            raise ParseError('no any change')

        tmp.__dict__.update(**data)
        tmp.save()
        action_explain = 'update user info'

    if request.method == 'DELETE':
        if not tmp:
            raise ParseError('user not exist')

        if tmp.is_superuser:
            raise PermissionDenied('delete user is super user')

        t = Token.objects.filter(user_id=tmp.id)

        if t:
            t.delete()
        tmp.delete()
        action_explain = 'delete user'

    return_data = {
        'code': 0,
        'msg': f'{action_explain} success'
    }
    if request.method == 'PUT':
        return_data['data'] = {'password': ''.join(random_pwd)}
    return Response(return_data)


def cache_request_user_meta_info(token_key, request):
    """
    将请求用户的ip地址、ua、最新使用时间，结合token key写入缓存
    用户登陆时，使用cache中的信息校验
    """
    ua = request.META.get('HTTP_USER_AGENT', 'unknown')
    remote_ip = get_client_ip(request)
    user = Token.objects.get(key=token_key).user

    # write token extra info to cache
    cache.set('token_%s' % token_key, (ua, remote_ip, time.time(), user), 3600)
    # print(cache.get('token_%s' % token_key))

