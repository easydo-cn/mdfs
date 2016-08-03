# -*- coding: utf-8 -*-
import os
import unittest


from mdfs.aliyun import  AliyunDevice
from mdfs.vfs import VfsDevice

session_id = ""

class AliyunTestCase(unittest.TestCase):
    def setUp(self):
        vfs_device = VfsDevice(name="vfs_test_one", title="vfs_test", root_path="C:\\testvfs")
        options = {
            'access_key_id': '3vN0eE9VgjAgKafY',
            'access_key_secret': 'lqDKfBQHrq0ovgVB49ICMk1KEselUz',
            'endpoint' : 'oss-cn-qingdao.aliyuncs.com',
            'bucket_name': 'edotest'
        }
        self.key = 'ff/.frs/aa.doc/archived/19.txt'
        self.aliyun_device = AliyunDevice('aliyun_test_one', title='aliyun_test', local_device=vfs_device, options=options)
        global session_id
        if session_id is "":
            session_id = self.aliyun_device.multiput_new(self.key, 400*1024)
        self.sessions = session_id


    def tearDown(self):
        pass



    def test_2_exists(self):
        self.assertTrue(
            self.aliyun_device.exists(self.key)
        )

    def test_3_upload(self):
        local_session_id = self.aliyun_device.multiput_new(self.key, 400*1024)
        offset = 0
        while offset < 400*1024:
            offset = self.aliyun_device.multiput(local_session_id, "a"*400*1024, offset)

        self.aliyun_device.multiput_save(local_session_id)
        self.assertTrue(self.aliyun_device.exists(self.key))

    def test_4_os_path(self):
        ospath = self.aliyun_device.os_path(self.key)
        self.assertIsInstance(ospath, str)

    def test_7_copy_data(self):
        to_key = 'ff/.frs/aa.doc/archived/abcd.txt'
        self.aliyun_device.copy_data(self.key, to_key)
        self.assertTrue(self.aliyun_device.exists(to_key))

    def test_8_remote(self):
        self.aliyun_device.remove(self.key)
        self.assertFalse(self.aliyun_device.exists(self.key))

    def test_9_rmdir(self):
        if self.aliyun_device.exists(self.key):
            self.aliyun_device.rmdir(self.key)
        self.assertFalse(os.path.exists(self.aliyun_device.local_device.os_path(self.key)))


if __name__ == '__main__':
    unittest.main()