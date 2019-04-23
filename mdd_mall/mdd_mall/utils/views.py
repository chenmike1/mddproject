from django.contrib.auth.decorators import login_required
from django.views import View


class LoginRequiredMixin(View):
    @classmethod
    def as_view(cls, **initkwargs):
        view= super().as_view(**initkwargs)
        return login_required(view)