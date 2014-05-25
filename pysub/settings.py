config = {
    'file_ext': [
        '.3g2', '.3gp', '.3gp2', '.3gpp', '.60d', '.ajp', '.asf', '.asx',
        '.avchd', '.avi', '.bik', '.bix', '.box', '.cam', '.dat', '.divx',
        '.dmf', '.dv', '.dvr-ms', '.evo', 'flc', '.fli', '.flic', '.flv',
        '.flx', '.gvi', '.gvp', '.h264', '.m1v', '.m2p', '.m2ts', '.m2v',
        '.m4e', '.m4v', '.mjp', '.mjpeg', '.mjpg', '.mkv', '.moov', '.mov',
        '.movhd', '.movie', '.movx', '.mp4', '.mpe', '.mpeg', '.mpg', '.mpv',
        '.mpv2', '.mxf', '.nsv', '.nut', '.ogg', '.ogm', '.omf', '.ps', '.qt',
        '.ram', '.rm', '.rmvb', '.swf', '.ts', '.vfw', '.vid', '.video',
        '.viv', '.vivo', '.vob', '.vro', '.wm', '.wmv', '.wmx', '.wrap',
        '.wvx', '.wx', '.x264', '.xvid'
    ],

    'sub_ext': [
        '.aqt', '.gsub', '.jss', '.sub', '.pjs', '.psb', '.rt', '.smi',
        '.stl', '.ssf', '.srt', '.ssa', '.ass', '.sub', '.usf'
    ],

    'overwrite': False,  # If subtitle exists in save location
    'auto_download': False,
    'not_found_prompt': False,
    'subfolder': None,  # Download to same directory as video if None
    'cutoff': 0.75,

    'lang': 'eng',  # Language to search
    'ua': 'ossubd',  # User Agent
    'server': 'http://api.opensubtitles.org/xml-rpc',
}

languages = {
    'Bosnian': 'bos',
    'Brazilian': 'pob',
    'Bulgarian': 'bul',
    'Croatian': 'hrv',
    'Czech': 'cze',
    'Danish': 'dan',
    'Dutch': 'dut',
    'Estonian': 'est',
    'English': 'eng',
    'Finnish': 'fin',
    'French': 'fre',
    'German': 'ger',
    'Greek': 'ell',
    'Icelandic': 'ice',
    'Inupiaq': 'ipk',
    'Irish': 'gle',
    'Italian': 'ita',
    'Japanese': 'jpn',
    'Latvian': 'lav',
    'Luxembourgish': 'ltz',
    'Macedonian': 'mac',
    'Montenegrin': 'mne',
    'Persian': 'per',
    'Pohnpeian': 'pon',
    'Polish': 'pol',
    'Portuguese': 'por',
    'Romanian': 'rum',
    'Russian': 'rus',
    'Sardinian': 'srd',
    'Serbian': 'scc',
    'Slovak': 'slo',
    'Slovenian': 'slv',
    'Spanish': 'spa',
    'Sundanese': 'sun',
    'Swedish': 'swe',
    'Thai': 'tha',
    'Turkish': 'tur',
    'Ukrainian': 'ukr',
    'Uzbek': 'uzb',
    'Vietnamese': 'vie',
    'Welsh': 'wel',
}
