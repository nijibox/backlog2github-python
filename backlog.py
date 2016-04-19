# -*- coding:utf8 -*-
"""Backlog v2 API
"""
import re
import os
import shutil
import requests
import yaml
from urllib import unquote


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


class Project(Model):
    @classmethod
    def from_api(cls, project_key, api):
        data = api.request('/projects/' + project_key).json()
        instance = cls(api, data)
        return instance

    def get_issues(self, params={}):
        params['projectId[]'] = self._data['id']
        resp = self._api.request('/issues', params).json()
        issues = []
        for issue in resp:
            issues.append(Issue(self._api, issue, parent=self))
        return issues


class Issue(Model):
    def init_workspace(self, base_dir):
        self.work_dir = '{}/{}'.format(base_dir, self._data['issueKey'])
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        self.comments_dir = '{}/{}'.format(self.work_dir, 'comments')
        if not os.path.exists(self.comments_dir):
            os.makedirs(self.comments_dir)
        self.attachment_dir = '{}/{}'.format(self.work_dir, 'attachments')
        if not os.path.exists(self.attachment_dir):
            os.makedirs(self.attachment_dir)

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

    def download_attatchments(self, save_dir=None):
        if save_dir is None:
            save_dir = self.attachment_dir
        attachments = self.get_attachments()
        for attachment in attachments:
            attachment.download(save_dir)

    def dump_all(self):
        detail_path = os.path.join(self.work_dir, 'Detail.yml')
        with open(detail_path, 'w') as fp:
            yaml.safe_dump(self._data, fp, allow_unicode=True, default_flow_style=False)
        # Dump comments
        comments = self.get_comments()
        for comment in comments:
            comment_path = os.path.join(self.comments_dir, '{}.yml'.format(comment._data['id']))
            with open(comment_path, 'w') as fp:
                yaml.safe_dump(comment._data, fp, allow_unicode=True, default_flow_style=False)
        # Dump attachments
        self.download_attatchments()


class Comment(Model):
    pass


class Attachment(Model):
    def download(self, save_dir):
        resp = self._api.request(
            '/issues/{}/attachments/{}'.format(self._parent._data['id'], self._data['id'])
            )
        d = resp.headers['content-disposition']
        fname = re.findall("''(.+)", d)
        save_path = '{}/{}'.format(save_dir, unquote(fname[0]))
        with open(save_path, 'wb') as fp:
            for chunk in resp.iter_content(1024):
                fp.write(chunk)
