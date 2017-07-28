import ast
import sys
import os.path
import requests
import zipfile
from datetime import date
from datetime import datetime
import xml.etree.ElementTree as etree
import qgis
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QDate, Qt, QThread, QObject, pyqtSignal
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QFileDialog, QTableWidgetItem, QWidget, QProgressBar


class SentinelSearch(QObject):

    finished = pyqtSignal(bool)
    set_message = pyqtSignal(str)
    connecting_message = pyqtSignal(str)
    searching_message = pyqtSignal(str)
    search_progress_max = pyqtSignal(int)
    search_progress_set = pyqtSignal(int)
    enable_btnSearch = pyqtSignal()

    def __init__(self, dialog):
        QObject.__init__(self)
        self.dlg = dialog
        self.killed = False


    def open(self):

        """Open file dialog and return selected directory path."""

    	self.fileDialog = QFileDialog()
    	#self.fileDialog.show()
    	self.dlg.writeDir_txtPath.setText(self.fileDialog.getExistingDirectory())


    def get_arguments(self):

        #
        # Create options namespace. Perhaps (definitely) bad practice, but whatever.
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
        if (self.dlg.s2Extract_checkBox.isChecked() == True
                and self.dlg.s2Extract_checkBox.isEnabled() == True):

            options.tile = self.dlg.s2Tile_lineEdit.text()

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
            options.start_date = QDate.toString(options.start_date, 'yyyy-MM-dd')
            options.end_date = QDate.toString(options.end_date, 'yyyy-MM-dd')

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
                and self.dlg.relOrbit_radioButton.isChecked() == True):

            options.rel_orbit = self.dlg.orbit_lineEdit.text()
            options.abs_orbit = None

        elif (self.dlg.orbit_lineEdit.text() != ''
                and self.dlg.absOrbit_radioButton.isChecked() == True):

            options.rel_orbit = None
            options.abs_orbit = self.dlg.orbit_lineEdit.text()

        else:
            options.rel_orbit = None
            options.abs_orbit = None

        #
        # S1 product (e.g. GRD, SLC, OCN).
        #
        if (self.dlg.s1Product_comboBox.currentText() != ''
                and self.dlg.s1Product_comboBox.isEnabled() == True):

            options.s1product = self.dlg.s1Product_comboBox.currentText()

        else:
            options.s1product = None

        #
        # S1 polarisation (e.g. HH, VH, HV, VV, HH+HV, VV+VH).
        #
        if (self.dlg.s1Polar_comboBox.currentText() != ''
                and self.dlg.s1Polar_comboBox.isEnabled() == True):

            options.s1polar = self.dlg.s1Polar_comboBox.currentText()

        else:
            options.s1polar = None

        #
        # S1 operational mode (e.g. SM, IW, EW, WV).
        #
        if (self.dlg.s1Mode_comboBox.currentText() != ''
                and self.dlg.s1Mode_comboBox.isEnabled() == True):

            options.s1mode = self.dlg.s1Mode_comboBox.currentText()

        else:
            options.s1mode = None

        #
        # S2 product (e.g. S2MSI1C, S2MSI2Ap).
        #
        if (self.dlg.s2Product_comboBox.currentText() != ''
                and self.dlg.s2Product_comboBox.isEnabled() == True):

            options.s2product = self.dlg.s2Product_comboBox.currentText()

        else:
            options.s2product = None

        #
        # Maximum cloud cover percentage for S2 images.
        #
        if (self.dlg.cloudCover_enable.isChecked()
                and self.dlg.cloudCover_spinBox.isEnabled() == True):

            options.max_cloud = self.dlg.cloudCover_spinBox.cleanText()

        else:
            options.max_cloud = None

        return options


    def args_to_messagebox(self, options, query = None):

        options_dict = vars(options)
        options_string = ''

        for key,value in options_dict.iteritems():

            options_string += '{} : {}\n'.format(key,value)

        msg_args = QMessageBox()
        msg_args.setIcon(QMessageBox.Information)
        msg_args.setText(options_string)
        #msg_args.setInformativeText("This is additional information")
        #msg_args.setWindowTitle("MessageBox demo")

        if query is not None:

            msg_args.setDetailedText(query)

        msg_args.exec_()


    def text_to_messagebox(self, header, message, long_text=None):

        msg_txt = QMessageBox()
        msg_txt.setIcon(QMessageBox.Information)
        msg_txt.setText(message)
        #msg_txt.setInformativeText("This is additional information")
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


    def create_query(self, options, huburl, maxrecords):

        """Creates a query string for the data hub based on GUI input."""

        #
        # Add tile query check -- made redundant in get_arguments().
        #
        if (options.tile != None
                and (options.sentinel != 'S2'
                or options.sentinel != 'S2A'
                or options.sentinel != 'S2B')
                and self.dlg.s2Extract_checkBox.isChecked()==True):

            message = 'Tile extraction option can only be used for Sentinel-2!'
            self.text_to_messagebox('Error', message)

            return None

        #
        # Build in checks for valid commands related to the spatial aspect.
        #
        if options.lat is None or options.lon is None:

            if (options.latmin is None
                    or options.lonmin is None
                    or options.latmax is None
                    or options.lonmax is None):

                #message = 'Please provide at least one point or rectangle!'
                #self.text_to_messagebox('Error.', message)

                geom = None

                #return None

            else:
                geom = 'rectangle'

        else:

            if (options.latmin is None
                    and options.lonmin is None
                    and options.latmax is None
                    and options.lonmax is None):

                geom = 'point'

            else:
                #message = 'Choose either a point or rectangle, not both!'
                #self.text_to_messagebox('Error.', message)

                geom = None
                #return None

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

                query += ('(footprint:\\"Intersects(POLYGON(({lonmin} {latmin}, '
                    '{lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax}, '
                    '{lonmin} {latmin})))\\")').format(latmin = options.latmin,
                    latmax = options.latmax, lonmin = options.lonmin,
                    lonmax = options.lonmax)

            else:

                query += ('(footprint:"Intersects(POLYGON(({lonmin} {latmin}, '
                    '{lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax}, '
                    '{lonmin} {latmin})))")').format(latmin = options.latmin,
                    latmax = options.latmax, lonmin = options.lonmin,
                    lonmax = options.lonmax)
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

            query += (' AND (beginPosition:[{0}T00:00:00.000Z TO {1}T23:59:59.999Z] '
                'AND endPosition:[{0}T00:00:00.000Z TO {1}T23:59:59.999Z])').format(
                options.start_date, options.end_date)

        else:
            pass

        #
        # Add database ingestion date.
        #
        if options.start_ingest_date is not None or options.end_ingest_date is not None:

            query += (' AND (ingestionDate:[{}T00:00:00.000Z TO {}T23:59:59.999Z])'
                ).format(options.start_ingest_date, options.end_ingest_date)

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

        if options.max_cloud is not None:
            query += ' AND (cloudcoverpercentage:[0.0 TO {}])'.format(
                options.max_cloud)

        elif (options.max_cloud is not None
                and (options.sentinel != 'S2'
                or options.sentinel != 'S2A'
                or options.sentinel != 'S2B')):

            message = 'Cloud cover is only relevant for Sentinel-2 images.'
            self.text_to_messagebox('Error.', message)
            return None

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

            query = '{}search?q=({})&rows={}&{}'.format(huburl, query, maxrecords, orderby)

        else:

            query = '{}search?q=({})&rows={}'.format(huburl, query, maxrecords)

        #
        # Print arguments to message box for test.
        #
        #self.args_to_messagebox(options, query)
        #self.text_to_messagebox('Query', query)

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

        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            value ='\$value'

        else:
            value ='$value'

        return value


    def get_query_xml(self):

        try:
            options = self.get_arguments()

            if options.user is None or options.password is None:

                message = 'Please enter a username and password!'
                self.text_to_messagebox('Error', message)
                self.enable_btnSearch.emit()
                return

            #
            # Create authenticated http session.
            #
            session, huburl, account, passwd, maxrecords = self.start_session(options)

            value = self.set_value()

            query = self.create_query(options, huburl, maxrecords)

            if query is None:

                return None

            tW1 = self.dlg.s1Results_tableWidget
            tW2 = self.dlg.s2Results_tableWidget


            """TODO: add loop to accomodate larger queries of more than 100 records,
            where start is updated. Max rows are hardcoded or modified to smaller
            numbers already in create_query()."""


            #
            # Create GET request from hub and parse it.
            #
            try:
                response = session.get(query, stream=True)
                query_tree = etree.fromstring(response.content)

            except:

                message = ('Error with connection.\n'
                    'Please check credentials, try another hub or try again later.')

                self.text_to_messagebox('Error', message)
                self.enable_btnSearch.emit()
                #query_tree = etree.parse('C:\Users\GISmachine\Documents\GitHub\AIQ\query_results.xml')
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

                if self.killed == True:
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
                uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
                    'id')).text
                title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
                    'title')).text
                #
                # Check both tables for UUID and filename -- skip if already in either table.
                #
                tW1_UUIDs = []
                tW1_fns = []
                tW1Rows = tW1.rowCount()
                for row in xrange(0,tW1Rows):

                    #
                    # Try loop to avoid when UUID is None (Database issue)
                    #
                    try:
                        tw1_col11 = tW1.item(row,11).text()
                        tW1_UUIDs.append(tw1_col11)

                        tw1_col0 = tW1.item(row,0).text()
                        tW1_fns.append(tw1_col0)

                    except:
                        # This seems to happen, if UUID is None.
                        pass

                tW2_UUIDs = []
                tW2_fns = []
                tW2Rows = tW2.rowCount()
                for row in xrange(0,tW2Rows):

                    #
                    # Try loop to avoid when UUID is None (Database issue)
                    #
                    try:
                        tw2_col11 = tW2.item(row,11).text()
                        tW2_UUIDs.append(tw2_col11)

                        tw2_col0 = tW2.item(row,0).text()
                        tW2_fns.append(tw2_col0)

                    except:
                        # This seems to happen, if UUID is None.
                        pass

                if uuid_element in tW2_UUIDs or uuid_element in tW1_UUIDs:

                    continue

                elif title_element in tW2_fns or title_element in tW1_fns:

                    continue

                #
                # If UUID and titel not in one of the tables, add record to respective table.
                #
                else:

                    #
                    # The title element contains the corresponding file name.
                    #
                    title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
                        'title')).text
                    filename = (entries[entry].find('.//*[@name="filename"]')).text
                    size_element = (entries[entry].find('.//*[@name="size"]')).text
                    rel_orbit = int((entries[entry].find('.//*[@name="relativeorbitnumber"]')).text)
                    footprint = (entries[entry].find('.//*[@name="footprint"]')).text
                    sensing_date = ((entries[entry].find('.//*[@name="beginposition"]')).text)[:10]
                    sentinel_link = ("{}odata/v1/Products('{}')/{}").format(
                        huburl, uuid_element, value)

                    footprint = footprint.replace('POLYGON ((', "").replace('))', "").split(',')
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
                            s1Product = (entries[entry].find('.//*[@name="producttype"]')).text
                        except:
                            s1Product = '---'

                        try:
                            s1Polar = (entries[entry].find('.//*[@name="polarisationmode"]')).text
                        except:
                            s1Polar = '---'

                        try:
                            s1Mode = (entries[entry].find('.//*[@name="sensoroperationalmode"]')).text
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
                            cloud_element = (entries[entry].find('.//*[@name="cloudcoverpercentage"]')
                                ).text
                            cloud_element = float('{0:.1f}'.format(float(cloud_element)))
                        except:
                            cloud_element = '---'

                        #
                        # Return tile names per entry using function return_tiles if desired
                        #
                        if filename.startswith('S2A_OPER_'):

                            try:
                                found_tiles = self.return_tiles(session, uuid_element, filename, huburl)

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
                                granules = (entries[entry].find('.//*[@name="tileid"]')).text

                            except:

                                numGranules = 1
                                granules = filename[-26:-21]

                        else:

                            numGranules = '---'
                            granules = '---'

                        if (options.tile is not None
                                and granules != '?'
                                and options.tile not in granules):

                            continue

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
            #self.text_to_messagebox('Results.', 'Total size of results: {}'.format(total_size))
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
        for row in xrange(0,tW1Rows):
            size_element = tW1.item(row,6).text()
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
        for row in xrange(0,tW2Rows):
            size_element = tW2.item(row,6).text()
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
           including the entire file name of one desired tile, if specified. '''

        #
        # Create link to search for tile/granule data.
        #
        granule_link = ("{}odata/v1/Products"
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
        granule_entries = granule_tree.findall('{http://www.w3.org/2005/Atom}entry')

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
            # If one tile is given as an optional arg, return entire tile file name.
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
        q = QMessageBox.question(i, caption, message, QMessageBox.Yes, QMessageBox.No)

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


    def download_results(self):

        options = self.get_arguments()

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
        session, huburl, account, passwd, maxrecords = self.start_session(options)

        #
        # Platform dependent stuff.
        #
        value = self.set_value()

        #
        # Define data tables for S1 and S2 results.
        #
        tW1 = self.dlg.s1Results_tableWidget
        tW2 = self.dlg.s2Results_tableWidget

        #
        # Download Sentinel-1 results from S1 table.
        #
        tW1Rows = tW1.rowCount()
        for row in xrange(0,tW1Rows):
            sentinel_link = tW1.item(row,12).text()
            title_element = tW1.item(row,0).text()
            filename = '{}.SAFE'.format(title_element)
            zfile = '{}.zip'.format(title_element)

            #
            # Skip files that have already been downloaded.
            #
            check = self.download_check(options.write_dir, title_element, filename)

            if check is True:

                pass

            else:

                target_path = os.path.join(options.write_dir, zfile)
                chunk_size = 1024*1024*10
                #
                # Download file in chunks using requests module.
                #
                try:
                    response = session.get(sentinel_link, stream=True)
                    with open(target_path, "wb") as handle:
                        #
                        # Iterate over content in 10MB chunks.
                        #
                        for chunk in response.iter_content(chunk_size):
                            if not chunk:
                                break
                            handle.write(chunk)
                except:
                    pass

            #
            # Unzip even if path names are really long.
            #
            if os.path.exists(os.path.join(options.write_dir, zfile)):
                try:
                    with zipfile.ZipFile(os.path.join(options.write_dir, zfile)) as z:

                        z.extractall(u'\\\\?\\{}'.format(options.write_dir))
                        #print 'Unzipped Scene # {}'.format(str(entry + 1))

                except zipfile.BadZipfile:
                    #print 'Zipfile corrupt or hub might have a problem.'
                    continue

            elif os.path.exists(os.path.join(options.write_dir, title_element)):
                try:
                    with zipfile.ZipFile(os.path.join(options.write_dir, title_element)) as z:

                        z.extractall(u'\\\\?\\{}'.format(options.write_dir))
                        #print 'Unzipped Scene # {}'.format(str(entry + 1))

                except zipfile.BadZipfile:
                    #print 'Zipfile corrupt or hub might have a problem.'
                    continue

            #
            # If the unzipped and zipped version exist, delete the zipped version.
            #
            if (os.path.exists(os.path.join(options.write_dir, filename))
                    and os.path.exists(os.path.join(options.write_dir, zfile))):

                os.remove(os.path.join(options.write_dir, zfile))

        #
        # Download Sentinel-2 results.
        #
        tW2Rows = tW2.rowCount()
        #
        # If you did not search for a specific tile, downloading will begin.
        #
        if options.tile is None:

            for row in xrange(0,tW2Rows):

                #
                # Create download command for the entry.
                #
                sentinel_link = tW2.item(row,12).text()
                title_element = tW2.item(row,0).text()
                filename = '{}.SAFE'.format(title_element)
                zfile = '{}.zip'.format(title_element)

                #
                # Skip files that have already been downloaded.
                #
                check = self.download_check(options.write_dir, title_element, filename)

                if check is True:

                    pass

                else:

                    target_path = os.path.join(options.write_dir, zfile)
                    chunk_size = 1024*1024*10
                    #
                    # Download file in chunks using requests module.
                    #
                    try:
                        response = session.get(sentinel_link, stream=True)
                        with open(target_path, "wb") as handle:
                            #
                            # Iterate over content in 10MB chunks.
                            #
                            for chunk in response.iter_content(chunk_size):
                                if not chunk:
                                    break
                                handle.write(chunk)
                    except:
                        pass

                #
                # Unzip folder.zip even if path names are really long.
                #
                if os.path.exists(os.path.join(options.write_dir, zfile)):
                    try:
                        with zipfile.ZipFile(os.path.join(options.write_dir, zfile)) as z:

                            z.extractall(u'\\\\?\\{}'.format(options.write_dir))


                    except zipfile.BadZipfile:
                        #
                        # Zipfile corrupt or hub might have a problem.
                        #
                        continue
                #
                # Unzip folder without ''.zip' ending even if long path.
                #
                elif os.path.exists(os.path.join(options.write_dir, title_element)):
                    try:
                        with zipfile.ZipFile(os.path.join(options.write_dir, title_element)) as z:

                            z.extractall(u'\\\\?\\{}'.format(options.write_dir))

                    except zipfile.BadZipfile:

                        continue

                #
                # If the unzipped and zipped version exist, delete the zipped version.
                #
                if (os.path.exists(os.path.join(options.write_dir, filename))
                        and os.path.exists(os.path.join(options.write_dir, zfile))):

                    os.remove(os.path.join(options.write_dir, zfile))

                elif options.tile is not None:
                    #
                    # Add tile extraction code.
                    #
                    pass

        session.close()


    def download_check(self, write_dir, title_element, filename):

        ''' Function checks if files have aleady been downloaded. If yes, but
           unzipped, it unzips them and deletes the zipped folder.'''

        #
        # Possible zipped folder name.
        #
        zfile = '{}.zip'.format(title_element)

        #
        # Check if file was already downloaded.
        #
        if os.path.exists(os.path.join(write_dir, title_element)):
            #print '{} already exists in unzipped form!'.format(title_element)
            return True
        elif os.path.exists(os.path.join(write_dir, filename)):
            #print '{} already exists in unzipped form!'.format(filename)
            return True
        elif os.path.exists(os.path.join(write_dir, zfile)):
            #print '{} has already been downloaded!'.format(zfile)
            with zipfile.ZipFile(os.path.join(write_dir, zfile)) as z:
                z.extractall(u'\\\\?\\{}'.format(write_dir))
                #print '\tAnd is now unzipped.'
            os.remove(os.path.join(write_dir, zfile))
            return True
        else:
            return False


    def remove_selected(self):

		#
        # Ask for confirmation.
        #
        caption = 'Remove rows.'
        message = 'Are you sure you want to remove highlighted rows from the table?'
        i = QWidget()
        q = QMessageBox.question(i, caption, message, QMessageBox.Yes, QMessageBox.No)

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
        rows  = []
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
