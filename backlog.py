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
        return session_method(url, params=params).json()

    def get_issues(self, params={}):
        path = '/issues'
        return self.request(path, params)

    def get_issue(self, key, params={}):
        path = '/issues/{}'.format(key)
        return self.request(path, params)

class Project(Api):
    @classmethod
    def from_api(cls, project_key, api):
        resp = api.request('/projects/' + project_key)
        instance = cls(api.space_id, api.api_key)
        instance.project_id = resp['id']
        return instance

    def get_issues(self, params={}):
        params['projectId[]'] = self.project_id
        return super(Project, self).get_issues(params)
