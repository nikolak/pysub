#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle downloader using OpenSubtitles.org API

GUI user interface
"""
# Copyright 2014 Nikola Kovacevic <nikolak@outlook.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

from PySide.QtCore import *
from PySide.QtGui import *

from pysub_objects import Video, OpenSubtitlesServer
from default_config import config
import main_ui


class PySubGUI(QDialog, main_ui.Ui_Dialog):
    def __init__(self, parent=None):
        """
        Initialize GUI and set up variables.

        Attributes:
            file_model: QStandardItemModel that contains header data
                        for list of filenames in QTreeView
            sub_model: QStandardItemModel that contains header data
                        for list of subtitles in QTreeView
            config: dictionary with (default) configuration values for
                    server url, user_agent, language
            video_files: list of video files added for which subtitles
                         will be searched for
            current_video: Instance of Video class/object for which
                           the subtitle is being chosen for right now
            download_mode: boolean value that indicates whether or not
                           subtitles are being searched for files
                           or is the GUI still in adding files mode
            server: Instance of OpenSubtitlesServer class
        """
        super(PySubGUI, self).__init__(parent)
        self.setupUi(self)

        self.file_model = QStandardItemModel(0, 6, parent)
        self.sub_model = QStandardItemModel(0, 4, parent)
        self.set_header_data()
        self.populate_languages()

        self.file_list.setModel(self.file_model)

        self.config = config
        self.video_files = []
        self.current_video = None
        self.download_mode = False

        self.server = OpenSubtitlesServer("http://localhost:8000",
                                          config['ua'],
                                          config['lang'])

        self.server.login()

    def set_header_data(self):
        """
        Sets header data for file_model and sub_model
        created in __init__ function
        """
        self.file_model.setHeaderData(0, Qt.Horizontal, '#')
        self.file_model.setHeaderData(1, Qt.Horizontal, 'File')
        self.file_model.setHeaderData(2, Qt.Horizontal, 'Series')
        self.file_model.setHeaderData(3, Qt.Horizontal, 'Season')
        self.file_model.setHeaderData(4, Qt.Horizontal, 'Episode')
        self.file_model.setHeaderData(5, Qt.Horizontal, 'Sub Exists')

        self.sub_model.setHeaderData(0, Qt.Horizontal, '#')
        self.sub_model.setHeaderData(1, Qt.Horizontal, 'Downloads')
        self.sub_model.setHeaderData(2, Qt.Horizontal, 'File Name')
        self.sub_model.setHeaderData(3, Qt.Horizontal, 'Synced')

    def populate_languages(self):
        """
        Adds list of available languages for which subtitles can
        be searched for to the language picker in Settings tab.
        """
        self.cbo_language.addItems(["English", "Serbian"])

    @Slot()
    def on_btn_add_folder_clicked(self):
        """
        Add folder button connection.

        Pass all files in the selected folder to the parse_files
        function which creates class instances and adds them to the
        video_files list.
        """
        directory = QFileDialog.getExistingDirectory(self,
                                                     "Add Folder",
                                                     QDir.currentPath())

        if directory:
            self.parse_files([directory + os.sep + name
                              for name in os.listdir(directory)])

    @Slot()
    def on_btn_add_file_clicked(self):
        """
        Add file(s) button:

        Pass the file selected to the parse_files function.
        """
        files = QFileDialog.getOpenFileNames(self, "Add Files",
                                             QDir.currentPath())
        if files:
            self.parse_files(files[0])

    @Slot()
    def on_btn_start_clicked(self):
        """
        Start Searching button:

        Set the maximum value of progress bar, which is equal to the
        number of valid files there are in the list

        If we're in download mode this button behaves as "stop search"
        button, changes mode, sets progresbar to 0, removes sub listing
        and re-freshes file listing.

        Otherwise it sets progressbar to appropriate max value,
        changes mode(disables add buttons/enable sub control buttons)
        and start search for subtitles on the next file
        """
        if self.download_mode:
            self.change_mode()
            self.update_file_list()
            self.overall_progress.setValue(0)
        else:
            self.overall_progress.setMaximum(len(self.video_files))
            self.change_mode()
            self.search_next()

    @Slot()
    def on_btn_skip_clicked(self):
        """
        Skip button:

        Skips current file and doesn't download any subtitles for it
        """
        self.search_next()

    @Slot()
    def on_btn_auto_dl_clicked(self):
        """
        Auto choose button:

        Auto choose from current subtitle list for this file only.

        Since all the logic is contained in the Video class instance
        just rely on that to do the job
        """
        # TODO: Video doesn't return anything, but it prints that the choosing
        # failed if nothing is found, maybe add True/False return value
        # and (optionally) implement some additional features if the auto
        # download fails, like e.g. "pick manually if auto download fails"
        self.current_video.auto_download()
        self.search_next()

    @Slot()
    def on_btn_dl_sel_clicked(self):
        """
        Download button:

        Downloads current selected subtitle.

        Basically the subtitle position in the list is equal to its
        value in first column so we just use that, convert it to int
        and use it as list index and then we execute the download function
        that all Subtitle class instances have.
        """
        if not any(self.file_list.selectedIndexes()):
            return
        sub_index = int(self.file_list.selectedIndexes()[0].data())
        self.current_video.subtitles[sub_index].download()

    @Slot()
    def on_btn_save_conf_clicked(self):
        """
        Save current config button:
        """
        pass

    @Slot()
    def on_btn_reset_conf_clicked(self):
        """
        Reset config to default values.
        """
        pass

    def parse_files(self, list_files):
        """
        Makes Video instances for each file that has valid extension
        and adds it to video_files list.

        Arguments:
            list_files: List of absolute file paths
        """
        for item in list_files:
            if os.path.splitext(item)[1] in config['file_ext']:
                self.video_files.append(Video(item, self.config))

        self.update_file_list()

    def update_file_list(self):
        """
        Creates the rows and assigns right data for the video files

        For each Video class instance in video_files list a new row
        is created, with it's position in a list as "#" identifier
        and other useful rows.

        If the video_files list has more than 1 valid item visible
        enable the Start Search button, otherwise disable it.
        """
        self.file_model.clear()
        for row_num, video in enumerate(self.video_files):
            vid_index = QStandardItem(str(row_num))
            vid_filename = QStandardItem(video.file_name)
            vid_series = QStandardItem(video.ep_info.get('series', 'Unknown'))
            vid_season = QStandardItem(str(video.ep_info.get('season',
                                                             'Unknown')))
            vid_episode = QStandardItem(str(video.ep_info.get('episodeNumber',
                                                              'Unknown')))
            vid_sub_exist = QStandardItem(["No", "Yes"][video.sub_exists])

            self.file_model.setItem(row_num, 0, vid_index)
            self.file_model.setItem(row_num, 1, vid_filename)
            self.file_model.setItem(row_num, 2, vid_series)
            self.file_model.setItem(row_num, 3, vid_season)
            self.file_model.setItem(row_num, 4, vid_episode)
            self.file_model.setItem(row_num, 5, vid_sub_exist)

        self.file_list.setModel(self.file_model)

        for i in range(5):
            self.file_list.resizeColumnToContents(i)

        if len(self.video_files) > 0:
            self.btn_start.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)

    def make_subtitle_list(self, video):
        """
        Creates the rows and assigns right data for the subtitle links

        For each Subtitle class instance in the Video instacne subtitles
        attribute row with the appropriate data (where found) is created,
        with subtitle position in a list as "#" identifier
        and other useful rows.

        Args:
            video: Instance of Video class with at least one subtitle
                   in its subtitles variable
        """
        for row_num, sub in enumerate(video.subtitles):
            sub_index = QStandardItem(str(row_num))
            sub_downloads = QStandardItem(str(sub.download_count))
            sub_name = QStandardItem(sub.sub_filename)
            sub_synced = QStandardItem(["No", "Yes"][sub.synced])

            self.sub_model.setItem(row_num, 0, sub_index)
            self.sub_model.setItem(row_num, 1, sub_downloads)
            self.sub_model.setItem(row_num, 2, sub_name)
            self.sub_model.setItem(row_num, 3, sub_synced)

        self.file_list.setModel(self.sub_model)

        for i in range(5):
            self.file_list.resizeColumnToContents(i)

    def search_next(self):
        """
        Sets the current_video variable to the first item in the
        video_files list, if any exist, and removes it from the list.
        for all intents and purposes, as far as GUI knows, this file has been
        processed - even if user presses the Stop button while on it

        If no files exist, but this is still called, for example
        by clicking skip button on the last subtitle
        change_mode and update file list is executed.

        If any files are left in the video_files list those will be displayed
        in the QTreeView via update_file_list() function
        """
        if any(self.video_files):
            self.current_video = self.video_files[0]
            self.video_files.pop(0)
        else:
            self.change_mode()
            self.update_file_list()
            return

        progress = self.overall_progress.maximum() - len(self.video_files)
        self.overall_progress.setValue(progress)

        overwrite = self.chk_overwrite.checkState() == Qt.CheckState.Checked
        if self.current_video.sub_exists and not overwrite:
            return

        if self.current_video.file_search_query:
            self.current_video.parse_response(self.server.query(
                self.current_video.file_search_query,
                desc="File Based Search"))

        if self.current_video.hash_search_query:
            self.current_video.parse_response(self.server.query(
                self.current_video.hash_search_query,
                desc="Hash Based Search"))

        # TODO: Remove print. add notification?
        if not self.current_video.subtitles:
            print("Couldn't find subtitles in "
                  "{} for {}".format(config['lang'],
                                     self.current_video.file_path))
        else:
            self.make_subtitle_list(self.current_video)

    def change_mode(self):
        """
        When changing to download mode all subtitle related buttons
        skip, auto download, download selected - are enabled
        add folder and add file(s) buttons are disabled.
        "Start search" text is changed to "stop search

        When changing from download mode the opposite is done.
        """
        if self.download_mode:
            self.btn_add_file.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_skip.setEnabled(False)
            self.btn_auto_dl.setEnabled(False)
            self.btn_dl_sel.setEnabled(False)
            self.btn_start.setText("Start Search")
            self.download_mode = False
        else:
            self.btn_add_file.setEnabled(False)
            self.btn_add_folder.setEnabled(False)
            self.btn_skip.setEnabled(True)
            self.btn_auto_dl.setEnabled(True)
            self.btn_dl_sel.setEnabled(True)
            self.btn_start.setText("Stop Search")
            self.download_mode = True

def main():
    app = QApplication(sys.argv)
    form = PySubGUI()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
