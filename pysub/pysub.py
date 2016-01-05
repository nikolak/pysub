#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle downloader using OpenSubtitles.org API

Command line command-line user interface
"""
# Copyright 2016 Nikola Kovacevic <nikolak@outlook.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import argparse

from pysub_objects import Video, OpenSubtitlesServer
from settings import default_config as config


def search_subtitles(file_list, config):
    """
    Searches subitles and if any are found initiates prompt and
    other functions.

    Instantiates server and does login.

    Args:
        file_list: list, list containing absolute paths of videos
                   for which to search subtitles for
    """
    server = None

    for count, file_path in enumerate(file_list):

        video = Video(file_path, config)

        print("-" * 50 + '\nSearching subtitle for '
                         '"{}" | ({}/{})'.format(video.file_name,
                                                 count + 1,
                                                 len(file_list)))

        if not config['overwrite'] and video.sub_exists:
            print("Subtitle already exists")
            continue

        if not server:
            server = OpenSubtitlesServer(config['server'],
                                         config['ua'],
                                         config['lang'])
            server.login()

            if not server.logged_in:
                exit()

        if video.file_search_query:
            video.parse_response(server.query(video.file_search_query,
                                              desc="File Based Search"))

        if video.hash_search_query:
            video.parse_response(server.query(video.hash_search_query,
                                              desc="Hash Based Search"))

        if not video.subtitles:
            print("Couldn't find subtitles in "
                  "{} for {}".format(config['lang_name'], file_path))
            continue

        download_prompt(video)

    if server:
        server.log_out()


# noinspection PyTypeChecker
def download_prompt(video, force=False):
    """
    List all found subtitles from video object and
    ask user to chose which subtitle to download.
    or to use auto download, skip this one or to quit.

    Args:
        video: Video class instance with at leas one item
               in subtitles attribute

    """
    if config['auto_download'] and not force:
        if not video.auto_download():
            print("Can't choose best subtitle automatically.")
            if config['not_found_prompt']:
                download_prompt(video, force=True)
        return

    user_choice = None
    possible_choices = ["a", "q", "s", ""] + range(len(video.subtitles))

    print("{:<2}: {:^10} {:<} {}\n{}".format("#", "Downloads", "Subtitle Name",
                                             " * - Sync subtitle", "-" * 50))

    for num, subtitle in enumerate(video.subtitles):
        print("{:<2}: {:^10} {:<}".format(num,
                                          str(subtitle.download_count) +
                                          ['', '*'][subtitle.synced],
                                          subtitle.sub_filename.encode('utf-8')))

    while user_choice not in possible_choices:
        user_input = input("return - download first, 's' - skip, "
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
        if not video.auto_download():
            print("Can't choose best subtitle automatically.")
            if config['not_found_prompt']:
                download_prompt(video, force=True)

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
    parser = argparse.ArgumentParser(description='Subtitle downloader for TV Shows')

    parser.add_argument("folder", type=str,
                        help="Folder which will be scanned for allowed "
                             "video files, and subtitles for those files "
                             "will be downloaded")

    parser.add_argument("-s", "--subfolder", type=str,
                        help="Subfolder to save subtitles to, relative to "
                             "original video file path")

    parser.add_argument("-l", "--language", type=str,
                        help="Subtitle language, must be an ISO 639-2 Code "
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
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Search files recursively")

    parser.add_argument("-p", "--nfprompt", action="store_true",
                        help="Prompt which subtitle to download if auto"
                             "downloader can't choose one")
    args = parser.parse_args()

    if args.format:
        config['file_ext'] += args.format.split(',')

    directory = args.folder
    if os.path.isfile(directory):
        valid_files = [directory]
    elif os.path.isdir(directory):
        directory += os.sep if not directory.endswith(os.sep) else ""
        valid_files = []
        if args.recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if os.path.splitext(file)[1] in config['file_ext']:
                        valid_files.append("{}{}{}".format(root, os.sep, file))
        else:
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
        elif len(args.language) > 3:
            config['lang'] = config['languages'].get(args.language.title())
            if not config['lang']:
                raise ValueError("Wrong language value")
            config['lang_name'] = args.language.title()
        else:
            print(
                'Argument not ISO 639-2 Code check this for list of valid '
                'codes http://en.wikipedia.org/wiki/List_of_ISO_639-2_codes')
            exit()

    if args.auto:
        config['auto_download'] = True

    if args.overwrite:
        config['overwrite'] = True

    if args.nfprompt:
        config['not_found_prompt'] = True

    search_subtitles(valid_files, config)


if __name__ == '__main__':
    main()
