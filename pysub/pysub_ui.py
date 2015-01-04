#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle downloader using OpenSubtitles.org API

GUI code
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
from PyQt4 import uic

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pysub_objects import Video, OpenSubtitlesServer
import settings
from ui import main_window
from __init__ import __version__


class addThread(QThread):
    def __init__(self, to_process, video_config):
        QThread.__init__(self)
        self.to_process = to_process
        self.processed = []
        self.config = video_config

    def __del__(self):
        self.wait()

    def run(self):
        self.running = True
        for number, file_path in enumerate(self.to_process):
            if not self.running:
                break

            self.processed.append(Video(file_path, self.config))
            self.emit(SIGNAL('update(QString)'), str(number))

        self.emit(SIGNAL('done(PyQt_PyObject)'), self.processed)

    def stop(self):
        self.running = False


class NumberSortModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        try:
            return int(left.data().toString()) > int(right.data().toString())
        except ValueError:
            return left.data().toString() > right.data().toString()


class PySubGUI(QMainWindow, main_window.Ui_MainWindow):
    # noinspection PyUnresolvedReferences
    def __init__(self, parent=None):
        super(PySubGUI, self).__init__(parent)
        self.setupUi(self)
        self.settings_widget.setVisible(False)
        self.btn_cancel_add.setVisible(False)
        self.status_label.setVisible(False)
        self.progressBar.setVisible(False)
        self.actionStop.setEnabled(True)
        # fixme: for some reason setEnabled(True) is impossible to set in qt designer
        self.setWindowTitle("PySub {}".format(__version__))

        self.file_model = QStandardItemModel(0, 6, parent)
        self.sub_model = QStandardItemModel(0, 4, parent)

        self.config = None
        self.server = None
        self.load_settings()

        self.video_files = []
        self.c_video_index = -1
        self.download_mode = False
        self.update_file_table()

        # Toolbar
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

        # Main UI
        self.btn_cancel_add.clicked.connect(self.cancel_add)

        # Settings
        self.btn_save_conf.clicked.connect(self.save_settings)
        self.btn_reset_conf.clicked.connect(self.reset_settings)
        self.btn_apply.clicked.connect(self.apply_settings)

#=========================================================================
# Toolbar Buttons/Actions
#=========================================================================


    def add_files(self):
        files = QFileDialog.getOpenFileNames(self, "Add Files",
                                             QDir.homePath())
        if files and files[0]:
            self.process_files([str(files[0])])


    def add_folder(self):
        directory = QFileDialog.getExistingDirectory(self,
                                                     "Add Folder",
                                                     QDir.homePath())

        if directory:
            self.process_files(
                [str(directory) + os.sep + name for name in os.listdir(directory)])

    def clear_list(self):
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
        if self.actionSettings.isVisible():
            self.main_wdiget.hide()
            self.settings_widget.show()
            self.actionSettings.setVisible(False)
            self.actionExitSettings.setVisible(True)
        else:
            self.main_wdiget.show()
            self.settings_widget.hide()
            self.actionSettings.setVisible(True)
            self.actionExitSettings.setVisible(False)

    def about(self):
        dialog = QDialog()
        dialog.ui = uic.loadUi('ui/about_dialog.ui', dialog)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.ui.btn_license.clicked.connect(self.show_license)
        dialog.ui.btn_credits.clicked.connect(self.show_credits)
        dialog.exec_()

    def show_license(self):
        dialog = QDialog()
        dialog.ui = uic.loadUi('ui/license_dialog.ui', dialog)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.exec_()

    def show_credits(self):
        dialog = QDialog()
        dialog.ui = uic.loadUi('ui/credits_dialog.ui', dialog)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.exec_()

    def cancel_add(self):
        if self.addThread:
            self.addThread.stop()

#=========================================================================
#   Configuration/Settings
#=========================================================================

    def load_settings(self, force_default=False, from_dict=None):
        if not from_dict:
            if force_default:
                self.config = settings.default_config
            else:
                self.config = settings.get_config()
        else:
            if from_dict == self.config:
                return

            self.config = from_dict

        if self.server:
            #TODO: Set to none only if server settings changed
            self.server = None

        self.set_ui_config()


    def set_ui_config(self):
        auto_dl = self.config['auto_download']
        self.chk_auto_dl.setCheckState(Qt.Checked if auto_dl else Qt.Unchecked)

        ovw = self.config['overwrite']
        self.chk_overwrite.setCheckState(Qt.Checked if ovw else Qt.Unchecked)

        prompt = self.config['not_found_prompt']
        self.chk_prompt.setCheckState(Qt.Checked if prompt else Qt.Unchecked)

        self.lne_save_folder.setText(self.config['subfolder'])

        lang_list = sorted(self.config['languages'].keys())
        # Move the currently selected language to the top of the list
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

    def get_ui_config(self):
        try:
            ui_config = {'file_ext': json.loads(str(self.txt_file_ext.toPlainText())),
                         'sub_ext': json.loads(str(self.txt_sub_ext.toPlainText())),
                         'overwrite': self.chk_overwrite.checkState() == Qt.Checked,
                         'auto_download': self.chk_auto_dl.checkState() == Qt.Checked,
                         'not_found_prompt': self.chk_prompt.checkState() == Qt.Checked,
                         'subfolder': None if str(self.lne_save_folder.text()) == "" else str(self.lne_save_folder.text()),
                         'cutoff': float(str(self.sl_label.text())) / 100.00,
                         'languages': json.loads(str(self.txt_lang_json.toPlainText())),
                         'lang': self.config['languages'].get(str(self.cbo_language.currentText())),
                         'lang_name': str(self.cbo_language.currentText()),
                         'ua': str(self.lne_ua.text()),
                         'server': str(self.lne_server.text())}

            if not ui_config['lang']:
                return None

            return ui_config
        except:
            return None

    def save_settings(self, this_session_only=False):
        ui_config = self.get_ui_config()

        if not ui_config:
            QMessageBox.critical(self, "Save error",
                                 "Saving new configuration has failed."
                                 "Fix the configuration options manually "
                                 "or reset to default settings and then save")
        else:
            if not this_session_only:
                if not settings.save_config(ui_config):
                    QMessageBox.critical(self, "Save error",
                                         "Saving new configuration has failed. "
                                         "The required file or folder could not be saved or created "
                                         "as '{}'".format(settings.config_file))
                    return

            if this_session_only:
                self.load_settings(from_dict=ui_config)
            else:
                self.load_settings()

            self.toggle_settings()

    def reset_settings(self):
        self.load_settings(force_default=True)

    def apply_settings(self):
        self.save_settings(this_session_only=True)
        #TODO: Re-configuring is only necessary when certain things change
        # like subfolder, this is a waste of time to do on each applied change
        #FIXME: Should be fixed before v1.0
        file_list = [v.file_path for v in self.video_files]
        self.clear_list()
        self.process_files(file_list)


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
        to_process = []
        self.actionSearch.setEnabled(False)

        for video_file in file_list:
            if os.path.splitext(video_file)[1] in self.config['file_ext']:
                to_process.append(video_file)

        self.addThread = addThread(to_process, self.config)

        self.connect(self.addThread, SIGNAL("update(QString)"), self.add_progress)
        self.connect(self.addThread, SIGNAL("done(PyQt_PyObject)"), self.done_adding)

        self.addThread.start()
        self.progressBar.setVisible(True)
        self.btn_cancel_add.setVisible(True)

    def add_progress(self, text):
        self.progressBar.setMaximum(len(self.addThread.to_process))
        self.progressBar.setValue(int(text))
        self.progressBar.setFormat("Processed: {} out of {} files".format(text, len(self.addThread.to_process)))

    def done_adding(self, processed_files):
        self.video_files.extend(processed_files)
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

        number_proxy = NumberSortModel()
        number_proxy.setSourceModel(self.file_model)
        self.file_list.setModel(number_proxy)

        for i in range(5):
            self.file_list.resizeColumnToContents(i)

        self.actionSearch.setEnabled(bool(self.video_files))
        self.actionClearList.setEnabled(bool(self.video_files))

        if self.status_label.isVisible():
            self.status_label.setVisible(False)


    def update_sub_table(self, video):
        self.sub_model.clear()

        self.status_label.setVisible(True)
        self.status_label.setText("Choose subtitle for: '{}'".format(video.file_name))

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

        number_proxy = NumberSortModel()
        number_proxy.setSourceModel(self.sub_model)
        self.file_list.setModel(number_proxy)

        for i in range(3):
            self.file_list.resizeColumnToContents(i)


def main():
    app = QApplication(sys.argv)
    form = PySubGUI()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
