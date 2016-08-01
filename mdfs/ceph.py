# encoding: utf-8
import os
from .device import BaseDevice
import mimetypes

class CephDevice(BaseDevice):
    """ ceph device """

    def __init__(self, name, title='', local_device=None, options={}):
        self.name = name
        self.title = title
        self.local_device = local_device

    def os_path(self, key):
        """ 找到key在操作系统中的地址 """
        os_path = self.local_device.os_path(key)
        if self.local_device.exists(key):
            return os_path
        else:
            # download to os_path
            pass

    def gen_key(self, prefix='', suffix=''):
        """
        使用uuid生成一个未使用的key, 生成随机的两级目录
        :param prefix: 可选前缀
        :param suffix: 可选后缀
        :return: 设备唯一的key
        """
        return self.local_device.gen_key(prefix, suffix)

    def exists(self, key):
        """ 判断key是否存在"""

    def get_data(self, key, offset=0, size=-1):
        """ 根据key返回文件内容，适合小文件 """
        if self.local_device.exists(key):
            return self.local_device.get_data(key, offset=offset, size=size)
        else:
            pass # download and cache

    def multiput_new(self, key, size=-1):
        """ 开始一个多次写入会话, 返回会话ID"""

    def multiput_offset(self, session_id):
        """ 某个文件当前上传位置 """

    def multiput(self, session_id, data, offset=None):
        """ 从offset处写入数据 """

    def multiput_save(self, session_id):
        """ 某个文件当前上传位置 """

    def multiput_delete(self, session_id):
        """ 删除一个写入会话 """

    def remove(self, key):
        """ 删除key文件，本地缓存也删除 """

    def rmdir(self, key):
        """ 删除key文件夹"""
        results = []
        for device in self.mirror_devices:
            results.append(device.rmdir(key))
        return results[0]

    def copy_data(self, from_key, to_key):
        """ 复制 """

    def stat(self, key):
        """ 得到状态 """
        os_path = self.os_path(key)
        return {
            "file_size": os.path.getsize(os_path),
            "hash": None,
            "mime_type": mimetypes.guess_type(key)[0],
            "put_time": os.path.getctime(os_path)
        }
