import PyIndi
import time
import sys
import threading
import matplotlib.pyplot as plt
from astropy.io import fits
import numpy as np
import io


class IndiClient(PyIndi.BaseClient):
    """General PyIndi Client without functionality.

       Implements all necessary virtual functions but does not contain any
       real functionality.
       Intended for being inherited and all necessary functions reimplemented.
    """

    def __init__(self):
        super(IndiClient, self).__init__()

    def newDevice(self, d):
        pass

    def newProperty(self, p):
        pass

    def removeProperty(self, p):
        pass

    def newBLOB(self, bp):
        pass

    def newSwitch(self, svp):
        pass

    def newNumber(self, nvp):
        pass

    def newText(self, tvp):
        pass

    def newLight(self, lvp):
        pass

    def newMessage(self, d, m):
        pass

    def serverConnected(self):
        pass

    def serverDisconnected(self, code):
        pass


class SxClient(IndiClient):

    def __init__(self):
        """Constructor."""
        super().__init__()

        # Device name, vectors and events
        self.ccd = "SX CCD LodeStar"
        self.device = None
        self.blob_event = threading.Event()
        self.exposure = None
        self.blob = None

        # For plotting
        self.fig = None
        self.ax = None

        # Connect to Server
        self.setServer("localhost", 7624)
        if self.check_server():
            self.connect_ccd()

        # Prepare Client for receiving blobs
        self.init_blob()

    def newBLOB(self, bp):
        """React to incoming BLOB."""
        print("new BLOB ", bp.name)
        self.blob_event.set()

    def check_server(self):
        """Check connection to Server."""
        if (not(self.connectServer())):
            print("No indiserver running on " + self.getHost() +
                  ":" + str(self.getPort()))
            return False
        else:
            return True

    def connect_ccd(self):
        """Connect Client to CCD."""
        # First get the CCD Device
        self.device = self.getDevice(self.ccd)
        while not(self.device):
            time.sleep(0.5)
            self.device = self.getDevice(self.ccd)
        # Connect to CCD
        # First get the "Connection"-Switch:
        # connection is now a vector pointing to that switch
        connection = self.device.getSwitch("CONNECTION")
        # Wait until connection is not None
        while not(connection):
            time.sleep(0.5)
            connection = self.device.getSwitch("CONNECTION")
        # If decive is not connected set the connection switch
        # and send to server
        if not(self.device.isConnected()):
            connection[0].s = PyIndi.ISS_ON  # the "CONNECT" switch
            connection[1].s = PyIndi.ISS_OFF  # the "DISCONNECT" switch
            self.sendNewSwitch(connection)

    def init_blob(self):
        """Initialize vectors and modes for receiving blobs."""
        self.exposure = self.device.getNumber("CCD_EXPOSURE")
        while not(self.exposure):
            time.sleep(0.5)
            self.exposure = self.device.getNumber("CCD_EXPOSURE")

        # we should inform the indi server that we want to receive the
        # "CCD1" blob from this device
        self.setBLOBMode(PyIndi.B_ALSO, self.ccd, "CCD1")

        self.blob = self.device.getBLOB("CCD1")
        while not(self.blob):
            time.sleep(0.5)
            self.blob = self.device.getBLOB("CCD1")

    def init_plot(self):
        """Initialize empty plot."""
        plt.ion()

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.fig.canvas.draw()

    def take_exposures(self,length_list, plot=True):
        """Take CCD exposure with defined lengths, save as FITS File and Plot.

           Input: list of exposure lengths as floats or integers.

           Output:
           """
        # Define exposure length (set vector[0])
        exp_number = 0
        self.exposure[0].value = length_list[exp_number]
        # Make exposure
        self.sendNewNumber(self.exposure)

        while (exp_number < len(length_list)):
            # Wait for BLOB to return
            if length_list[exp_number]*3 > 1:
                wait_for = length_list[exp_number]*3
            else: wait_for = 1
            if not self.blob_event.wait(wait_for):
                print('No BLOB Event')
                return False
            # we can start immediately the next one
            if (exp_number + 1 < len(length_list)):
                self.exposure[0].value = length_list[exp_number + 1]
                self.blob_event.clear()
                self.sendNewNumber(self.exposure)
            # and meanwhile process the received one
            for blob in self.blob:
                print("name: ", blob.name, " size: ",
                      blob.size, " format: ", blob.format)
                # pyindi-client adds a getblobdata() method to IBLOB item
                # for accessing the contents of the blob,
                # which is a bytearray in Python
                fits_blob = blob.getblobdata()
                print("fits data type: ", type(fits_blob))

                blobfile = io.BytesIO(fits_blob)
                # open a file and save buffer to disk
                image_file = 'images/IMAGE_py.fits'
                with open(image_file, "wb") as f:
                    f.write(blobfile.getvalue())

                if plot == False:
                    break

                if self.fig is None:
                    self.init_plot()
                # If figure already exists
                if self.fig:
                    hdu_list = fits.open(image_file)
                    image_data = hdu_list[0].data
                    image_data = image_data.astype(int)
                    hdu_list.close()

                    print('Median: ', np.median(image_data))

                    self.ax.clear()
                    ax2 = self.ax.imshow(image_data, cmap='gray',
                                         vmin=np.median(image_data) -
                                         3 * np.std(image_data),
                                         vmax=np.median(image_data) +
                                         3 * np.std(image_data))
                    self.fig.canvas.draw()

                exp_number += 1

    def stream_video(self, length):
        """Streams SX Camera's current footage."""
        # Shows 100000 images with chosen length
        # Change that at later stage
        length_list = np.ones(100000) * length
        return (self.take_exposures(length_list))


# connect the server
sx_client = SxClient()

exposure_list = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
while not sx_client.stream_video(1):
    continue
