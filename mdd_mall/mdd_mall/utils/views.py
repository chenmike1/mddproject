from django import http
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import wraps

from mdd_mall.utils.response_code import RETCODE


class LoginRequiredMixin(View):
    @classmethod
    def as_view(cls, **initkwargs):
        view= super().as_view(**initkwargs)
        return login_required(view)



def login_required_json(view_func):
    """
    判断是否登录，以json格式返回
    :param view_func:
    :return:
    """
    @wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})
        return view_func(request,*args,**kwargs)

    return wrapper


class LoginRequiredJSONMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view= super().as_view(**initkwargs)
        return login_required_json(view)