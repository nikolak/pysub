#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle downloader using OpenSubtitles.org API
"""
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

from __future__ import print_function

import os
import re
import gzip
import time
import struct
import difflib
import urllib2
import argparse
import xmlrpclib
from StringIO import StringIO

import guessit


config = {
    'file_ext': [
        '.3g2', '.3gp', '.3gp2', '.3gpp', '.60d', '.ajp', '.asf', '.asx',
        '.avchd', '.avi', '.bik', '.bix', '.box', '.cam', '.dat', '.divx',
        '.dmf', '.dv', '.dvr-ms', '.evo', 'flc', '.fli', '.flic', '.flv',
        '.flx', '.gvi', '.gvp', '.h264', '.m1v', '.m2p', '.m2ts', '.m2v',
        '.m4e', '.m4v', '.mjp', '.mjpeg', '.mjpg', '.mkv', '.moov', '.mov',
        '.movhd', '.movie', '.movx', '.mp4', '.mpe', '.mpeg', '.mpg', '.mpv',
        '.mpv2', '.mxf', '.nsv', '.nut', '.ogg', '.ogm', '.omf', '.ps', '.qt',
        '.ram', '.rm', '.rmvb', '.swf', '.ts', '.vfw', '.vid', '.video',
        '.viv', '.vivo', '.vob', '.vro', '.wm', '.wmv', '.wmx', '.wrap',
        '.wvx', '.wx', '.x264', '.xvid'
    ],

    # List of subtitle extensions to check when checking if subtitle already
    # exists in the save location
    'sub_ext': [
        '.aqt', '.gsub', '.jss', '.sub', '.pjs', '.psb', '.rt', '.smi',
        '.stl', '.ssf', '.srt', '.ssa', '.ass', '.sub', '.usf'
    ],

    'overwrite': False,  # If subtitle exists in save location
    'auto_download': False,
    # Skip prompts, auto choose, continue on none found
    'subfolder': None,  # Download to same directory as video if None
    'cutoff': 0.75,
    # Cutoff:
    # 0 - Name of video and subtitle dont' have anything in common
    # 1 - Name of video and subtitle are identical

    # OpenSubtitles API default settings
    'lang': 'eng',  # Language to search
    'ua': 'ossubd',  # User Agent
    'server': 'http://api.opensubtitles.org/xml-rpc',
}


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

        sub_zip_file = urllib2.urlopen(self.download_link)
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

    def __init__(self, file_path):
        """
        Initalizing class for file specified in file_path

        Attributes:
            file_path: String with absolute path to file

        Raises:
            IOError: if file does not exist in that location
        """
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
        if config['subfolder']:
            path += "{}{}".format(config['subfolder'], os.sep)

        return path

    @property
    def file_hash(self):
        """
        Calculates hash for video file if the file is larger
        than 128kb.

        Returns:
            String containing file has or None if the file
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
        type_1 = "{0}{1}".format(self.sub_path, self.file_name)
        type_2 = "{0}{1}".format(self.sub_path,
                                 "".join(self.file_name.split('.')[:-1]))

        for sub_format in config['sub_ext']:
            if os.path.exists(type_1 + sub_format):
                return True

            if os.path.exists(type_2 + sub_format):
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

            return [{'sublanguageid': config['lang'],
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
            return [{"sublanguageid": config['lang'],
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

        """
        sequence = difflib.SequenceMatcher(None, "", "")
        possible_matches = []
        best_choice = None

        for subtitle in self.subtitles:

            subtitle_title_name = re.sub(r'[^a-zA-Z0-9\s+]', '',
                                         subtitle.movie_name).lower()
            episode_title_name = "{} {}".format(
                self.ep_info.get('series', "0").lower(),
                self.ep_info.get('title', "0").lower()
            )

            sequence.set_seqs(subtitle_title_name, episode_title_name)
            if sequence.ratio() > config['cutoff']:
                possible_matches.append(subtitle)

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
        else:
            print("Can't choose best subtitle automatically.")

    def __repr__(self):
        """
        repr,returns full video path
        """
        return "<Video {}>".format(self.file_name)


class OpenSubtitlesServer(object):
    """OpenSubtitles Server connection/handling class

    OpenSubtitlesServer class handles logging in,
    upon initialization. Conducting queries, and handling
    retries and exceptions

    Attrs:
        language: str, Language used for searches ISO639-2 format
        user_agent: str, user agent for for auth with opensubtitles server
        tokken: str, acquired after successful login and required for queries
        logged_in: bool, self set to indicate whether login was done or not
        server: ServerProxy object


    """

    def __init__(self, server=config['server'],
                 ua=config['ua'],
                 language=config['lang']):
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
            results = self.server.SearchSubtitles(self.token, query)
            if results['status'] != '200 OK':
                results = None
                attempts_left -= 1
            else:
                return results
        print("{} failed...".format(desc))
        return None

    def __repr__(self):
        """
        repr of OpenSubtitlesServer instance with current set token
        """
        return "<Server {}>".format(self.token)


def search_subtitles(file_list):
    """
    Searches subitles and if any are found initiates prompt and
    other functions.

    Instantiates server and does login.

    Args:
        file_list: list, list containing absolute paths of videos
                   for which to search subtitles for
    """
    server = OpenSubtitlesServer()
    server.login()

    if not server.logged_in:
        exit()

    for count, file_path in enumerate(file_list):

        video = Video(file_path)

        print("-" * 50 + '\nSearching subtitle for '
                         '"{}" | ({}/{})'.format(video.file_name,
                                                 count + 1,
                                                 len(file_list)))

        if not config['overwrite'] and video.sub_exists:
            print("Subtitle already exists")
            continue

        if video.file_search_query:
            video.parse_response(server.query(video.file_search_query,
                                              desc="File Based Search"))

        if video.hash_search_query:
            video.parse_response(server.query(video.hash_search_query,
                                              desc="Hash Based Search"))

        if not video.subtitles:
            print("Couldn't find subtitles in "
                  "{} for {}".format(config['lang'], file_path))
            continue

        download_prompt(video)

    server.log_out()


# noinspection PyTypeChecker
def download_prompt(video):
    """
    List all found subtitles from video object and
    ask user to chose which subtitle to download.
    or to use auto download, skip this one or to quit.

    Args:
        video: Video class instance with at leas one item
               in subtitles attribute

    """
    if config['auto_download']:
        video.auto_download()
        return

    user_choice = None
    possible_choices = ["a", "q", "s", ""] + range(len(video.subtitles))

    print("{:<2}: {:^10} {:<} {}\n{}".format("#", "Downloads", "Subtitle Name",
                                             " * - Sync subtitle", "-" * 50))

    for num, subtitle in enumerate(video.subtitles):
        print("{:<2}: {:^10} {:<}".format(num,
                                          str(subtitle.download_count) +
                                          ['', '*'][subtitle.synced],
                                          subtitle.sub_filename))

    while user_choice not in possible_choices:
        user_input = raw_input("return - download first, 's' - skip, "
                               "'a' - auto choose, 'q' - quit \n>>>")

        user_choice = int(
            user_input) if user_input.isdigit() else user_input.lower()

        if user_choice not in possible_choices:
            print("Invalid input.")

    if type(user_choice) is int:
        try:
            video.subtitles[user_choice].download()
        except IndexError:
            print("Invalid input only subtitle choices "
                  "from {} to {} are available".format(0,
                                                       len(video.subtitles)))

    elif user_choice.lower() == "a":
        video.auto_download()

    elif user_choice.lower() == "q":
        print('Quitting')
        exit()

    elif user_choice.lower() == "s":
        print("skipping...")

    elif user_choice == "":
        video.subtitles[0].download()

    else:
        print("Invalid input")

def main():
    """
    Parse command line arguments, set CONFIG object,
    get valid files and call search_subtitles function
    """
    valid_files = []
    parser = argparse.ArgumentParser(
        description='Subtitle downloader for TV Shows')

    parser.add_argument("folder", type=str,
                        help="Folder which will be scanned for allowed "
                             "video files, and subtitles for those files "
                             "will be downloaded")

    parser.add_argument("-s", "--subfolder", type=str,
                        help="Subfolder to save subtitles to, relative to "
                             "original video file path")

    parser.add_argument("-l", "--language", type=str,
                        help="Subtitle language, must be an ISO 639-1 Code "
                             "i.e. (eng,fre,deu) Default English(eng)")

    parser.add_argument("-a", "--auto", action="store_true",
                        help="Auto download subtitles for all files "
                             "without prompt ")

    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="Overwrite if subtitle with same filename exist.")

    parser.add_argument("-f", "--format", type=str,
                        help="Additional file formats that will be checked, "
                             "comma separated, specify only file formats "
                             "e.g. 'avix,temp,format2' (without quotes)")
    args = parser.parse_args()

    if args.format:
        config['file_ext'] += args.format.split(',')

    directory = args.folder
    if os.path.isfile(directory):
        valid_files = [directory]
    elif os.path.isdir(directory):
        directory += os.sep if not directory.endswith(os.sep) else ""

        valid_files = [directory + name for name in os.listdir(directory)
                       if os.path.splitext(name)[1] in config['file_ext']]
    else:
        print("{} is not a valid file or directory".format(directory))
        exit()
    if args.subfolder:
        config['subfolder'] = args.subfolder
        config['subfolder'] = config['subfolder'].replace(os.sep, "")
    if args.language:
        if len(args.language) == 3:
            config['lang'] = args.language.lower()
        else:
            print(
                'Argument not ISO 639-1 Code check this for list of valid '
                'codes http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes')
            exit()

    if args.auto:
        config['auto_download'] = True

    if args.overwrite:
        config['overwrite'] = True

    search_subtitles(valid_files)


if __name__ == '__main__':
    main()
