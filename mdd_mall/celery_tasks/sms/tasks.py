from celery_tasks.main import celery_app

# bind=True:  第一个参数就是self
# name = '一般是函数名':  没有用,但是必须要配
# retry_backoff=3: 失败后再次尝试的次数
# from celery_tasks.yuntongxun.ccp_sms import CCP
from mdd_mall.libs.yuntongxun.ccp_sms import CCP


@celery_app.task(bind=True, name='send_sms_code', retry_backoff=3)
def send_sms_code(self, mobile, sms_code):

    # 发送短信:
    try:
        result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
        # print('celery has run')
        # result=0
    except Exception as e:
        raise self.retry(exc=e, max_retries=3)

    if result != 0:
        raise self.retry(exc=Exception('发送短信失败'), max_retries=3)

    return result