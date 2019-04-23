import re

from django.contrib.auth.backends import ModelBackend
from django.db.models import QuerySet

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
