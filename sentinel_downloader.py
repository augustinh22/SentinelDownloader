# -*- coding: utf-8 -*-
"""
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
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QDate
from PyQt4.QtGui import QAction, QIcon, QMessageBox
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from sentinel_downloader_dialog import SentinelDownloaderDialog
import os.path
import requests
import ast


class SentinelDownloader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
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


        # Declare instance attributes
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
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
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
        """Add a toolbar icon to the toolbar.

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
        """

        # Create the dialog (after translation) and keep reference
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

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SentinelDownloader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sentinel Downloader'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&Sentinel Downloader'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()

        self.dlg.btnSearch.clicked.connect(self.get_arguments)
        self.dlg.btnTileSearch.clicked.connect(self.get_tile_coords)

        # # Run the dialog event loop
        # result = self.dlg.exec_()
        # # See if OK was pressed
        # if result:
        #     # Do something useful here - delete the line containing pass and
        #     # substitute with your code.
        #     pass

    def get_arguments(self):

        #
        # Create options namespace. Perhaps (definitely) bad practice, but whatever.
        #
        options = Namespace()

        options.user = self.dlg.user_lineEdit.text()
        options.password = self.dlg.pass_lineEdit.text()

        if self.dlg.hub_comboBox.currentText() == 'API Hub':
            options.hub = 'apihub'
        elif self.dlg.hub_comboBox.currentText() == 'Dhus':
            options.hub = 'dhus'

        if self.dlg.sensor_comboBox.currentText() == 'All':
            options.sentinel = 'all'
        elif self.dlg.sensor_comboBox.currentText() == 'Sentinel-1':
            options.sentinel = 'S1'
        elif self.dlg.sensor_comboBox.currentText() == 'Sentinel-1A':
            options.sentinel = 'S1A'
        elif self.dlg.sensor_comboBox.currentText() == 'Sentinel-1B':
            options.sentinel = 'S1B'
        elif self.dlg.sensor_comboBox.currentText() == 'Sentinel-2':
            options.sentinel = 'S2'
        elif self.dlg.sensor_comboBox.currentText() == 'Sentinel-2A':
            options.sentinel = 'S2A'
        elif self.dlg.sensor_comboBox.currentText() == 'Sentinel-2B':
            options.sentinel = 'S2B'

        options.sortby = self.dlg.sortBy_comboBox.currentText()
        options.lonmin = self.dlg.LLX_lineEdit.text()
        options.lonmax = self.dlg.ULX_lineEdit.text()
        options.latmin = self.dlg.LLY_lineEdit.text()
        options.lonmax = self.dlg.ULY_lineEdit.text()
        options.tile = self.dlg.s2Tile_lineEdit.text()
        options.writedir = self.dlg.writeDir_txtPath.text()
        options.s1mode = self.dlg.s1Mode_comboBox.currentText()
        options.s1polar = self.dlg.s1Polar_comboBox.currentText()
        options.s1product = self.dlg.s1Product_comboBox.currentText()
        if self.dlg.cloudCover_enable.isChecked():
            options.max_cloud = self.dlg.cloudCover_spinBox.cleanText()
        options.absorbit = self.dlg.absOrbit_lineEdit.text()
        options.orbitdir = self.dlg.orbitDir_comboBox.currentText()
        options.relorbit = self.dlg.relOrbit_lineEdit.text()

        if self.dlg.ingest_enable.isChecked():

            #
            # Get ingestion dates.
            #
            options.start_ingest_date = self.dlg.ingestFrom_dateEdit.date()
            options.end_ingest_date = self.dlg.ingestTo_dateEdit.date()

            #
            # Convert ingestion dates to proper ISO format.
            #
            options.start_ingest_date = QDate.toString(
                options.start_ingest_date, 'yyyy-MM-dd')
            options.end_ingest_date = QDate.toString(
                options.end_ingest_date, 'yyyy-MM-dd')

        if self.dlg.date_enable.isChecked():

            #
            # Get sensing dates in date format.
            #
            options.start_date = self.dlg.dateFrom_dateEdit.date()
            options.end_date = self.dlg.dateTo_dateEdit.date()

            #
            # Convert sensing dates to proper ISO format.
            #
            options.start_date = QDate.toString(options.start_date, 'yyyy-MM-dd')
            options.end_date = QDate.toString(options.end_date, 'yyyy-MM-dd')

        options.MaxRecords = self.dlg.maxRecords_spinBox.cleanText()


        #
        # Print arguments to message box for test.
        #
        self.text_to_messagebox(options)


    def text_to_messagebox(self, options):

        options_dict = vars(options)
        options_string = ''
        for key,value in options_dict.iteritems():
            options_string += '{} : {}\n'.format(key,value)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Check the detailed text to see the options!")
        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setDetailedText(options_string)
        msg.exec_()

    def get_tile_coords(self):

        s2_tile = self.dlg.s2Tile_lineEdit.text()
        coords = self.kml_api(s2_tile)
        try:
            lon = str(round((float(coords[0])), 3))
            lat = str(round((float(coords[1])), 3))
            coords_str = '{}: lon {}, lat {}'.format(s2_tile, lon, lat)
            self.dlg.tileSearch_textBrowser.setText(coords_str)
        except:
            self.dlg.tileSearch_textBrowser.setText('API failed or tile not found.')


    def kml_api(self, tile):

        '''This function returns the center point of a defined S2 tile based on an
            API developed by M. Sudmanns, or from the kml file if request fails.'''

        #
        # Formulate request and get it.
        #
        with requests.Session() as s:

            api_request = ('http://cf000008.geo.sbg.ac.at/cgi-bin/s2-dashboard/'
                'api.py?centroid={}').format(tile)

            try:
                r = s.get(api_request)

                #
                # Read string result as a dictionary.
                #
                result = {}
                result = r.text
                result = ast.literal_eval(result)

            #
            # Catch base-class exception.
            #
            except requests.exceptions.RequestException as e:
                #print '\n\n{}\n\n'.format(e)
                result = {"status": "FAIL"}

        #
        # Extract lat, lon from API request, or try to get from file if failed.
        #
        if result["status"] == "OK" and result["data"]:
            coords = [result["data"]["x"], result["data"]["y"]]

        else:
            return 'API failed.'

        return coords

#
# Ultimately this exists to create an empty namespace similar to the output of
# optparse or argparse to keep from having to change much code from before.
#
class Namespace(object):
    pass
