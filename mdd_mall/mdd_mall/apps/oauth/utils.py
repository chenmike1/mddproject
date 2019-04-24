import itsdangerous

from mdd_mall.settings.dev import SECRET_KEY


def generate_access_token(openid):
    serializer=itsdangerous.TimedJSONWebSignatureSerializer(SECRET_KEY,300)
    data={
        'client_open_id':openid
    }
    client_token = serializer.dumps(data)

    return client_token.decode()



def check_access_token(access_token):
    serializer=itsdangerous.TimedJSONWebSignatureSerializer(SECRET_KEY,300)
    try:
        ser_data = serializer.loads(access_token)
    except:
        return None
    else:
        return ser_data
