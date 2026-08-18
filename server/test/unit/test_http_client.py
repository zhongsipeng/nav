from src.app.common.utils.client_util import HttpClient

with HttpClient(timeout=10) as client:
    res = client.get("https://blog.csdn.net/favicon.ico")
    res2 = client.get("https://blog.csdn.net/shaochenshuo/article/details/128735528")
    print(res.content)
    print(res2.content)
