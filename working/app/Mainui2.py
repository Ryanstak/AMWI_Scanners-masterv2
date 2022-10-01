import ipaddress
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
import acconeer.exptool as et
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
    

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.clicksCount = 0
        self.setupUI()
     
 
        
    def setupUI(self):
        self.setWindowTitle("AMWI Scanner")
        
        pagelayout = QHBoxLayout()
        optionslayout = QFormLayout()
        self.stackedlayout = QStackedLayout()
        
        pagelayout.addLayout(self.stackedlayout)
        pagelayout.addLayout(optionslayout)

        self.logo = QPixmap("C:/users/Ryan.Stakenborghs/AMWI_Scanners-master/working/app/logo.png")
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
        self.btn_3 = QtWidgets.QPushButton("Save")
        
        self.IP = QLineEdit()
        self.DataName = QLineEdit()
        #optionsLayout.addRow('Scanner IP Address', self.IP)
        #optionsLayout.addRow('Scan File Name', self.DataName)
        optionslayout.addWidget(self.btn_1)
        optionslayout.addWidget(self.btn_2)
        optionslayout.addWidget(self.btn_3)

        self.btn_1.clicked.connect(self.runRadarActivation)
        self.btn_2.clicked.connect(self.scanner_start)
        self.btn_3.clicked.connect(self.screenshot)
        self.btn_1.clicked.connect(self.layoutchange)

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)
    

    def layoutchange(self):
        self.stackedlayout.setCurrentIndex(1) 
        
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
    def scanner_start(self):
        args = et.a111.ExampleArgumentParser(num_sens=1).parse_args()
        et.utils.config_logging(args)

        client = et.a111.Client(**et.a111.get_client_args(args))
        config = et.a111.EnvelopeServiceConfig()
        config.sensor = args.sensors
        config.update_rate = 30

        session_info = client.setup_session(config)

        start = session_info["range_start_m"]
        length = session_info["range_length_m"]
        num_depths = session_info["data_length"]
        step_length = session_info["step_length_m"]
        depths = np.linspace(start, start + length, num_depths)
        num_hist = 2 * int(round(config.update_rate))
        hist_data = np.zeros([num_hist, depths.size])
        smooth_max = et.utils.SmoothMax(config.update_rate)

        app = QtWidgets.QApplication([])
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")
        pg.setConfigOptions(antialias=True)
        win = pg.GraphicsLayoutWidget()
        win.setWindowTitle("Acconeer PyQtGraph example")

        env_plot = win.addPlot(title="Envelope")
        env_plot.showGrid(x=True, y=True)
        env_plot.setLabel("bottom", "Depth (m)")
        env_plot.setLabel("left", "Amplitude")
        env_curve = env_plot.plot(pen=pg.mkPen("k", width=2))

        win.nextRow()
        hist_plot = win.addPlot()
        hist_plot.setLabel("bottom", "Time (s)")
        hist_plot.setLabel("left", "Depth (m)")
        hist_image_item = pg.ImageItem()
        tr = QtGui.QTransform()
        tr.translate(-2, start)
        tr.scale(2 / num_hist, step_length)
        hist_image_item.setTransform(tr)
        hist_plot.addItem(hist_image_item)

        # Get a nice colormap from matplotlib
        hist_image_item.setLookupTable(et.utils.pg_mpl_cmap("viridis"))

        win.show()

        interrupt_handler = et.utils.ExampleInterruptHandler()
        win.closeEvent = lambda _: interrupt_handler.force_signal_interrupt()
        print("Press Ctrl-C to end session")

        client.start_session()

        while not interrupt_handler.got_signal:
            info, data = client.get_next()

            hist_data = np.roll(hist_data, -1, axis=0)
            hist_data[-1] = data

            env_curve.setData(depths, data)
            env_plot.setYRange(0, smooth_max.update(data))
            hist_image_item.updateImage(hist_data, levels=(0, np.max(hist_data) * 1.05))

            app.processEvents()

        print("Disconnecting...")
        
        

        filename = "data.h5"
        if os.path.exists(filename):
            print("File '{}' already exists, won't overwrite".format(filename))
            sys.exit(1)    
            
        recorder = et.a111.recording.Recorder(sensor_config=config, session_info=session_info)
        record = recorder.close()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        et.a111.recording.save(filename, record)
        print("Saved to '{}'".format(filename))
        
        app.closeAllWindows()
        client.disconnect()

    
    def scanner(self):
        ipValue = self.IP.text()
        check_output(f"python -m envelope -s 192.168.1.131")
        # check_output(f"python -m barebones -s {ipValue}")
    #THis should be embedded in the main ui. change the layout from the logo to this
        
    def screenshot(self):
        im = pyautogui.screenshot('screenshot.png', region=(500,300, 300, 400))
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())