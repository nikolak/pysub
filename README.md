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

----

usage: `ossd.py [-h] [-s SUBFOLDER] [-l LANGUAGE] [-a] folder`

Subtitle downloader for TV Shows

*positional arguments:*

  `folder`                - *Folder which will be scanned for allowed video files, and subtitles for those files will be downloaded*

*optional arguments:*

  `-h, --help`                          - *show this help message and exit*

  `-s SUBFOLDER, --subfolder SUBFOLDER` - *Subfolder to save subtitles to, relative to original video file path*

  `-l LANGUAGE, --language LANGUAGE`    - *Subtitle language, must be an ISO 639-1 Code i.e.(eng,fre,deu) Default English(eng)*

  `-a, --auto`                          - *Auto download subtitles for all files without prompt (Overwrites subtitles with same filename)*


Usage examples
--------

Auto download subtiles for all video files in the specified folder and save them to "Subs" subfolder


`$ python ossd.py -a -s Subs "/TV/The Office/Season 6"`
--------------------------------------------------
Searching subtitle for "The Office (US) - [06x01] - Gossip.flv" | (1/12)
Downloaded subtitle...
--------------------------------------------------
Searching subtitle for "The Office (US) - [06x02] - The Meeting.flv" | (2/12)
Can't match subtitle...

Search and ask which subtitle to download for specific file, subtitle will be saved in same directory as video file.


`$ python ossd.py "/The Office/Season 4/The Office (US) - Dunder Mifflin Infinity.flv"`
1: the.office.s04e02.dvdrip.xvid-orpheus.EN.srt | Downloads: 9338
2: The Office (US) - 04x02 - Dunder Mifflin infinity.srt | Downloads: 3800
3: the.office.402.pro.cap.EN.srt | Downloads: 1841
4: The.Office.US.S04E02.Dunder.Mifflin.Infinity.HDTV.XviD-XOR.srt | Downloads: 1242
5: The.Office.S04E02.Dunder Mifflin Infinity.720p.WEB-DL.AAC2.0.AVC-CtrlHD.srt | Downloads: 139
6: Hannah.Montana.S04E02.iNT.HDTV.XviD-OSHT.srt | Downloads: 171
Enter subtitle # to download or 's' - skip this file, 'a' - auto download, 'q' - quit
>>>