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
from objects import Video

from default_config import config

import main_ui


class PySubGUI(QDialog, main_ui.Ui_Dialog):
    def __init__(self, parent=None):
        super(PySubGUI, self).__init__(parent)
        self.config=config
        self.setupUi(self)

        self.file_model = QStandardItemModel(0, 5, parent)
        self.file_model.setHeaderData(0, Qt.Horizontal, '#')
        self.file_model.setHeaderData(1, Qt.Horizontal, 'File')
        self.file_model.setHeaderData(2, Qt.Horizontal, 'Series')
        self.file_model.setHeaderData(3, Qt.Horizontal, 'Season')
        self.file_model.setHeaderData(4, Qt.Horizontal, 'Episode')

        self.sub_model = QStandardItemModel(0, 4, parent)
        self.sub_model.setHeaderData(0, Qt.Horizontal, '#')
        self.sub_model.setHeaderData(1, Qt.Horizontal, 'Downloads')
        self.sub_model.setHeaderData(2, Qt.Horizontal, 'File Name')
        self.sub_model.setHeaderData(3, Qt.Horizontal, 'Synced')

        self.file_list.setModel(self.file_model)
        self.video_files=[]

    @Slot()
    def on_btn_add_folder_clicked(self):
        directory = QFileDialog.getExistingDirectory(self, "Add Folder",
                                                           QDir.currentPath(),
                                                           )
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
        pass

    @Slot()
    def on_btn_skip_clicked(self):
        pass

    @Slot()
    def on_btn_dl_sel_clicked(self):
        print self.treeView.selectedIndexes()


    def parse_files(self, list_files):
        for item in list_files:
            item="".join(item)
            if os.path.splitext(item)[1] in config['file_ext']:
                self.video_files.append(Video(item, self.config))
        self.update_file_list()

    def update_file_list(self):
        for counter, video in enumerate(self.video_files):
            self.file_model.setItem(counter, 0, QStandardItem(str(counter)))
            self.file_model.setItem(counter, 1, QStandardItem(video.file_name))
            self.file_model.setItem(counter, 2, QStandardItem(video.ep_info.get('series','Unknown')))
            self.file_model.setItem(counter, 3, QStandardItem(str(video.ep_info.get('season','Unknown'))))
            self.file_model.setItem(counter, 4, QStandardItem(str(video.ep_info.get('episodeNumber', 'Unknown'))))
        self.file_list.setModel(self.file_model)
        for i in range(5):
            self.file_list.resizeColumnToContents(i)

        if len(self.video_files)>0:
            self.btn_start.setEnabled(True)
def main():
    app = QApplication(sys.argv)
    form = PySubGUI()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()