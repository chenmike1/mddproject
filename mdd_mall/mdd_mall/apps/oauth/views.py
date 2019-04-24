import re

from django import http
from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here.
from QQLoginTool.QQtool import OAuthQQ
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from mdd_mall.apps.oauth.utils import generate_access_token, check_access_token
from users.models import User
from .models import OAuthQQUser
from mdd_mall.utils.response_code import RETCODE

import logging

logger = logging.getLogger('django')


class QQURLView(View):
    def get(self, request):
        next = request.GET.get('next')
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        qq_url = oauth.get_qq_url()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'login_url': qq_url})


class QQUserView(View):
    def get(self, request):
        code = request.GET.get('code')
        logger.info(code)
        if not code:
            return http.HttpResponseForbidden('缺少参数')
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            access_token = oauth.get_access_token(code)
            open_id = oauth.get_open_id(access_token)
        except Exception as e:
            return http.HttpResponseServerError('OAuth2.0认证失败')

        try:
            oauthqq = OAuthQQUser.objects.get(openid=open_id)

        except:
            ct_access_token = generate_access_token(open_id)
            context = {
                'access_token': ct_access_token
            }
            return render(request, 'oauth_callback.html', context)
        else:
            state = request.GET.get('state')
            qq_username = oauthqq.user.username
            qq_user = oauthqq.user
            login(request, qq_user)
            response=redirect(state)
            response.set_cookie('username', qq_username, max_age=3600 * 24 * 15)
            return response

    def post(self, request):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code = request.POST.get('sms_code')
        access_token = request.POST.get('access_token')

        if not all([mobile, password, sms_code, access_token]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        redis_conn = get_redis_connection('verify_code')
        redis_data = redis_conn.get('%s_%s' % (sms_code, mobile))
        if not redis_data:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})

        if redis_data.decode() != sms_code:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '验证码错误'})

        token = check_access_token(access_token)

        if not token:
            return http.HttpResponseForbidden('token错误')

        token=token.get('client_open_id')


        try:
            user = User.objects.get(mobile=mobile)
        except:
            cur_user=User.objects.create_user(username=mobile,password=password,mobile=mobile)
            OAuthQQUser.objects.create(user=cur_user, openid=token)
            cook_name=cur_user.username

        else:
            if user.check_password():
                cur_user=OAuthQQUser.objects.create(user=user,openid=token)
                cook_name = cur_user.user.username
            else:
                return render(request, 'oauth_callback.html', {'account_errmsg': '密码错误'})
        login(request,cur_user)

        response=redirect(reverse('contents:index'))
        response.set_cookie('username',cook_name)

        return response

