# encoding: utf-8

import threading

_local = threading.local()


class BaseDevice:

    def __init__(self, name, title='', options={}):
        self.name = name
        self.title = title
        self.options = options

    def gen_key(self, prefix='', suffix=''):
        """ 生成一个未用的key """

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

    def multiput_save(self, session_id, key):
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

    def __init__(self):
        self.devices = dict()

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
        return key + '/.frs.' + mime + '/' + subpath

    def os_path(self, name, key):
        device, cache_device = self.devices[name]
        return device.os_path(key)

    def cache_os_path(self, name, key):
        device, cache_device = self.devices[name]
        return cache_device.os_path(key)

    def remove(self, name, key):
        """ 删除一个文件，同时删除缓存 """
        device, cache_device = self.devices[name]
        device.remove(key)
        # TODO 需要删除所有的缓存
        cache_device.remove(self.get_cache_key(key))

    def get_data(self, name, key):
        """ 读取数据 """
        device, cache_device = self.devices[name]
        return device.get_data(key)

    def get_stream(self, name, key):
        """ 读取数据流 """
        device, cache_device = self.devices[name]
        return device.get_stream(key)

    def start_put_transaction(self):
        """ 开始一个写入线程 """
        if getattr(_local, 'put_files', None) is None:
            setattr(_local, 'put_files', [])

    def abort_put_transaction(self):
        """ 废弃一个写入线程 """
        for device, key in threading.local.put_files:
            self.remove(device, key)
        _local.put_files = None

    def commit_put_transaction(self):
        """ 完结一个写入线程 """
        _local.put_files = None

    def put_data(self, name, key, data):
        """ 存储数据 """
        device, cache_device = self.devices[name]
        if getattr(_local, 'put_files', None) is not None:
            _local.put_files.append((name, key))
        return device.put_data(key, data)

    def copy_data(self, name, from_key, to_key):
        """ 直接存储一个数据，适合小文件 """
        device, cache_device = self.devices[name]
        if getattr(_local, 'put_files', None) is not None:
            _local.put_files.append((name, to_key))
        return device.copy_data(from_key, to_key)

    def multiput_new(self, name, key, size):
        """ 开始一个多次写入会话, 返回会话ID"""
        device, cache_device = self.devices[name]
        return device.multiput_new(key, size)

    def multiput_offset(self, name, session_id):
        """ 会话写入位置 """
        device, cache_device = self.devices[name]
        return device.multiput_offset(session_id)

    def multiput(self, name, session_id, data, offset=None):
        """ 多次写入会话 """
        device, cache_device = self.devices[name]
        return device.multiput(session_id, data, offset)

    def multiput_save(self, name, session_id, key):
        """ 保存、完结会话 """
        device, cache_device = self.devices[name]
        if getattr(_local, 'put_files', None) is not None:
            _local.put_files.append((name, key))
        return device.multiput_save(session_id, key)

    def multiput_delete(self, name, session_id):
        """ 删除一个写入会话 """
        device, cache_device = self.devices[name]
        return device.multiput_delete(session_id)
