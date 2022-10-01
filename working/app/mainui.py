import ipaddress
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
#from PIL.ImageQt import ImageQt
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import sys
import os
import time
#from server import http_server
import multiprocessing
import sys
import threading
import time
import traceback
import PySide6.QtWebEngineCore
import logging
import operator
import signal
import struct
import sys
import time
from datetime import datetime
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
from plot_with_pyqtgraph import main
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

#from radar_activate import radar_start

from PySide6 import QtCore, QtGui, QtWidgets

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
    

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.clicksCount = 0
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle("AMWI Scanner")
        outerLayout = QHBoxLayout()
        topLayout = QFormLayout()
        
        self.logo = QPixmap("C:/users/Ryan.Stakenborghs/AMWI_Scanners-master/working/app/logo.png")
        self.label = QLabel()
        self.label.setPixmap(self.logo)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.btn_1 = QtWidgets.QPushButton("Start Radar")
        self.btn_2 = QtWidgets.QPushButton("Start Scanner")
        self.btn_3 = QtWidgets.QPushButton("Save")
        
        topLayout.addWidget(self.label)
        
        optionsLayout = QFormLayout()
        
        
        self.IP = QLineEdit()
        self.DataName = QLineEdit()
        #optionsLayout.addRow('Scanner IP Address', self.IP)
        #optionsLayout.addRow('Scan File Name', self.DataName)
        optionsLayout.addWidget(self.btn_1)
        optionsLayout.addWidget(self.btn_2)
        optionsLayout.addWidget(self.btn_3)

        self.btn_1.clicked.connect(self.runRadarActivation)
        self.btn_2.clicked.connect(self.scanner)
        self.btn_3.clicked.connect(self.screenshot)
        
        outerLayout.addLayout(topLayout)
        outerLayout.addLayout(optionsLayout)
        
        self.setLayout(outerLayout)
        

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
    
    
    def scanner(self):
        ipValue = self.IP.text()
        check_output(f"python -m plot_with_pyqtgraph -s 192.168.1.131")
        # check_output(f"python -m barebones -s {ipValue}")
    #THis should be embedded in the main ui. change the layout from the logo to this
        
    def screenshot(self):
        im = pyautogui.screenshot('screenshot.png', region=(500,300, 300, 400))
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())