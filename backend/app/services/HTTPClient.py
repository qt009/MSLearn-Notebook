import httpx
import json
class HTTPClient():
    @staticmethod
    def get(url):
        try:
            res = httpx.get(url)
            return res.content
        except httpx.HTTPError as e:
            print(e)