# encoding: utf-8

import os
from device import BaseDevice

class VFS:

    def __init__(self, root_ospath):
        self.root_ospath = root_ospath

    def ospath(self, vpath):
        if os.path.splitor != '/':
            vpath = vpath.replace('/', os.path.splitor)
        if '++versions++' in vpath:
            # 历史版本，直接找到对应的历史版本文件夹
            # ff/aa.doc/++versions++/1.doc
            # ff/.frs/aa.doc/archived/1.doc
            vpath, version = vpath.split('/++versions++/')
            vpath = vpath.split('/')
            vpath.insert(-1, self.frs.dotfrs)
            #_, ext = os.path.splitext(site_path[-1])
            vpath.append('archived')
            vpath.append(version)
            vpath = '/'.join(vpath)
        return os.path.join(self.root_ospath, vpath.replace('/', os.path.splitor))

class VfsDevice(BaseDevice):

    def __init__(self, path):
        self.vfs = VFS(path)

    def gen_key(self, prefix='', suffix=''):
        """ 生成一个未用的key """
    
    def get_data(self, key):
        """ 根据key返回文件内容，不适合大文件 """
        path = self.vfs.ospath(key)
        return open(path, 'rb').read()

    def get_stream(self, key):
        """ 返回文件的一个stream对象，可以通过iterator来逐步得到文件，适合大文件 """
        path = self.vfs.ospath(key)
        return open(path, 'rb')

    def put_data(self, key, data):
        """ 直接存储一个数据，适合小文件 """
        ospath = self.vfs.ospath(key)
        dirpath = os.path.dirname(ospath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(ospath, 'wb') as fd:
            fd.write(data)

    def put_stream(self, key, stream):
        ospath = self.vfs.ospath(key)
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

