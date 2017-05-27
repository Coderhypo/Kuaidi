import requests
from config import API_KEY
from requests.exceptions import HTTPError

DEFAULT_TIMEOUT_SECONDS = 10


class Client(requests.Session):

    def __init__(self, timeout=DEFAULT_TIMEOUT_SECONDS):
        super(Client, self).__init__()
        self.base_url = "http://apis.baidu.com/netpopo/express"
        self._timeout = timeout
        self._headers = {"Content-Type": "application/json", "apikey": "{}".format(API_KEY)}
        self.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

    def _set_request_timeout(self, kwargs):
        kwargs.setdefault('timeout', self._timeout)
        kwargs.setdefault('headers', self._headers)
        return kwargs

    def _get(self, url, **kwargs):
        return self.get(url, **self._set_request_timeout(kwargs))

    def get_all_express(self):
        url = "{}{}".format(self.base_url, "/express2")
        rsp = self._get(url)
        rsp.raise_for_status()
        rsp_json = rsp.json()
        result = rsp_json['result']
        return result

    def get_package(self, code, number):
        url = "{}{}".format(self.base_url, "/express1")
        params = {
            "type": code,
            "number": number,
        }
        rsp = self._get(url, params=params)
        rsp.raise_for_status()
        rsp_json = rsp.json()
        result = rsp_json['result']
        status = rsp_json['status']
        if int(status) != 0:
            raise
        return result


