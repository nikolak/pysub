#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013, 2014 Nikola Kovacevic <nikolak@outlook.com>


from sys import version_info

import os
import gzip
import struct
import difflib
import argparse

if version_info >= (3, 0):
    import urllib.request as request
    from io import StringIO
    from xmlrpc.client import ServerProxy
else:  # Assume 2.x (Works on 2.7.x, not sure about older versions)
    import urllib2 as request
    from StringIO import StringIO
    from xmlrpclib import ServerProxy

import guessit

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

sub_language = 'eng'
useragent = "ossubd"
server = ServerProxy("http://api.opensubtitles.org/xml-rpc")

OVERWRITE = False
AUTO_DOWNLOAD = False
SUBFOLDER = None
MATCH_CUTOFF = 0.75  # difflib ratio cutoff float range[0,1],
# 0- strings don't have anything in common, 1- strings are identical

class Video(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.sub_path = os.path.dirname(os.path.abspath(file_path))
        self.sub_path += os.sep if SUBFOLDER is None else os.sep + SUBFOLDER + os.sep
        self.file_size = os.path.getsize(file_path)
        self.file_hash = self.__set_file_hash()
        self.subtitle_exists=self.__sub_exists()
        self.subtitles=[]

        self.ep_info = guessit.guess_episode_info(file_path)


        try: # ep_info might raise key error
            _f_query = "{} S{:02d}E{:02d}".format(self.ep_info['series'],
                                                       int(self.ep_info['season']),
                                                       int(self.ep_info['episodeNumber']))
            self.file_search_query = [{'sublanguageid': sub_language,
                                       'query': _f_query,
                                       'season': self.ep_info['season'],
                                       'episode': self.ep_info['episodeNumber']}]
        except KeyError:
            self.file_hash_query=None

        if self.file_hash:
            # if/elif/elif:
            # **If you define moviehash and moviebytesize, then imdbid and query in same array are ignored.**
            # If you define imdbid, then moviehash, moviebytesize and query is ignored.
            # If you define query, then moviehash, moviebytesize and imdbid is ignored.
            self.hash_search_query = [{"sublanguageid": sub_language,
                                       'moviehash': self.file_hash,
                                       'moviebytesize': self.file_size}]
        else:
            self._hash_search_query=None



    def __set_file_hash(self):
        if self.file_size < 65536 * 2:
            return None
        try:
            longlongformat = 'q'  # long long
            bytesize = struct.calcsize(longlongformat)

            with open(self.file_name, "rb") as f:

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


    def __sub_exists(self):
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


class Subtitle(object):
    def __init__(self):
        pass


def search_subtitles(file_list):
    #TODO: Instead of performing search for each file, construct queries and execute them all at once
    """
    :rtype : object
    :param file_list: list of video files(with full path) for which to search subtitles
    """
    #TODO: Check if user is over the download limit
    #http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#ServerInfo
    count = 0
    try:
        session = server.LogIn("", "", sub_language, useragent)
    except:
        print("Error logging in to opensubtiles API.")
        exit()

    if session['status'] != "200 OK":
        print("Error logging in to opensubtiles API.", session['status'])
        exit()
    else:
        token = session["token"]

    for file_path in file_list:

        count += 1
        video = Video(file_path)

        print("-" * 50 + '\nSearching subtitle for "{}" | ({}/{})'.format(video.file_name,
                                                                          count,
                                                                          len(file_list)))

        if not OVERWRITE:
            if video.subtitle_exists:
                print("Subtitle already exists")
            continue

        if video.file_search_query:
            query_results = server.SearchSubtitles(token, video.file_search_query)
            if query_results['status'] != "200 OK":  # FIXME: This doesn't happen, like, ever.
                print("Query search failed ", query_results['status'])
                query_results = None
            else:
                if not query_results['data']:
                    query_results = None
                else:
                    query_results = query_results['data']

        if video.hash_search:
            hash_results = server.SearchSubtitles(token, video.hash_search_query)
            if hash_results['status'] != '200 OK':
                print('"Hash search failed', hash_results['status'])
                hash_results = None
            else:
                hash_results = hash_results['data']

        if not video.hash_search_query and not video.file_search_query:
            do_download = False
            print("Couldn't find subtitles in {} for {}".format(sub_language, file_path))
        else:
            do_download = True

        if do_download:
            ep_info["filename"] = file_path
            ep_info['sub_folder'] = video.sub_path
            subtitles_list = []
            if query_results:  # Subtitle results exist
                for item in query_results:
                    subtitles_list.append(item)
            if hash_results:
                for item in hash_results:
                    subtitles_list.append(item)
            if subtitles_list == []:
                print("Couldn't find subtitles in {} for {}".format(sub_language, file_path))
            else:
                download_prompt(subtitles_list, ep_info)

    server.LogOut(token)


# noinspection PyBroadException
def download_prompt(subtitles_list, ep_info):
    """
    :param subtitles_list: list containing dicts of each subtitle returned from opensubtitles api
    :param ep_info:  dict containing episode info; most important -- 'series' - tv show name and 'title' -ep title
    :return: Nothing
    """
    if AUTO_DOWNLOAD:
        auto_download(subtitles_list, ep_info)
        return
    user_choice = None
    possible_choices = ["a", "q", "s", ""]
    sub_dict = {}
    count = 1
    print("{:<2}: {:^10} {:<} {}\n{}".format("#", "Downloads", "Subtitle Name", " * - Sync subtitle", "-" * 50))

    for subtitle in subtitles_list:
        sync = subtitle['MatchedBy'] == 'moviehash'
        print("{:<2}: {:^10} {:<}".format(count,
                                          subtitle["SubDownloadsCnt"] + "*" if sync else subtitle["SubDownloadsCnt"],
                                          subtitle["SubFileName"]))
        sub_dict[count] = subtitle
        count += 1
    possible_choices.extend(list(sub_dict.keys()))

    while user_choice not in possible_choices:
        prompt_text = "return - download first, 's' - skip, 'a' - auto choose, 'q' - quit \n>>>"

        if version_info >= (3, 0):
            user_input = input(prompt_text)
        else:
            user_input = raw_input(prompt_text)

        user_choice = int(user_input) if user_input.isdigit() else user_input.lower()

        if user_choice not in possible_choices:
            print "|{}|".format(user_choice)
            print("invalid input")

    if type(user_choice) is int:
        if sub_dict.get(user_choice, False):
            download_subtitle(sub_dict[user_choice], ep_info)
        else:
            print("Invalid input only subtitle choices from {} to {} are available".format(1, count))

    elif user_choice.lower() == "a":
        auto_download(subtitles_list, ep_info)

    elif user_choice.lower() == "q":
        print('Quitting')
        exit()

    elif user_choice.lower() == "s":
        print("skipping...")

    elif user_choice == "":
        download_subtitle(sub_dict[1], ep_info)

    else:
        print("Invalid input")


def auto_download(subtitles_list, ep_info):
    """
    :param subtitles_list: list containing (all) subtitle dicts returned from opensubtitles
    :param ep_info: episode info dict
    ep_info example:
    {u'mimetype': u'video/x-flv', u'episodeNumber': 11, u'container': u'flv',
    u'title': u'Adventures in Babysitting', u'series': u'Supernatural',
    u'type': u'episode', u'season': 7, u'filename':<full file path>}
    """
    # MatchedBy can be: moviehash, imdbid, tag, fulltext

    sequence = difflib.SequenceMatcher(None, "", "")
    possible_matches = []
    best_choice = {"best": None, "downloads": 0}

    for subtitle in subtitles_list:
        # Change title from i.e. "The Office (US) Dunder Mifflin Infinity" to the office (us) dunder mifflin infinity
        try:
            subtitle_title_name = subtitle['MovieName'].replace("'", "").replace('"', '').lower()
            episode_title_name = "{} {}".format(ep_info['series'].lower(), ep_info['title'].lower())
        except KeyError:
            # Those keys don't exist, we can't compare sub info with anything
            subtitle_title_name = "0"
            episode_title_name = "1"
            # TV Show name and title are separate keys in ep_info dict, not like in sub dict

        sequence.set_seqs(subtitle_title_name, episode_title_name)
        if sequence.ratio() > MATCH_CUTOFF:
            # Names of series title and episode names match enough, should be valid subtitle
            possible_matches.append(subtitle)

        if subtitle['MatchedBy'] == 'moviehash':
            possible_matches.append(subtitle)

    for sub in possible_matches:
        if sub['MatchedBy'] == 'moviehash':
            best_choice['best'] = sub
            best_choice['downloads'] = "Movie hash"
            break
        if int(sub["SubDownloadsCnt"]) > best_choice["downloads"]:
            best_choice["best"] = sub
            best_choice["downloads"] = sub["SubDownloadsCnt"]

    if best_choice["best"] is not None:
        download_subtitle(best_choice["best"], ep_info)
    else:
        print("Can't find correct subtitle")


# noinspection PyBroadException
def download_subtitle(subtitle_info, ep_info):
    """
    :param subtitle_info: dict of the subtitle with sub info such as download link etc.
    :param ep_info: episode info dict
    ep_info example:
    {u'mimetype': u'video/x-flv', u'episodeNumber': 11, u'container': u'flv',
    u'title': u'Adventures in Babysitting', u'series': u'Supernatural',
    u'type': u'episode', u'season': 7, u'filename':<full file path>}
    """
    download_url = subtitle_info["SubDownloadLink"]
    subtitle_folder = ep_info['sub_folder']
    subtitle_name = subtitle_folder + os.path.basename(ep_info["filename"])
    subtitle_name += "." + subtitle_info["SubFormat"]  # .srt only on opensubtitles?

    if not os.path.isdir(subtitle_folder):
        os.mkdir(subtitle_folder)
        # TODO: Add exception handling, if we can't create folder we won't be able to save sub there (probably)

    # Not in try/except because this shouldn't ever fail, and if it does other subtitles
    # won't be downloaded too so ignoring it seems useless. letting it to raise
    # error makes more sense
    sub_zip_file = request.urlopen(download_url)
    sub_gzip = gzip.GzipFile(fileobj=StringIO(sub_zip_file.read()))
    subtitle_content = sub_gzip.read()
    try:
        with open(subtitle_name, 'wb') as subtitle_output:
            subtitle_output.write(subtitle_content)
        print("Downloaded subtitle...")
    except:
        print("Couldn't save subtitle, permissions issue?")


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
