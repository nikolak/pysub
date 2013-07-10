OSSubDownloader
===============

Simple subtitle downloader written in python using [OpenSubtitles.org](http://www.opensubtitles.org/) API.

Parses input folder for supported video files extentions and then uses opensubtitles.org api to search and download subtitles for that video file.

Works best if used in combination with [tvnamer](tvnamer) which you can use to set proper file name/info.

Dependencies: guessit lib
Subtitles are in `srt` format and are saved as `<original video filename>.srt` in same directory

Optionally can overwrite already existing subtitle files, if they're the same name as video file.


usage: `ossd.py [-h] [-o] [-l LANGUAGE] folder`


**positional arguments:**

  `folder`                *Folder which will be scanned for allowed video files, and subtitles for those files will be downloaded.*

**optional arguments:**

  `-h, --help`            *show this help message and exit*
  
  `-o, --overwrite`       *Downloads subtitle file even if subtitle with <video filename>.srt already exists; overwrites existing file*
                        
  `-l LANGUAGE, --language LANGUAGE` *Subtitle language, must be an ISO 639-1 Code (en,fr,de, etc) Default English(en); Full list http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes*
`                        

Usage examples
--------

Download subtitles in default language(English), don't download if subtitle already exist with same filename

`python ossd.py "D:\TV\The Wire\Season 3"`

Download subtitles in default language(English), download even if subtitle already exist, this overwrites the existing one.

`python ossd.py "D:\TV\The Wire\Season 3" -o`

Download subtitles in German 

`python ossd.py "D:\TV\The Wire\Season 3" -l de`
