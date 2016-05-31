# -*- coding:utf8 -*-
"""Backlog v2 API
"""
import re
import os
import shutil
import requests
import yaml
from urllib import unquote
import time


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
            if method == 'GET':
                params['apiKey'] = self.api_key
            else:
                url = '{}?apiKey={}'.format(url, self.api_key)
        if method == 'GET':
            return self.session.get(url, params=params)
        elif method == 'POST':
            return self.session.post(url, data=params)
        elif method == 'PATCH':
            return self.session.patch(url, data=params)
        else:
            return None
        # print(session_method)
        # return session_method(url, params=params)

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
        self._dirty = {}
        self._parent = parent

    def __contains__(self, key):
        return key in self._data or key in self._dirty

    def __getitem__(self, key):
        return self._dirty.get(key, self._data[key])

    def __setitem__(self, key, value):
        self._dirty[key] = value


class Project(Model):
    @classmethod
    def from_api(cls, project_key, api):
        data = api.request('/projects/' + project_key).json()
        instance = cls(api, data)
        return instance

    def get_issues(self, params={}):
        params['projectId[]'] = self['id']
        resp = self._api.request('/issues', params).json()
        issues = []
        for issue in resp:
            issues.append(Issue(self._api, issue, parent=self))
        return issues

    def count_wiki(self):
        """Wikiページを取得する
        """
        params = {'projectIdOrKey': self['id']}
        resp = self._api.request('/wikis/count', params).json()
        return int(resp['count'])

    def get_wikis(self):
        """
        """
        params = {'projectIdOrKey': self['id']}
        resp = self._api.request('/wikis', params).json()
        wikis = []
        for wiki_ in resp:
            wikis.append(self.get_wiki(wiki_['id']))
        return wikis


    def get_wiki(self, wiki_id):
        """
        """
        resp = self._api.request('/wikis/{}'.format(wiki_id), {}).json()
        return Wiki(self._api, resp, parent=self)


class Issue(Model):
    def init_workspace(self, base_dir):
        self.work_dir = '{}/{}'.format(base_dir, self['issueKey'])
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        self.comments_dir = '{}/{}'.format(self.work_dir, 'comments')
        if not os.path.exists(self.comments_dir):
            os.makedirs(self.comments_dir)
        self.attachment_dir = '{}/{}'.format(self.work_dir, 'attachments')
        if not os.path.exists(self.attachment_dir):
            os.makedirs(self.attachment_dir)

    def get_comments(self):
        path = '/issues/{}/comments'.format(self['id'])
        resp = self._api.request(path, params={}, method='GET').json()
        comments = []
        for comment in resp:
            comments.append(Comment(self._api, comment, parent=self))
        return comments

    def get_attachments(self):
        path = '/issues/{}/attachments'.format(self['id'])
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
            comment_path = os.path.join(self.comments_dir, '{}.yml'.format(comment['id']))
            with open(comment_path, 'w') as fp:
                yaml.safe_dump(comment._data, fp, allow_unicode=True, default_flow_style=False)
        # Dump attachments
        time.sleep(0.1)
        self.download_attatchments()


class Comment(Model):
    pass


class Attachment(Model):
    def download(self, save_dir):
        resp = self._api.request(
            '/issues/{}/attachments/{}'.format(self._parent['id'], self['id'])
            )
        d = resp.headers['content-disposition']
        fname = re.findall("''(.+)", d)
        save_path = '{}/{}'.format(save_dir, unquote(fname[0]))
        with open(save_path, 'wb') as fp:
            for chunk in resp.iter_content(1024):
                fp.write(chunk)


class Wiki(Model):
    def save(self):
        if 'content' not in self._dirty:
            return
        path = '/wikis/{}'.format(self['id'])
        params = {
            'name': self['name'],
            'content': self['content'],
        }
        resp = self._api.request(path, params=params, method='PATCH')
        if resp.status_code == 200:
            self._data['content'] = self._dirty['content']
            del self._dirty['content']
            print('OK')
            return
        return

    def dump(self, save_dir):
        dump_path = os.path.join(save_dir, self['name']) + '.yml'
        dump_dir = os.path.dirname(dump_path)
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)
        with open(dump_path, 'w') as fp:
            yaml.safe_dump(self._data, fp, allow_unicode=True, default_flow_style=False)

    def get_attachments(self):
        path = '/wikis/{}/attachments'.format(self['id'])
        resp = self._api.request(path, params={}, method='GET').json()
        attachments = []
        for attachment in resp:
            attachments.append(WikiAttachment(self._api, attachment, parent=self))
        return attachments

    def download_attatchments(self, save_dir=None):
        if save_dir is None:
            save_dir = os.path.join(save_dir, self['name']) + '.files'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        attachments = self.get_attachments()
        for attachment in attachments:
            attachment.download(save_dir)


class WikiAttachment(Model):
    def download(self, save_dir):
        resp = self._api.request(
            '/wikis/{}/attachments/{}'.format(self._parent['id'], self['id'])
            )
        d = resp.headers['content-disposition']
        fname = re.findall("''(.+)", d)
        save_path = '{}/{}'.format(save_dir, unquote(fname[0]))
        with open(save_path, 'wb') as fp:
            for chunk in resp.iter_content(1024):
                fp.write(chunk)
