from django.shortcuts import render
from django.views import View

# Create your views here.
from contents.models import ContentCategory
from goods.utils import get_categories

class IndexView(View):
    def get(self, request):
        '''
        提供首页页面
        :param request:
        :return:
        '''
        # 1. 获取分类的三级数据
        categiries = get_categories()


        # 2. 获取所有的广告分类
        content_categories = ContentCategory.objects.all()

        # 5. 组织数据
        dict = {}

        # 3. 遍历所有的广告分类, 获取每一个分类
        for cat in content_categories:

            # 4. 根据分类获取广告内容(展示的)
            dict[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories':categiries,
            'contents':dict
        }

        # 6. 返回
        return render(request, 'index.html', context=context)


