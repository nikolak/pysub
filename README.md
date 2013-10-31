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

    usage: ossd.py [-h] [-s SUBFOLDER] [-l LANGUAGE] [-a] [-o] folder

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


Usage examples
--------

Search subtitle for one file even if subtitle already exists and save it to `Subs` subfolder in same directory as video file.


    python .\ossd.py 'D:\TV\Futurama\Season 4\Futurama - S04E01 - Kif Gets Knocked Up A Notch.avi' -s Subs -o
    --------------------------------------------------
    Searching subtitle for "Futurama - S04E01 - Kif Gets Knocked Up A Notch.avi" | (1/1)
    # : Downloads  Subtitle Name  * - Sync subtitle
    --------------------------------------------------
    1 :   12054    s4e01 - Kif Gets Knocked Up A Notch.srt
    2 :    981     19.srt
    3 :    148     futurama.s04e01.flangerrip.srt
    4 :    8058    Futurama - 4x01 - Roswell That Ends Well.srt
    5 :    1022    Futurama - 4x01 - Roswell that Ends Well.EN.sub
    6 :    321     Futurama [4x01] - Roswell That Ends Well - CiWaN.sub
    7 :   1490*    1.srt
    8 :   12054*   s4e01 - Kif Gets Knocked Up A Notch.srt
    9 :    789*    Futurama [5x05] - Kif Gets Knocked Up A Notch - CiWaN.sub
    return - download first, 's' - skip, 'a' - auto choose, 'q' - quit
    >>>