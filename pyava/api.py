from typing import List, Tuple, Dict
from urllib.parse import urljoin
import json
import requests

from pyava import *

class AvaClient:
    def __init__(self, url=None, session=None):
        '''
        Creates an instance of the client

        :param url: The URL where avalanchego node is running
        :param session: A requests Session used to make API calls
        '''
        self.url = url or 'http://localhost:9650'
        self.session = session or requests

    def call(self, path, method, **kwargs):
        payload = {
            "method": method,
            "params": kwargs,
            "jsonrpc": "2.0",
            "id": 0,
        }
        res = self.session.post(urljoin(self.url, path), json=payload).json()
        if 'error' in res:
            raise RuntimeError(res['error']['message'])
        return res['result']

    def ethcall(self, method, params):
        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": 0
        }
        res = self.session.post(urljoin(self.url, 'ext/bc/C/rpc'), json=payload).json()
        return res['result']

defaultClient = AvaClient()
