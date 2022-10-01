import argparse
import csv
import json
import os

import numpy as np

import acconeer.exptool as et

import sys
import os
import csv
import json

import h5py
import numpy as np
import pandas as pd

from pandas import HDFStore
from random import choice
from collections import namedtuple

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QSize, Qt, QFileInfo
from PySide6.QtGui import QPixmap, QAction, QPalette, QColor, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QToolBar,
    QStatusBar,
    QPushButton,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QStackedLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QMenu,
    QApplication
)
import numpy
import numpy as np
#from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
plt.style.use('seaborn-poster')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()      
        self.setWindowTitle("H5 to CSV")

        pagelayout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self.stacklayout = QStackedLayout()

        pagelayout.addLayout(button_layout)
        pagelayout.addLayout(self.stacklayout)
        
        btn = QPushButton("Load .H5 File")
        btn.clicked.connect(self.activate_load)
        button_layout.addWidget(btn)

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)

    
    def activate_load(self, s):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load scan",
            "",
            "HDF5 data files (*.h5);; NumPy data files (*.npz)",
            options=options,
        )
        print(filename)
     
        with h5py.File((filename), 'r') as f:
            print(json.loads(f["session_info"][()]))
            record = et.a111.recording.load(filename)
            depths = et.a111.get_range_depths(record.sensor_config, record.session_info)
            print(depths)

        #f = h5py.File((filename), 'r')
            list(f.keys())
            print(f.keys())
            sweeps = f['data']
            time = f['sample_times']
            #config = f['sensor_config_dump']
        #print(config.attrs('range_interval'))
            #print(config[()])
    


            print(sweeps.shape)        
            print(time.shape)
            print(type(sweeps))
            print(sweeps.fields)

            sweeps_arr = np.zeros(sweeps.shape)
            sweeps.read_direct(sweeps_arr)
        
            print(sweeps_arr)


            time_arr = np.zeros(time.shape)
            time.read_direct(time_arr)
        
        #print(sweeps_arr)

        #print(config_arr)

            print(sweeps_arr[0])
            print(time[()])


#Show Graph
        fig = plt.figure(figsize = (50,300))
        ax = plt.axes(projection='3d')

        z = depths
        x = sweeps_arr
        y = time_arr
        #z = sweeps_arr

        X, Y, Z = np.meshgrid(x, y, z)
        #Z = np.sin(X)*np.cos(Y)
        

        surf = ax.plot_trisurf(X, Y, Z, cmap = plt.cm.cividis)

# Set axes label
        ax.set_xlabel('x', labelpad=20)
        ax.set_ylabel('y', labelpad=20)
        ax.set_zlabel('z', labelpad=20)

        fig.colorbar(surf, shrink=0.5, aspect=30)

        plt.show()

        #for a in sweeps:
            #print(a)
        #for b in time:
            #print(b)
        

            
        
    
   

        

app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
