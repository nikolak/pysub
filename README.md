OSSubDownloader
===============

Simple CLI subtitle downloader written in python using [OpenSubtitles.org](http://www.opensubtitles.org/) API and [guessit](https://github.com/wackou/guessit) module (where available).

Licensed under GPLv3 - for more info see LICENSE file.

Subtitles can be searched for files in a folder or by specifying specific files to search subtitles for.

Subtitle search can be preformed in two ways either by using filename hash (works for every file) this
works great if the hash is in opensubtitles database, which if you downloaded file from streaming services
or something similar probably isn't the case. This also, in theory, works for movies.

The other way of searching for subtitles is using guessit library and gathering video information from filename.
This should work and offer more subtitle choices than hash search.
For this method to work well the filenames should contain idealy tv show name, season number and episode number
however some parts might be extracted from folder names, so having it in file isn't required but it is still
recommended. This doesn't work with anything other than TV Shows (e.g. movies)

It's recommended that you install `guessit` module by running `pip install guessit` to improve subtitle search accuracy.

Works best if the files are already properly named using [tvnamer](https://github.com/dbr/tvnamer) or similar software .

Subtitles are usually in `srt` format and are saved as `<original video filename>.<subtitle ext>` in same directory if no subfolder has been specified.

Optionally can overwrite already existing subtitle files, if they are named after original video file and exist in the directory you're ownloading subtitles to by using `-o` or `--overwrite` argument.



Usage arguments:
----

    usage: ossd.py [-h] [-s SUBFOLDER] [-l LANGUAGE] [-a] [-o] [-f FORMAT] folder

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
                            Subtitle language, must be an ISO 639-1 Code i.e.
                            (eng,fre,deu) Default English(eng)
      -a, --auto            Auto download subtitles for all files without prompt
      -o, --overwrite       Overwrite if subtitle with same filename exist.
      -f FORMAT, --format FORMAT
                            Additional file formats that will be checked, comma
                            separated,specify ony file formats e.g.
                            'avix,temp,format2' (without quotes)


Usage examples
--------

Search subtitles for all video files in a folder and save them to `Subs` subfolder in same directory.


    ~/tv/Sherlock$ ossd.py Season\ 3/ -s Subs -a
    --------------------------------------------------
    Searching subtitle for "Sherlock - [03x03] - His Last Vow.mkv" | (1/3)
    Downloaded subtitle...
    --------------------------------------------------
    Searching subtitle for "Sherlock - [03x02] - The Sign of Three.mkv" | (2/3)
    Downloaded subtitle...
    --------------------------------------------------
    Searching subtitle for "Sherlock - [03x01] - The Empty Hearse.mkv" | (3/3)
    Downloaded subtitle...
    ~/tv/Sherlock$ ls Season\ 3/Subs/
    Sherlock - [03x01] - The Empty Hearse.mkv.srt
    Sherlock - [03x02] - The Sign of Three.mkv.srt
    Sherlock - [03x03] - His Last Vow.mkv.srt
    ~/tv/Sherlock$

Search subtitle for one file, manually choose results, and save subtitle it in same folder:

    ~/tv/Sherlock$ ossd.py Season\ 3/Sherlock\ -\ \[03x01\]\ -\ The\ Empty\ Hearse.mkv
    --------------------------------------------------
    Searching subtitle for "Sherlock - [03x01] - The Empty Hearse.mkv" | (1/1)
    # : Downloads  Subtitle Name  * - Sync subtitle
    --------------------------------------------------
    1 :   67688    Sherlock (2010) - 03x01 - The Empty Hearse.x264-FoV.English.HI.orig.Addic7ed.com.srt
    2 :   14942    Sherlock.S03E01.The.Empty.Hearse.1080p.WEB-DL.DD5.1.H.264-BS.srt
    3 :   14670    Sherlock (2010) - 03x01 - The Empty Hearse.x264-FoV.English.HI.updated.Addic7ed.com.srt
    4 :   13100    Sherlock (2010) - 03x01 - The Empty Hearse.x264-FoV.English.updated.Addic7ed.com.srt
    5 :   12114    Sherlock S03E01 720p HDTV x264 [GlowGaze.Com].srt
    6 :   10685    Sherlock (2010) - 03x01 - The Empty Hearse.WEB-DL-1080p-BS.English.updated.Addic7ed.com.srt
    7 :    9200    Sherlock.3x01.The_Empty_Hearse_FoV_retimed.srt
    8 :    7386    Sherlock - S03E01 - The Empty Hearse.srt
    9 :    7143    Sherlock.S03E01.480p.HDTV.x264.350MB-Micromkv.srt
    10:    3130    Sherlock 3x01 The Empty Hearse.en.srt
    11:    2079    sherlock.s03e01.bdrip.x264-haggis.srt
    12:    1914    Sherlock 3x00 Many Happy Returns.srt
    13:    2530    The Adventures Of Sherlock Holmes [S06E02] - The Last Vampyre.EN.srt
    14:    5338    Sherlock.S03E01.480p.HDTV.x264.350MB-Micromkv.CHI.srt
    15:    667     1993-01-27 - Sherlock Holmes - The Last Vampyre - 100min.srt
    16:    592     The Last Vampyre.srt
    17:    940     Sherlock Holmes - The Last Vampyre.srt
    18:    350     S06E02 - The Last Vampyre.srt
    19:   67704*   Sherlock (2010) - 03x01 - The Empty Hearse.x264-FoV.English.HI.orig.Addic7ed.com.srt
    20:   13104*   Sherlock (2010) - 03x01 - The Empty Hearse.x264-FoV.English.updated.Addic7ed.com.srt
    21:   14671*   Sherlock (2010) - 03x01 - The Empty Hearse.x264-FoV.English.HI.updated.Addic7ed.com.srt
    return - download first, 's' - skip, 'a' - auto choose, 'q' - quit
    >>> 1
    Downloaded subtitle...
    ~/tv/Sherlock$

