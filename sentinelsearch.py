import ast
import sys
import os.path
import requests
import zipfile
from datetime import date
from datetime import datetime
import xml.etree.ElementTree as etree
import qgis

from PyQt4.QtCore import QDate, Qt, QObject, pyqtSignal
from PyQt4.QtGui import QMessageBox, QFileDialog, QTableWidgetItem, QWidget


class SentinelSearch(QObject):

    finished = pyqtSignal(bool)
    finished_download = pyqtSignal(bool)
    # finished_S1download = pyqtSignal(bool)
    set_message = pyqtSignal(str)
    connecting_message = pyqtSignal(str)
    searching_message = pyqtSignal(str)
    search_progress_max = pyqtSignal(int)
    search_progress_set = pyqtSignal(int)
    download_progress_set = pyqtSignal(int)
    enable_btnSearch = pyqtSignal()

    def __init__(self, dialog):
        QObject.__init__(self)
        self.dlg = dialog
        self.killed = False

    def open(self):

        """Open file dialog and return selected directory path."""

        self.fileDialog = QFileDialog()
        # self.fileDialog.show()
        self.dlg.writeDir_txtPath.setText(
            self.fileDialog.getExistingDirectory())

    def get_arguments(self):

        #
        # Create options namespace. Perhaps (definitely) bad practice.
        #
        options = Namespace()

        #
        # Initialize variables.
        #
        options.user = None
        options.password = None
        options.hub = None
        options.sentinel = None
        options.orderby = None
        options.latmin = None
        options.latmax = None
        options.lonmin = None
        options.lonmax = None
        options.lat = None
        options.lon = None
        options.tile = None
        options.write_dir = None
        options.max_records = None
        options.start_date = None
        options.end_date = None
        options.start_ingest_date = None
        options.end_ingest_date = None
        options.rel_orbit = None
        options.abs_orbit = None
        options.orbitdir = None
        options.s1mode = None
        options.s1polar = None
        options.s1product = None
        options.s2product = None
        options.max_cloud = None

        #
        # Determine data download hub (e.g. ESA API or dhus)
        #
        if self.dlg.hub_comboBox.currentText() == 'API Hub':
            options.hub = 'apihub'
        elif self.dlg.hub_comboBox.currentText() == 'Dhus':
            options.hub = 'dhus'
        elif self.dlg.hub_comboBox.currentText() == 'ZAMG':
            options.hub = 'zamg'
        elif self.dlg.hub_comboBox.currentText() == 'HNSDMS':
            options.hub = 'hnsdms'
        # elif self.dlg.hub_comboBox.currentText() == 'Finhub':
        #     options.hub = 'finhub'
        else:
            options.hub = None

        #
        # Define which sensor should be queried.
        #
        if self.dlg.sensor_comboBox.currentText() == 'All':
            options.sentinel = None
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

        #
        # Sort results by ingestion or acquisition date, asc. or desc..
        #
        if self.dlg.orderBy_comboBox.currentText() != '':
            options.orderby = self.dlg.orderBy_comboBox.currentText()
        else:
            options.orderby = None

        #
        # User credentials.
        #
        if self.dlg.user_lineEdit.text() != '':
            options.user = self.dlg.user_lineEdit.text()
        else:
            options.user = None

        if self.dlg.pass_lineEdit.text() != '':
            options.password = self.dlg.pass_lineEdit.text()
        else:
            options.password = None

        #
        # Coordinates for polygon or point locations.
        #
        if self.dlg.LLX_lineEdit.text() != '':
            options.lonmin = self.dlg.LLX_lineEdit.text()
        else:
            options.lonmin = None

        if self.dlg.ULX_lineEdit.text() != '':
            options.lonmax = self.dlg.ULX_lineEdit.text()
        else:
            options.lonmax = None

        if self.dlg.LLY_lineEdit.text() != '':
            options.latmin = self.dlg.LLY_lineEdit.text()
        else:
            options.latmin = None

        if self.dlg.ULY_lineEdit.text() != '':
            options.latmax = self.dlg.ULY_lineEdit.text()
        else:
            options.latmax = None

        if self.dlg.lat_lineEdit.text() != '':
            options.lat = self.dlg.lat_lineEdit.text()
        else:
            options.lat = None

        if self.dlg.lon_lineEdit.text() != '':
            options.lon = self.dlg.lon_lineEdit.text()
        else:
            options.lon = None

        #
        # Sentinel-2 tile name for S2 tile extraction.
        #
        if (self.dlg.s2Extract_checkBox.isChecked() is True
                and self.dlg.s2Extract_checkBox.isEnabled() is True):

            options.tile = (self.dlg.s2Tile_lineEdit.text()).upper()

        else:

            options.tile = None

        #
        # Directory to save data.
        #
        if self.dlg.writeDir_txtPath.text() != '':
            options.write_dir = self.dlg.writeDir_txtPath.text()
        else:
            options.write_dir = None

        #
        # Maximum record number (max. 100 for API hub, 10 for dhus).
        #
        options.max_records = self.dlg.maxRecords_spinBox.cleanText()

        #
        # Ingestion dates.
        #
        if self.dlg.ingest_enable.isChecked():

            options.start_ingest_date = self.dlg.ingestFrom_dateEdit.date()
            options.end_ingest_date = self.dlg.ingestTo_dateEdit.date()

            #
            # Convert ingestion dates to proper ISO format.
            #
            options.start_ingest_date = QDate.toString(
                options.start_ingest_date, 'yyyy-MM-dd')
            options.end_ingest_date = QDate.toString(
                options.end_ingest_date, 'yyyy-MM-dd')

        else:
            options.start_ingest_date = None
            options.end_ingest_date = None

        #
        # Dates of capture.
        #
        if self.dlg.date_enable.isChecked():

            options.start_date = self.dlg.dateFrom_dateEdit.date()
            options.end_date = self.dlg.dateTo_dateEdit.date()

            #
            # Convert sensing dates to proper ISO format.
            #
            options.start_date = QDate.toString(
                options.start_date, 'yyyy-MM-dd')
            options.end_date = QDate.toString(
                options.end_date, 'yyyy-MM-dd')

        else:
            options.start_date = None
            options.end_date = None

        #
        # Orbit direction (e.g. ascending, descending).
        #
        if self.dlg.orbitDir_comboBox.currentText() != '':
            options.orbitdir = self.dlg.orbitDir_comboBox.currentText()
        else:
            options.orbitdir = None

        #
        # Relative or absolute orbit number.
        #
        if (self.dlg.orbit_lineEdit.text() != ''
                and self.dlg.relOrbit_radioButton.isChecked() is True):

            options.rel_orbit = self.dlg.orbit_lineEdit.text()
            options.abs_orbit = None

        elif (self.dlg.orbit_lineEdit.text() != ''
                and self.dlg.absOrbit_radioButton.isChecked() is True):

            options.rel_orbit = None
            options.abs_orbit = self.dlg.orbit_lineEdit.text()

        else:
            options.rel_orbit = None
            options.abs_orbit = None

        #
        # S1 product (e.g. GRD, SLC, OCN).
        #
        if (self.dlg.s1Product_comboBox.currentText() != ''
                and self.dlg.s1Product_comboBox.isEnabled() is True):

            options.s1product = self.dlg.s1Product_comboBox.currentText()

        else:
            options.s1product = None

        #
        # S1 polarisation (e.g. HH, VH, HV, VV, HH+HV, VV+VH).
        #
        if (self.dlg.s1Polar_comboBox.currentText() != ''
                and self.dlg.s1Polar_comboBox.isEnabled() is True):

            options.s1polar = self.dlg.s1Polar_comboBox.currentText()

        else:
            options.s1polar = None

        #
        # S1 operational mode (e.g. SM, IW, EW, WV).
        #
        if (self.dlg.s1Mode_comboBox.currentText() != ''
                and self.dlg.s1Mode_comboBox.isEnabled() is True):

            options.s1mode = self.dlg.s1Mode_comboBox.currentText()

        else:
            options.s1mode = None

        #
        # S2 product (e.g. S2MSI1C, S2MSI2Ap).
        #
        if (self.dlg.s2Product_comboBox.currentText() != ''
                and self.dlg.s2Product_comboBox.isEnabled() is True):

            options.s2product = self.dlg.s2Product_comboBox.currentText()

        else:
            options.s2product = None

        #
        # Maximum cloud cover percentage for S2 images.
        #
        if (self.dlg.cloudCover_enable.isChecked()
                and self.dlg.cloudCover_spinBox.isEnabled() is True):

            options.max_cloud = self.dlg.cloudCover_spinBox.cleanText()

        else:
            options.max_cloud = None

        return options

    def args_to_messagebox(self, options, query=None):

        options_dict = vars(options)
        options_string = ''

        for key, value in options_dict.iteritems():

            options_string += '{} : {}\n'.format(key, value)

        msg_args = QMessageBox()
        msg_args.setIcon(QMessageBox.Information)
        msg_args.setText(options_string)
        # msg_args.setInformativeText("This is additional information")
        # msg_args.setWindowTitle("MessageBox demo")

        if query is not None:

            msg_args.setDetailedText(query)

        msg_args.exec_()

    def text_to_messagebox(self, header, message, long_text=None):

        msg_txt = QMessageBox()
        msg_txt.setIcon(QMessageBox.Information)
        msg_txt.setText(message)
        # msg_txt.setInformativeText("This is additional information")
        msg_txt.setWindowTitle(header)
        if long_text is not None:
            msg_txt.setDetailedText(long_text)
        msg_txt.exec_()

    def get_tile_coords(self):

        """Prints returned tile center coordinates to GUI or creates an
            error message box."""

        #
        # Get tile name from GUI and conduct API request with kml_api()
        #
        s2_tile = self.dlg.s2Tile_lineEdit.text()
        coords = self.kml_api(s2_tile)

        #
        # Parse the response and print to GUI or throw exception.
        #
        try:

            lon = str(round((float(coords[0])), 4))
            lat = str(round((float(coords[1])), 4))
            coords_str = '{}: lon {}, lat {}'.format(s2_tile, lon, lat)
            self.dlg.lat_lineEdit.setText(lat)
            self.dlg.lon_lineEdit.setText(lon)

        except:

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText('API failed or tile not found.')
            msg.setWindowTitle('Sentinel-2 Tile Search')
            msg.exec_()

    def kml_api(self, tile):

        """Returns the center point of a defined S2 tile based on an
            API developed by M. Sudmanns."""

        with requests.Session() as s:

            api_request = (
                'http://cf000008.geo.sbg.ac.at/cgi-bin/s2-dashboard/api.py?'
                'centroid={}').format(tile)

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
                # print '\n\n{}\n\n'.format(e)
                result = {"status": "FAIL"}

        #
        # Extract lat, lon from API request, or try to get from file if failed.
        #
        if result["status"] == "OK" and result["data"]:

            coords = [result["data"]["x"], result["data"]["y"]]

        else:
            return 'API failed.'

        return coords

    def create_query(self, options, huburl, maxrecords):

        """Creates a query string for the data hub based on GUI input."""

        #
        # Build in checks for valid commands related to the spatial aspect.
        #
        if options.lat is None or options.lon is None:

            if (options.latmin is None
                    or options.lonmin is None
                    or options.latmax is None
                    or options.lonmax is None):

                # message = 'Please provide at least one point or rectangle!'
                # self.text_to_messagebox('Error.', message)

                geom = None

                # return None

            else:
                geom = 'rectangle'

        else:

            if (options.latmin is None
                    and options.lonmin is None
                    and options.latmax is None
                    and options.lonmax is None):

                geom = 'point'

            else:
                # message = 'Choose either a point or rectangle, not both!'
                # self.text_to_messagebox('Error.', message)

                geom = None
                # return None

        #
        # Instantiate query string.
        #
        query = ''

        #
        # Create spatial parts of the query ::: point or rectangle.
        # Beware of the quotation marks in the query string.
        #
        if geom == 'point':

            if (sys.platform.startswith('linux')
                    or sys.platform.startswith('darwin')):

                query += '(footprint:\\"Intersects({} {})\\")'.format(
                    options.lon, options.lat)

            else:

                query += '(footprint:"Intersects({} {})")'.format(
                    options.lon, options.lat)

        elif geom == 'rectangle':

            if (sys.platform.startswith('linux')
                    or sys.platform.startswith('darwin')):

                query += (
                    '(footprint:\\"Intersects(POLYGON(({lonmin} {latmin}, '
                    '{lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax}, '
                    '{lonmin} {latmin})))\\")').format(
                        latmin=options.latmin,
                        latmax=options.latmax, lonmin=options.lonmin,
                        lonmax=options.lonmax)

            else:

                query += (
                    '(footprint:"Intersects(POLYGON(({lonmin} {latmin}, '
                    '{lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax}, '
                    '{lonmin} {latmin})))")').format(
                        latmin=options.latmin,
                        latmax=options.latmax, lonmin=options.lonmin,
                        lonmax=options.lonmax)
        else:
            pass

        #
        # Add Sentinel mission.
        #
        if options.sentinel == 'S1':

            query += ' AND (platformname:Sentinel-1)'

        elif options.sentinel == 'S2':

            query += ' AND (platformname:Sentinel-2)'

        elif options.sentinel == 'S3':

            query += ' AND (platformname:Sentinel-3)'

        elif options.sentinel == 'S1A':

            query += ' AND (platformname:Sentinel-1 AND filename:S1A_*)'

        elif options.sentinel == 'S1B':

            query += ' AND (platformname:Sentinel-1 AND filename:S1B_*)'

        elif options.sentinel == 'S2A':

            query += ' AND (platformname:Sentinel-2 AND filename:S2A_*)'

        elif options.sentinel == 'S2B':

            query += ' AND (platformname:Sentinel-2 AND filename:S2B_*)'

        else:
            pass

        #
        # Add sensing/acquisition/capture date.
        #
        if options.start_date is not None or options.end_date is not None:

            query += (
                ' AND (beginPosition:[{0}T00:00:00.000Z TO {1}T23:59:59.999Z] '
                'AND endPosition:[{0}T00:00:00.000Z TO {1}T23:59:59.999Z])'
                    ).format(
                        options.start_date, options.end_date)

        else:
            pass

        #
        # Add database ingestion date.
        #
        if (options.start_ingest_date is not None
                or options.end_ingest_date is not None):

            query += (
                ' AND (ingestionDate:[{}T00:00:00.000Z TO {}T23:59:59.999Z])'
                    ).format(
                        options.start_ingest_date, options.end_ingest_date)

        else:
            pass

        #
        # Add orbits, if defined (default: NONE).
        #
        if options.rel_orbit is not None:

            query += ' AND (relativeorbitnumber:{})'.format(options.rel_orbit)

        elif options.abs_orbit is not None:

            query += ' AND (orbitnumber:{})'.format(options.abs_orbit)

        else:
            pass

        #
        # Orbit direction as free text.
        #
        if options.orbitdir is not None:

            query += ' AND {}'.format(options.orbitdir)

        else:
            pass

        #
        # Add Sentinel-1 specific query parameters.
        #
        if options.s1product is not None:

            query += ' AND (producttype:{})'.format(options.s1product)

        else:
            pass

        if options.s1polar is not None:

            query += ' AND (polarisationmode:{})'.format(options.s1polar)

        else:
            pass

        if options.s1mode is not None:

            query += ' AND (sensoroperationalmode:{})'.format(options.s1mode)

        else:
            pass

        #
        # Add Sentinel-2 specific query parameters.
        #
        if options.s2product is not None:

            query += ' AND (producttype:{})'.format(options.s2product)

        else:
            pass

        if (options.max_cloud is not None
                and (
                    options.sentinel == 'S2'
                    or options.sentinel == 'S2A'
                    or options.sentinel == 'S2B')):

            query += ' AND (cloudcoverpercentage:[0.0 TO {}])'.format(
                options.max_cloud)

        else:
            pass

        #
        # Sort results, if desired.
        #
        if options.orderby == 'Ingestion date, ascending':
            orderby = 'orderby=ingestiondate asc'
        elif options.orderby == 'Ingestion date, descending':
            orderby = 'orderby=ingestiondate desc'
        elif options.orderby == 'Sensing date, ascending':
            orderby = 'orderby=beginposition asc'
        elif options.orderby == 'Sensing date, descending':
            orderby = 'orderby=beginposition desc'
        else:
            orderby = None

        #
        # Set rows to number of maxrecords or less, if query is smaller.
        #
        if int(options.max_records) <= maxrecords:

            maxrecords = options.max_records
        else:
            maxrecords = str(maxrecords)

        #
        # Correct query string if no geographic coordinates are given.
        #
        if query.startswith(' AND'):

            query = query[5:]

        #
        # Create query string.
        #
        if orderby is not None:

            query = '{}search?q=({})&rows={}&{}'.format(
                huburl, query, maxrecords, orderby)

        else:

            query = '{}search?q=({})&rows={}'.format(
                huburl, query, maxrecords)

        #
        # Print arguments to message box for test.
        #
        # self.args_to_messagebox(options, query)
        # self.text_to_messagebox('Query', query)

        return query

    def start_session(self, options):

        #
        # Emit message to UI.
        #
        self.connecting_message.emit('Connecting . . .')

        #
        # Set data source (apihub vs dhus -- more could be added).
        #
        if options.hub == 'apihub':
            huburl = 'https://scihub.copernicus.eu/apihub/'
            maxrecords = 100

        elif options.hub == 'dhus':
            huburl = 'https://scihub.copernicus.eu/dhus/'
            maxrecords = 10

        elif options.hub == 'zamg':
            huburl = 'https://data.sentinel.zamg.ac.at/'
            maxrecords = 100

        elif options.hub == 'hnsdms':
            huburl = 'https://sentinels.space.noa.gr/dhus/'
            maxrecords = 100

        # elif options.hub == 'finhub':
        #     huburl = 'https://finhub.nsdc.fmi.fi/odata/'
        #     maxrecords = 100

        else:
            huburl = None
            maxrecords = None

        #
        # Authorize ESA API or DataHub Credentials
        #
        if options.user is not None and options.password is not None:
            account = options.user
            passwd = options.password

        else:
            account = None
            passwd = None

        #
        # Start session/authorization using requests module.
        #
        session = requests.Session()
        session.auth = (account, passwd)

        return session, huburl, account, passwd, maxrecords

    def set_value(self):

        """A place to set platform dependent bits."""

        # TODO: platform dependent testing.

        if (sys.platform.startswith('linux')
                or sys.platform.startswith('darwin')):

            value = '\$value'

        else:
            value = '$value'

        return value

    def get_query_xml(self):

        try:
            options = self.get_arguments()

            if (options.tile is not None
                    and options.sentinel != 'S2'
                    and options.sentinel != 'S2A'
                    and options.sentinel != 'S2B'):

                message = (
                    'Tile extraction option can only be used for {}!'
                    ).format(options.sentinel)

                self.text_to_messagebox('Error', message)
                # self.enable_btnSearch.emit()
                # return

            if options.user is None or options.password is None:

                message = 'Please enter a username and password!'
                self.text_to_messagebox('Error', message)
                self.enable_btnSearch.emit()
                return

            #
            # Create authenticated http session.
            #
            session, huburl, account, passwd, maxrecords = self.start_session(
                options)

            value = self.set_value()

            query = self.create_query(options, huburl, maxrecords)

            if query is None:

                return None

            tW1 = self.dlg.s1Results_tableWidget
            tW2 = self.dlg.s2Results_tableWidget

            """TODO: add loop to accomodate larger queries of more than 100
            records, where start is updated. Max rows are hardcoded or modified
            to smallernumbers already in create_query()."""

            #
            # Create GET request from hub and parse it.
            #
            try:
                response = session.get(query, stream=True)
                query_tree = etree.fromstring(response.content)

            except:

                message = (
                    'Error with connection.\n'
                    'Please check credentials, try another hub or try again '
                    'later.')

                self.text_to_messagebox('Error', message)
                self.enable_btnSearch.emit()
                # query_tree = etree.parse(
                #    'C:\Users\GISmachine\Documents\GitHub\AIQ\query_results.xml')
                return

            entries = query_tree.findall('{http://www.w3.org/2005/Atom}entry')

            #
            # Save the number of scenes to a variable.
            #
            scenes = str(len(entries))

            #
            # Create progress bar with maximum as the number of entries.
            #
            self.search_progress_max.emit(len(entries))
            self.searching_message.emit('Searching . . .')

            #
            # Set a counter to reference the progress.
            #
            i = 0

            for entry in range(len(entries)):

                if self.killed is True:
                    # kill request received, exit loop early.
                    break
                #
                # Update progress bar.
                #
                i = i + 1
                percent = int((i/float(len(entries))) * 100)
                self.search_progress_set.emit(percent)

                #
                # The UUID element is unique for each record and the key
                # ingredient for creating the path to the file.
                #
                uuid_element = (entries[entry].find(
                    '{http://www.w3.org/2005/Atom}id')).text
                title_element = (entries[entry].find(
                    '{http://www.w3.org/2005/Atom}title')).text

                #
                # Check both tables for UUID and filename.
                # Skip if already in either table.
                #
                tW1_UUIDs = []
                tW1_fns = []
                tW1Rows = tW1.rowCount()
                for row in xrange(0, tW1Rows):

                    #
                    # Try loop to avoid when UUID is None (Database issue)
                    #
                    try:
                        tw1_col11 = tW1.item(row, 11).text()
                        tW1_UUIDs.append(tw1_col11)

                        tw1_col0 = tW1.item(row, 0).text()
                        tW1_fns.append(tw1_col0)

                    except:
                        # This seems to happen, if UUID is None.
                        pass

                tW2_UUIDs = []
                tW2_fns = []
                tW2Rows = tW2.rowCount()
                for row in xrange(0, tW2Rows):

                    #
                    # Try loop to avoid when UUID is None (Database issue)
                    #
                    try:
                        tw2_col11 = tW2.item(row, 11).text()
                        tW2_UUIDs.append(tw2_col11)

                        tw2_col0 = tW2.item(row, 0).text()
                        tW2_fns.append(tw2_col0)

                    except:
                        # This seems to happen, if UUID is None.
                        pass

                if uuid_element in tW2_UUIDs or uuid_element in tW1_UUIDs:

                    continue

                elif title_element in tW2_fns or title_element in tW1_fns:

                    continue

                elif uuid_element is None or title_element is None:

                    continue
                #
                # If UUID and titel not in one of the tables, add record
                # to respective table.
                #
                else:

                    #
                    # The title element contains the corresponding file name.
                    #
                    filename = (entries[entry].find(
                        './/*[@name="filename"]')).text
                    size_element = (entries[entry].find(
                        './/*[@name="size"]')).text
                    rel_orbit = int((entries[entry].find(
                        './/*[@name="relativeorbitnumber"]')).text)
                    footprint = (entries[entry].find(
                        './/*[@name="footprint"]')).text
                    sensing_date = ((entries[entry].find(
                        './/*[@name="beginposition"]')).text)[:10]
                    sentinel_link = ("{}odata/v1/Products('{}')/{}").format(
                        huburl, uuid_element, value)

                    footprint = footprint.replace(
                        'POLYGON ((', "").replace('))', "").split(',')

                    xList = []
                    yList = []

                    for coords in footprint:

                        xList.append(float(coords.split(' ')[0]))
                        yList.append(float(coords.split(' ')[1]))

                    lonmin = float('{0:.2f}'.format(min(xList)))
                    lonmax = float('{0:.2f}'.format(max(xList)))
                    latmin = float('{0:.2f}'.format(min(yList)))
                    latmax = float('{0:.2f}'.format(max(yList)))

                    if filename.startswith('S1'):

                        try:

                            s1Product = (entries[entry].find(
                                './/*[@name="producttype"]')).text

                        except:

                            s1Product = '---'

                        try:

                            s1Polar = (entries[entry].find(
                                './/*[@name="polarisationmode"]')).text

                        except:

                            s1Polar = '---'

                        try:

                            s1Mode = (entries[entry].find(
                                './/*[@name="sensoroperationalmode"]')).text

                        except:

                            s1Mode = '---'

                        #
                        # Add items to S1 table.
                        #
                        c = tW1.rowCount()
                        tW1.setRowCount(c + 1)
                        self.add_to_table(tW1, title_element, c, 0)
                        self.add_to_table(tW1, s1Product, c, 1)
                        self.add_to_table(tW1, s1Polar, c, 2)
                        self.add_to_table(tW1, s1Mode, c, 3)
                        self.add_to_table(tW1, sensing_date, c, 4)
                        self.add_to_table(tW1, rel_orbit, c, 5)
                        self.add_to_table(tW1, size_element, c, 6)
                        self.add_to_table(tW1, latmin, c, 7)
                        self.add_to_table(tW1, latmax, c, 8)
                        self.add_to_table(tW1, lonmin, c, 9)
                        self.add_to_table(tW1, lonmax, c, 10)
                        self.add_to_table(tW1, uuid_element, c, 11)
                        self.add_to_table(tW1, sentinel_link, c, 12)

                    elif filename.startswith('S2'):

                        try:

                            cloud_element = (entries[entry].find(
                                './/*[@name="cloudcoverpercentage"]')).text
                            cloud_element = float(
                                '{0:.1f}'.format(float(cloud_element)))

                        except:

                            cloud_element = '---'

                        #
                        # Return tile names per entry using function
                        # return_tiles if desired.
                        #
                        if filename.startswith('S2A_OPER_'):

                            try:

                                found_tiles = self.return_tiles(
                                    session, uuid_element, filename, huburl)

                                #
                                # Print the number of tiles and their names.
                                #
                                numGranules = str(len(found_tiles[0]))
                                granules = found_tiles[1]

                            except:

                                numGranules = '---'
                                granules = '---'

                        elif (filename.startswith('S2A_MSIL1C_')
                                or filename.startswith('S2A_MSIL2A_')
                                or filename.startswith('S2B_MSIL1C_')
                                or filename.startswith('S2B_MSIL2A_')):

                            try:

                                numGranules = 1
                                granules = (entries[entry].find(
                                    './/*[@name="tileid"]')).text

                            except:

                                numGranules = 1
                                granules = filename[-26:-21]

                        else:

                            numGranules = '---'
                            granules = '---'

                        if (options.tile is not None
                                and options.tile not in granules):

                            pass

                        else:

                            #
                            # Add items to S2 table.
                            #
                            c = tW2.rowCount()
                            tW2.setRowCount(c + 1)
                            self.add_to_table(tW2, title_element, c, 0)
                            self.add_to_table(tW2, granules, c, 1)
                            self.add_to_table(tW2, numGranules, c, 2)
                            self.add_to_table(tW2, cloud_element, c, 3)
                            self.add_to_table(tW2, sensing_date, c, 4)
                            self.add_to_table(tW2, rel_orbit, c, 5)
                            self.add_to_table(tW2, size_element, c, 6)
                            self.add_to_table(tW2, latmin, c, 7)
                            self.add_to_table(tW2, latmax, c, 8)
                            self.add_to_table(tW2, lonmin, c, 9)
                            self.add_to_table(tW2, lonmax, c, 10)
                            self.add_to_table(tW2, uuid_element, c, 11)
                            self.add_to_table(tW2, sentinel_link, c, 12)

            total_size = self.return_total_size(tW1, tW2)
            # self.text_to_messagebox(
            #    'Results.', 'Total size of results: {}'.format(total_size))
            size_message = 'Total size of results: {}'.format(total_size)
            self.set_message.emit(size_message)
            session.close()

        except Exception, e:

            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())

        self.finished.emit(self.killed)

    def return_total_size(self, tW1, tW2):

        #
        # Calculate cumulative size of all scenes in both tables.
        #
        total_size = 0

        tW1Rows = tW1.rowCount()

        for row in xrange(0, tW1Rows):

            size_element = tW1.item(row, 6).text()

            if 'GB' in size_element:

                size_element = size_element.replace(' GB', '')
                size_element = float(size_element)
                total_size += size_element

            elif 'MB' in size_element:

                size_element = size_element.replace(' MB', '')
                size_element = float(size_element) / 1024
                size_element = size_element
                total_size += size_element

        tW2Rows = tW2.rowCount()

        for row in xrange(0, tW2Rows):

            size_element = tW2.item(row, 6).text()

            if 'GB' in size_element:

                size_element = size_element.replace(' GB', '')
                size_element = float(size_element)
                total_size += size_element

            elif 'MB' in size_element:

                size_element = size_element.replace(' MB', '')
                size_element = float(size_element) / 1024
                size_element = size_element
                total_size += size_element

        total_size = '{0:.2f} GB'.format(total_size)

        return total_size

    def return_tiles(self, session, uuid_element, filename, huburl, tile=''):

        '''Function returns tiles incldued in the GRANULE folder of a product,
           including the entire file name of one desired tile, if specified.'''

        #
        # Create link to search for tile/granule data.
        #
        granule_link = (
            "{}odata/v1/Products"
            "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes").format(
                huburl, uuid_element, filename)

        #
        # Create GET request from hub and parse it.
        #
        response = session.get(granule_link, stream=True)
        granule_tree = etree.fromstring(response.content)

        #
        # Search for all entires (i.e. tiles)
        #
        granule_entries = granule_tree.findall(
            '{http://www.w3.org/2005/Atom}entry')

        #
        # Empty string to fill with all tiles in the file.
        #
        granules = ''

        #
        # Go through each tile appending each name to string.
        #
        for granule_entry in range(len(granule_entries)):

            #
            # UUID element creates the path to the file.
            #
            granule_dir_name = (granule_entries[granule_entry].find(
                '{http://www.w3.org/2005/Atom}title')).text
            granule = granule_dir_name[50:55]
            granules += ' {}'.format(granule)

            #
            # If one tile is given as an optional arg, return tile file name.
            #
            if tile != '':

                if tile in granule_dir_name:

                    granule_file = granule_dir_name

            else:

                granule_file = ''

        #
        # Return the number of granules and their names, or just the individual
        # tile file name if a specific tile was asked for.
        #
        if not granule_file:
            return(granule_entries, granules)

        else:
            return(granule_file)

    def add_to_table(self, table, item, row, column):

        itMID = QTableWidgetItem()

        itMID.setData(Qt.DisplayRole, item)

        table.setItem(row, column, itMID)

    def clearTable(self):

        """Clears both Sentinel-1 and Sentinel-2 results tables."""

        #
        # Confirm clearing of tables.
        #
        caption = 'Clear results.'
        message = 'Would you like to clear all results?'
        i = QWidget()
        q = QMessageBox.question(
            i, caption, message, QMessageBox.Yes, QMessageBox.No)

        if q == QMessageBox.Yes:

            tW1 = self.dlg.s1Results_tableWidget
            tW2 = self.dlg.s2Results_tableWidget
            tW1.clearContents()

            for i in range(0, tW1.rowCount()):

                tW1.removeRow(0)

            tW2.clearContents()

            for i in range(0, tW2.rowCount()):

                tW2.removeRow(0)

        if q == QMessageBox.No:

            pass

    def make_dir(self, location, filename):

        ''' Creates a directory in another directory if it doesn't
            already exist.'''

        dir_name = '{}/{}'.format(location, filename)

        if not(os.path.exists(dir_name)):

            os.mkdir(dir_name)

        return dir_name

    def download_results(self):

        options = self.get_arguments()

        #
        # Create download directory if it doesn't yet exist.
        #
        if not(os.path.exists(options.write_dir)):

                os.mkdir(options.write_dir)

        #
        # Make sure write_dir is formatted properly.
        #
        if (sys.platform.startswith('linux')
                or sys.platform.startswith('darwin')
                and options.write_dir is not None):
            # Add whatever might be necessary here.
            pass

        elif options.write_dir is not None:
            options.write_dir = (options.write_dir).replace('/', '\\')

        elif options.write_dir is None:
            message = 'Please enter a directory to download the data to!'
            self.text_to_messagebox('Error', message)
            return None
        else:
            pass

        #
        # Create authenticated http session.
        #
        session, huburl, account, passwd, maxrecords = self.start_session(
            options)

        #
        # Platform dependent stuff.
        #
        value = self.set_value()

        #
        # Define data tables for S1 and S2 results.
        #
        tW1 = self.dlg.s1Results_tableWidget
        tW2 = self.dlg.s2Results_tableWidget
        tW1Rows = tW1.rowCount()
        tW2Rows = tW2.rowCount()

        total_size = self.return_total_size(tW1, tW2)
        chunks_to_download = (float(total_size[:-3]))*1024/10

        #
        # Set a counter to reference the progress.
        #
        i = 0

        #
        # Download Sentinel-1 results from S1 table.
        #
        for row in xrange(0, tW1Rows):

            if self.killed is True:
                # kill request received, exit loop early.
                break

            sentinel_link = tW1.item(row, 12).text()
            title_element = tW1.item(row, 0).text()
            filename = '{}.SAFE'.format(title_element)
            zfile = '{}.zip'.format(title_element)

            #
            # Skip files that have already been downloaded.
            #
            check = self.download_check(
                options.write_dir, title_element, filename)

            if check is True:

                pass

            i = self.download_link(
                session, zfile, sentinel_link, options.write_dir, i,
                chunks_to_download)

            if self.killed is True:
                # kill request received, exit loop early.
                break
            #
            # Unzip even if path names are really long.
            #
            self.unzip_result(
                options.write_dir, filename, zfile, title_element)

        #
        # Download Sentinel-2 results.
        #
        #
        # If you did not search for a specific tile, downloading will begin.
        #
        if options.tile is None:

            for row in xrange(0, tW2Rows):

                if self.killed is True:
                    # kill request received, exit loop early.
                    break

                #
                # Create download command for the entry.
                #
                sentinel_link = tW2.item(row, 12).text()
                title_element = tW2.item(row, 0).text()
                filename = '{}.SAFE'.format(title_element)
                zfile = '{}.zip'.format(title_element)

                #
                # Skip files that have already been downloaded.
                #
                check = self.download_check(
                    options.write_dir, title_element, filename)

                if check is True:

                    pass

                i = self.download_link(
                    session, zfile, sentinel_link, options.write_dir, i,
                    chunks_to_download)

                if self.killed is True:
                    # kill request received, exit loop early.
                    break

                #
                # Unzip folder.zip even if path names are really long.
                #
                self.unzip_result(
                    options.write_dir, filename, zfile, title_element)

        #
        # If you want to download a tile that you searched for, then it will
        # create the proper file structure mimicing a complete download and
        # fill it with data specific to the tile you want, or, post 06.12.16,
        # simply download complete matching tile packages.
        #
        elif options.tile is not None:

            for row in xrange(0, tW2Rows):

                if self.killed is True:
                    # kill request received, exit loop early.
                    break

                #
                # Create download command for the entry.
                #
                uuid_element = tW2.item(row, 11).text()
                sentinel_link = tW2.item(row, 12).text()
                title_element = tW2.item(row, 0).text()
                filename = '{}.SAFE'.format(title_element)
                zfile = '{}.zip'.format(title_element)
                included_tiles = tW2.item(row, 1).text()

                if (options.tile in included_tiles
                        and filename.startswith('S2A_OPER_')):

                    #
                    # Adjust sentinel_link path.
                    #
                    sentinel_link = (
                        "{}odata/v1/Products('{}')/Nodes('{}')/Nodes").format(
                            huburl, uuid_element, filename)

                    #
                    # Skip files that have already been downloaded.
                    #
                    check = self.download_check(
                        options.write_dir, title_element, filename)

                    if check is True:

                        pass

                # File structire---------------------------------------------

                    product_dir_name = self.make_dir(
                        options.write_dir, filename)

                    #
                    # Create GRANULE directory in product directory.
                    #
                    granule_dir = self.make_dir(product_dir_name, 'GRANULE')

                    #
                    # Create tile dir in GRANULE dir based on tile file name.
                    #
                    tile_file = self.return_tiles(
                        session, uuid_element, filename, huburl, options.tile)

                    #
                    # If tile folder already exists, then it skips downloading.
                    #
                    # TODO: check if this is redundant to top download_check

                    if os.path.exists(os.path.join(granule_dir, tile_file)):

                        # print 'Tile Folder already downloaded.'

                        continue

                    tile_dir = self.make_dir(granule_dir, tile_file)

                    if self.killed is True:
                        # kill request received, exit loop early.
                        break

                # Downloads--------------------------------------------------

                    # print 'Downloading from scene #{}'.format(str(entry + 1))

                    #
                    # Download the product header file after finding the name
                    #
                    header_file = self.return_header(
                        session, huburl, uuid_element, filename)
                    header_link = "{}('{}')/{}".format(
                        sentinel_link, header_file, value)
                    i = self.download_link(
                        session, header_file, header_link, product_dir_name, i,
                        chunks_to_download)

                    if self.killed is True:
                        # kill request received, exit loop early.
                        break

                    #
                    # Download INSPIRE.xml
                    #
                    inspire_file = 'INSPIRE.xml'
                    inspire_link = "{}('{}')/{}".format(
                        sentinel_link, inspire_file, value)
                    i = self.download_link(
                        session, inspire_file, inspire_link,
                        product_dir_name, i, chunks_to_download)

                    if self.killed is True:
                        # kill request received, exit loop early.
                        break

                    #
                    # Download manifest.safe
                    #
                    manifest_file = 'manifest.safe'
                    manifest_link = "{}('{}')/{}".format(
                        sentinel_link, manifest_file, value)
                    i = self.download_link(
                        session, manifest_file, manifest_link,
                        product_dir_name, i, chunks_to_download)

                    if self.killed is True:
                        # kill request received, exit loop early.
                        break

                    #
                    # Download tile xml and create AUX_DATA, IMG_DATA, QI_DATA
                    # folders in the tile folder and download their contents.
                    #

                    i = self.get_tile_files(
                        session, huburl, value, uuid_element, filename,
                        tile_file, tile_dir, i, chunks_to_download)

                    # print 'Downloaded tile {} from scene #{}\n'.format(
                    #     options.tile, str(entry + 1))

                elif (options.tile in included_tiles
                        and (
                            filename.startswith('S2A_MSIL')
                            or filename.startswith('S2B_MSIL'))):

                    #
                    # Skip files that have already been downloaded.
                    #
                    check = self.download_check(
                        options.write_dir, title_element, filename)

                    if check is True:

                        pass

                    i = self.download_link(
                        session, zfile, sentinel_link, options.write_dir, i,
                        chunks_to_download)

                    if self.killed is True:
                        # kill request received, exit loop early.
                        break

                    #
                    # Unzip folder.zip even if path names are really long.
                    #
                    self.unzip_result(
                        options.write_dir, filename, zfile, title_element)

        session.close()
        self.finished_download.emit(self.killed)

    def get_tile_files(
            self, session, huburl, value, uuid_element, filename, tile_file,
            tile_dir, i, chunks_to_download):

        ''' Creates structure for tile specific download (tile inside GRANULE
           folder), and fills it.'''

        #
        # Define link to tile folder in data hub.
        #
        tile_folder_link = (
            "{}odata/v1/Products('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes"
            "('{}')/Nodes").format(
                huburl, uuid_element, filename, tile_file)

        #
        # Connect to server and stream the metadata as a string, parsing it.
        #
        response = session.get(tile_folder_link, stream=True)
        tile_folder_tree = etree.fromstring(response.content)

        #
        # Search for all entires
        #
        tile_folder_entries = (tile_folder_tree.findall(
            '{http://www.w3.org/2005/Atom}entry'))

        #
        # Go through each entry and identify information for download.
        #
        for tile_folder_entry in range(len(tile_folder_entries)):

            if self.killed is True:
                # kill request received, exit loop early.
                break

            tile_entry_title = (tile_folder_entries[tile_folder_entry].find(
                '{http://www.w3.org/2005/Atom}title')).text

            tile_entry_id = (tile_folder_entries[tile_folder_entry].find(
                '{http://www.w3.org/2005/Atom}id')).text

            #
            # Download xml file
            #
            if '.xml' in tile_entry_title:

                tile_xml_file = tile_entry_title
                tile_xml_link = '{}/{}'.format(tile_entry_id, value)

                i = self.download_link(
                    session, tile_xml_file, tile_xml_link, tile_dir, i,
                    chunks_to_download)

            else:

                #
                # Create folder for files and go get them
                #
                inside_folder_dir = self.make_dir(tile_dir, tile_entry_title)
                i = self.get_inside_files(
                    session, value, inside_folder_dir, tile_entry_id, i,
                    chunks_to_download)

        return i

    def get_inside_files(
            self, session, value, inside_folder_dir, tile_entry_id, i,
            chunks_to_download):

        ''' Go deeper in the element tree and download contents to the specified
           folder. This is relevant for tile specific downloads in the old file
           structure, pre-06.12.16.'''

        #
        # Get xml link and connect to server, parsing response as a string.
        #
        inside_folder_link = '{}/Nodes'.format(tile_entry_id)
        resp = session.get(inside_folder_link, stream=True)
        inside_folder_tree = etree.fromstring(resp.content)

        #
        # Search for all entires
        #
        inside_folder_entries = (inside_folder_tree.findall(
            '{http://www.w3.org/2005/Atom}entry'))

        #
        # Download each entry saving in the defined directory.
        #
        for inside_folder_entry in range(len(inside_folder_entries)):

            if self.killed is True:
                # kill request received, exit loop early.
                break

            inside_entry_title = (
                inside_folder_entries[inside_folder_entry].find(
                    '{http://www.w3.org/2005/Atom}title')).text
            inside_entry_id = (
                inside_folder_entries[inside_folder_entry].find(
                    '{http://www.w3.org/2005/Atom}id')).text
            inside_entry_file = inside_entry_title
            inside_entry_link = '{}/{}'.format(inside_entry_id, value)

            i = self.download_link(
                session, inside_entry_file, inside_entry_link,
                inside_folder_dir, i, chunks_to_download)

        return i

    def unzip_result(self, target_dir, filename, zfile, title_element):

        '''This function checks for zipped copies of results and handles
            accordingly.'''

        unzipped_path = os.path.join(target_dir, filename)
        zipped_path = os.path.join(target_dir, zfile)
        title_path = os.path.join(target_dir, title_element)

        if os.path.exists(zipped_path):

            self.unzip_path(target_dir, zipped_path)

        elif os.path.exists(title_path):

            self.unzip_path(target_dir, title_path)

        #
        # If the unzipped and zipped version exist, delete the zipped version.
        #
        if (os.path.exists(unzipped_path)
                and os.path.exists(zipped_path)):

            os.remove(zipped_path)

    def unzip_path(self, target_dir, zfile_path):

        '''This function unzips a result in linux and windows, even if
            the pathname is really long.'''

        try:

            with zipfile.ZipFile(zfile_path) as z:

                if (sys.platform.startswith('linux')
                        or sys.platform.startswith('darwin')):

                    z.extractall(u'{}'.format(target_dir))

                else:

                    z.extractall(u'\\\\?\\{}'.format(target_dir))

        except zipfile.BadZipfile:

            # print 'Zipfile corrupt or hub might have a problem.'
            # TODO: Add some sort of error exception action.
            os.remove(zfile_path)

    def download_link(
            self, session, file_toGet, link_toGet, target_folder, i,
            chunks_to_download):

        target_path = os.path.join(target_folder, file_toGet)
        chunk_size = 1024*1024*10

        #
        # Download file in chunks using requests module.
        #
        try:
            response = session.get(link_toGet, stream=True)
            with open(target_path, "wb") as handle:
                #
                # Iterate over content in 10MB chunks.
                #
                for chunk in response.iter_content(chunk_size):
                    if not chunk:
                        break

                    if self.killed is True:
                        # kill request received, exit loop early.
                        break
                    #
                    # Update progress bar.
                    #
                    i = i + 1
                    percent = int((i/float(chunks_to_download) * 100))
                    self.download_progress_set.emit(percent)
                    handle.write(chunk)

        except:
            pass

        return i

    def return_header(self, session, huburl, uuid_element, filename):

        ''' Function returns name of header xml incldued in a product.
            This is used only for pre-December 06, 2016 tile extraction.'''

        #
        # Create link to search for tile/granule data.
        #
        safe_link = (
            "{}odata/v1/Products('{}')/Nodes('{}')/Nodes").format(
                huburl, uuid_element, filename)
        #
        # Create GET request from hub and essentially parse it.
        #
        response = session.get(safe_link, stream=True)
        safe_tree = etree.fromstring(response.content)

        #
        # Search for all entires.
        #
        safe_entries = safe_tree.findall('{http://www.w3.org/2005/Atom}entry')

        #
        # Go through each entry in the safe folder and return header xml name.
        #
        for safe_entry in range(len(safe_entries)):

            #
            # UUID element creates the path to the file.
            #
            safe_name = (safe_entries[safe_entry].find(
                '{http://www.w3.org/2005/Atom}title')).text

            if 'SAFL1C' in safe_name:

                header_xml = safe_name

                return header_xml

        if not header_xml:

            pass
            # print 'Header xml could not be located!'
            # Maybe change to throw some sort of exception?

    def download_check(self, write_dir, title_element, filename):

        ''' Function checks if files have aleady been downloaded. If yes, but
           unzipped, it unzips them and deletes the zipped folder.'''

        #
        # Possible zipped folder name.
        #
        zfile = '{}.zip'.format(title_element)
        unzipped_path = os.path.join(write_dir, filename)
        zipped_path = os.path.join(write_dir, zfile)
        title_path = os.path.join(write_dir, title_element)

        #
        # Check if file was already downloaded.
        #
        if os.path.exists(title_path):
            # print '{} already exists in unzipped form!'.format(title_element)
            return True

        elif os.path.exists(unzipped_path):
            # print '{} already exists in unzipped form!'.format(filename)
            return True

        elif os.path.exists(zipped_path):
            # print '{} has already been downloaded!'.format(zfile)
            try:

                with zipfile.ZipFile(zipped_path) as z:

                    if (sys.platform.startswith('linux')
                            or sys.platform.startswith('darwin')):

                        z.extractall(u'{}'.format(write_dir))

                    else:

                        z.extractall(u'\\\\?\\{}'.format(write_dir))

                    os.remove(zipped_path)

                    return True

            except zipfile.BadZipfile:
                # print 'Zipfile corrupt or hub might have a problem.'
                os.remove(zipped_path)
                return False

        else:

            return False

    def remove_selected(self):

        #
        # Ask for confirmation.
        #
        caption = 'Remove rows.'
        message = (
            'Are you sure you want to remove highlighted rows from the table?')
        i = QWidget()
        q = QMessageBox.question(
            i, caption, message, QMessageBox.Yes, QMessageBox.No)

        #
        # If yes, delete selection.
        #
        if q == QMessageBox.Yes:
            tW1 = self.dlg.s1Results_tableWidget
            tW2 = self.dlg.s2Results_tableWidget

            self.removeRowsFromTable(tW1)
            self.removeRowsFromTable(tW2)

        else:
            pass

    def removeRowsFromTable(self, table):

        tW = table
        c = tW.rowCount()

        #
        # List of entries to remove (single cell selections count!).
        #
        rows = []

        for i in tW.selectedIndexes():

            rows.append(i.row())

        v = list(set(rows))

        #
        # Remove entries.
        #
        for i in reversed(range(0, len(v))):

            tW.removeRow(v[i])


#
# Ultimately this exists to create an empty namespace similar to the output of
# optparse or argparse to keep from having to change much code from before.
#
class Namespace(object):
    pass
