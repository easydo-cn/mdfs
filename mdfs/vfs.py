# encoding: utf-8

import os
import sys
import uuid
import shutil
import mimetypes
#from types import UnicodeType
from .device import BaseDevice

FS_CHARSET = sys.getfilesystemencoding()

class VfsDevice(BaseDevice):

    def __init__(self, name, title='', options={}):
        self.name = name
        self.title = title
        self.options = options
        # 读取环境变量  VFS_xxx 做为环境变量
        self.root_path = os.environ['VFS_' + self.name.upper()]

        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)

    def os_path(self, key):
        """ 找到key在操作系统中的地址 """
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
        # key can't be an absolute path
        key = key.lstrip(os.sep)
        return os.path.join(self.root_path, key)

    def gen_key(self, prefix='', suffix=''):
        """
        使用uuid生成一个未使用的key, 生成随机的两级目录
        :param prefix: 可选前缀
        :param suffix: 可选后缀
        :return: 设备唯一的key
        """
        key = uuid.uuid4().hex
        key = '/'.join((key[:2], key[2:5], key[5:]))
        return prefix + key + suffix

    def exists(self, key):
        return os.path.exists(self.os_path(key))

    @staticmethod
    def makedirs(path):
        dir_name = os.path.dirname(path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    def get_data(self, key, offset=0, size=-1):
        """ 根据key返回文件内容，适合小文件 """
        path = self.os_path(key)
        with open(path, 'rb') as f:
            return f.read()

    def multiput_new(self, key, size=-1):
        """ 开始一个多次写入会话, 返回会话ID"""
        os_path = self.os_path(key)
        self.makedirs(os_path)
        with open(os_path, 'wb'):
            pass
        return os_path + ':' + str(size)

    def multiput_offset(self, session_id):
        """ 某个文件当前上传位置 """
        os_path = session_id.rsplit(':', 1)[0]
        return os.path.getsize(os_path)

    def multiput(self, session_id, data, offset=None):
        """ 从offset处写入数据 """
        os_path = session_id.rsplit(':', 1)[0]
        if offset is None:
            with open(os_path, 'ab') as f:
                f.write(data)
                return f.tell()
        with open(os_path, 'r+b') as f:
            f.seek(offset)
            f.write(data)
            return f.tell()

    def multiput_save(self, session_id):
        """ 某个文件当前上传位置 """
        os_path, size = session_id.rsplit(':', 1)
        if size == '-1': 
            return os_path[len(self.root_path)+1:].replace('\\', '/')
        elif int(size) != os.path.getsize(os_path):
            raise Exception('File Size Check Failed')

    def multiput_delete(self, session_id):
        """ 删除一个写入会话 """
        os_path = session_id.rsplit(':', 1)[0]
        os.remove(os_path)

    def put_data(self, key, data):
        """ 直接存储一个数据，适合小文件 """
        os_path = self.os_path(key)
        self.makedirs(os_path)
        with open(os_path, 'wb') as fd:
            fd.write(data)

    def put_stream(self, key, stream):
        os_path = self.os_path(key)
        self.makedirs(os_path)
        with open(os_path, 'ab') as f:
            shutil.copyfileobj(stream, f)
            return f.tell()

    def remove(self, key):
        """ 删除key文件 """
        ospath = self.os_path(key)
        if os.path.exists(ospath):
            os.remove(ospath)

    def move(self, key, new_key):
        """ 升级旧的key，更换为一个新的 """
        ossrc, osdst = self.os_path(key), self.os_path(new_key)
        # umove dosn't work with unicode filename yet
        #if type(osdst) is UnicodeType and \
        #       not os.path.supports_unicode_filenames:
        #    ossrc = ossrc.encode(FS_CHARSET)
        #    osdst = osdst.encode(FS_CHARSET)

        self.makedirs(osdst)
        # windows move 同一个文件夹会有bug，这里改为rename
        # 例子： c:\test move to c:\Test
        if ossrc.lower() == osdst.lower():
            os.rename(ossrc, osdst)
        else:
            shutil.move(ossrc, osdst)

    def copy_data(self, from_key, to_key):
        src = self.os_path(from_key)
        dst = self.os_path(to_key)
        self.makedirs(dst)
        shutil.copy(src, dst)

    def stat(self, key):
        os_path = self.os_path(key)
        return {
            "file_size": os.path.getsize(os_path),
            "hash": None,
            "mime_type": mimetypes.guess_type(key)[0],
            "put_time": os.path.getctime(os_path)
        }
