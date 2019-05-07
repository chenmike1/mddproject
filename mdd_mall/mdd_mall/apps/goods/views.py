import datetime

from django import http
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage

# Create your views here.
from django.utils import timezone
from django.views import View

from .utils import get_categories, get_breadcrumb, get_goods_and_spec
from .models import GoodsCategory, SKU, GoodsVisitCount


class ListView(View):
    def get(self, request, category_id, page_num):
        sort = request.GET.get('sort', 'default')
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except:
            return http.HttpResponseNotFound('GoodsCategory 不存在')
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category)
        if sort == 'price':
            sortkind = 'price'
        elif sort == 'hot':
            sortkind = '-sales'
        else:
            sortkind = 'create_time'
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sortkind)
        paginator = Paginator(skus, 5)
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseNotFound('not found')
        total_page=paginator.num_pages
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'page_skus':page_skus,
            'total_page':total_page,
            'page_num':page_num,
            'category':category

        }
        return render(request, 'list.html', context=context)


class HotGoodsView(View):

    def get(self, request, category_id):
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        hot_skus=[]
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'name':sku.name,
                'price':sku.price
            })

        return http.JsonResponse({'code':'ok','errmsg':'ok','hot_skus':hot_skus})


class DetailView(View):

    def get(self,request,sku_id):
        categories = get_categories()
        data=get_goods_and_spec(sku_id,request)
        goods = data.get('goods')
        goods_specs = data.get('goods_specs')
        sku = data.get('sku')
        context={
            'categories':categories,
            'sku':sku,
            'goods':goods,
            'goods_specs':goods_specs
        }
        return render(request,'detail.html',context=context)

class DetailVisitView(View):
    def post(self,request,category_id):
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except:
            return http.HttpResponseForbidden('缺少必传参数')

        time = timezone.localdate()
        today_str='%d-%02d-%02d'%(time.year,time.month,time.day)
        today_date=datetime.datetime.strptime(today_str,'%Y-%m-%d')
        try:
            counts_data = category.goodsvisitcount_set.get(date=today_date)
        except:
            counts_data = GoodsVisitCount()
        try:
            counts_data.category=category
            counts_data.count+=1
            counts_data.save()
        except:
            return http.HttpResponseServerError('服务器异常')
        return http.JsonResponse({'code': 'ok', 'errmsg': 'OK'})