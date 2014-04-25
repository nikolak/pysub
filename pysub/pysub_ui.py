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
import json
from PySide.QtCore import *
from PySide.QtGui import *
from objects import Video,OpenSubtitlesServer

from default_config import config

import main_ui


class PySubGUI(QDialog, main_ui.Ui_Dialog):
    def __init__(self, parent=None):
        super(PySubGUI, self).__init__(parent)
        self.setupUi(self)

        self.file_model = QStandardItemModel(0, 6, parent)
        self.sub_model = QStandardItemModel(0, 4, parent)
        self.set_header_data()
        self.populate_languages()

        self.file_list.setModel(self.file_model)

        self.config = config
        self.video_files=[]
        self.current_video=None
        self.max_progressbar=None
        self.download_mode=False

        self.server=OpenSubtitlesServer("http://localhost:8000",
                                        config['ua'],
                                        config['lang'])

        self.server.login()

    def set_header_data(self):
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
        self.cbo_language.addItems(["English","Serbian"])

    @Slot()
    def on_btn_add_folder_clicked(self):
        directory = QFileDialog.getExistingDirectory(self, "Add Folder",QDir.currentPath())

        if directory:
            self.parse_files([directory +os.sep+ name for name in os.listdir(directory)
                          if os.path.splitext(name)[1] in self.config['file_ext']])

    @Slot()
    def on_btn_add_file_clicked(self):
        files = QFileDialog.getOpenFileNames(self, "Add Files",
                                             QDir.currentPath())
        if files:
            self.parse_files(files[0])

    @Slot()
    def on_btn_start_clicked(self):
        self.overall_progress.setMaximum(len(self.video_files))
        self.change_mode()

    @Slot()
    def on_btn_skip_clicked(self):
        self.search_next()

    @Slot()
    def on_btn_auto_dl_clicked(self):
        self.current_video.auto_download()
        self.search_next()

    @Slot()
    def on_btn_dl_sel_clicked(self):
        if not any(self.file_list.selectedIndexes()):
            return
        sub_index=int(self.file_list.selectedIndexes()[0].data())
        print sub_index
        # self.current_video.subtitles[sub_index].download()

    @Slot()
    def on_btn_save_conf_clicked(self):
        pass

    @Slot()
    def on_btn_reset_conf_clicked(self):
        pass


    def parse_files(self, list_files):
        for item in list_files:
            item="".join(item)
            if os.path.splitext(item)[1] in config['file_ext']:
                self.video_files.append(Video(item, self.config))
        self.update_file_list()

    def update_file_list(self):
        self.file_model.clear()
        for counter, video in enumerate(self.video_files):
            self.file_model.setItem(counter, 0, QStandardItem(str(counter)))
            self.file_model.setItem(counter, 1, QStandardItem(video.file_name))
            self.file_model.setItem(counter, 2, QStandardItem(video.ep_info.get('series','Unknown')))
            self.file_model.setItem(counter, 3, QStandardItem(str(video.ep_info.get('season','Unknown'))))
            self.file_model.setItem(counter, 4, QStandardItem(str(video.ep_info.get('episodeNumber', 'Unknown'))))
            self.file_model.setItem(counter, 5, QStandardItem(["No","Yes"][video.sub_exists]))

        self.file_list.setModel(self.file_model)

        for i in range(5):
            self.file_list.resizeColumnToContents(i)

        if len(self.video_files)>0:
            print len(self.video_files)
            self.btn_start.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)

    def search_next(self):
        if any(self.video_files):
            self.current_video=self.video_files[0]
            self.video_files.pop(0)
        else:
            self.change_mode()
            return
        self.overall_progress.setValue(self.overall_progress.maximum()-len(self.video_files))
        if self.current_video.sub_exists and self.chk_overwrite.checkState() == Qt.CheckState.Unchecked:
            return


        if self.current_video.file_search_query:
            self.current_video.parse_response(self.server.query(self.current_video.file_search_query,
                                              desc="File Based Search"))

        if self.current_video.hash_search_query:
            self.current_video.parse_response(self.server.query(self.current_video.hash_search_query,
                                              desc="Hash Based Search"))

        if not self.current_video.subtitles:
            print("Couldn't find subtitles in "
                  "{} for {}".format(config['lang'], self.current_video.file_path))
        else:
            self.make_subtitle_list(self.current_video.subtitles)



    def make_subtitle_list(self, subtitles):
        """
        self.sub_model.setHeaderData(0, Qt.Horizontal, '#')
        self.sub_model.setHeaderData(1, Qt.Horizontal, 'Downloads')
        self.sub_model.setHeaderData(2, Qt.Horizontal, 'File Name')
        self.sub_model.setHeaderData(3, Qt.Horizontal, 'Synced')
        """
        for counter, sub in enumerate(subtitles):
            self.sub_model.setItem(counter, 0, QStandardItem(str(counter)))
            self.sub_model.setItem(counter, 1, QStandardItem(str(sub.download_count)))
            self.sub_model.setItem(counter, 2, QStandardItem(sub.sub_filename))
            self.sub_model.setItem(counter, 3, QStandardItem(["No","Yes"][sub.synced]))

        self.file_list.setModel(self.sub_model)

        for i in range(5):
            self.file_list.resizeColumnToContents(i)


    def change_mode(self):
        if self.download_mode:
            self.btn_add_file.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_skip.setEnabled(False)
            self.btn_auto_dl.setEnabled(False)
            self.btn_dl_sel.setEnabled(False)
            self.btn_start.setText("Start Search")
            self.download_mode = False
            self.update_file_list()
        else:
            self.btn_add_file.setEnabled(False)
            self.btn_add_folder.setEnabled(False)
            self.btn_skip.setEnabled(True)
            self.btn_auto_dl.setEnabled(True)
            self.btn_dl_sel.setEnabled(True)
            self.btn_start.setText("Stop Search")
            self.download_mode = True
            self.search_next()

def main():
    app = QApplication(sys.argv)
    form = PySubGUI()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()