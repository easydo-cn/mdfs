# encoding: utf-8

import os
import json
import time
import threading
from os.path import expanduser

_local = threading.local()

SESSION_DIR = os.path.join(expanduser("~") + ".mdfs-sessions")

class BaseDevice:

    def __init__(self, name, title='', options={}):
        self.name = name
        self.title = title
        self.options = options

    def gen_key(self, prefix='', suffix=''):
        """ 生成一个未用的key """

    def stat(self, key):
        """ state of a key
        {    "fsize":        5122935,
            #"hash":         "ljfockr0lOil_bZfyaI2ZY78HWoH",
            "mimeType":     "application/octet-stream",
            "putTime":      13603956734587420
        }"""

    def put_data(self, key, data):
        """ 直接存储一个数据，适合小文件 """

    def copy_data(self, from_key, to_key):
        """ 直接存储一个数据，适合小文件 """

    def multiput_new(self, key, size):
        """ 开始一个多次写入会话, 返回会话ID"""

    def multiput_offset(self, session_id):
        """ 会话写入位置 """

    def multiput(self, session_id, data, offset):
        """ 多次写入会话 """

    def multiput_save(self, session_id):
        """ 保存、完结会话 """

    def multiput_delete(self, session_id):
        """ 删除一个写入会话 """

    def remove(self, key):
        """ 删除key文件 """

    def get_data(self, key):
        """ 根据key返回文件内容，不适合大文件 """

    def get_stream(self, key):
        """ 返回文件的一个stream对象，可以通过iterator来逐步得到文件，适合大文件 """

class StorageDeviceManager:
    """ 支持缓存多设备的文件存储管理器 """

    def __init__(self, session_dir=SESSION_DIR):

        self.devices = dict()
        self.sessions = Sessions(session_dir=session_dir)

    def add(self, device, cache_device):
        self.devices[device.name] = (device, cache_device)

    def get_cache_device(self, name):
        device, cache_device = self.devices[name]
        return cache_device

    def gen_key(self, name, prefix='', suffix=''):
        """ 生成一个未用的key """
        device, cache_device = self.devices[name]
        return device.gen_key(prefix, suffix)

    def get_cache_key(self, key, mime='', subpath=''):
        mime = mime.replace('/', '_')
        return key + '.' + mime + '/' + subpath

    def os_path(self, name, key):
        device, cache_device = self.devices[name]
        return device.os_path(key)

    #def cache_os_path(self, name, key):
    #    device, cache_device = self.devices[name]
    #    return cache_device.os_path(key)

    def exists(self, name, key):
        device, cache_device = self.devices[name]
        return device.exists(key)

    def stat(self, name, key):
        device, cache_device = self.devices[name]
        return device.stat(key)

    def remove(self, name, key):
        """ 删除一个文件，同时删除缓存 """
        device, cache_device = self.devices[name]
        device.remove(key)
        # TODO 需要删除所有的缓存
        cache_device.remove(self.get_cache_key(key))

    def move(self, name, key, new_key):
        """ 更换key """
        device, cache_device = self.devices[name]
        device.move(key, new_key)
        # TODO 需要移动所有的缓存
        cache_key = self.get_cache_key(key)
        if cache_device.exists(cache_key):
            cache_device.move(cache_key, self.get_cache_key(new_key))

    def get_data(self, name, key, offset=0, size=-1):
        """ 读取数据 """
        device, cache_device = self.devices[name]
        return device.get_data(key, offset, size)

    def _t_add(self, name, key):
        if getattr(_local, 'put_files', None) is None:
            _local.put_files = [(name, key)]
        else:
            _local.put_files.append((name, key))

    def commit(self):
        """ 完结一个写入线程 """
        #print 'commit mdfs', getattr(_local, 'put_files', [])
        for (name, key) in getattr(_local, 'put_files', []):
            self.sessions.delete(name, key)
        _local.put_files = []

    def abort(self):
        """ 删除一个写入会话 """
        for (name, key) in getattr(_local, 'put_files', []):
             self.remove(name, key)
             self.sessions.delete(name, key)
        _local.put_files = []

    def cleanup(self, expire):
        """ 删除超时没有保存文件的中间文件 """
        for session in self.sessions.query(expire=expire):
            self.abort(session['device'], session['key'])
            if session.get('session_id'):
                self.multiput_delete(session['device'], session['session_id'])
            else:
                self.remove(session['device'], session['key'])

    def put_data(self, name, key, data, mime_type=None, auto_commit=False):
        """ 存储数据 """
        device, cache_device = self.devices[name]
        device.put_data(key, data)
        if not auto_commit:
            self.sessions.new(name, key)
            self._t_add(name, key)

    def put_stream(self, name, key, stream, mime_type=None, auto_commit=False):
        """ 存储数据 """
        device, cache_device = self.devices[name]
        device.put_stream(key, stream)
        if not auto_commit:
            self.sessions.new(name, key)
            self._t_add(name, key)

    def copy_data(self, name, from_key, to_key, auto_commit=False):
        """ 直接存储一个数据，适合小文件 """
        device, cache_device = self.devices[name]
        device.copy_data(from_key, to_key)
        if not auto_commit:
            self.sessions.new(name, to_key)
            self._t_add(name, to_key)

    def multiput_new(self, name, key, size=-1, mime_type=None):
        """ 开始一个多次写入会话, 返回会话ID"""
        device, cache_device = self.devices[name]
        session = device.multiput_new(key, size)
        self.sessions.new(name, key, session_id=session)
        self._t_add(name, key)
        return session

    def multiput_offset(self, name, session_id):
        """ 会话写入位置 """
        device, cache_device = self.devices[name]
        return device.multiput_offset(session_id)

    def multiput(self, name, session_id, data, offset=None):
        """ 多次写入会话 """
        device, cache_device = self.devices[name]
        return device.multiput(session_id, data, offset)

    def multiput_delete(self, name, session_id):
        """ 删除会话 """
        device, cache_device = self.devices[name]
        return device.multiput_delete(session_id)

    def multiput_save(self, name, session_id):
        """ 保存、完结会话 """
        device, cache_device = self.devices[name]
        key = device.multiput_save(session_id)
        self.sessions.update(name, key, session_id='')
        return key

class Sessions:

    def __init__(self, session_dir='/var/session'):
        self.tmp = session_dir
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)

    def os_path(self, device, key):
        upload_session = device+'-'+key
        upload_session = upload_session.replace('\\', '-').replace('/', '').replace(':', '-')
        return os.path.join(self.tmp, upload_session)

    def new(self, device, key, **kwargs):
        session = {
            'device': device,
            'key': key,
        }
        session.update(kwargs)
        with open(self.os_path(device, key), 'w') as f:
            json.dump(session, f)

    def load(self, device, key):
        with open(self.os_path(device, key)) as f:
            return json.load(f)

    def delete(self, device, key):
        os.remove(self.os_path(device, key))

    def update(self, device, key, **kwargs):
        session = self.load(device, key)
        session.update(kwargs)
        with open(self.os_path(device, key), 'w') as f:
            json.dump(session, f)

    def query(self, expire=None):
        for upload_session in os.listdir(self.tmp):
            fpath = self.os_path(upload_session)
            if os.path.isfile(fpath) and (expire is None or time.time() - os.path.getmtime(fpath) > expire):
                yield self.load(upload_session)

