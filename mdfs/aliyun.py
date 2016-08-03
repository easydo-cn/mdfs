# encoding: utf-8

# refer document: https://help.aliyun.com/document_detail/32030.html?spm=5176.doc32032.6.306.4N1U2T
import os
import mimetypes

import oss2
from oss2 import determine_part_size
from oss2.models import PartInfo

from device import BaseDevice

UPLOAD_DETAIL = []
PART_SIZE = 4 * 1024


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
                self.local_device.multiput(session_id, self.get_data(key, offset, size))
                offset += 100
            return self.local_device.multiput_save(session_id)

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
            data = self.bucket.get_object(self.os_path(key), byte_range=(offset, offset+100))
            return data

    def multiput_new(self, key, size=-1):
        """
        开始一个多次写入会话, 返回会话ID"
       从服务端获取所有执行中的断点续传事件
       参考网址: https://help.aliyun.com/document_detail/31997.html?spm=5176.doc31850.2.8.Ew9mpc
       """
        multipart_uploads = self.bucket.list_multipart_uploads()
        upload_detail = {
            'upload_id': None,
            'parts': [],
            'offset': 0,
            'part_number': 1,
            'session_id': ''
        }
        session = ':'.join([key, str(size)])
        if not self._get_upload_detail(session):
            for uploads in multipart_uploads.upload_list:
                if uploads.key == key:
                    upload_detail['upload_id'] = uploads.upload_id
                    # 获取对当前key文件的parts列表
                    upload_detail['parts'] = self.bucket.list_parts(key, upload_detail['upload_id']).parts
                    upload_detail['part_number'] = len(upload_detail['parts']) + 1
                    for part in upload_detail['parts']:
                        upload_detail['offset'] += part.size
                    break
            if upload_detail['part_number'] is None:
                upload_detail['part_number'] = self.bucket.init_multipart_upload(key).upload_id
            upload_detail['session_id'] = session
            UPLOAD_DETAIL.append(upload_detail)
        return session

    @staticmethod
    def _get_upload_detail(session_id):
        for upload_detail in UPLOAD_DETAIL:
            if upload_detail.get('session_id') == session_id:
                return upload_detail

    def multiput_offset(self, session_id):
        """ 某个文件当前上传位置 """
        return self._get_upload_detail(session_id).get('offset')

    def multiput(self, session_id, data, offset=None):
        """ 从offset处写入数据 """
        os_path, size = session_id.rsplit(':', 1)
        upload_detail = self._get_upload_detail(session_id)
        if upload_detail and upload_detail.get('offset') < int(size):
            num_to_upload = min(PART_SIZE, int(size) - upload_detail.get('offset'))
            result = self.bucket.upload_part(os_path, upload_detail.get('upload_id'),
                                             upload_detail.get('part_number'), data)
            upload_detail['offset'] += num_to_upload
            upload_detail['part_number'] += 1
        return upload_detail.get('offset')

    def multiput_save(self, session_id):
        """ 某个文件当前上传位置 """
        os_path, size = session_id.rsplit(':', 1)
        upload_detail = self._get_upload_detail(session_id)
        if int(size) != '-1' and upload_detail.get('offset') != int(size):
            raise Exception("File Size Check Failed")

        self.bucket.complete_multipart_upload(os_path, upload_detail.get('upload_id'), upload_detail.get('parts'))
        UPLOAD_DETAIL.remove(upload_detail)
        return os_path

    def multiput_delete(self, session_id):
        """ 删除一个写入会话 """
        os_path, size = session_id.rsplit(':', 1)
        upload_detail = self._get_upload_detail(session_id)
        self.bucket.abort_multipart_upload(os_path, upload_detail.get('upload_id'))
        UPLOAD_DETAIL.remove(upload_detail)

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
