import random

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from mdd_mall.libs.captcha.captcha import captcha
from mdd_mall.utils.response_code import RETCODE
from celery_tasks.sms.tasks import send_sms_code

import logging

logger = logging.getLogger('django')


class ImageCodeView(View):
    def get(self, request, uuid):
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % uuid, 300, text)
        return http.HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    def get(self, request, mobile):
        image_code = request.GET.get('image_code')
        image_code_id = request.GET.get('image_code_id')



        if not all([image_code, image_code_id]):
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})

        redis_conn = get_redis_connection('verify_code')
        redis_str = redis_conn.get('img_%s' % image_code_id)
        redis_flag = redis_conn.get(mobile)
        if redis_str is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码超时'})

        redis_str = redis_str.decode().lower()
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except Exception as e:
            logger.error(e)

        if redis_str != image_code.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '验证码错误'})

        if redis_flag != None:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '访问过于频繁'})

        rand_int = '%06d' % random.randint(0, 999999)
        logger.info(rand_int)
        # redis_conn = get_redis_connection('verify_code').pipeline()
        # redis_conn.setex('%s_%s' % (rand_int, mobile), 300, rand_int)
        # redis_conn.setex('%s' % mobile, 60, 1)
        # redis_conn.execute()

        # send_sms_code.delay(mobile,rand_int)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
