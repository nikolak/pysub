#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pysub
----------------------------------

Tests for `pysub` module.
"""

import unittest
import os
import guessit
import sys


from SimpleXMLRPCServer import SimpleXMLRPCServer

from pysub import pysub


class TestPysubVideo(unittest.TestCase):

    def setUp(self):
        self.filename="Awesome Test - [01x01] - Hopefully it passes.avi"

        with open(self.filename, 'w') as tmp_file:
            tmp_file.write("dummy"*30000)

        self.video=pysub.Video(self.filename)
        self.ep_info=guessit.guess_episode_info(self.filename)

    def test_video_init(self):
        self.assertEqual(self.filename,
                         self.video.file_path)

        self.assertEqual(self.filename,
                         self.video.file_name)

        self.assertEqual(os.getcwd() + os.sep,
                         self.video.sub_path)

        self.assertEqual(150000,
                         self.video.file_size)

        self.assertEqual('b7b7afc0abb9e5b7',
                         self.video.file_hash)

        self.assertFalse(self.video.sub_exists)

        self.assertEqual([{'query': 'Awesome Test S01E01', 'sublanguageid': 'eng', 'episode': 1, 'season': 1}],
                         self.video.file_search_query)

        self.assertEqual([{'moviebytesize': '150000', 'sublanguageid': 'eng', 'moviehash': 'b7b7afc0abb9e5b7'}],
                         self.video.hash_search_query)

        self.assertEqual(self.ep_info, self.video.ep_info)

    def test_file_hash(self):
        pass

    def test_sub_exists(self):
        pass

    def test_queries(self):
        pass

    def tearDown(self):
        os.remove(self.filename)

class TestServerInstance(object):

    def __init__(self, port=8000):
        self.session=None
        self.__serve(port)

    def __serve(self, port):
        self.server = SimpleXMLRPCServer(("localhost", port))
        self.server.register_function(self.LogIn, 'LogIn')
        self.server.register_function(self.LogOut, 'LogOut')
        self.server.register_function(self.SearchSubtitles, 'SearchSubtitles')
        self.server.serve_forever()

    def LogIn(self, user, password, lang, user_agent):
        self.session['user']=user
        self.session['password']=password
        self.session['lang']=lang
        self.session['user_agent']=user_agent
        self.session['token']='valid_token'
        return self.session['token']

    def LogOut(self, token):
        if self.session['token']==token:
            self.session=None
        else:
            raise ValueError('Invalid token value')
        return None

    def SearchSubtitles(self, token, query):
        if not self.session or self.session['token']!=token:
            raise ValueError('Invalid token or session')

        pass


class TestPysubServer(unittest.TestCase):

    def setUp(self):
        pass

    def test_init(self):
        pass

    def test_login(self):
        pass

    def test_logout(self):
        pass

    def test_query(self):
        pass

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main(verbosity=2)