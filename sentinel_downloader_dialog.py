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
        # self.orderBy_comboBox
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
        # self.s2Product_comboBox
        # self.cloudCover_enable
        # self.cloudCover_spinBox
        # self.orbitDir_comboBox
        # self.orbit_lineEdit
        # self.ingestFrom_dateEdit
        # self.ingestTo_dateEdit
        # self.ingest_enable
        # self.dateFrom_dateEdit
        # self.dateTo_dateEdit
        # self.date_enable
        # self.maxRecords_spinBox
        # self.results_tableWidget
        # self.btnTileSearch
        # self.lat_lineEdit
        # self.lon_lineEdit
        # self.search_label

        self.pass_lineEdit.setText('')
        self.user_lineEdit.setText('')

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
        self.s2Extract_checkBox.setEnabled(False)

        #
        # Enable tile center coordinate search button.
        #
        self.s2Tile_lineEdit.textChanged.connect(self.enable_tile_search)

        #
        # Adjust max records based on api hub.
        #
        self.hub_comboBox.currentIndexChanged.connect(self.adjust_maxRecords)

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

        #
        # Orbit type radio buttons -- set relative as default.
        #
        self.relOrbit_radioButton.setAutoExclusive(False)
        self.relOrbit_radioButton.setChecked(True)
        self.relOrbit_radioButton.setAutoExclusive(True)

        self.btnSearchCancel.setEnabled(False)
        self.btnSearch.setEnabled(True)

        self.btnDownloadCancel.setEnabled(False)
        self.btnDownload.setEnabled(True)

    def adjust_maxRecords(self):

        """Adjusts the possible max values based on download hub."""

        if self.hub_comboBox.currentText() == 'Dhus':
            self.maxRecords_spinBox.setMaximum(10)
            self.maxRecords_spinBox.setMinimum(1)
            self.maxRecords_spinBox.setSingleStep(1)
            self.maxRecords_spinBox.setValue(10)

        elif self.hub_comboBox.currentText() == 'API Hub':
            self.maxRecords_spinBox.setMaximum(100)
            self.maxRecords_spinBox.setMinimum(1)
            self.maxRecords_spinBox.setSingleStep(10)
            self.maxRecords_spinBox.setValue(100)

        elif self.hub_comboBox.currentText() == 'ZAMG':
            self.maxRecords_spinBox.setMaximum(100)
            self.maxRecords_spinBox.setMinimum(1)
            self.maxRecords_spinBox.setSingleStep(10)
            self.maxRecords_spinBox.setValue(100)

        elif self.hub_comboBox.currentText() == 'HNSDMS':
            self.maxRecords_spinBox.setMaximum(100)
            self.maxRecords_spinBox.setMinimum(1)
            self.maxRecords_spinBox.setSingleStep(10)
            self.maxRecords_spinBox.setValue(100)

        elif self.hub_comboBox.currentText() == 'Finhub':
            self.maxRecords_spinBox.setMaximum(100)
            self.maxRecords_spinBox.setMinimum(1)
            self.maxRecords_spinBox.setSingleStep(10)
            self.maxRecords_spinBox.setValue(100)

        else:
            self.maxRecords_spinBox.setMaximum(100)
            self.maxRecords_spinBox.setMinimum(1)
            self.maxRecords_spinBox.setSingleStep(10)
            self.maxRecords_spinBox.setValue(100)

    def enable_cloudcover(self):

        """Toggles the max cloud cover input field and label depending
            on whether the 'enable' checkbox has been checked."""

        if self.cloudCover_enable.isChecked() is True:
            self.cloudCover_spinBox.setEnabled(True)
            self.cloudCover_label.setEnabled(True)

        else:
            self.cloudCover_spinBox.setEnabled(False)
            self.cloudCover_label.setEnabled(False)

    def enable_date(self):

        """Toggles sensing date input fields and labels depending on whether
            the 'enable' checkbox has been checked."""

        if self.date_enable.isChecked() is True:
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

        """Toggles ingestion date input fields and labels depending on whether
            the 'enable' checkbox has been checked."""

        if self.ingest_enable.isChecked() is True:
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

            self.s2Extract_checkBox.setEnabled(True)

            #
            # Adjust possible capture and ingest dates if only S2.
            #
            dt = self.ingestFrom_dateEdit.date()
            if dt.year() <= 2015 and dt.month() <= 06 and dt.day() <= 23:
                self.ingestFrom_dateEdit.setDate(QtCore.QDate(2015, 06, 23))

            dt = self.dateFrom_dateEdit.date()
            if dt.year() <= 2015 and dt.month() <= 06 and dt.day() <= 23:
                self.dateFrom_dateEdit.setDate(QtCore.QDate(2015, 06, 23))

            self.s1Mode_label.setEnabled(False)
            self.s1Mode_comboBox.setEnabled(False)
            self.s1Polar_label.setEnabled(False)
            self.s1Polar_comboBox.setEnabled(False)
            self.s1Product_label.setEnabled(False)
            self.s1Product_comboBox.setEnabled(False)

            self.s2Product_label.setEnabled(True)
            self.s2Product_comboBox.setEnabled(True)
            self.cloudCover_enable.setEnabled(True)
            if self.cloudCover_enable.isChecked() is True:
                self.cloudCover_spinBox.setEnabled(True)
                self.cloudCover_label.setEnabled(True)

        elif (self.sensor_comboBox.currentText() == 'Sentinel-1'
                or self.sensor_comboBox.currentText() == 'Sentinel-1A'
                or self.sensor_comboBox.currentText() == 'Sentinel-1B'):

            self.s2Extract_checkBox.setEnabled(False)

            self.s1Mode_label.setEnabled(True)
            self.s1Mode_comboBox.setEnabled(True)
            self.s1Polar_label.setEnabled(True)
            self.s1Polar_comboBox.setEnabled(True)
            self.s1Product_label.setEnabled(True)
            self.s1Product_comboBox.setEnabled(True)

            self.s2Product_label.setEnabled(False)
            self.s2Product_comboBox.setEnabled(False)
            self.cloudCover_enable.setEnabled(False)
            self.cloudCover_spinBox.setEnabled(False)
            self.cloudCover_label.setEnabled(False)

        elif (self.sensor_comboBox.currentText() == 'Sentinel-3'
                or self.sensor_comboBox.currentText() == 'Sentinel-3A'
                or self.sensor_comboBox.currentText() == 'Sentinel-3B'):

            #
            # Adjust possible capture and ingest dates if only S3.
            #
            dt = self.ingestFrom_dateEdit.date()
            if dt.year() <= 2016 and dt.month() <= 02 and dt.day() <= 16:
                self.ingestFrom_dateEdit.setDate(QtCore.QDate(2016, 02, 16))

            dt = self.dateFrom_dateEdit.date()
            if dt.year() <= 2016 and dt.month() <= 02 and dt.day() <= 16:
                self.dateFrom_dateEdit.setDate(QtCore.QDate(2016, 02, 16))

        else:

            self.s2Extract_checkBox.setEnabled(False)

            self.s1Mode_label.setEnabled(False)
            self.s1Mode_comboBox.setEnabled(False)
            self.s1Polar_label.setEnabled(False)
            self.s1Polar_comboBox.setEnabled(False)
            self.s1Product_label.setEnabled(False)
            self.s1Product_comboBox.setEnabled(False)

            self.s2Product_label.setEnabled(False)
            self.s2Product_comboBox.setEnabled(False)
            self.cloudCover_enable.setEnabled(False)
            self.cloudCover_spinBox.setEnabled(False)
            self.cloudCover_label.setEnabled(False)

    def enable_tile_search(self):

        if str(len(self.s2Tile_lineEdit.text())) == '5':
            self.btnTileSearch.setEnabled(True)

        else:
            self.btnTileSearch.setEnabled(False)
