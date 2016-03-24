# encoding: utf-8

import os
import tempfile
from device import BaseDevice

class VfsDevice(BaseDevice):

    def ospath(self, key):
        """ 找到key在操作系统中的地址 """
        # 读取环境变量  VFS_xxx 做为环境变量
        root_ospath = os.environ['VFS_' + self.name.upper()]
        if '++versions++' in key:
            # 历史版本，直接找到对应的历史版本文件夹
            # ff/aa.doc/++versions++/1.doc
            # ff/.frs/aa.doc/archived/1.doc
            key, version = key.split('/++versions++/')
            key= key.split('/')
            key.insert(-1, self.frs.dotfrs)
            #_, ext = os.path.splitext(site_path[-1])
            key.append('archived')
            key.append(version)
            key = '/'.join(key)
        if os.path.splitor != '/':
            key = key.replace('/', os.path.splitor)
        return os.path.join(root_ospath, key)

    def gen_key(self, prefix='', suffix=''):
        """ 生成一个未用的key """
    
    def get_data(self, key):
        """ 根据key返回文件内容，不适合大文件 """
        path = self.ospath(key)
        return open(path, 'rb').read()

    def get_stream(self, key):
        """ 返回文件的一个stream对象，可以通过iterator来逐步得到文件，适合大文件 """
        path = self.ospath(key)
        return open(path, 'rb')

    def put_data(self, key, data):
        """ 直接存储一个数据，适合小文件 """
        ospath = self.ospath(key)
        dirpath = os.path.dirname(ospath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(ospath, 'wb') as fd:
            fd.write(data)

    def put_stream(self, key, stream):
        ospath = self.ospath(key)
        dirpath = os.path.dirname(ospath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        # 先复制到临时文件上，在覆盖目标文档
        temp_file = tempfile.mktemp(dir=dirpath)
        # 支持expect 100-continue HTTP协议
        # 在最后，如果上传文件还剩余1KB需要上传，但是data.read读取大于1KB会令socket抛出timeout错误
        while content_length > 0:
            n = min(content_length, bufsize)
            readbuffer = data.read(n)
            read_buf_length = len(readbuffer)
            if not read_buf_length > 0:
                break
            fd.write(readbuffer)
            content_length -= read_buf_length

        #shutil.move(temp_file, ospath)
        move_file(temp_file, ospath)

    def remove(self, key):
        """ 删除key文件 """

