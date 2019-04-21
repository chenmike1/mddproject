import re

from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from .models import User
# from mdd_mall.apps.users.models import User
from mdd_mall.utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('mobile')
        sms_code = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        if not all([username, password, password2, phone, allow]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名格式不对')

        if not re.match('^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码格式不对')

        if not re.match('^1[345789]\d{9}$', phone):
            return http.HttpResponseForbidden('电话格式不对')

        if allow != 'on':
            return http.HttpResponseForbidden('没同意协议')

        redis_conn = get_redis_connection('verify_code')
        check_redis = redis_conn.get('%s_%s' % (sms_code, phone))
        if check_redis is None:
            return render(request, 'register.html', {'sms_code_errmsg': '验证码过期'})
        if check_redis.decode() != sms_code:
            return render(request, 'register.html', {'sms_code_errmsg': '验证码错误'})

        try:
            user = User.objects.create_user(username=username, password=password, mobile=phone)
        except Exception as e:
            logger.error(e)
            return render(request, 'register.html', {'register_errmsg': '保存失败'})

        login(request, user)

        return redirect(reverse('contents:index'))


class UsernameCountView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': 'ok', 'errmsg': RETCODE.OK, 'count': count})


class MobileCountView(View):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': 'ok', 'errmsg': RETCODE.OK, 'count': count})
