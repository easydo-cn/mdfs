# encoding: utf-8

# refer document: https://help.aliyun.com/document_detail/32030.html?spm=5176.doc32032.6.306.4N1U2T
import os
import mimetypes

import oss2
from oss2 import determine_part_size
from oss2.models import PartInfo

from device import BaseDevice

UPLOAD_SESSIONS = {}
PART_SIZE = 400 * 1024
BUFFER_SIZE = 400 * 1024


class AliyunDevice(BaseDevice):
    """aliyun deveice """

    def __init__(self, name, title='', local_device=None, options={}):
        self.name = name
        self.title = title
        self.local_device = local_device
        self.options = options
        auth = oss2.Auth(options['access_key_id'], options['access_key_secret'])
        self.bucket = oss2.Bucket(auth, options['endpoint'], options['bucket_name'])

    def os_path(self, key):
        """找到key在操作系统中的地址 """
        os_path = self.local_device.os_path(key)
        if self.local_device.exists(key):
            return os_path
        else:
            # download to os_path
            session_id = self.local_device.multiput_new(key)
            size = self.bucket.head_object(key).content_length
            offset = 0
            while offset < size:
                self.local_device.multiput(session_id, self.get_data(key, offset, PART_SIZE))
                offset += PART_SIZE
            return self.local_device.multiput_save(session_id)

    def _get_upload_session(self, session_id):
        if not UPLOAD_SESSIONS.has_key(session_id):
            upload_id, key, size = session_id.rsplit(':', 2)
            parts = self.bucket.list_parts(key, upload_id).parts
            part_number = len('parts') + 1
            offset = 0
            for part in parts:
                offset += part.size
            UPLOAD_SESSIONS[session_id] = {
                'parts': parts, 'part_number': part_number,
                'offset': offset, 'buffer': ''
            }
        return UPLOAD_SESSIONS[session_id]

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
        return os.path.exists(self.local_device.os_path(key)) or \
               self.bucket.object_exists(key)

    def get_data(self, key, offset=0, size=-1):
        """ 根据key返回文件内容，适合小文件 """
        if self.local_device.exists(key):
            return self.local_device.get_data(key, offset=offset, size=size)
        else:
            data = self.bucket.get_object(self.os_path(key), byte_range=(offset, offset + size))
            return data

    def multiput_new(self, key, size=-1):
        """
        开始一个多次写入会话, 返回会话ID"
       从服务端获取所有执行中的断点续传事件
       参考网址: https://help.aliyun.com/document_detail/31997.html?spm=5176.doc31850.2.8.Ew9mpc
       """
        session_id = ':'.join([self.bucket.init_multipart_upload(key).upload_id, key, str(size)])
        UPLOAD_SESSIONS[session_id] = {'parts': [], 'offset': 0, 'part_number': 1, 'buffer': ''}
        return session_id

    def multiput_offset(self, session_id):
        """ 某个文件当前上传位置 """
        upload_id, key, size = session_id.rsplit(':', 2)
        if not UPLOAD_SESSIONS.has_key(session_id):
            UPLOAD_SESSIONS[upload_id] = self._get_upload_session(session_id)
        return UPLOAD_SESSIONS[session_id].get('offset')

    def multiput(self, session_id, data, offset=None):
        """ 从offset处写入数据 """
        upload_id, key, size = session_id.rsplit(':', 2)
        upload_session = self._get_upload_session(session_id)
        buffer_data = self._get_buffer_data(upload_session, data, size)
        if buffer_data is not None:
            if upload_session.get('offset') < int(size):
                num_to_upload = min(PART_SIZE, int(size) - upload_session.get('offset'))
                result = self.bucket.upload_part(key,
                                                 upload_id,
                                                 upload_session.get('part_number'),
                                                 buffer_data
                                                 )
                upload_session['parts'].append(PartInfo(upload_session['part_number'], result.etag))

                upload_session['offset'] += num_to_upload
                upload_session['part_number'] += 1
        return upload_session.get('offset')

    def multiput_save(self, session_id):
        """ 某个文件当前上传位置 """
        upload_id, key, size = session_id.rsplit(':', 2)
        upload_session = self._get_upload_session(session_id)
        if int(size) != '-1' and upload_session.get('offset') != int(size):
            raise Exception("File Size Check Failed")

        self.bucket.complete_multipart_upload(key, upload_id, upload_session.get('parts'))
        UPLOAD_SESSIONS.pop(session_id)
        return upload_id

    def multiput_delete(self, session_id):
        """ 删除一个写入会话 """
        upload_id, size = session_id.rsplit(':', 1)
        upload_session = self._get_upload_session(session_id)
        self.bucket.abort_multipart_upload(upload_id, upload_session.get('upload_id'))
        UPLOAD_SESSIONS.pop(session_id)

    def remove(self, key):
        """ 删除key文件，本地缓存也删除 """
        if self.local_device.exists(key):
            self.local_device.remove(key)
        self.bucket.delete_object(key)

    def rmdir(self, key):
        """ 删除key文件夹"""
        return self.local_device.rmdir(key)

    def copy_data(self, from_key, to_key):
        """复制文件"""
        total_size = self.bucket.head_object(from_key).content_length
        part_size = determine_part_size(total_size, preferred_size=100 * 1024)

        # 初始化分片
        upload_id = self.bucket.init_multipart_upload(to_key).upload_id
        parts = []

        # 逐个分片拷贝
        part_number = 1
        offset = 0
        while offset < total_size:
            num_to_upload = min(part_size, total_size - offset)
            byte_range = (offset, offset + num_to_upload - 1)

            result = self.bucket.upload_part_copy(self.bucket.bucket_name, from_key
                                                  , byte_range, to_key, upload_id, part_number)
            parts.append(PartInfo(part_number, result.etag))
            offset += num_to_upload
            part_number += 1

        # 完成分片上传
        self.bucket.complete_multipart_upload(to_key, upload_id, parts)

    def stat(self, key):
        """ 得到状态 """
        os_path = self.os_path(key)
        return {
            "file_size": os.path.getsize(os_path),
            "hash": None,
            "mime_type": mimetypes.guess_type(key)[0],
            "put_time": os.path.getctime(os_path)
        }

    def _get_buffer_data(self, upload_session, data, size):
        upload_session['buffer'] += data
        if len(upload_session['buffer']) >= BUFFER_SIZE:
            buffer_data = upload_session['buffer'][:BUFFER_SIZE]
            upload_session['buffer'] = upload_session['buffer'][BUFFER_SIZE:]
            return buffer_data
        elif len(upload_session['buffer']) >= size:
            return upload_session['buffer']
        else:
            return None
