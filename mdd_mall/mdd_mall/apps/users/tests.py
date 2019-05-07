import base64
import pickle
from django.test import TestCase

# Create your tests here.
if __name__ == '__main__':
    testdata={
        "sku_id1":{
            "count":"1",
            "selected":"True"
        },
        "sku_id3":{
            "count":"3",
            "selected":"True"
        },
        "sku_id5":{
            "count":"3",
            "selected":"False"
        }
    }

    base = base64.b64encode(pickle.dumps(testdata)).decode()
    print(base)
    data = pickle.loads(base64.b64decode(base.encode()))
    print(data)
