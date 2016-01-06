#Python Subtitle Downloader

[![Build Status](https://travis-ci.org/Nikola-K/pysub.svg)](https://travis-ci.org/Nikola-K/pysub)

Fast and free subtitle downloader written in python. Has both command line and GUI interfaces (see screenshots below)

Use `pysub --help` for command line help.

##Features

* Automatic downloading

* Supports all languages

* Support for all video and subtitle files

* Uses opensubtitles.org which has over 3484542 subtitles

* File hash based search - to find the most suitable subitle for the video file

* Fast - downloading all subtitles for an average TV show takes less than a minute

* Free - Licensed under Apache License, Version 2. All features are free and open source.

##Installing

For the moment there are no binary distributions available - there will be in future versions.
 
Recommended way to install pysub at the moment is by using `pip`:

`pip install git+https://github.com/Nikola-K/pysub.git` from the command line,

Or by downloading the repository and running `python setup.py install`.



##Command Line Interace Help

    usage: pysub [-h] [-s SUBFOLDER] [-l LANGUAGE] [-a] [-o] [-f FORMAT] [-r] [-p] folder

    Subtitle downloader for TV Shows

    positional arguments:
      folder                Folder which will be scanned for allowed video files,
                            and subtitles for those files will be downloaded

    optional arguments:
      -h, --help            show this help message and exit
      -s SUBFOLDER, --subfolder SUBFOLDER
                            Subfolder to save subtitles to, relative to original
                            video file path
                            
      -l LANGUAGE, --language LANGUAGE
                            Subtitle language, must be an ISO 639-2 Code i.e.
                            (eng,fre,deu) Default English(eng)
                            
      -a, --auto            Auto download subtitles for all files without prompt
      
      -o, --overwrite       Overwrite if subtitle with same filename exist.
      
      -f FORMAT, --format FORMAT
                            Additional file formats that will be checked, comma
                            separated, specify only file formats e.g.
                            'avix,temp,format2' (without quotes)
                            
      -r, --recursive       Search files recursively
      
      -p, --nfprompt        Prompt which subtitle to download if autodownloader
                            can't choose one

#License

    Copyright 2016 Nikola Kovacevic <nikolak@outlook.com>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

