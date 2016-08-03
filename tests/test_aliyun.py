# -*- coding: utf-8 -*-
import os
import unittest


from mdfs.aliyun import  AliyunDevice
from mdfs.vfs import VfsDevice


class AliyunTestCase(unittest.TestCase):
    def setUp(self):
        vfs_device = VfsDevice(name="vfs_test_one", title="vfs_test", root_path="C:\\testvfs")
        options = {
            'access_key_id': '3vN0eE9VgjAgKafY',
            'access_key_secret': 'lqDKfBQHrq0ovgVB49ICMk1KEselUz',
            'endpoint' : 'oss-cn-qingdao.aliyuncs.com',
            'bucket_name': 'edotest'
        }
        self.key = 'ff/.frs/aa.doc/archived/15.txt'
        self.aliyun_device = AliyunDevice('aliyun_test_one', title='aliyun_test', local_device=vfs_device, options=options)
        self.sessions = self.aliyun_device.multiput_new(self.key, 42)

    def tearDown(self):
        pass

    def test_1_os_path(self):
        ospath = self.aliyun_device.os_path(self.key)
        self.assertIsInstance(ospath, str)

    def test_2_exists(self):
        self.assertTrue(
            self.aliyun_device.exists(self.key)
        )

    def test_3_multiput_new(self):
        self.assertIsInstance(self.sessions, str)

    def test_4_multiput(self):
        next_position = self.aliyun_device.multiput(self.sessions, "this is a test")
        self.assertIsInstance(next_position, int)

    def test_5_multiput_offset(self):
        self.assertIsInstance(
            self.aliyun_device.multiput_offset(self.sessions),
            int
        )

    def test_6_multiput_save(self):
        path = self.aliyun_device.multiput_save(self.sessions)
        self.assertTrue(
            self.aliyun_device.exists(self.sessions.rsplit(":")[0])
        )

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
        self.assertTrue(os.path.exists(self.aliyun_device.local_device.os_path(self.key)))

    def test_10_multiput_delete(self):
        path = self.aliyun_device.multiput_delete(self.sessions)
        self.assertIsNone(path)


if __name__ == '__main__':
    unittest.main()