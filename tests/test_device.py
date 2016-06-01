# -*- coding: utf-8 -*-
import copy
import json
import os
import shutil
import unittest
import tempfile
import time

from mdfs.device import Sessions

class SessionsTestCase(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.mkdtemp()
        self.sessions = Sessions(session_dir=self.workspace)
        self.device, self.key = 'default', 'ab/cd/efghijklmnopqrstuvwxyz.docx'
        self.data_extra = {
            'a': '1',
            'b': 2,
        }
        self.data_update = {
            'b': 3,
            'c': '3',
            'd': 3.141592653,
        }
        self.sessions.new(self.device, self.key, **self.data_extra)

    def tearDown(self):
        shutil.rmtree(self.workspace)

    def test_1_basic_inheritance(self):
        assert isinstance(self.sessions, Sessions)

    def test_2_session_new(self):
        session_file = self.sessions.os_path(self.device, self.key)
        self.assertTrue(
            os.path.isfile(session_file),
            'Session should be stored in file'
        )

    def test_3_session_load(self):
        with open(self.sessions.os_path(self.device, self.key)) as f:
            stored_session_data = json.load(f)
            self.assertTrue(
                all(
                    stored_session_data[i] == self.data_extra[i]
                    for i in self.data_extra.keys()
                ),
                'Session file should store all extra data correctly'
            )
            self.assertEqual(
                self.sessions.load(self.device, self.key),
                stored_session_data,
                'Sessions.load() should return JSON data from session file'
            )

    def test_4_session_update(self):
        session_data = copy.deepcopy(self.sessions.load(self.device, self.key))
        session_data.update(self.data_update)
        self.sessions.update(self.device, self.key, **self.data_update)
        self.assertEqual(
            self.sessions.load(self.device, self.key),
            session_data,
            'Session content should be updated'
        )

    def test_5_session_query(self):
        new_session_data = {
            'a': 'new session',
            'b': 'test value',
        }
        new_device = 'default'
        new_key = '/as/df/qwertyuiofdgdasf4567d.pptx'
        expire = time.time() - os.path.getmtime(
            self.sessions.os_path(self.device, self.key)
        )
        # Delay creation of the second session
        time.sleep(0.1)
        self.sessions.new(new_device, new_key, **new_session_data)

        sessions = []
        for session in self.sessions.query(expire=expire):
            sessions.append(session)
        self.assertEqual(
            len(sessions), 1, 'Should be able to query by expiration'
        )
        self.assertEqual(
            sessions[0]['key'],
            self.key,
            'Should return the same session as we created'
        )

    def test_6_session_delete(self):
        session_file_path = self.sessions.os_path(self.device, self.key)
        self.sessions.delete(self.device, self.key)
        self.assertFalse(
            os.path.exists(session_file_path),
            'Session files should be deleted'
        )

