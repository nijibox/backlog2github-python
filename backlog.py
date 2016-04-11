# -*- coding:utf8 -*-
"""Backlog v2 API
"""
import re
import shutil
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

    def get_issues(self, params={}):
        path = '/issues'
        return self.request(path, params).json()

    def get_issue(self, key, params={}):
        path = '/issues/{}'.format(key)
        resp = self.request(path, params).json()
        return Issue(self, resp)


class Model(object):
    def __init__(self, api, data, parent=None):
        self._api = api
        self._data = data
        self._parent = parent

    def __gettattr__(self, key):
        if key in self._data:
            return self._data[key]
        return super(Model, self).__gettattr__(key)


class Project(Api):
    @classmethod
    def from_api(cls, project_key, api):
        resp = api.request('/projects/' + project_key)
        instance = cls(api.space_id, api.api_key)
        instance.project_id = resp['id']
        return instance

    def get_issues(self, params={}):
        params['projectId[]'] = self.project_id
        return super(Project, self).get_issues(params).json()


class Issue(Model):
    def get_comments(self):
        path = '/issues/{}/comments'.format(self._data['id'])
        resp = self._api.request(path, params={}, method='GET').json()
        comments = []
        for comment in resp:
            comments.append(Comment(self._api, comment, parent=self))
        return comments

    def get_attachments(self):
        path = '/issues/{}/attachments'.format(self._data['id'])
        resp = self._api.request(path, params={}, method='GET').json()
        attachments = []
        for attachment in resp:
            attachments.append(Attachment(self._api, attachment, parent=self))
        return attachments


class Comment(Model):
    pass


class Attachment(Model):
    def download(self, save_dir):
        resp = self._api.request(
            '/issues/{}/attachments/{}'.format(self._parent._data['id'], self._data['id'])
            )
        d = resp.headers['content-disposition']
        fname = re.findall("''(.+)", d)
        save_path = '{}/{}'.format(save_dir, fname[0])
        with open(save_path, 'wb') as fp:
            for chunk in resp.iter_content(1024):
                fp.write(chunk)
