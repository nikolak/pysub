#!/usr/bin/env python33
# -*- coding: utf-8 -*-

# Copyright 2016 Nikola Kovacevic <nikolak@outlook.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import xmlrpc.client as xmlrpclib


class OpenSubtitlesServer(object):
    """OpenSubtitles Server connection/handling class

    OpenSubtitlesServer class handles logging in,
    upon initialization. Conducting queries, and handling
    retries and exceptions

    Attributes:
        language: str, Language used for searches ISO639-2 format
        user_agent: str, user agent for for auth with opensubtitles server
        tokken: str, acquired after successful login and required for queries
        logged_in: bool, self set to indicate whether login was done or not
        server: ServerProxy object


    """

    def __init__(self, server, ua, language):
        """
        Initialization of server instance. By default values
        are taken from CONFIG dictionary

        Args:
            server: str, XMLRPC server URL
            user_agent: str, user agent for for auth with opensubtitles server
            language: str, Language used for searches ISO639-2 format

        """
        self.language = language
        self.user_agent = ua
        self.token = None
        self.logged_in = False
        self.server = xmlrpclib.ServerProxy(server)

    def login(self, login_attempts=3):
        """
        Login to server and aquire token. If Protocol error occurs
        retry certain amount of times

        Args:
            login_attempts: int, number of retries in case of errors
                            before giving up on logging in
        """
        tries = login_attempts
        session = None
        while not session and tries > 0:
            try:
                session = self.server.LogIn('', '',
                                            self.language,
                                            self.user_agent)
            except xmlrpclib.ProtocolError as err:
                print("Error while logging in to API. {}".format(err.errmsg))
                time.sleep(2)
                tries -= 1

        if session is None or session['status'] != '200 OK':
            print("Login to OpenSubtitles API failed...")
        else:
            try:
                self.token = session['token']
                self.logged_in = True
            except KeyError:
                print("Token not found.")

    def log_out(self):
        """
        Run LogOut on server and set token to None and logged_in to False.
        Without this it's impossible to do query.
        """
        if self.token:
            self.server.LogOut(self.token)
            self.token = None
            self.logged_in = False

    def query(self, query, attempts=2, desc="Search query"):
        """
        Execute query and return server response regardless of what it is.

        Args:
            query: list with dict containing query fields
            attempts: int, number of attempts before giving up on trying
                       to make the query.
            desc: str, description of query displayed in case of fail

        Returns:
            Server response, json/dict if the query was successful, otherwise
            returns None
        """
        results = None
        attempts_left = attempts
        while not results and attempts_left > 0:
            try:
                results = self.server.SearchSubtitles(self.token, query)
                if results['status'] != '200 OK':
                    results = None
                    attempts_left -= 1
                else:
                    return results
            except:
                results = None
                attempts_left-=1
        print("{} failed...".format(desc))
        return None

    def __repr__(self):
        """
        repr of OpenSubtitlesServer instance with current set token
        """
        return "<Server {}>".format(self.token)
