
import sys
import os
import subprocess

from PIL import Image
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from subprocess import check_output
from PySide6 import QtCore, QtWidgets
from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal
)

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
    
        self.stackedlayout.addWidget(self.label)
        
        self.btn_1 = QtWidgets.QPushButton("Start Radar")
        self.btn_2 = QtWidgets.QPushButton("Start Scanner")
        self.btn_3 = QtWidgets.QPushButton("Load Scan")
        self.btn_4 = QtWidgets.QPushButton("Close")
        
        self.IP = QLineEdit()
        self.DataName = QLineEdit()
        #optionsLayout.addRow('Scanner IP Address', self.IP)
        #optionsLayout.addRow('Scan File Name', self.DataName)
        optionslayout.addWidget(self.btn_1)
        optionslayout.addWidget(self.btn_2)
        optionslayout.addWidget(self.btn_3)
        optionslayout.addWidget(self.btn_4)

        self.btn_1.clicked.connect(self.runRadarActivation)
        self.btn_2.clicked.connect(self.scanner)
        self.btn_3.clicked.connect(self.activate_load)
        self.btn_1.clicked.connect(self.layoutchange)
        self.btn_4.clicked.connect(self.close)

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