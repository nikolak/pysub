#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013, 2014 Nikola Kovacevic <nikolak@outlook.com>


import os
import re
import sys
import gzip
import time
import struct
import difflib
import argparse

import guessit


if sys.version >= '3':
    import urllib.request as request
    from io import StringIO
    from xmlrpc.client import ServerProxy
else:  # Assume 2.x (Works on 2.7.x, not sure about older versions)
    import urllib2 as request
    from StringIO import StringIO
    from xmlrpclib import ServerProxy

    input = raw_input

FILE_EXT = [
    '.3g2', '.3gp', '.3gp2', '.3gpp', '.60d', '.ajp', '.asf', '.asx', '.avchd', '.avi',
    '.bik', '.bix', '.box', '.cam', '.dat', '.divx', '.dmf', '.dv', '.dvr-ms', '.evo',
    'flc', '.fli', '.flic', '.flv', '.flx', '.gvi', '.gvp', '.h264', '.m1v', '.m2p',
    '.m2ts', '.m2v', '.m4e', '.m4v', '.mjp', '.mjpeg', '.mjpg', '.mkv', '.moov', '.mov',
    '.movhd', '.movie', '.movx', '.mp4', '.mpe', '.mpeg', '.mpg', '.mpv', '.mpv2', '.mxf',
    '.nsv', '.nut', '.ogg', '.ogm', '.omf', '.ps', '.qt', '.ram', '.rm', '.rmvb',
    '.swf', '.ts', '.vfw', '.vid', '.video', '.viv', '.vivo', '.vob', '.vro', '.wm',
    '.wmv', '.wmx', '.wrap', '.wvx', '.wx', '.x264', '.xvid'
]

SUB_EXT = ['.aqt', '.gsub', '.jss', '.sub', '.pjs', '.psb', '.rt', '.smi', '.stl', '.ssf',
           '.srt', '.ssa', '.ass', '.sub', '.usf', ]

OVERWRITE = False
AUTO_DOWNLOAD = False
SUBFOLDER = None
MATCH_CUTOFF = 0.75  # difflib ratio cutoff float range[0,1],
# 0- strings don't have anything in common, 1- strings are identical

sub_language = 'eng'


class Subtitle(object):
    def __init__(self, json_data, save_path, video_fname):
        """

        :param json_data:
        :param save_path:
        :param video_fname:
        """
        self.ISO639 = json_data.get('ISO639')
        self.MatchedBy = json_data.get('MatchedBy')
        self.synced = self.MatchedBy == "moviehash"
        self.movie_name = json_data.get('MovieName', "")  # episode name or movie name
        self.episode_num = json_data.get('SeriesEpisode')  # episode number
        self.season_num = json_data.get('SeriesSeason')
        self.download_link = json_data.get('SubDownloadLink')
        self.download_count = json_data.get('SubDownloadsCnt')
        self.sub_format = json_data.get('SubFormat')
        self.sub_filename = json_data.get('SubFileName')
        self.save_path = save_path
        self.video_fname = video_fname
        self.full_path = "{folder}{name}.{format}".format(self.save_path,
                                                          self.video_fname,
                                                          self.sub_format)


    def download(self):
        """


        """
        if not os.path.isdir(self.save_path):
            try:
                os.mkdir(self.save_path)
            except IOError:
                print("Can't create subfolder. Check that you have write "
                      "access for {}".format(self.save_path))

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
        return "<Sub {}S{}E{}>".format(self.MovieName,
                                       self.SeriesSeason,
                                       self.SeriesEpisode)


class Video(object):
    def __init__(self, file_path):
        """

        :param file_path:
        """
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.sub_path = os.path.dirname(os.path.abspath(file_path))
        self.sub_path += os.sep if SUBFOLDER is None else os.sep + SUBFOLDER + os.sep
        self.file_size = os.path.getsize(file_path)

        self.file_search_query = None
        self.hash_search_query = None
        self.ep_info = guessit.guess_episode_info(file_path)

        self.__set_queries()
        self.subtitles = []

    @property
    def file_hash(self):
        """


        :return: :rtype:
        """
        if self.file_size < 65536 * 2:
            return None
        try:
            longlongformat = 'q'  # long long
            bytesize = struct.calcsize(longlongformat)

            with open(self.file_path, "rb") as f:

                file_hash = self.file_size

                for x in range(65536 / bytesize):
                    file_buffer = f.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, file_buffer)
                    file_hash += l_value
                    file_hash &= 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

                f.seek(max(0, self.file_size - 65536), 0)
                for x in range(65536 / bytesize):
                    file_buffer = f.read(bytesize)
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
        """
        type_1 = "{0}{1}".format(self.sub_path, self.file_name)
        type_2 = "{0}{1}".format(self.sub_path,
                                 "".join(self.file_name.split('.')[:-1]))

        for sub_format in SUB_EXT:
            if os.path.exists(type_1 + sub_format) or os.path.exists(type_2 + sub_format):
                return True

        return False

    def __set_queries(self):
        """


        """
        try:  # ep_info might raise key error
            _f_query = "{} S{:02d}E{:02d}".format(self.ep_info['series'],
                                                  int(self.ep_info['season']),
                                                  int(self.ep_info['episodeNumber']))
            self.file_search_query = [{'sublanguageid': sub_language,
                                       'query': _f_query,
                                       'season': self.ep_info['season'],
                                       'episode': self.ep_info['episodeNumber']}]
        except KeyError:
            pass  # file_Search_query is already None - no need to modify it

        if self.file_hash:
            # if/elif/elif:
            # **If you define moviehash and moviebytesize, then imdbid and query in same array are ignored.**
            # If you define imdbid, then moviehash, moviebytesize and query is ignored.
            # If you define query, then moviehash, moviebytesize and imdbid is ignored.
            self.hash_search_query = [{"sublanguageid": sub_language,
                                       'moviehash': self.file_hash,
                                       'moviebytesize': self.file_size}]


    def parse_response(self, full_json):
        """


        :rtype : None
        :param full_json:
        :return: :rtype:
        """
        if not full_json or not full_json['data']:  # There is no subtitle data in the response
            return

        for subtitle_json in full_json['data']:
            self.subtitles.append(Subtitle(subtitle_json,
                                           self.sub_path,
                                           self.file_name)
            )


    def __repr__(self):
        return "<Video {}>".format(self.file_name)


class OpenSubtitlesServer(object):
    def __init__(self, server="http://api.opensubtitles.org/xml-rpc",
                 ua='ossubd',
                 language="eng"):
        """

        :param server:
        :param ua:
        :param language:
        """
        self.language = language
        self.user_agent = ua
        self.token = None
        self.logged_in = False
        self.server = ServerProxy(server)

    def login(self, login_attempts=3):
        """

        :param login_attempts:
        """
        tries = login_attempts
        session = None
        while not session and tries > 0:
            try:
                session = self.server.LogIn('', '', self.language, self.user_agent)
            except:
                print("Exception while logging in to API. "
                      "Trying again - {} attempt(s) left.".format(tries))
                time.sleep(2)
                tries -= 1

        if session is None or session['status'] != '200 OK':
            print("Error logging in to opensubtitles API. "
                  "Error {}".format(session['status']))
        else:
            try:
                self.token = session['token']
                self.logged_in = True
            except KeyError:
                print("Token not found.")

    def log_out(self):
        """


        """
        if self.token:
            self.server.LogOut(self.token)
            self.token = None
            self.logged_in = False

    def query(self, query, attempts=2, desc="Search query"):
        """

        :param query:
        :param tries:
        :param desc:
        :return: :rtype:
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
        return "<Server {}>".format(self.token)


def search_subtitles(file_list):
    """

    :param file_list:
    """
    server = OpenSubtitlesServer()
    server.login()

    if not server.logged_in:
        exit()

    for count, file_path in enumerate(file_list):

        video = Video(file_path)

        print("-" * 50 + '\nSearching subtitle for "{}" | ({}/{})'.format(video.file_name,
                                                                          count + 1,
                                                                          len(file_list)))

        if not OVERWRITE and video.subtitle_exists:
            print("Subtitle already exists")
            continue

        if video.file_search_query:
            video.get_subtitles(server.query(video.file_search_query,
                                             desc="File Based Search"))

        if video.hash_search_query:
            video.get_subtitles(server.query(video.hash_search_query,
                                             desc="Hash Based Search"))

        if (not video.hash_search_query and not video.file_search_query) or video.subtitles == []:
            print("Couldn't find subtitles in {} for {}".format(sub_language, file_path))
            continue

        download_prompt(video)

    server.log_out()


def download_prompt(video):
    """

    :param video:
    :return: :rtype:
    """
    if AUTO_DOWNLOAD:
        auto_download(video)
        return

    user_choice = None
    possible_choices = ["a", "q", "s", ""] + [i for i in range(len(video.subtitles))]  # py2/3

    print("{:<2}: {:^10} {:<} {}\n{}".format("#", "Downloads", "Subtitle Name", " * - Sync subtitle", "-" * 50))

    for num, subtitle in enumerate(video.subtitles):
        print("{:<2}: {:^10} {:<}".format(num,
                                          subtitle.download_count + "*" if subtitle.synced else "",
                                          subtitle.sub_filename)
        )

    while user_choice not in possible_choices:
        user_input = input("return - download first, 's' - skip, "
                           "'a' - auto choose, 'q' - quit \n>>>")

        user_choice = int(user_input) if user_input.isdigit() else user_input.lower()

        if user_choice not in possible_choices:
            print("Invalid input.")

    if type(user_choice) is int:
        try:
            video.subtitles[user_choice].download()
        except IndexError:
            print("Invalid input only subtitle choices "
                  "from {} to {} are available".format(0, len(video.subtitles)))

    elif user_choice.lower() == "a":
        auto_download(video)

    elif user_choice.lower() == "q":
        print('Quitting')
        exit()

    elif user_choice.lower() == "s":
        print("skipping...")

    elif user_choice == "":
        video.subtitles[0].download()

    else:
        print("Invalid input")


def auto_download(video):
    """

    :param video:
    """
    sequence = difflib.SequenceMatcher(None, "", "")
    possible_matches = []
    best_choice = None

    for subtitle in video.subtitles:

        subtitle_title_name = re.sub(r'[^a-zA-Z0-9\s+]', '', subtitle.movie_name)
        episode_title_name = "{} {}".format(video.ep_info.get('series', "0").lower(),
                                            video.ep_info.get('title', "0").lower()
        )

        sequence.set_seqs(subtitle_title_name, episode_title_name)
        if sequence.ratio() > MATCH_CUTOFF:
            # Names of series title and episode names match enough, should be valid subtitle
            possible_matches.append(subtitle)

        if subtitle.synced:
            possible_matches.append(subtitle)

    for sub in possible_matches:
        if sub.synced:
            best_choice = sub
        if sub.download_count > best_choice.download_count:
            if best_choice.synced and not sub.synced:
                continue
            else:
                best_choice = sub

    if best_choice:
        best_choice.download()
    else:
        print("Can't find best subtitle automatically.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Subtitle downloader for TV Shows')
    parser.add_argument("folder", type=str,
                        help="Folder which will be scanned for allowed video files, "
                             "and subtitles for those files will be downloaded")
    parser.add_argument("-s", "--subfolder", type=str,
                        help="Subfolder to save subtitles to, relative to original video file path")
    parser.add_argument("-l", "--language", type=str,
                        help="Subtitle language, must be an ISO 639-1 Code i.e. (eng,fre,deu) Default English(eng)")
    parser.add_argument("-a", "--auto", action="store_true",
                        help="Auto download subtitles for all files without prompt ")
    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="Overwrite if subtitle with same filename exist.")
    parser.add_argument("-f", "--format", type=str,
                        help="Additional file formats that will be checked, comma separated,"
                             "specify ony file formats e.g. 'avix,temp,format2' (without quotes)")
    args = parser.parse_args()

    if args.format:
        FILE_EXT += args.format.split(',')

    directory = args.folder
    if os.path.isfile(directory):
        valid_files = [directory]  # single file, although its name is directory
    elif os.path.isdir(directory):
        directory += os.sep if not directory.endswith(os.sep) else ""

        valid_files = [directory + name for name in os.listdir(directory)
                       if os.path.splitext(name)[1] in FILE_EXT]
    else:
        print("{} is not a valid file or directory".format(directory))
        exit()
    if args.subfolder:
        SUBFOLDER = args.subfolder
        SUBFOLDER = SUBFOLDER.replace(os.sep, "")
    if args.language:
        if len(args.language) == 3:
            sub_language = args.language.lower()
        else:
            print('Argument not ISO 639-1 Code check this for list of valid codes'
                  ' http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes')
            exit()

    if args.auto:
        AUTO_DOWNLOAD = True

    if args.overwrite:
        OVERWRITE = True

    search_subtitles(valid_files)
