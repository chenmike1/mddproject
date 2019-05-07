from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):

    def save(self, name, content, max_length=None):
        # 创建客户端对象:
        client = Fdfs_client(settings.FDFS_CLIENT_CONF)

        result = client.upload_by_buffer(content.read())
        if result.get('Status') == 'Upload successed.':

            file_id = result.get('Remote file_id')

            return file_id

        else:

            raise Exception('上传失败')

    def exists(self, name):
        '''
        判断当前要传入的图片是否已存在
        :param name:
        :return:
        '''
        return False

    def url(self, name):
        return settings.FDFS_URL + name