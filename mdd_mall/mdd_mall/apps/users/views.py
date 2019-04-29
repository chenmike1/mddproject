import json
import re

from django import http
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url, check_verify_email_token
from mdd_mall.utils.views import LoginRequiredMixin, LoginRequiredJSONMixin
from .models import User, Address
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
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')

        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名密码错误'})

        login(request, user)
        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=15 * 24 * 3600)
        return response


class LogoutView(View):
    def get(self, request):
        logout(request)
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')
        return response


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        username = request.user.username
        mobile = request.user.mobile
        email = request.user.email
        email_active = request.user.email_active
        context = {
            'username': username,
            'mobile': mobile,
            'email': email,
            'email_active': email_active
        }

        return render(request, 'user_center_info.html', context=context)


class EmailView(LoginRequiredJSONMixin, View):
    def put(self, request):
        json_email = json.loads(request.body.decode())
        email = json_email.get('email')

        if not email:
            return http.HttpResponseForbidden('缺少email参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')

        try:
            request.user.email = email
            request.user.save()
        except:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
        else:
            verify_url = generate_verify_email_url(request.user)
            send_verify_email.delay(email, verify_url)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


class VerifyEmailView(View):
    def get(self, request):
        token = request.GET.get('token')
        if not token:
            return http.HttpResponseForbidden('token lacked')
        user = check_verify_email_token(token)
        if not user:
            return http.HttpResponseForbidden('bad token')
        try:
            user.email_active = True
            user.save()
        except:
            return http.HttpResponseServerError('激活邮件失败')
        return redirect(reverse('users:info'))


class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        addresses = Address.objects.filter(user=request.user, is_deleted=False)
        address_dict_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            default_address = request.user.default_address
            if address == default_address:
                address_dict_list.insert(0, address_dict)
            else:
                address_dict_list.append(address_dict)
        context = {
            'default_address_id': request.user.default_address_id,
            'addresses': address_dict_list,
        }
        return render(request, 'user_center_site.html', context)


class CreateAddressView(LoginRequiredJSONMixin, View):
    def post(self, request):
        count = Address.objects.filter(user=request.user).count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})
        # logger.info(count)

        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver, place, mobile, province_id, city_id, district_id]):
            return http.HttpResponseForbidden('parameters lacked')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        try:
            address = Address.objects.create(
                user=request.user,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                title=receiver,
                receiver=receiver,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': 'save error'})
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):

    def put(self, request, address_id):
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})

        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': '更新地址成功',
                                  'address': address_dict})

    def delete(self,request,address_id):
        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted=True
            address.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})
        else:
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址success'})

class DefaultAddressView(LoginRequiredJSONMixin,View):
    def put(self,request,address_id):
        try:
            request.user.default_address_id=address_id
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})
        else:
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(LoginRequiredJSONMixin,View):
    def put(self,request,address_id):
        json_data=json.loads(request.body.decode())
        title=json_data.get('title')
        try:
            address = Address.objects.get(id=address_id)
            address.title=title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '修改title失败'})
        else:
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改title成功'})

class ChangePasswordView(LoginRequiredMixin,View):
    def get(self,request):
        return render(request,'user_center_pass.html')

    def post(self,request):
        old_password = request.POST.get('old_pwd')
        new_password = request.POST.get('new_pwd')
        new_password2 = request.POST.get('new_cpwd')

        if not all([old_password,new_password,new_password2]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            pwd_flag = request.user.check_password(old_password)
        except Exception as e:
            return http.HttpResponseForbidden('检查发生错误')
        else:
            if not pwd_flag:
                return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
            if new_password2!=new_password:
                return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '两次输入的密码不一致'})
            if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
                return http.HttpResponseForbidden('密码最少8位，最长20位')
        try:
            request.user.set_password(new_password)
            request.user.save()
        except:
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})
        else:
            logout(request)
            response=redirect(reverse('users:login'))
            response.delete_cookie('username')
            return response
