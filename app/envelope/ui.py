from PySide6 import QtGui

import pyqtgraph as pg

import acconeer.exptool as et

from ._processor import ProcessingConfiguration

import numpy as np
import math
import pyautogui
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets

class PGUpdater:
    def __init__(self, sensor_config, processing_config, session_info):
        self.sensor_config = sensor_config
        self.processing_config = processing_config

        self.depths = et.a111.get_range_depths(sensor_config, session_info)
        self.depth_res = session_info["step_length_m"]
        self.smooth_max = et.utils.SmoothMax(sensor_config.update_rate)
        self.r = et.a111.get_range_depths(sensor_config, session_info)
        
        self.setup_is_done = False

    def setup(self, win):
        self.win = QtWidgets.QMainWindow()
        self.area = DockArea()
        self.win.setCentralWidget(self.area)
        self.win.setWindowTitle("Acconeer Distance Detector")
        self.win.resize(1610,1010)

        self.d1 = Dock('Options', size=(10,10))
        self.d2 = Dock('Amplitude Plot', size=(800,500))
        self.d3 = Dock('History Plot', size=(800,500))
        self.d4 = Dock('Sensor Results', size=(10,10))
        
        self.area.addDock(self.d1, 'left')
        self.area.addDock(self.d2, 'bottom')
        self.area.addDock(self.d4, 'bottom')
        self.area.addDock(self.d3, 'bottom')
        
        self.w1 = pg.LayoutWidget()
        self.filelabel = QtWidgets.QLabel('File Name:')
        self.filename = QtWidgets.QLineEdit('name.png')
        self.constantlabel = QtWidgets.QLabel('Dielectirc Constant')
        self.constantDrop = QtWidgets.QComboBox()
        self.saveBtn = QtWidgets.QPushButton('Save File')
        self.closeBtn = QtWidgets.QPushButton('Close')
        
        self.constantDrop.addItems(['None', 'HDPE (2.2)', 'GFRP (4.4)'])
        if self.constantDrop.currentIndex() == 0:
            self.constant_variable = 1
        elif self.constantDrop.currentIndex() == 1:
            self.constant_variable = math.sqrt(4.4)
        elif self.constantDrop.currentIndex() == 2:
            self.constant_variable = math.sqrt(2.2)
        
        
        self.w1.addWidget(self.filelabel, row=0, col=0)
        self.w1.addWidget(self.filename, row=0, col=1)
        self.w1.addWidget(self.constantlabel, row=1, col=0)
        self.w1.addWidget(self.constantDrop, row=1, col=1)
        self.w1.addWidget(self.saveBtn, row=2, col=0)
        self.w1.addWidget(self.closeBtn, row=2, col=1)
        self.d1.addWidget(self.w1)
        #state = None

        
        self.saveBtn.clicked.connect(self.screenshot)
        self.closeBtn.clicked.connect(self.close)
        
        num_sensors = len(self.sensor_config.sensor)

        self.ampl_plot = pg.PlotWidget(title="Amplitude", row=0, colspan=num_sensors)
        self.ampl_plot.setMenuEnabled(False)
        self.ampl_plot.setMouseEnabled(x=False, y=False)
        self.ampl_plot.hideButtons()
        self.ampl_plot.showGrid(x=True, y=True)
        self.ampl_plot.setLabel("bottom", "Depth (m)")
        self.ampl_plot.setLabel("left", "Amplitude")
        self.ampl_plot.setXRange(*self.depths.take((0, -1)))
        self.ampl_plot.setYRange(0, 1)  # To avoid rendering bug
        self.ampl_plot.addLegend(offset=(-10, 10))

        self.ampl_curves = []
        self.bg_curves = []
        self.peak_lines = []
        for i, sensor_id in enumerate(self.sensor_config.sensor):
            legend = "Sensor {}".format(sensor_id)
            ampl_curve = self.ampl_plot.plot(pen=et.utils.pg_pen_cycler(i), name=legend)
            bg_curve = self.ampl_plot.plot(pen=et.utils.pg_pen_cycler(i, style="--"))
            color_tuple = et.utils.hex_to_rgb_tuple(et.utils.color_cycler(i))
            peak_line = pg.InfiniteLine(pen=pg.mkPen(pg.mkColor(*color_tuple, 150), width=2))
            self.ampl_plot.addItem(peak_line)
            self.ampl_curves.append(ampl_curve)
            self.bg_curves.append(bg_curve)
            self.peak_lines.append(peak_line)



        self.peak_lines = []
        for i in range(3):
            color_idx = 1 if i > 0 else 0
            width = 2 if i == 0 else 1
            color_tuple = et.utils.hex_to_rgb_tuple(et.utils.color_cycler(color_idx))
            line = pg.InfiniteLine(pen=pg.mkPen(pg.mkColor(*color_tuple, 150), width=width))
            self.ampl_plot.addItem(line)
            self.peak_lines.append(line)

        self.peak_text = pg.TextItem(
            anchor=(0, 1),
            color=et.utils.color_cycler(0),
            fill=pg.mkColor(0xFF, 0xFF, 0xFF, 150),
        )
        self.peak_text.setPos(self.r[0] * 1000, 0)
        self.peak_text.setZValue(100)
        self.ampl_plot.addItem(self.peak_text)


        bg = pg.mkColor(0xFF, 0xFF, 0xFF, 150)
        self.peak_text = pg.TextItem(anchor=(0, 1), color="k", fill=bg)
        self.peak_text.setPos(self.depths[0], 0)
        self.peak_text.setZValue(100)
        self.ampl_plot.addItem(self.peak_text)

        rate = self.sensor_config.update_rate
        xlabel = "Sweeps" if rate is None else "Time (s)"
        x_scale = 1.0 if rate is None else 1.0 / rate
        y_scale = self.depth_res
        x_offset = -self.processing_config.history_length * x_scale
        y_offset = self.depths[0] - 0.5 * self.depth_res
        is_single_sensor = len(self.sensor_config.sensor) == 1

        self.history_plots = []
        self.history_ims = []
        for i, sensor_id in enumerate(self.sensor_config.sensor):
            title = None if is_single_sensor else "Sensor {}".format(sensor_id)
            plot = pg.PlotWidget(title="Histpory Plot", row=1, col=i)
            plot.setMenuEnabled(False)
            plot.setMouseEnabled(x=False, y=False)
            plot.hideButtons()
            plot.setLabel("bottom", xlabel)
            plot.setLabel("left", "Depth (m)")
            im = pg.ImageItem(autoDownsample=True)
            im.setLookupTable(et.utils.pg_mpl_cmap("viridis"))
            im.resetTransform()
            tr = QtGui.QTransform()
            tr.translate(x_offset, y_offset)
            tr.scale(x_scale, y_scale)
            im.setTransform(tr)
            plot.addItem(im)
            self.history_plots.append(plot)
            self.history_ims.append(im)

            self.d2.addWidget(self.ampl_plot)
            self.d3.addWidget(plot)

        self.setup_is_done = True
        self.update_processing_config()

        self.win.show()

    def screenshot(self):
        file_name = self.filename.text()
        im = pyautogui.screenshot(file_name, region=(0,0,1610,1010))
    
    def close(self):
        quit()
    


    def update_processing_config(self, processing_config=None):
        if processing_config is None:
            processing_config = self.processing_config
        else:
            self.processing_config = processing_config

        if not self.setup_is_done:
            return

        self.show_peaks = processing_config.show_peak_depths
        self.peak_text.setVisible(self.show_peaks)

        show_bg = processing_config.bg_mode == ProcessingConfiguration.BackgroundMode.LIMIT

        for curve in self.bg_curves:
            curve.setVisible(show_bg)

    def update(self, data):
        sweeps = data["output_data"]
        bgs = data["bg"]
        histories = data["history"]
        

        for i, _ in enumerate(self.sensor_config.sensor):
            self.ampl_curves[i].setData(self.depths, sweeps[i])

            if bgs is None:
                self.bg_curves[i].clear()
            else:
                self.bg_curves[i].setData(self.depths, bgs[i])

            peak = data["peak_depths"][i]
            if peak is not None and self.show_peaks:
                self.peak_lines[i].setPos(peak)
                self.peak_lines[i].show()
            else:
                self.peak_lines[i].hide()

            im = self.history_ims[i]
            history = histories[:, i]
            im.updateImage(history, levels=(0, 1.05 * history.max()))

        m = self.smooth_max.update(sweeps.max())
        self.ampl_plot.setYRange(0, m)

        # Update peak text item
        val_strs = ["-" if p is None else "{:5.3f} m".format(p) for p in data["peak_depths"]]
        z = zip(self.sensor_config.sensor, val_strs)
        t = "\n".join(["Sensor {}: {}".format(sid, v) for sid, v in z])
        self.peak_text.setText(t)
