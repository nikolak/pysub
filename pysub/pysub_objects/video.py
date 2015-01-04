#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 Nikola Kovacevic <nikolak@outlook.com>
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

import re
import os
import struct
import difflib

import guessit

from subtitle import Subtitle


class Video(object):
    """Contains information for one video file

    Video class contains attributes relevant for video file
    Checks if subtitle exists and sets queries to be executed
    when searching for subtitles.
    This class also splits full server response to query
    into smaller parts and instantiates new Subtitle class
    for every subtitle found in the full server response.


    Attributes:
        file_path: absolute path of video file
        file_name: name of file
        file_size: file size in bytes
        ep_info: dictionary from guessit module
        subtitles: list of all subtitles found for this file

        sub_path: full absolute path to where sub should be saved
        file_hash: hash for this file or None
        sub_exists: bool, subtitle exists in save location
        file_search_query: query based on guessit data
        hash_search_query: query based on file hash/size data

    """

    def __init__(self, file_path, config):
        """
        Initalizing class for file specified in file_path

        Attributes:
            file_path: String with absolute path to file

        Raises:
            IOError: if file does not exist in that location
        """
        self.config = config
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_size = os.path.getsize(file_path)

        self.ep_info = guessit.guess_episode_info(file_path)

        self.subtitles = []

    @property
    def sub_path(self):
        """
        Constructs full absolute path where the subtitle should be saved to.

        Returns:
            Absolute path in which to save subtitle,
            including subfolder (if any).
            If no subfolder is set then path is same as video path
        """
        path = os.path.dirname(os.path.abspath(self.file_path)) + os.sep
        if self.config['subfolder']:
            path += "{}{}".format(self.config['subfolder'], os.sep)

        return path

    @property
    def file_hash(self):
        """
        Calculates hash for video file if the file is larger
        than 128kb.

        Returns:
            String containing file hash or None if the file
            is not found or is too small (<128kb)
        """
        if self.file_size < 65536 * 2:
            return None
        try:
            longlongformat = 'q'  # long long
            bytesize = struct.calcsize(longlongformat)

            with open(self.file_path, "rb") as in_file:

                file_hash = self.file_size

                for _ in range(65536 / bytesize):
                    file_buffer = in_file.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, file_buffer)
                    file_hash += l_value
                    file_hash &= 0xFFFFFFFFFFFFFFFF
                    # to remain as 64bit number

                in_file.seek(max(0, self.file_size - 65536), 0)
                for _ in range(65536 / bytesize):
                    file_buffer = in_file.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, file_buffer)
                    file_hash += l_value
                    file_hash &= 0xFFFFFFFFFFFFFFFF
                return "%016x" % file_hash

        except IOError:
            return None

    @property
    def sub_exists(self):
        """
        This script will download subtitles as
        original_filename.original_extension.subtitle_extension

        Some other applications download as original_filename.sub_ext
        We need to check both to be sure whether the subtitle exists or not
        type_1 is naming this script uses
        type_2 is naming without original file extension

        Returns:
            True if subtitle exists in same path, False otherwise
            Only subtitle extensions specified in CONFIG are checked.
        """
        possible_filenames = [self.file_name,  # video_filename.ext.sub_ext
                              "".join(self.file_name.split('.')[:-1])  # video_filename.sub_ext
        ]
        possible_folders = [self.sub_path,  # same folder as video
                            "{}{}{}".format(self.sub_path, "Subs", os.sep)  # Subs folder
        ]

        for sub_format in self.config['sub_ext']:
            for name in possible_filenames:
                for folder in possible_folders:
                    if os.path.exists("{}{}{}".format(folder, name.decode('utf-8').encode('utf-8'), sub_format)):
                        return True
        return False

    @property
    def file_search_query(self):
        """
        Query based on information available from guessit module.
        Search relies on series name, season,episode number for results

        Returns:
            None if not enough information is available,
            otherwise query to execute is returned
        """
        try:  # ep_info might raise key error
            _ = "{} S{:02d}E{:02d}".format(self.ep_info['series'],
                                           int(self.ep_info['season']),
                                           int(self.ep_info['episodeNumber']))

            return [{'sublanguageid': self.config['lang'],
                     'query': _,
                     'season': self.ep_info['season'],
                     'episode': self.ep_info['episodeNumber']}]
        except KeyError:
            return None

    @property
    def hash_search_query(self):
        """
         Query based on file hash. Most reliable, in theory,
         Needs only valid hash and moviesize

        Returns:
            None if file hash can't be calculated,
            otherwise query based on hash and filesize is returned
        """
        if self.file_hash:
            return [{"sublanguageid": self.config['lang'],
                     'moviehash': self.file_hash,
                     'moviebytesize': str(self.file_size)}]

        return None

    def parse_response(self, full_json):
        """
        Parses response for query from server. And constructs
        multiple Subtitle instances for every subtitle found in
        the json response.

        Args:
            full_json: Complete json response from XMLRPC server
                       including all subtitles
        """
        if not full_json or not full_json['data']:
            return

        for subtitle_json in full_json['data']:
            self.subtitles.append(Subtitle(subtitle_json,
                                           self.sub_path,
                                           self.file_name))

    def auto_download(self):
        """
        Automatically choose best subtitle based on
        how similar the subtitle and video file names are
        or based on the type of match.

        Returns:
            True if suitable subtitle is found else False

        """
        sequence = difflib.SequenceMatcher(None, "", "")
        possible_matches = []
        best_choice = None

        for subtitle in self.subtitles:

            sub_info = guessit.guess_episode_info(subtitle.sub_filename)

            sub_series = sub_info.get('series', "None Found").lower().encode('utf-8')
            sub_season = sub_info.get('season', None)
            sub_episode = sub_info.get('episodeNumber', None)

            vid_series = self.ep_info.get('series', "None").lower().encode('utf-8')
            vid_season = self.ep_info.get('season', None)
            vid_episode = self.ep_info.get('episodeNumber', None)

            if vid_series == sub_series:
                if sub_season and vid_season and sub_episode and vid_episode:
                    if [sub_season, sub_episode] == [vid_season, vid_episode]:
                        possible_matches.append(subtitle)
                    else:
                        continue

            subtitle_title_name = re.sub(r'[^a-zA-Z0-9\s+]', '',
                                         subtitle.movie_name).lower()
            episode_title_name = "{} {}".format(
                self.ep_info.get('series', "0").lower().encode('utf-8'),
                self.ep_info.get('title', "0").lower().encode('utf-8')
            )

            sequence.set_seqs(subtitle_title_name, episode_title_name)
            if sequence.ratio() > self.config['cutoff']:
                possible_matches.append(subtitle)
                continue

            if subtitle.synced:
                possible_matches.append(subtitle)

        for sub in possible_matches:
            if not best_choice:
                best_choice = sub
            elif sub.download_count > best_choice.download_count:
                if best_choice.synced and sub.synced is False:
                    continue
                else:
                    best_choice = sub

        if best_choice:
            best_choice.download()
            return True
        else:
            return False

    def __repr__(self):
        """
        repr,returns full video path
        """
        return "<Video {}>".format(self.file_name)

