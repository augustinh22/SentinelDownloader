# -*- coding: utf-8 -*-
'''
/***************************************************************************
 SentinelDownloader
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
'''
import os.path

import pyproj
import qgis
from PyQt4.QtCore import (
    QSettings, QTranslator, qVersion, QCoreApplication, QDate, QThread)
from PyQt4.QtGui import QAction, QIcon, QMessageBox
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from sentinel_downloader_dialog import SentinelDownloaderDialog
from sentinelsearch import SentinelSearch


class SentinelDownloader:

    '''
    QGIS Plugin Implementation.
    '''

    def __init__(self, iface):
        '''
        Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        '''
        #
        # Save reference to the QGIS interface.
        #
        self.iface = iface

        #
        # Initialize class variables.
        #
        self.dlg = None
        self.downloader = None
        self.worker = None
        self.workerD = None
        self.thread = None
        self.threadD = None

        #
        # Initialize plugin directory.
        #
        self.plugin_dir = os.path.dirname(__file__)

        #
        # Initialize locale.
        #
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SentinelDownloader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        #
        # Declare instance attributes.
        #
        self.actions = []

        #
        # Set plugin label under 'Web' tab in QGIS toolbar.
        #
        self.menu = self.tr(u'&Sentinel Downloader')

        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SentinelDownloader')
        self.toolbar.setObjectName(u'SentinelDownloader')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        '''
        Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        '''
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SentinelDownloader', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):

        '''
        Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        '''

        #
        # Create the dialog (after translation) and keep reference.
        #
        self.dlg = SentinelDownloaderDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        '''
        TODO: Need to add threading for button actions.
        '''

        self.downloader = SentinelSearch(self.dlg)

        #
        # Button actions.
        #
        self.dlg.writeDir_toolButton.clicked.connect(self.downloader.open)
        self.dlg.btnExtent.clicked.connect(self.get_extent)
        self.dlg.btnSearch.clicked.connect(self.search_thread)
        self.dlg.btnSearchCancel.clicked.connect(self.kill)
        self.dlg.btnReset.clicked.connect(self.reset_parameters)
        self.dlg.btnTileSearch.clicked.connect(self.downloader.get_tile_coords)
        self.dlg.btnClearSelected.clicked.connect(
            self.downloader.remove_selected)
        self.dlg.btnDownload.clicked.connect(self.download_thread)
        # self.dlg.btnDownload.clicked.connect(self.download_S1thread)
        self.dlg.btnDownloadCancel.clicked.connect(self.kill)
        self.dlg.btnClear.clicked.connect(self.downloader.clearTable)

        return action

    def initGui(self):

        '''
        Create the menu entries and toolbar icons inside the QGIS GUI.
        '''

        icon_path = ':/plugins/SentinelDownloader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sentinel Downloader'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):

        '''
        Removes the plugin menu item and icon from QGIS GUI.
        '''

        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&Sentinel Downloader'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):

        '''
        Run method that performs all the real work.
        '''

        #
        # Show the dialog.
        #
        self.dlg.show()

        # # Run the dialog event loop
        # result = self.dlg.exec_()
        # # See if OK was pressed
        # if result:
        #     # Do something useful here - delete the line containing pass and
        #     # substitute with your code.
        #     pass

    def get_extent(self):

        '''
        Returns current extent shown in QGIS as upper and lower limits for both
        X and Y axis in the current projection.
        '''

        #
        # Get current extent coordinates.
        #
        e = self.iface.mapCanvas().extent()

        ULX = e.xMaximum()
        ULY = e.yMaximum()
        LLX = e.xMinimum()
        LLY = e.yMinimum()

        #
        # Determine origin CRS and define destination CRS (EPSG:4326).
        #
        canvas = self.iface.mapCanvas()
        epsg_code = canvas.mapRenderer().destinationCrs().authid()
        inProj = pyproj.Proj(init=epsg_code)
        outProj = pyproj.Proj(init='epsg:4326')

        #
        # Transform coordinates
        #
        ULX_new, ULY_new = pyproj.transform(inProj, outProj, ULX, ULY)
        LLX_new, LLY_new = pyproj.transform(inProj, outProj, LLX, LLY)

        #
        # Set values.
        #
        self.dlg.LLX_lineEdit.setText(str('{0:.2f}'.format(LLX_new)))
        self.dlg.ULX_lineEdit.setText(str('{0:.2f}'.format(ULX_new)))
        self.dlg.LLY_lineEdit.setText(str('{0:.2f}'.format(LLY_new)))
        self.dlg.ULY_lineEdit.setText(str('{0:.2f}'.format(ULY_new)))

    def search_thread(self):

        '''
        Creates Qt thread for searching so that the GUI does not freeze and
        QGIS does not crash.
        '''

        #
        # Disable search button while searching.
        #
        self.dlg.btnSearch.setEnabled(False)
        self.dlg.btnSearchCancel.setEnabled(True)

        self.worker = SentinelSearch(self.dlg)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.start()
        self.thread.started.connect(self.worker.get_query_xml)

        #
        # Signal handelling from thread.
        #
        self.worker.connecting_message.connect(self.set_search_label)
        self.worker.searching_message.connect(self.set_search_label)
        self.worker.enable_btnSearch.connect(self.enable_btnSearch)
        self.worker.search_progress_max.connect(self.set_progress_max)
        self.worker.search_progress_set.connect(self.set_progress)
        self.worker.set_message.connect(self.set_messageBar)
        self.worker.finished.connect(self.search_finished)

    def set_search_label(self, text):

        self.dlg.search_label.setText(text)

        if text == 'Connecting . . .':
            #
            # This makes progressBar move until real max is set.
            #
            self.dlg.search_progressBar.setMinimum(0)
            self.dlg.search_progressBar.setMaximum(0)

    def set_progress_max(self, max_value):

        if max_value == 0:
            #
            # If there are no entries, reset bar to avoid problems.
            #
            self.dlg.search_progressBar.setMinimum(0)
            self.dlg.search_progressBar.reset()

        else:
            self.dlg.search_progressBar.setMinimum(0)
            self.dlg.search_progressBar.setMaximum(100)

    def set_progress(self, percent):

        if percent > 100:
            percent = 100

        self.dlg.search_progressBar.setValue(percent)

    def enable_btnSearch(self):

        self.dlg.btnSearch.setEnabled(True)
        self.dlg.btnSearchCancel.setEnabled(False)

    def search_finished(self, killed=False):

        #
        # Clear progress bar widget and label.
        #
        self.dlg.search_progressBar.reset()
        self.dlg.search_progressBar.setMinimum(0)
        self.set_search_label('')

        if killed is False:

            self.text_to_messagebox('Done!', 'Done fetching search results!')

        #
        # Clean up Thread.
        #
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.deleteLater()

        #
        # Enable search button after searching.
        #
        self.dlg.btnSearch.setEnabled(True)
        self.dlg.btnSearchCancel.setEnabled(False)

    def kill(self):

        '''
        Starts to kill either the search or download processes, which are
        both initiated by Cancel buttons. It also disables the Cancel
        buttons such that the user does not crash QGIS.
        '''

        if self.worker:

            self.worker.killed = True
            self.dlg.btnSearchCancel.setEnabled(False)

        if self.workerD:

            self.workerD.killed = True
            self.dlg.btnDownloadCancel.setEnabled(False)

    def reset_parameters(self):

        '''
        Sets all user input back to default values. Initaited by the user
        clicking the reset button.
        '''

        self.dlg.sensor_comboBox.setCurrentIndex(0)

        self.dlg.maxRecords_spinBox.setValue(100)
        self.dlg.orderBy_comboBox.setCurrentIndex(0)
        self.dlg.LLX_lineEdit.clear()
        self.dlg.ULX_lineEdit.clear()
        self.dlg.LLY_lineEdit.clear()
        self.dlg.ULY_lineEdit.clear()
        self.dlg.lat_lineEdit.clear()
        self.dlg.lon_lineEdit.clear()
        self.dlg.s2Tile_lineEdit.clear()
        self.dlg.s2Extract_checkBox.setChecked(False)

        today = QDate.currentDate()
        self.dlg.ingestFrom_dateEdit.setEnabled(False)
        self.dlg.ingestFrom_dateEdit.setDate(QDate(2013, 04, 13))
        self.dlg.ingestTo_dateEdit.setEnabled(False)
        self.dlg.ingestTo_dateEdit.setDate(today)
        self.dlg.ingest_enable.setChecked(False)
        self.dlg.dateFrom_dateEdit.setEnabled(False)
        self.dlg.dateFrom_dateEdit.setDate(QDate(2013, 04, 13))
        self.dlg.dateTo_dateEdit.setEnabled(False)
        self.dlg.dateTo_dateEdit.setDate(today)
        self.dlg.date_enable.setChecked(False)

        self.dlg.orbit_lineEdit.clear()
        self.dlg.relOrbit_radioButton.setChecked(True)
        self.dlg.orbitDir_comboBox.setCurrentIndex(0)

        self.dlg.s1Mode_comboBox.setCurrentIndex(0)
        self.dlg.s1Polar_comboBox.setCurrentIndex(0)
        self.dlg.s1Product_comboBox.setCurrentIndex(0)

        self.dlg.s2Product_comboBox.setCurrentIndex(0)
        self.dlg.cloudCover_spinBox.setValue(10)
        self.dlg.cloudCover_enable.setChecked(False)

    def download_thread(self):

        '''
        Starts a download thread. Initiated by the user clicking the download
        button.
        '''

        self.dlg.btnDownload.setEnabled(False)
        self.dlg.btnDownloadCancel.setEnabled(True)
        self.dlg.download_progressBar.setMinimum(0)
        self.dlg.download_progressBar.setMaximum(100)

        self.workerD = SentinelSearch(self.dlg)
        self.threadD = QThread()
        self.workerD.moveToThread(self.threadD)

        self.threadD.start()
        self.threadD.started.connect(self.workerD.download_results)
        self.workerD.download_progress_set.connect(self.set_download_progress)

        self.workerD.finished_download.connect(self.download_finished)

    def set_download_progress(self, percent):

        '''
        Sets the download progress bar for the overall download progress in
        percent, based on the total bits to download according to the products
        sizes in the GUI tables.
        '''

        if percent > 100:
            percent = 100

        self.dlg.download_progressBar.setValue(percent)

    def download_finished(self, killed=False):

        '''
        Cleans up the download thread once downloading is complete, or if the
        process was killed by the user.
        '''

        if killed is False:

            self.text_to_messagebox(
                'Done!', 'Done downloading Sentinel products!')

        #
        # Clean up Thread.
        #
        self.workerD.deleteLater()
        self.threadD.quit()
        self.threadD.deleteLater()

        #
        # Enable search button after searching.
        #
        self.dlg.btnDownload.setEnabled(True)
        self.dlg.btnDownloadCancel.setEnabled(False)

        #
        # Clear progress bar widget and label.
        #
        self.dlg.download_progressBar.reset()
        self.dlg.download_progressBar.setMinimum(0)
        # self.set_search_label('')

    @staticmethod
    def text_to_messagebox(header, message, long_text=None):

        '''
        Prints a given message to a pop-up message box.
        '''

        msg_txt = QMessageBox()
        msg_txt.setIcon(QMessageBox.Information)
        msg_txt.setText(message)
        # msg_txt.setInformativeText("This is additional information")
        msg_txt.setWindowTitle(header)
        if long_text is not None:
            msg_txt.setDetailedText(long_text)
        msg_txt.exec_()

    def set_messageBar(self, message):

        '''
        Prints the total size of all products in the GUI tables to the QGIS
        message bar.
        '''

        self.iface.messageBar().pushMessage('Results', message, duration=30)
