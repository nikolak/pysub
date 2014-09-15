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
import settings
from ui import main_window


video_files = []
to_process = []
video_config = None


class addThread(QThread):
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        self.running = True
        for number, file_path in enumerate(to_process):
            if not self.running:
                break
            new_video = Video(file_path, video_config)
            video_files.append(new_video)
            self.emit(SIGNAL('update(QString)'), str(number))

        self.emit(SIGNAL('done()'))


    def stop(self):
        self.running = False


class PySubGUI(QMainWindow, main_window.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PySubGUI, self).__init__(parent)
        self.setupUi(self)
        self.settings_widget.setVisible(False)
        self.btn_cancel_add.setVisible(False)
        self.progressBar.setVisible(False)
        self.actionStop.setEnabled(True)
        # fixme: for some reason setEnabled(True) is impossible to set in qt designer

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

        self.actionAddFiles.triggered.connect(self.add_files)
        self.actionAddFolder.triggered.connect(self.add_folder)
        self.actionClearList.triggered.connect(self.clear_list)

        self.actionSearch.triggered.connect(self.start_search)
        self.actionStop.triggered.connect(self.stop_search)

        self.actionDownload.triggered.connect(self.download)
        self.actionSkip.triggered.connect(self.skip)

        self.actionSettings.triggered.connect(self.toggle_settings)
        self.actionExitSettings.triggered.connect(self.toggle_settings)

        self.actionAbout.triggered.connect(self.about)


#=========================================================================
# Toolbar Buttons/Actions
#=========================================================================


    def add_files(self):
        files = QFileDialog.getOpenFileNames(self, "Add Files",
                                             QDir.homePath())
        if files:
            self.process_files(files[0])


    def add_folder(self):
        directory = QFileDialog.getExistingDirectory(self,
                                                     "Add Folder",
                                                     QDir.homePath())

        if directory:
            self.process_files(
                [directory + os.sep + name for name in os.listdir(directory)])

    def clear_list(self):
        global to_process, video_files
        to_process, video_files = [], []

        self.video_files = []
        self.update_file_table()

    def start_search(self):
        self.actionAddFolder.setEnabled(False)
        self.actionAddFiles.setEnabled(False)
        self.actionClearList.setEnabled(False)

        self.actionSearch.setVisible(False)
        self.actionStop.setVisible(True)

        self.search()

    def stop_search(self):
        self.actionAddFolder.setEnabled(True)
        self.actionAddFiles.setEnabled(True)

        self.actionSearch.setVisible(True)
        self.actionStop.setVisible(False)

        self.actionDownload.setEnabled(False)
        self.actionSkip.setEnabled(False)

        self.c_video_index = -1

        self.update_file_table()

    def download(self):
        if self.file_list.selectionModel().selectedRows():
            try:
                sub_index = self.file_list.selectionModel().selectedRows()[0].row() - 1
            except:  # no sub selected
                QMessageBox.information(self, "Not selected",
                                        "Please select the subtitle  you want to download"
                                        "before clicking 'Download' button")
                return
        else:
            return

        self.statusBar.showMessage("Downloading...")
        self.video_files[self.c_video_index].subtitles[sub_index].download()

        self.statusBar.showMessage("Subtitle downloaded for {}".format(
            self.video_files[self.c_video_index].file_name))
        self.search()

    def skip(self):
        self.search()

    def toggle_settings(self):
        self.actionSettings.setVisible(not self.actionSettings.isVisible())
        self.actionExitSettings.setVisible(not self.actionSettings.isVisible())

        # Not implemented in UI yet
        # def auto_download(self):
        #     downloaded = self.video_files[self.c_video_index].auto_download()
        #     if self.config['not_found_prompt'] and not downloaded:
        #         self.search(index=self.c_video_index)
        #     else:
        #         self.search()
        #
        # def remove_selected(self):
        #     rows = self.file_list.selectionModel().selectedRows()
        #     rm_indexes = [row.row() for row in rows]
        #     if rm_indexes:
        #         self.video_files = [v for v in self.video_files
        #                             if self.video_files.index(v) not in rm_indexes]
        #     self.update_file_table()

    def about(self):
        self.statusBar.showMessage("Not implemented yet.")

    @Slot()
    def on_btn_cancel_add_clicked(self):
        if self.addThread:
            self.addThread.stop()

#=========================================================================
#   Configuration/Settings
#=========================================================================

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

        if not settings.save_config(new_config):
            QMessageBox.critical(self, "Save error",
                                 "Saving new configuration has failed. "
                                 "The required file or folder could not be saved or created "
                                 "as '{}'".format(settings.config_file))

        self.__load_config()

    @Slot()
    def on_btn_reset_conf_clicked(self):
        self.__load_config(force_default=True)

    @Slot()
    def on_btn_apply_clicked(self):
        # TODO: Add applying settings to this session only
        pass


#=========================================================================
#   Backend - logging to server, downloading subtitles etc
#=========================================================================


    def __login_to_server(self):
        if self.server:
            self.server.log_out()

        self.server = OpenSubtitlesServer(self.config['server'],
                                          self.config['ua'],
                                          self.config['lang'])
        self.server.login()

    def process_files(self, file_list):
        global video_files, to_process, video_config
        video_config = self.config
        for video_file in file_list:
            if os.path.splitext(video_file)[1] in self.config['file_ext']:
                to_process.append(video_file)

        self.addThread = addThread()

        self.connect(self.addThread, SIGNAL("update(QString)"), self.add_progress)
        self.connect(self.addThread, SIGNAL("done()"), self.done_adding)

        self.addThread.start()
        self.progressBar.setVisible(True)
        self.btn_cancel_add.setVisible(True)

    def add_progress(self, text):
        self.progressBar.setMaximum(len(to_process))
        self.progressBar.setValue(int(text))
        self.progressBar.setFormat("Processed: {} out of {} files".format(text, len(to_process)))

    def done_adding(self):
        self.video_files = video_files
        self.update_file_table()
        self.btn_cancel_add.setVisible(False)
        self.progressBar.setVisible(False)

    def auto_search_all(self):
        #TODO: Not implemented
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
            self.stop_search()
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

#=========================================================================
#   Table models
#=========================================================================


    def update_file_table(self):

        self.file_model.clear()
        self.file_model = QStandardItemModel(0, 6, None)

        for row_num, video in enumerate(self.video_files):
            vid_index = QStandardItem(str(row_num + 1))
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

        self.actionSearch.setEnabled(bool(self.video_files))
        self.actionClearList.setEnabled(bool(self.video_files))


    def update_sub_table(self, video):
        self.sub_model.clear()

        # self.status_label.setText("Subtitles for: '{}'".format(video.file_name))

        if not video.subtitles:
            self.sub_model.setItem(0, 0, QStandardItem("N/A"))
            self.sub_model.setItem(0, 1, QStandardItem("N/A"))
            self.sub_model.setItem(0, 2, QStandardItem("Subtitle not found"))
            self.sub_model.setItem(0, 3, QStandardItem("N/A"))
            self.actionDownload.setEnabled(False)
            self.actionSkip.setEnabled(True)

        else:
            for row, sub in enumerate(video.subtitles):
                sub_index = QStandardItem(str(row + 1))
                sub_downloads = QStandardItem(str(sub.download_count))
                sub_name = QStandardItem(sub.sub_filename)
                sub_synced = QStandardItem("Yes" if sub.synced else "No")

                self.sub_model.setItem(row, 0, sub_index)
                self.sub_model.setItem(row, 1, sub_downloads)
                self.sub_model.setItem(row, 2, sub_name)
                self.sub_model.setItem(row, 3, sub_synced)

            self.actionDownload.setEnabled(True)
            self.actionSkip.setEnabled(True)

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
