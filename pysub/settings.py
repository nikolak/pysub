#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle downloader using OpenSubtitles.org API

Settings module
"""
# Copyright 2014 Nikola Kovacevic <nikolak@outlook.com>
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
import json

from appdirs import AppDirs


dirs = AppDirs("pysub", "pysub")
config_file = dirs.user_data_dir + os.sep + "config.json"

default_config = {
    "file_ext": [
        ".3g2", ".3gp", ".3gp2", ".3gpp", ".60d", ".ajp", ".asf", ".asx",
        ".avchd", ".avi", ".bik", ".bix", ".box", ".cam", ".dat", ".divx",
        ".dmf", ".dv", ".dvr-ms", ".evo", "flc", ".fli", ".flic", ".flv",
        ".flx", ".gvi", ".gvp", ".h264", ".m1v", ".m2p", ".m2ts", ".m2v",
        ".m4e", ".m4v", ".mjp", ".mjpeg", ".mjpg", ".mkv", ".moov", ".mov",
        ".movhd", ".movie", ".movx", ".mp4", ".mpe", ".mpeg", ".mpg", ".mpv",
        ".mpv2", ".mxf", ".nsv", ".nut", ".ogg", ".ogm", ".omf", ".ps", ".qt",
        ".ram", ".rm", ".rmvb", ".swf", ".ts", ".vfw", ".vid", ".video",
        ".viv", ".vivo", ".vob", ".vro", ".wm", ".wmv", ".wmx", ".wrap",
        ".wvx", ".wx", ".x264", ".xvid"
    ],

    "sub_ext": [
        ".aqt", ".gsub", ".jss", ".sub", ".pjs", ".psb", ".rt", ".smi",
        ".stl", ".ssf", ".srt", ".ssa", ".ass", ".sub", ".usf"
    ],

    "overwrite": False,
    "auto_download": False,
    "not_found_prompt": False,
    "subfolder": None,
    "cutoff": 0.75,

    "lang": "eng",
    "lang_name": "English",
    "ua": "ossubd",
    "server": "http://api.opensubtitles.org/xml-rpc",

    "languages": {
        "Bosnian": "bos",
        "Brazilian": "pob",
        "Bulgarian": "bul",
        "Croatian": "hrv",
        "Czech": "cze",
        "Danish": "dan",
        "Dutch": "dut",
        "Estonian": "est",
        "English": "eng",
        "Finnish": "fin",
        "French": "fre",
        "German": "ger",
        "Greek": "ell",
        "Icelandic": "ice",
        "Inupiaq": "ipk",
        "Irish": "gle",
        "Italian": "ita",
        "Japanese": "jpn",
        "Latvian": "lav",
        "Luxembourgish": "ltz",
        "Macedonian": "mac",
        "Montenegrin": "mne",
        "Persian": "per",
        "Pohnpeian": "pon",
        "Polish": "pol",
        "Portuguese": "por",
        "Romanian": "rum",
        "Russian": "rus",
        "Sardinian": "srd",
        "Serbian": "scc",
        "Slovak": "slo",
        "Slovenian": "slv",
        "Spanish": "spa",
        "Sundanese": "sun",
        "Swedish": "swe",
        "Thai": "tha",
        "Turkish": "tur",
        "Ukrainian": "ukr",
        "Uzbek": "uzb",
        "Vietnamese": "vie",
        "Welsh": "wel"
    }
}


def get_config():
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as in_config:
                return json.load(in_config)
        except:
            print "Loading config failed"
            return default_config

    return default_config


def save_config(user_config):
    with open(config_file, "w") as out_config:
        json.dump(user_config, out_config)


if __name__ == '__main__':
    print config_file