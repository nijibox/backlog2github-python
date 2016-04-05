# -*- coding:utf8 -*-
"""Backlog v2 API
"""
import requests


class Api(object):
    """docstring for BacklogApi"""
    def __init__(self, space_id, api_key=None):
        self.space_id = space_id
        self.api_key = api_key
        self.session = requests.Session()

    @property
    def endpoint_url(self):
        return 'https://{}.backlog.jp/api/v2'.format(
            self.space_id,
        )

    def request(self, path, params={}, method='GET'):
        if not path.startswith('/'):
            # raise Exception('Request path must be started /')
            path = '/' + path
        url = '{}{}'.format(self.endpoint_url, path)
        if self.api_key is not None:
            if method != 'GET':
                params['apiKey'] = self.api_key
            else:
                url = '{}?apiKey={}'.format(url, self.api_key)
        session_method = getattr(self.session, method.lower())
        return session_method(url, params=params)
