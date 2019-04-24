import re

from django import http
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from mdd_mall.utils.views import LoginRequiredMixin
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

        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=15 * 24 * 3600)
        return response



class UsernameCountView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': 'ok', 'errmsg': RETCODE.OK, 'count': count})


class MobileCountView(View):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': 'ok', 'errmsg': RETCODE.OK, 'count': count})


class LoginView(View):
    def get(self,request):
        return render(request,'login.html')

    def post(self,request):
        username=request.POST.get('username')
        password=request.POST.get('password')
        remembered=request.POST.get('remembered')

        if not all([username,password]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')

        user = authenticate(username=username, password=password)
        if user is None:
            return render(request,'login.html',{'account_errmsg':'用户名密码错误'})

        login(request,user)
        if remembered!='on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        next = request.GET.get('next')
        if next:
            response=redirect(next)
            response.set_cookie('username',user.username,max_age=15*24*3600)
        else:
            response=redirect(reverse('contents:index'))
            response.set_cookie('username',user.username,max_age=15*24*3600)
        return response

class LogoutView(View):
    def get(self,request):
        logout(request)
        response=redirect(reverse('contents:index'))
        response.delete_cookie('username')
        return response


class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):
        return render(request,'user_center_info.html')