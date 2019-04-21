# 中间人的地址:
# 如果以rabbitmq作为中间人: 则应该这样写:
# broker_url = 'amqp://用户:密码@IP地址:端口'
broker_url = 'amqp://admin:123456@localhost:5672'


# redis作为中间人:
# broker_url = 'redis://127.0.0.1:6379'