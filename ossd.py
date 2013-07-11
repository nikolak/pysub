# Copyright (C) 2012, Nikola Kovcevic <nikolak@outlook.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from xmlrpclib import ServerProxy
import StringIO
import argparse
import gzip
import os
import struct
import sys
import urllib2

try:
    import guessit
except ImportError:
    print "Can't import guessit module, only subtitle searches based on file hashes can be preformed"

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

sub_language = 'eng'
opensub_domain = "http://api.opensubtitles.org/xml-rpc"
useragent = "ossubd"

server = ServerProxy(opensub_domain)

# overwrite = False
hash_search = False
AUTO_DOWNLOAD= False
SUBFOLDER="Subs"

def get_tests(file_name):
    session = server.LogIn("", "", sub_language, useragent)
    token = session["token"]
    ep_info = guessit.guess_episode_info(file_name)
    tv_show = ep_info['series']
    season = ep_info['season']
    episode = ep_info['episodeNumber']
    print ep_info
    query_info = ("%s S%.2dE%.2d" % (tv_show,
                                     int(season),
                                     int(episode),)
    ).replace(" ", "+")
    searchlist = []
    searchlist.append({'sublanguageid': sub_language, 'query': query_info})
    moviesList = server.SearchSubtitles(token, searchlist)
    print moviesList
    with open("query.log", "a") as q:
        q.write(file_name + "\n")
        q.write(str(moviesList) + "\n")
        q.write("\n\n\n")

# noinspection PyBroadException
def search_subtitles(file_list):
    # session = server.LogIn("", "", sub_language, useragent)
    # token = session["token"]
    count = 0
    done_count = 0
    for file_name in file_list:
        count += 1
        do_download = True
        file_name, file_extension = os.path.splitext(file_name)
        # print file_name, file_xtension
        print "-"*50
        print 'Searching subtitle for "{0}" | ({1}/{2})'.format(os.path.basename(file_name), count, len(file_list))

        # if os.path.exists(file_name + '.srt'):
        #     if overwrite:
        #         print 'Subtitle exist, but new one will be downloaded'
        #     else:
        #         print 'Subtitle already exists, skipping'
        #         do_download = False

        if do_download and hash_search:
            current_hash = get_hash(file_name + file_extension)
            file_size = os.path.getsize(file_name + file_extension)

            if current_hash is None:
                print "Can't calculate hash for {}".format(file_name)
                do_download = False
        elif do_download and not hash_search:
            ep_info = guessit.guess_episode_info(file_name)
            ep_info["filename"]=file_name
            tv_show = ep_info['series']
            season = ep_info['season']
            episode = ep_info['episodeNumber']

            query_info = ("%s S%.2dE%.2d" % (tv_show,
                                             int(season),
                                             int(episode),)
                                            ).replace(" ", "+")
        if do_download:
            searchlist = []
            if hash_search:
                searchlist.append({'sublanguageid': sub_language, 'moviehash': current_hash,
                                   'moviebytesize': str(file_size)})
            else:
                searchlist.append({'sublanguageid': sub_language, 'query': query_info})
            # moviesList = server.SearchSubtitles(token, searchlist)
            import json#XXX: Debug stuff
            moviesList = json.load(open("data.json"))
            if moviesList["status"]!="200 OK":
                print "Error searching for subtitles..."
            else:
                if moviesList['data']:
                    download_prompt(moviesList["data"],ep_info)
                #http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
                else:
                    print 'Couldn\'t find subtitles in {0} for {1}'.format(sub_language, file_name)
    print '-' * 30 + \
          '\nDownloaded subtitles for {0} out of {1} files'.format(done_count, len(file_list))




def download_prompt(subtitles_list, episode_info):
    if AUTO_DOWNLOAD:
        auto_download(subtitles_list,episode_info)
        return
    user_choice=""
    possible_choices=["a","q","s"]
    sub_dict={}
    count=1
    for subtitle in subtitles_list:
        print "{}: {} | Downloads: {:^}".format(count,
                                                subtitle["SubFileName"],
                                                subtitle["SubDownloadsCnt"],)
        sub_dict[count]={"SubFileName":subtitle["SubFileName"],
                         "SubDownloadLink":subtitle["SubDownloadLink"]}
        count+=1
    possible_choices.extend(sub_dict.keys())

    while user_choice not in possible_choices:
        inp=raw_input("Enter subtitle # to download or 's' - skip this file, 'a' - auto download, 'q' - quit\n>>")
        try:#Faster than .isdigit()
            user_choice=int(inp)
        except:
            user_choice=inp

        if user_choice not in possible_choices:
            print "invalid input"
    if user_choice in possible_choices: # if needed?
        if type(user_choice) is int:
            if sub_dict.get(user_choice,False) is not False:
                download_subtitle(sub_dict[user_choice], episode_info)
            else:
                print "Invalid input only subtitle choices from {} to {} are available".format(1,count)
        elif user_choice.lower()=="a":
            auto_download(subtitles_list,episode_info)
        elif user_choice.lower()=="q":
            print 'Quitting'
            exit()
        elif user_choice.lower()=="s":
            print "skipping..."
        else:
            print "Invalid input"



def auto_download(subtitles_list, ep_info):
    """
    episode_info:
    {u'mimetype': u'video/x-flv', u'episodeNumber': 11, u'container': u'flv',
    u'title': u'Adventures in Babysitting', u'series': u'Supernatural',
    u'type': u'episode', u'season': 7, u'filename':<full file path>}
    """
    if len(subtitles_list)<2:
        print "Only one subtitle found, this may be wrong one..."
        download_subtitle(subtitles_list[0])

    possible_matches=[]
    best_choice={"best":None,"downloads":0}

    for subtitle in subtitles_list:
        # if subtitle['SeriesSeason']==str(ep_info['season']) and \
        #                 subtitle['SeriesEpisode']==str(ep_info['episodeNumber']):
        #     # Subtitle is for same season and episode number, it's probably something we want
        #     # Wrong subtitles in most cases don't have same season/episode numbers
        #     # FIXME: Yeah, this isn't working as described above; too much "false positives"
        #     possible_matches.append(subtitle)
        #     print 'first if'
        subtitle_title_name=subtitle['MovieName'].replace("'","").replace('"','').lower()
        episode_title_name="{} {}".format(ep_info['series'].lower(),ep_info['title'].lower())
        if subtitle_title_name==episode_title_name:
            # Subtitle has same series name+episode name as our file.
            possible_matches.append(subtitle)

    for sub in possible_matches:
        # print sub['SubFileName']
        if int(sub["SubDownloadsCnt"])>best_choice["downloads"]:
            best_choice["best"]=sub
            best_choice["downloads"]=sub["SubDownloadsCnt"]
    print best_choice["best"],best_choice["downloads"]
    if best_choice["best"] is not None:
        download_subtitle(best_choice["best"],ep_info)
    else:
        print "Can't match subtitle..."


def download_subtitle(subtitle_info,ep_info):
    """
    episode_info:
    {u'mimetype': u'video/x-flv', u'episodeNumber': 11, u'container': u'flv',
    u'title': u'Adventures in Babysitting', u'series': u'Supernatural',
    u'type': u'episode', u'season': 7, u'filename':<full file path>}
    """
    download_url=subtitle_info["SubDownloadLink"]
    subtitle_folder=os.path.dirname(ep_info['filename'])
    subtitle_folder+="/" if SUBFOLDER is None else "/"+SUBFOLDER.replace("/","")+"/"
    subtitle_name=subtitle_folder+os.path.basename(ep_info["filename"])
    print "Downloading from {} and saving as {}.srt ".format(download_url,subtitle_name)

    if not os.path.isdir(subtitle_folder):
        os.mkdir(subtitle_folder)
        # TODO: Add exception handling, if we can't create folder we won't be able to save sub there (probably)

    sub_zip_file = urllib2.urlopen(download_url)
    try:
        sub_gzip = gzip.GzipFile(fileobj=StringIO.StringIO(sub_zip_file.read()))
        subtitle_content = sub_gzip.read()
        # TODO: Save subtitle as original filename.srt
        # TODO: Add support for subfolder to save ot
        with open(subtitle_name + '.srt', 'wb') as subtitle_output:
            subtitle_output.write(subtitle_content)
            # FIXME: This should be in try/except loop and notify of possible permission issues on fail
        print 'Done!'
    except:
        print "Couldn't save subtitle, permissions issue?"
    pass


def get_hash(name):
    """
    :param name: File path for which to calculate hash
    :return: Hash or None
    """
    try:
        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat)

        f = open(name, "rb")

        filesize = os.path.getsize(name)
        file_hash = filesize

        if filesize < 65536 * 2:
            return "SizeError"

        for x in range(65536 / bytesize):
            file_buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, file_buffer)
            file_hash += l_value
            file_hash &= 0xFFFFFFFFFFFFFFFF# to remain as 64bit number

        f.seek(max(0, filesize - 65536), 0)
        for x in range(65536 / bytesize):
            file_buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, file_buffer)
            file_hash += l_value
            file_hash &= 0xFFFFFFFFFFFFFFFF

        f.close()
        return "%016x" % file_hash

    except IOError:
        return None

if __name__ == '__main__':
    # filename="/media/8C82817682816614/TV/Supernatural/Season 7/Supernatural - [07x11] - Adventures in Babysitting.flv"
    # search_subtitles([filename])
    valid_files = []

    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=str,
                        help="Folder which will be scanned for allowed video files, and subtitles for those files will be downloaded")
    parser.add_argument("-o", "--output", type=str,
                         help="Subfolder to save subtitles to, relative to original video file path")
    parser.add_argument("-l", "--language", type=str,
                        help="Subtitle language, must be an ISO 639-1 Code i.e. (eng,fre,deu) Default English(eng); Full list http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes")
    parser.add_argument("-t","--type", type=str,
                        help="Subtitle search type 'hash' or 'filename'")
    parser.add_argument("-a","--auto", action="store_true",
                        help="Auto download subtitles for all files without prompt (Overwrites subtitles with same filename)")
    args = parser.parse_args()

    directory = args.folder
    if not directory.endswith('/'):
        directory += '/'
    if args.output:
        SUBFOLDER=args.output
    if args.type:
        if args.type=="hash":
            hash_search=True
        elif args.type=="filename":
            hash_search=False
        else:
            print "Invalid search type 'hash' or 'filename' are available options\n defaulting to hash search"
    if args.language:
        if len(args.language) == 3:
            sub_language = args.language.lower()
        else:
            print 'Argument not  ISO 639-1 Code check this for list of valid codes http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes'
            sys.exit()

    if args.auto:
        AUTO_DOWNLOAD=True
    print "Dir: {}, subfolder: {}, hash search type: {}, language: {}, auto download: {} ".format(
        directory,SUBFOLDER,hash_search, sub_language, AUTO_DOWNLOAD
    )
    names = os.listdir(directory)

    for name in names:
        file_name, file_extension = os.path.splitext(name)
        if file_extension in FILE_EXT:
            valid_files.append(directory + file_name + file_extension)

    search_subtitles(valid_files)
