
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
#from PIL.ImageQt import ImageQt
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import sys
import pyqtgraph as pg
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import sys
from PIL import Image
import time

import sys
import time

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineQuick import QtWebEngineQuick
import numpy as np
import serial.tools.list_ports
from packaging import version
import subprocess
import sys
import pyautogui
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QLineEdit,
    QMainWindow, QPushButton, QToolBar)
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from acconeer.exptool import utils
#from acconeer.exptool.a111 import _clients
from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal
)
import sys
import PySide6.QtWebEngineWidgets
from PySide6 import QtCore
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (QApplication, QDockWidget, QLabel,
                               QLineEdit, QMainWindow, QToolBar)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QPlainTextEdit,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QApplication,
    QComboBox,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
    QWidget,
    QApplication,
    QFormLayout,
    QMainWindow,
    QApplication,
    QPushButton,
    QMenu,
)
from subprocess import check_output

import acconeer.exptool as et
from PySide6 import QtCore, QtGui, QtWidgets

HERE = os.path.dirname(os.path.realpath(__file__))

class RadarActivation(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def radar_start(self):
        ssh = subprocess.Popen('plink -ssh pi@192.168.1.131 -pw raspberry', #need to figure out how ot pass the ip address variable to here
                shell=False,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE)

        ssh.communicate("./rpi_xc112/out/acc_exploration_server_a111\n")

        self.finished.emit()
    

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.clicksCount = 0
        self.setupUI()
     
 
        
    def setupUI(self):
        self.setWindowTitle("AMWI Scanner")
        logo_image = os.path.join(HERE, "logo.png")
        pagelayout = QHBoxLayout()
        optionslayout = QFormLayout()
        self.stackedlayout = QStackedLayout()
        
        pagelayout.addLayout(self.stackedlayout)
        pagelayout.addLayout(optionslayout)

        self.logo = QPixmap(logo_image)
        self.label = QLabel()
        self.label.setPixmap(self.logo)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
    
        
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")
        pg.setConfigOptions(antialias=True)
        win = pg.GraphicsLayoutWidget()
        env_plot = win.addPlot(title="Envelope")
        env_plot.showGrid(x=True, y=True)
        env_plot.setLabel("bottom", "Depth (m)")
        env_plot.setLabel("left", "Amplitude")


        win.nextRow()
        hist_plot = win.addPlot()
        hist_plot.setLabel("bottom", "Time (s)")
        hist_plot.setLabel("left", "Depth (m)")


        #hist_image_item.setLookupTable(et.utils.pg_mpl_cmap("viridis"))
            
        self.stackedlayout.addWidget(self.label)
        self.stackedlayout.addWidget(win)
        
        self.btn_1 = QtWidgets.QPushButton("Start Radar")
        self.btn_2 = QtWidgets.QPushButton("Start Scanner")
        self.btn_3 = QtWidgets.QPushButton("Load Scan")
        
        self.IP = QLineEdit()
        self.DataName = QLineEdit()
        #optionsLayout.addRow('Scanner IP Address', self.IP)
        #optionsLayout.addRow('Scan File Name', self.DataName)
        optionslayout.addWidget(self.btn_1)
        optionslayout.addWidget(self.btn_2)
        optionslayout.addWidget(self.btn_3)

        self.btn_1.clicked.connect(self.runRadarActivation)
        self.btn_2.clicked.connect(self.scanner)
        self.btn_3.clicked.connect(self.activate_load)
        self.btn_1.clicked.connect(self.layoutchange)

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)
    

    def layoutchange(self):
        self.stackedlayout.setCurrentIndex(0) 
        
    def runRadarActivation(self):
        self.thread = QThread()
        self.worker = RadarActivation()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.radar_start)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.deleteLater)
        
        self.thread.start()
    
        self.btn_1.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.btn_1.setEnabled(True)
        )

    def activate_load(self, s):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load scan",
            "",
            "PNG (*.png)",
            options=options,
        )
        
        image = Image.open(filename)
        image.show()
        
    def scanner(self):
        ipValue = self.IP.text()
        check_output(f"python -m distance_detector -s 192.168.1.131")
    #THis should be embedded in the main ui. change the layout from the logo to this
        
          
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())