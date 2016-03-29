# encoding: utf-8

import os
import uuid
import shutil

from mdfs.device import BaseDevice


class VfsDevice(BaseDevice):
    def os_path(self, key):
        """ 找到key在操作系统中的地址 """

        # 读取环境变量  VFS_xxx 做为环境变量
        try:
            root_path = os.environ['VFS_' + self.name.upper()]
        except KeyError as e:
            raise e

        if '++versions++' in key:
            # 历史版本，直接找到对应的历史版本文件夹
            # ff/aa.doc/++versions++/1.doc -> ff/.frs/aa.doc/archived/1.doc
            key, version = key.split('/++versions++/')
            key = key.split('/')
            key.insert(-1, '.frs')
            key.append('archived')
            key.append(version)
            key = '/'.join(key)
        if os.sep != '/':
            key = key.replace('/', os.sep)
        return os.path.join(root_path, key)

    def gen_key(self, prefix='', suffix=''):
        """
        使用uuid生成一个未使用的key, 生成随机的两级目录
        :param prefix: 可选前缀
        :param suffix: 可选后缀
        :return: 设备唯一的key
        """
        key = uuid.uuid4().hex
        key = os.sep.join((key[:2], key[2:5], key[5:]))
        if prefix:
            prefix = prefix + os.sep
        return prefix + key + suffix

    @staticmethod
    def mkdir(path):
        dir_name = os.path.dirname(path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    def get_data(self, key):
        """ 根据key返回文件内容，适合小文件 """
        path = self.os_path(key)
        with open(path, 'rb') as f:
            return f.read()

    def get_stream(self, key, buffer_size=8192):
        """ 返回文件的一个stream对象，可以通过iterator来逐步得到文件，适合大文件 """
        path = self.os_path(key)
        with open(path, 'rb') as f:
            data = f.read(buffer_size)
            while data:
                yield data
                data = f.read(buffer_size)

    def put_data(self, key, data):
        """ 直接存储一个数据，适合小文件 """
        os_path = self.os_path(key)
        self.mkdir(os_path)
        with open(os_path, 'wb') as fd:
            fd.write(data)

    def put_stream(self, key, stream):
        os_path = self.os_path(key)
        self.mkdir(os_path)
        with open(os_path, 'ab') as f:
            shutil.copyfileobj(stream, f)
            return f.tell()

    def remove(self, key):
        """ 删除key文件 """
        os.remove(self.os_path(key))
