import re

from django.contrib.auth.backends import ModelBackend
from itsdangerous import TimedJSONWebSignatureSerializer
from django.db.models import QuerySet

from mdd_mall.settings.dev import SECRET_KEY, EMAIL_VERIFY_URL
from .models import User
import logging

logger = logging.getLogger('django')


def get_user_by_account(account):
    user_get = User.objects.filter(mobile=account)
    if len(user_get) == 0:
        user_get = user_get if user_get else User.objects.filter(username=account)
        if len(user_get) == 0:
            return None
        else:
            return user_get[0]
    else:
        return user_get[0]


class UsernameMobileAuthBackend(ModelBackend):
    # def authenticate(self, request, username=None, password=None, **kwargs):
    #     user=get_user_by_account(username)
    #
    #     if user and user.check_password(password):
    def authenticate(self, request, username=None, password=None, **kwargs):
        return super().authenticate(request, get_user_by_account(username), password, **kwargs)



def generate_verify_email_url(user):
    serializer = TimedJSONWebSignatureSerializer(SECRET_KEY, expires_in=300)
    data={
        'user_id':user.id,
        'email':user.email
    }
    token=serializer.dumps(data).decode()
    verify_url=EMAIL_VERIFY_URL+'?token='+token
    return verify_url


def check_verify_email_token(token):
    serializer = TimedJSONWebSignatureSerializer(SECRET_KEY, expires_in=300)
    try:
        data = serializer.loads(token)
    except:
        return None
    else:
        user_id=data.get('user_id')
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id, email=email)
        except:
            return None
        else:
            return user



