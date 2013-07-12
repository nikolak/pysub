OSSubDownloader
===============

Simple subtitle downloader written in python using [OpenSubtitles.org](http://www.opensubtitles.org/) API and guessit module.

Gathers video files from input folder and tries to download subtitles for those files.

Subtitle search can be preformed in two ways either by using filename hash (works for every file) this
works great if the hash is in opensubtitles database, which if you downloaded file from streaming services
or something similar probably isn't the case. This also, in theory, works for movies.

The other way of searching for subtitles is using guessit library and gathering video information from filename.
This should work and offer more subtitle choices than hash search.
For this method to work well the filenames should contain idealy tv show name, season number and episode number
however some parts might be extracted from folder names, so having it in file isn't required but it is still
recommended. This doesn't work with anything other than TV Shows (e.g. movies)

Works best if used in combination with [tvnamer](tvnamer) which you can use to set proper file name/info.

Subtitles are in `srt` format and are saved as `<original video filename>.srt` in same directory

Optionally can overwrite already existing subtitle files, if they're the same name as video file.

usage: `ossd.py [-h] [-o OUTPUT] [-l LANGUAGE] [-t TYPE] [-a] folder`

**positional arguments:**
  `folder`                              *Folder which will be scanned for allowed video files and subtitles for those files will be downloaded*

**optional arguments:**
  `-h, --help`                          *show this help message and exit*

  `-o OUTPUT, --output OUTPUT`          *Subfolder to save subtitles to, relative to original video file path*

  `-l LANGUAGE, --language LANGUAGE`    *Subtitle language, must be an ISO 639-1 Code i.e. (eng,fre,deu) Default English(eng); Full list http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes*

  `-t TYPE, --type TYPE`                *Subtitle search type 'hash' or 'filename'*

  `-a, --auto`                          *Auto download subtitles for all files without prompt (Overwrites subtitles with same filename)*


Usage examples
--------

Search subtitles based on filename and save them to 'Subs' subdirectory in the same folder as files.
`$ python ossd.py -o Subs -t filename "/media/8C82817682816614/TV/The Office/Season 4"`


Output for the  first file:


--------------------------------------------------
Searching subtitle for "The Office (US) - [04x01] Fun Run" | (1/14)
1: the.office.s04e01.hdtv.xvid-xor.[VTV].srt | Downloads: 13159
2: the.office.s04e01.dvdrip.xvid-orpheus.EN.srt | Downloads: 7909
Enter subtitle # to download or 's' - skip this file, 'a' - auto download, 'q' - quit
>>1
Done!

----


Search subtitles based on filename and save them to 'Subs' subdirectory in the same folder as files, don't prompt user, auto download.
`$ python ossd.py -o Subs -t filename "/media/8C82817682816614/TV/IT Crowd/Season 4" -a`


Output for the first file:


--------------------------------------------------
Searching subtitle for "The IT Crowd - [04x03] - Something Happened" | (1/4)
Done!

**Note:** The output might not be 100% the same as above due to some changes in the code, but in essence it should show same type of message.



