#!/usr/bin/env python3
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

import os
import gzip
from urllib import request
from io import StringIO


class Subtitle(object):
    """ Contains information about subtitle and handles downloading.

    Subtitle class, stores subtitle information returned from
    server as attributes and handles downloading and saving
    the subtitle from server to location passed from video class.

    Attributes:
        synced: bool, true if subtitle is found by hash search
        movie_name: str or None, name of the movie or Series name
        episode_num: int or None, episode number
        season_num: int or none, episode number
        download_link: str or None, direct link to gziped subtitle
        download_count: int, -1 if not found in json
        sub_format: str or none, format of the subtitle, used in saving
        sub_filename: str or none, name of subtitle file on subtitles
        save_path: str, absolute path of folder to save subtitle to
        full_path: str, absolute path of subtitle to save to

    """

    def __init__(self, json_data, save_path, video_fname):
        """
        Initialize Subtitle class with one subtitle json data and
        information for saving subtitle

        Args:
            json_data: Part of json response from server containing
                       only information for one subtitle, dict.
            save_path: folder where to save subtitle, string
            video_fname: original name of video file associated with
                         this subtitle, string.

        """
        self.synced = json_data.get('MatchedBy') == "moviehash"
        self.movie_name = json_data.get('MovieName', "")
        self.episode_num = json_data.get('SeriesEpisode')
        self.season_num = json_data.get('SeriesSeason')
        self.download_link = json_data.get('SubDownloadLink')
        self.download_count = int(json_data.get('SubDownloadsCnt', -1))
        self.sub_format = json_data.get('SubFormat')
        self.sub_filename = json_data.get('SubFileName')
        self.save_path = save_path
        self.full_path = "{folder}{name}.{format}".format(
            folder=self.save_path,
            name=video_fname,
            format=self.sub_format)

    def download(self):
        """
        Download subtitle to folder/file specified in self.full_path
        variable.

        """
        if not os.path.isdir(self.save_path):
            try:
                os.mkdir(self.save_path)
            except IOError:
                print("Can't create subfolder. "
                      "Check that you have write access for "
                      "{}".format(self.save_path))

        sub_zip_file = request.urlopen(self.download_link)
        sub_gzip = gzip.GzipFile(fileobj=StringIO(sub_zip_file.read()))
        subtitle_content = sub_gzip.read()
        try:
            with open(self.full_path, 'wb') as subtitle_output:
                subtitle_output.write(subtitle_content)
            print("Downloaded subtitle...")
        except IOError:
            print("Couldn't save subtitle, permissions issue?")

    def __repr__(self):
        return "<Sub {}S{}E{}>".format(self.movie_name,
                                       self.season_num,
                                       self.episode_num)
