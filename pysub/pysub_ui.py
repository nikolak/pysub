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
# http://www.apache.org/licenses/LICENSE-2.0
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

from pysub_objects import Video, OpenSubtitlesServer
import ui_design
import settings


class PySubGUI(QDialog, ui_design.Ui_Dialog):
    def __init__(self, parent=None):
        super(PySubGUI, self).__init__(parent)
        self.setupUi(self)

        self.file_model = QStandardItemModel(0, 6, parent)
        self.sub_model = QStandardItemModel(0, 4, parent)
        self.file_list.setModel(self.file_model)

        self.config = None
        self.server = None
        self.__load_config()

        self.video_files = []
        self.c_video_index = -1
        self.download_mode = False
        self.update_file_table()

    def __load_config(self, force_default=False):
        if force_default:
            self.config = settings.default_config
        else:
            self.config = settings.get_config()

        if self.server:
            self.server = None

        self.__update_settings_ui()


    def __update_settings_ui(self):
        auto_dl = self.config['auto_download']
        self.chk_auto_dl.setCheckState(Qt.Checked if auto_dl else Qt.Unchecked)

        ovw = self.config['overwrite']
        self.chk_overwrite.setCheckState(Qt.Checked if ovw else Qt.Unchecked)

        prompt = self.config['not_found_prompt']
        self.chk_prompt.setCheckState(Qt.Checked if prompt else Qt.Unchecked)

        self.lne_save_folder.setText(self.config['subfolder'])

        lang_list = sorted(self.config['languages'].keys())
        # Move English and Serbian to the top of the list
        lang_list.insert(0, lang_list.pop(lang_list.index(self.config['lang_name'])))
        self.cbo_language.addItems(lang_list)

        # Advanced Settings
        self.txt_file_ext.setPlainText(json.dumps(self.config['file_ext']))
        self.txt_sub_ext.setPlainText(json.dumps(self.config['sub_ext']))
        self.txt_lang_json.setPlainText(json.dumps(self.config['languages']))

        self.sl_label.setText("{}".format(int(self.config['cutoff'] * 100)))
        self.sl_cutoff.setValue(int(self.config['cutoff'] * 100))

        self.lne_ua.setText(self.config['ua'])
        self.lne_server.setText(self.config['server'])

    @Slot()
    def on_btn_save_conf_clicked(self):
        try:
            new_config = {}
            new_config['file_ext'] = json.loads(self.txt_file_ext.toPlainText())
            new_config['sub_ext'] = json.loads(self.txt_sub_ext.toPlainText())
            new_config['overwrite'] = self.chk_overwrite.checkState() == Qt.Checked
            new_config['auto_download'] = self.chk_auto_dl.checkState() == Qt.Checked
            new_config['not_found_prompt'] = self.chk_prompt.checkState() == Qt.Checked
            new_config['subfolder'] = None if self.lne_save_folder.text() == "" else self.lne_save_folder.text()
            new_config['cutoff'] = float(self.sl_label.text()) / 100.00
            new_config['languages'] = json.loads(self.txt_lang_json.toPlainText())
            new_config['lang'] = self.config['languages'].get(self.cbo_language.currentText())
            if not new_config['lang']:
                raise ValueError("Wrong lang value")
            new_config['lang_name'] = self.cbo_language.currentText()
            new_config['ua'] = self.lne_ua.text()
            new_config['server'] = self.lne_server.text()
        except:
            QMessageBox.critical(self, "Save error",
                                 "Saving new configuration has failed."
                                 "Fix the configuration options manually "
                                 "or reset to default settings and then save")
            return

        settings.save_config(new_config)

        self.__load_config()

    def __login_to_server(self):
        if self.server:
            self.server.log_out()

        self.server = OpenSubtitlesServer(self.config['server'],
                                          self.config['ua'],
                                          self.config['lang'])
        self.server.login()

    @Slot()
    def on_btn_add_folder_clicked(self):
        directory = QFileDialog.getExistingDirectory(self,
                                                     "Add Folder",
                                                     QDir.homePath())

        if directory:
            self.add_files(
                [directory + os.sep + name for name in os.listdir(directory)])

    @Slot()
    def on_btn_add_file_clicked(self):
        files = QFileDialog.getOpenFileNames(self, "Add Files",
                                             QDir.homePath())
        if files:
            self.add_files(files[0])

    @Slot()
    def on_btn_start_clicked(self):
        self.change_mode()

    @Slot()
    def on_btn_skip_clicked(self):
        if self.btn_skip.text() == "Remove selected":
            rows = self.file_list.selectionModel().selectedRows()
            rm_indexes = [row.row() for row in rows]
            if rm_indexes:
                self.video_files = [v for v in self.video_files
                                    if self.video_files.index(
                        v) not in rm_indexes]
                self.update_file_table()
        else:
            self.search()

    @Slot()
    def on_btn_auto_dl_clicked(self):
        if self.btn_auto_dl.text() == "Remove all":
            self.video_files = []
            self.update_file_table()
        else:
            downloaded = self.video_files[self.c_video_index].auto_download()
            if self.config['not_found_prompt'] and not downloaded:
                self.search(index=self.c_video_index)
            else:
                self.search()

    @Slot()
    def on_btn_dl_sel_clicked(self):
        if self.file_list.selectionModel().selectedRows():
            try:
                sub_index = self.file_list.selectionModel().selectedRows()[0].row()
            except:  # no sub selected
                QMessageBox.information(self, "Not selected",
                                        "Please select the subtitle  you want to download"
                                        "before clicking 'Download' button")
                return
        else:
            return

        self.video_files[self.c_video_index].subtitles[sub_index].download()
        self.search()

    @Slot()
    def on_btn_reset_conf_clicked(self):
        self.__load_config(force_default=True)


    def change_mode(self):
        if self.download_mode:
            self.download_mode = False

            self.btn_add_folder.setEnabled(True)
            self.btn_add_file.setEnabled(True)

            self.btn_start.setText("Start searching")

            self.btn_skip.setEnabled(False)
            self.btn_auto_dl.setEnabled(False)
            self.btn_dl_sel.setEnabled(False)

            self.c_video_index = -1

            self.update_file_table()
        else:
            self.download_mode = True

            self.btn_add_folder.setEnabled(False)
            self.btn_add_file.setEnabled(False)
            self.btn_start.setText("Stop")

            self.btn_skip.setEnabled(True)
            self.btn_auto_dl.setEnabled(True)
            self.btn_dl_sel.setEnabled(True)

            self.btn_skip.setText("Skip")
            self.btn_auto_dl.setText("Auto download")
            self.search()


    def add_files(self, file_list):
        for video_file in file_list:
            if os.path.splitext(video_file)[1] in self.config['file_ext']:
                new_video = Video(video_file, self.config)
                self.video_files.append(new_video)
            else:
                pass

        if self.file_list:
            self.update_file_table()
            self.btn_start.setEnabled(True)

    def auto_search_all(self):
        for index, video in enumerate(self.video_files):
            if self.config['not_found_prompt'] and not video.auto_download():
                self.search(index)

        self.update_file_table()

    def search(self, index=None):
        if index:
            self.c_video_index = index
        else:
            self.c_video_index += 1

        if self.c_video_index >= len(self.video_files):
            self.change_mode()
            return
        else:
            video = self.video_files[self.c_video_index]
        if video.sub_exists and not self.config['overwrite']:
            self.search()
        else:
            if not video.subtitles:
                try:
                    if not self.server:
                        self.__login_to_server()

                    if video.file_search_query:
                        video.parse_response(self.server.query(video.file_search_query,
                                                               desc="File Based Search"))
                    if video.hash_search_query:
                        video.parse_response(self.server.query(video.hash_search_query,
                                                               desc="Hash Based Search"))
                except:
                    pass
            if self.config['auto_download'] and video.subtitles:
                if self.config['not_found_prompt'] and not video.auto_download():
                    self.update_sub_table(video)
                    return
            else:
                self.update_sub_table(video)
                return

    def update_file_table(self):

        self.status_label.setText("List of video files:")

        self.file_model.clear()

        for row_num, video in enumerate(self.video_files):
            vid_index = QStandardItem(str(row_num))
            vid_filename = QStandardItem(video.file_name)
            vid_series = QStandardItem(video.ep_info.get('series', 'Unknown'))
            vid_season = QStandardItem(str(video.ep_info.get('season', 'Unknown')))
            vid_episode = QStandardItem(str(video.ep_info.get('episodeNumber', 'Unknown')))
            vid_sub_exist = QStandardItem("Yes" if video.sub_exists else "No")

            self.file_model.setItem(row_num, 0, vid_index)
            self.file_model.setItem(row_num, 1, vid_filename)
            self.file_model.setItem(row_num, 2, vid_series)
            self.file_model.setItem(row_num, 3, vid_season)
            self.file_model.setItem(row_num, 4, vid_episode)
            self.file_model.setItem(row_num, 5, vid_sub_exist)

        self.file_model.setHeaderData(0, Qt.Horizontal, '#')
        self.file_model.setHeaderData(1, Qt.Horizontal, 'File')
        self.file_model.setHeaderData(2, Qt.Horizontal, 'Series')
        self.file_model.setHeaderData(3, Qt.Horizontal, 'Season')
        self.file_model.setHeaderData(4, Qt.Horizontal, 'Episode')
        self.file_model.setHeaderData(5, Qt.Horizontal, 'Sub Exists')

        self.file_list.setModel(self.file_model)

        for i in range(5):
            self.file_list.resizeColumnToContents(i)

        if self.video_files:
            self.btn_start.setEnabled(True)

            self.btn_skip.setText("Remove selected")
            self.btn_skip.setEnabled(True)

            self.btn_auto_dl.setText("Remove all")
            self.btn_auto_dl.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)

            self.btn_skip.setText("")
            self.btn_skip.setEnabled(False)

            self.btn_auto_dl.setText("")
            self.btn_auto_dl.setEnabled(False)

    def update_sub_table(self, video):
        self.sub_model.clear()

        self.status_label.setText("Subtitles for: '{}'".format(
            video.file_name))

        if not video.subtitles:
            self.sub_model.setItem(0, 0, QStandardItem("N/A"))
            self.sub_model.setItem(0, 1, QStandardItem("N/A"))
            self.sub_model.setItem(0, 2, QStandardItem("Subtitle not found"))
            self.sub_model.setItem(0, 3, QStandardItem("N/A"))
            self.btn_dl_sel.setEnabled(False)
            self.btn_auto_dl.setEnabled(False)

        else:
            for row, sub in enumerate(video.subtitles):
                sub_index = QStandardItem(str(row))
                sub_downloads = QStandardItem(str(sub.download_count))
                sub_name = QStandardItem(sub.sub_filename)
                sub_synced = QStandardItem("Yes" if sub.synced else "No")

                self.sub_model.setItem(row, 0, sub_index)
                self.sub_model.setItem(row, 1, sub_downloads)
                self.sub_model.setItem(row, 2, sub_name)
                self.sub_model.setItem(row, 3, sub_synced)

            self.btn_dl_sel.setEnabled(True)
            self.btn_auto_dl.setEnabled(True)
            self.btn_skip.setEnabled(True)

        self.sub_model.setHeaderData(0, Qt.Horizontal, '#')
        self.sub_model.setHeaderData(1, Qt.Horizontal, 'Downloads')
        self.sub_model.setHeaderData(2, Qt.Horizontal, 'File Name')
        self.sub_model.setHeaderData(3, Qt.Horizontal, 'Synced')

        self.file_list.setModel(self.sub_model)

        for i in range(3):
            self.file_list.resizeColumnToContents(i)


def main():
    app = QApplication(sys.argv)
    form = PySubGUI()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
