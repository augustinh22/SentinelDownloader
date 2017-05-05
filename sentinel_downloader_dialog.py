# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SentinelDownloaderDialog
                                 A QGIS plugin
 Sentinel data downloader.
                             -------------------
        begin                : 2017-04-30
        git sha              : $Format:%H$
        copyright            : (C) 2017 by h. Augustin
        email                : hannah.augustin@stud.sbg.ac.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, QtCore, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sentinel_downloader_dialog_base.ui'))


class SentinelDownloaderDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(SentinelDownloaderDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        #
        # All fields, buttons, etc. for reference.
        #
        # self.btnClose
        # self.btnSearch
        # self.btnDownload
        # self.btnClear
        # self.pass_lineEdit
        # self.user_lineEdit
        # self.hub_comboBox
        # self.sensor_comboBox
        # self.sortBy_comboBox
        # self.LLX_lineEdit
        # self.ULX_lineEdit
        # self.LLY_lineEdit
        # self.ULY_lineEdit
        # self.s2Tile_lineEdit
        # self.writeDir_toolButton
        # self.writeDir_txtPath
        # self.s1Mode_comboBox
        # self.s1Polar_comboBox
        # self.s1Product_comboBox
        # self.cloudCover_enable
        # self.cloudCover_spinBox
        # self.absOrbit_lineEdit
        # self.orbitDir_comboBox
        # self.relOrbit_lineEdit
        # self.ingestFrom_dateEdit
        # self.ingestTo_dateEdit
        # self.ingest_enable
        # self.dateFrom_dateEdit
        # self.dateTo_dateEdit
        # self.date_enable
        # self.maxRecords_spinBox
        # self.results_tableWidget
        # self.btnTileSearch
        # self.tileSearch_textBrowser

        #
        # Hide password.
        #
        self.pass_lineEdit.setEchoMode(QtGui.QLineEdit.Password)

        #
        # Depending on platform chosen, enable or disable options.
        #
        self.sensor_comboBox.currentIndexChanged.connect(self.enable_platform)

        #
        # Disable tile query button and results window until tile entered.
        #
        self.btnTileSearch.setEnabled(False)
        self.tileSearch_textBrowser.setEnabled(False)
        #
        # Enable tile center coordinate search button.
        #
        self.s2Tile_lineEdit.textChanged.connect(self.enable_tile_search)

        #
        # Add directory search functionality.
        #
        # self.writeDir_toolButton

        #
        # Disable date, ingestion date and cloudcover options until enabled.
        #
        self.dateFrom_dateEdit.setEnabled(False)
        self.dateTo_dateEdit.setEnabled(False)
        self.dateFrom_label.setEnabled(False)
        self.dateTo_label.setEnabled(False)
        self.ingestFrom_dateEdit.setEnabled(False)
        self.ingestTo_dateEdit.setEnabled(False)
        self.ingestFrom_label.setEnabled(False)
        self.ingestTo_label.setEnabled(False)
        self.cloudCover_spinBox.setEnabled(False)
        self.cloudCover_label.setEnabled(False)

        #
        # If enable checkbox clicked, enable options, if not, disable.
        #
        self.date_enable.stateChanged.connect(self.enable_date)
        self.ingest_enable.stateChanged.connect(self.enable_ingest)
        self.cloudCover_enable.stateChanged.connect(self.enable_cloudcover)

        #
        # Set "to" dates to current day.
        #
        today = QtCore.QDate.currentDate()
        self.ingestTo_dateEdit.setDate(today)
        self.dateTo_dateEdit.setDate(today)



    def enable_cloudcover(self):

        '''This function toggles the max cloud cover input field and label
            depending on whether the 'enable' checkbox has been checked.'''

        if self.cloudCover_enable.isChecked() == True:
            self.cloudCover_spinBox.setEnabled(True)
            self.cloudCover_label.setEnabled(True)

        else:
            self.cloudCover_spinBox.setEnabled(False)
            self.cloudCover_label.setEnabled(False)


    def enable_date(self):

        '''This function toggles sensing date input fields and labels
            depending on whether the 'enable' checkbox has been checked.'''

        if self.date_enable.isChecked() == True:
            self.dateFrom_dateEdit.setEnabled(True)
            self.dateTo_dateEdit.setEnabled(True)
            self.dateFrom_label.setEnabled(True)
            self.dateTo_label.setEnabled(True)

        else:
            self.dateFrom_dateEdit.setEnabled(False)
            self.dateTo_dateEdit.setEnabled(False)
            self.dateFrom_label.setEnabled(False)
            self.dateTo_label.setEnabled(False)


    def enable_ingest(self):

        '''This function toggles ingestion date input fields and labels
            depending on whether the 'enable' checkbox has been checked.'''

        if self.ingest_enable.isChecked() == True:
            self.ingestFrom_dateEdit.setEnabled(True)
            self.ingestTo_dateEdit.setEnabled(True)
            self.ingestFrom_label.setEnabled(True)
            self.ingestTo_label.setEnabled(True)

        else:
            self.ingestFrom_dateEdit.setEnabled(False)
            self.ingestTo_dateEdit.setEnabled(False)
            self.ingestFrom_label.setEnabled(False)
            self.ingestTo_label.setEnabled(False)

    def enable_platform(self):

        if (self.sensor_comboBox.currentText() == 'Sentinel-2'
                or self.sensor_comboBox.currentText() == 'Sentinel-2A'
                or self.sensor_comboBox.currentText() == 'Sentinel-2B'):

            self.s2Tile_label.setEnabled(True)
            self.s2Tile_lineEdit.setEnabled(True)
            self.btnTileSearch.setEnabled(True)
            self.tileSearch_textBrowser.setEnabled(True)

            self.s1Mode_label.setEnabled(False)
            self.s1Mode_comboBox.setEnabled(False)
            self.s1Polar_label.setEnabled(False)
            self.s1Polar_comboBox.setEnabled(False)
            self.s1Product_label.setEnabled(False)
            self.s1Product_comboBox.setEnabled(False)

            self.cloudCover_enable.setEnabled(True)
            if self.cloudCover_enable.isChecked() == True:
                self.cloudCover_spinBox.setEnabled(True)
                self.cloudCover_label.setEnabled(True)


        elif (self.sensor_comboBox.currentText() == 'Sentinel-1'
                or self.sensor_comboBox.currentText() == 'Sentinel-1A'
                or self.sensor_comboBox.currentText() == 'Sentinel-1B'):

            self.s2Tile_label.setEnabled(False)
            self.s2Tile_lineEdit.setEnabled(False)
            self.btnTileSearch.setEnabled(False)
            self.tileSearch_textBrowser.setEnabled(False)

            self.s1Mode_label.setEnabled(True)
            self.s1Mode_comboBox.setEnabled(True)
            self.s1Polar_label.setEnabled(True)
            self.s1Polar_comboBox.setEnabled(True)
            self.s1Product_label.setEnabled(True)
            self.s1Product_comboBox.setEnabled(True)

            self.cloudCover_enable.setEnabled(False)
            self.cloudCover_spinBox.setEnabled(False)
            self.cloudCover_label.setEnabled(False)
            self.cloudCover_enable.setChecked(False)

        else:

            self.s2Tile_label.setEnabled(False)
            self.s2Tile_lineEdit.setEnabled(False)
            self.btnTileSearch.setEnabled(False)
            self.tileSearch_textBrowser.setEnabled(False)

            self.s1Mode_label.setEnabled(True)
            self.s1Mode_comboBox.setEnabled(True)
            self.s1Polar_label.setEnabled(True)
            self.s1Polar_comboBox.setEnabled(True)
            self.s1Product_label.setEnabled(True)
            self.s1Product_comboBox.setEnabled(True)

            self.cloudCover_enable.setEnabled(True)
            if self.cloudCover_enable.isChecked() == True:
                self.cloudCover_spinBox.setEnabled(True)
                self.cloudCover_label.setEnabled(True)


    def enable_tile_search(self):

        if str(len(self.s2Tile_lineEdit.text())) == '5':
            self.btnTileSearch.setEnabled(True)
            self.tileSearch_textBrowser.setEnabled(True)
        else:
            self.btnTileSearch.setEnabled(False)
            self.tileSearch_textBrowser.setEnabled(False)
            self.tileSearch_textBrowser.setText('')
