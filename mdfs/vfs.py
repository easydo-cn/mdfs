# encoding: utf-8

import os
import time
import sys
import uuid
import shutil
import mimetypes
#from types import UnicodeType
from .device import BaseDevice
try:
    from types import UnicodeType
except ImportError:
    UnicodeType = None

FS_CHARSET = sys.getfilesystemencoding()
OPEN_FILE_TIMEOUT = 60 * 10

class OpenFiles:
    """ 管理打开的文件，打开10分钟就关闭；释放资源 """
    
    def __init__(self):
        self._fps = {}

    def new_file(self, path):
        """ 新建文件 """
        self._fps[path] = (open(path, 'wb'), 0, int(time.time()))  # cache
        return self._fps[path]

    def get_size(self, path):
        if path in self._fps:
            return self._fps[path][1]
        else:
            return os.path.getsize(path)

    def clean(self):
        """ 清理cache, 关闭和删除超时的 """
        now = int(time.time())
        for path, info in list(self._fps.items()):
            modified = info[2]
            if now > modified + OPEN_FILE_TIMEOUT:
                self.close_file(path)

    def close_file(self, path):
        """ 关闭文件 """
        try:
            self._fps[path][0].close()
        except Exception as e:
            print('close session error:' + str(e))
        del self._fps[path]

    def append_data(self, path, data, offset=None):
        """ 文件写数据 """
        if path not in self._fps:
            fp, size = open(path, 'ab'), 0
        else:
            fp, size, _ = self._fps.pop(path)  # pop避免被清理

        if offset is not None:
            fp.seek(offset)
            size = offset

        fp.write(data)
        size += len(data)
        self._fps[path] = fp, size, int(time.time())
        return size

OPEN_FILES = OpenFiles()

class VfsDevice(BaseDevice):

    PART_SIZE = 1024*1024

    def __init__(self, name, title='', root_path=None, options={}):
        self.name = name
        self.title = title
        self.options = options
        self.root_path = root_path

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
    def _makedirs(path):
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
        self._makedirs(os_path)
        session = os_path + ':' + str(size)
        OPEN_FILES.clean()  # 关闭全部超时不用的文件
        OPEN_FILES.new_file(os_path)
        return session
    
    def multiput_offset(self, session_id):
        """ 某个文件当前上传位置 """
        os_path = session_id.rsplit(':', 1)[0]
        return OPEN_FILES.get_size(os_path)

    def multiput(self, session_id, data, offset=None):
        """ 从offset处写入数据 """
        os_path = session_id.rsplit(':', 1)[0]
        return OPEN_FILES.append_data(os_path, data, offset)

    def multiput_save(self, session_id):
        """ 某个文件当前上传位置 """
        os_path, size = session_id.rsplit(':', 1)
        OPEN_FILES.close_file(os_path)
    
        if size != '-1' and int(size) != os.path.getsize(os_path):
            raise Exception('File Size Check Failed')
        return os_path[len(self.root_path)+1:].replace('\\', '/')

    def multiput_delete(self, session_id):
        """ 删除一个写入会话 """
        os_path = session_id.rsplit(':', 1)[0]
        OPEN_FILES.close_file(os_path)
        os.remove(os_path)

    def put_data(self, key, data):
        """ 直接存储一个数据，适合小文件 """
        os_path = self.os_path(key)
        self._makedirs(os_path)
        with open(os_path, 'wb') as fd:
            fd.write(data)

    def put_stream(self, key, stream, size=-1):
        """ 流式上传 """
        os_path = self.os_path(key)
        self._makedirs(os_path)

        with open(os_path, 'ab') as f:
            for data in stream:
                f.write(data)
            return f.tell()

    def remove(self, key):
        """ 删除key文件 """
        ospath = self.os_path(key)
        os.remove(ospath)

    def rmdir(self, key):
        """ 删除key文件夹"""
        ospath = self.os_path(key)
        shutil.rmtree(ospath)

    def move(self, key, new_key):
        """ 升级旧的key，更换为一个新的 """
        ossrc, osdst = self.os_path(key), self.os_path(new_key)
        # umove dosn't work with unicode filename yet
        if type(osdst) is UnicodeType and \
               not os.path.supports_unicode_filenames:
            ossrc = ossrc.encode(FS_CHARSET)
            osdst = osdst.encode(FS_CHARSET)

        self._makedirs(osdst)
        # windows move 同一个文件夹会有bug，这里改为rename
        # 例子： c:\test move to c:\Test
        if ossrc.lower() == osdst.lower():
            os.rename(ossrc, osdst)
        else:
            shutil.move(ossrc, osdst)

    def copy_data(self, from_key, to_key):
        src = self.os_path(from_key)
        dst = self.os_path(to_key)
        self._makedirs(dst)
        shutil.copy(src, dst)

    def stat(self, key):
        os_path = self.os_path(key)
        return {
            "file_size": os.path.getsize(os_path),
            "hash": None,
            "mime_type": mimetypes.guess_type(key)[0],
            "put_time": os.path.getctime(os_path)
        }
