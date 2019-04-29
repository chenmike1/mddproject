from django import http
from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from django.views import View
from .models import Area

from mdd_mall.utils.response_code import RETCODE


class ProvinceAreasView(View):
    def get(self,request):
        province_list = cache.get('province_list')
        if not province_list:
            try:
                province_model_list = Area.objects.filter(parent__isnull=True)
                province_list = []
                for province_model in province_model_list:
                    province_list.append({'id': province_model.id, 'name': province_model.name})
                cache.set('province_list',province_list,3600)
            except:
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '省份数据错误'})
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})


class SubAreasView(View):
    def get(self,request,pk):
        sub_data = cache.get('sub_data'+pk)
        if not sub_data:
            try:
                p_area = Area.objects.get(id=pk)
                subs_area = p_area.subs.all()
                subs_list = []
                for sub_model in subs_area:
                    subs_list.append({'id': sub_model.id, 'name': sub_model.name})
                sub_data = {
                    'id': p_area.id,  # 父级pk
                    'name': p_area.name,  # 父级name
                    'subs': subs_list  # 父级的子集
                }
                cache.set('sub_data'+pk,sub_data,3600)
            except:
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '城市或区数据错误'})
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})