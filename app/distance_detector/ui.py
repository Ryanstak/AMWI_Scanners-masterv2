import numpy as np
import pyqtgraph as pg
import math
import acconeer.exptool as et
import pyautogui
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets
class PGUpdater:
    def __init__(self, sensor_config, processing_config, session_info):
        self.sensor_config = sensor_config
        self.processing_config = processing_config
        self.r = et.a111.get_range_depths(sensor_config, session_info)
        self.setup_is_done = False
    def update_processing_config(self, processing_config=None):
        if processing_config is None:
            processing_config = self.processing_config
        else:
            self.processing_config = processing_config
        if not self.setup_is_done:
            return
        # Hide the first_distance_above_threshold data
        self.first_distance_above_threshold.setVisible(
            processing_config.show_first_above_threshold
        )
        # ...and hide the marker and text in the legend.
        #self.hist_plot.legend.items[2][0].setVisible(processing_config.show_first_above_threshold)
        #self.hist_plot.legend.items[2][1].setVisible(processing_config.show_first_above_threshold)
        self.hist_plot.setXRange(-processing_config.history_length_s, 0)
    def setup(self, win):
        #app = pg.mkQApp("Distance Detector")
        self.win = QtWidgets.QMainWindow()
        self.area = DockArea()
        self.win.setCentralWidget(self.area)
        self.win.setWindowTitle("Acconeer Distance Detector")
        self.win.resize(1610,1010)
        self.d1 = Dock('Options', size=(10,10))
        self.d2 = Dock('Sweep Plot', size=(800,500))
        self.d3 = Dock('History Plot', size=(800,500))

        self.area.addDock(self.d1, 'right')
        self.area.addDock(self.d2, 'right')
        self.area.addDock(self.d2, 'bottom')
        self.area.addDock(self.d3, 'bottom')

        self.w1 = pg.LayoutWidget()
        self.filelabel = QtWidgets.QLabel('File Name:')
        self.filename = QtWidgets.QLineEdit()
        self.filename = QtWidgets.QLineEdit('name.png')
        self.constantlabel = QtWidgets.QLabel('Dielectirc Constant')
        self.constantDrop = QtWidgets.QComboBox()
        self.saveBtn = QtWidgets.QPushButton('Save File')
        self.closeBtn = QtWidgets.QPushButton('Close')
        
        self.constantDrop.addItems(['HDPE (2.2)', 'GFRP (4.4)'])
        if self.constantDrop.currentIndex() == 0 :
            self.constant = math.sqrt(2.2)
        else :
            self.constant = math.sqrt(4.4)
        

        self.w1.addWidget(self.filelabel, row=0, col=0)
        self.w1.addWidget(self.filename, row=0, col=1)
        self.w1.addWidget(self.constantlabel, row=1, col=0)
        self.w1.addWidget(self.constantDrop, row=1, col=1)
        self.w1.addWidget(self.saveBtn, row=2, col=0)
        self.w1.addWidget(self.closeBtn, row=2, col=1)
        self.w1.addWidget(self.constantlabel, row=0, col=2)
        self.w1.addWidget(self.constantDrop, row=0, col=3)
        self.w1.addWidget(self.saveBtn, row=1, col=2)
        self.w1.addWidget(self.closeBtn, row=1, col=3)
        self.d1.addWidget(self.w1)
        state = None

        
        self.saveBtn.clicked.connect(self.screenshot)
        self.closeBtn.clicked.connect(self.close)
        # Sweep Plot
        self.sweep_plot = pg.PlotWidget(title="Sweep and threshold")
        #self.sweep_plot.setMenuEnabled(False)
        self.sweep_plot.setMouseEnabled(x=False, y=False)
        #self.sweep_plot.hideButtons()
        self.sweep_plot.showGrid(x=True, y=True)
        self.sweep_plot.addLegend()
        self.sweep_plot.setLabel("bottom", "Distance (mm)")
        self.sweep_plot.setYRange(0, 20000)
        self.sweep_plot.setXRange(1000.0 * self.r[0], 1000.0 * self.r[-1])
        self.sweep_curve = self.sweep_plot.plot(
            pen=et.utils.pg_pen_cycler(5),
            name="Envelope sweep",
        )
        self.mean_sweep_curve = self.sweep_plot.plot(
            pen=et.utils.pg_pen_cycler(0, width=3),
            name="Mean Envelope sweep",
        )
        self.threshold_curve = self.sweep_plot.plot(
            pen=et.utils.pg_pen_cycler(1),
            name="Threshold",
        )
        self.smooth_max_sweep = et.utils.SmoothMax(
            self.sensor_config.update_rate,
            hysteresis=0.6,
            tau_decay=3,
        )
        self.peak_lines = []
        for i in range(3):
            color_idx = 1 if i > 0 else 0
            width = 2 if i == 0 else 1
            color_tuple = et.utils.hex_to_rgb_tuple(et.utils.color_cycler(color_idx))
            line = pg.InfiniteLine(pen=pg.mkPen(pg.mkColor(*color_tuple, 150), width=width))
            self.sweep_plot.addItem(line)
            self.peak_lines.append(line)
        self.peak_text = pg.TextItem(
            anchor=(0, 1),
            color=et.utils.color_cycler(0),
            fill=pg.mkColor(0xFF, 0xFF, 0xFF, 150),
        )
        self.peak_text.setPos(self.r[0] * 1000, 0)
        self.peak_text.setZValue(100)
        self.sweep_plot.addItem(self.peak_text)
        #win.nextRow()
        # Detection history Plot
        self.hist_plot = pg.PlotWidget(title="Detected peaks")
        self.hist_plot.setMenuEnabled(False)
        self.hist_plot.setMouseEnabled(x=False, y=False)
        self.hist_plot.hideButtons()
        self.hist_plot.showGrid(x=True, y=True)
        self.hist_plot.addLegend()
        self.hist_plot.setLabel("bottom", "Time history (s)")
        self.hist_plot.setLabel("left", "Distance (mm)")
        self.hist_plot.setXRange(-10, 0)
        self.hist_plot.setYRange(1000.0 * self.r[0], 1000.0 * self.r[-1])
        self.main_peak = self.hist_plot.plot(
            pen=None,
            symbol="o",
            symbolSize=8,
            symbolPen="k",
            symbolBrush=et.utils.color_cycler(0),
            name="Main peak",
        )
        self.minor_peaks = self.hist_plot.plot(
            pen=None,
            symbol="o",
            symbolSize=5,
            symbolPen="k",
            symbolBrush=et.utils.color_cycler(1),
            name="Minor peaks",
        )
        self.first_distance_above_threshold = self.hist_plot.plot(
            pen=None,
            symbol="o",
            symbolSize=3,
            symbolPen="k",
            symbolBrush=et.utils.color_cycler(2),
            name="First distance above threshold",
            visible=False,
        )
        self.d2.addWidget(self.sweep_plot)
        self.d3.addWidget(self.hist_plot)
        self.win.show()
        self.setup_is_done = True
        self.update_processing_config()
    def screenshot(self):
        file_name = self.filename.text()
        im = pyautogui.screenshot(file_name, region=(0,0,1610,1010))
    
    def close(self):
        quit()
        
    def update(self, data):
        self.sweep_curve.setData(1000.0 * self.r, data["sweep"])
        self.mean_sweep_curve.setData(1000.0 * self.r, data["last_mean_sweep"])
        self.threshold_curve.setData(1000.0 * self.r, data["threshold"])
        m = np.nanmax(
            np.concatenate(
                [
                    2 * data["threshold"],
                    data["sweep"],
                    data["last_mean_sweep"],
                ]
            )
        )
        ymax = self.smooth_max_sweep.update(m)
        self.sweep_plot.setYRange(0, ymax)
        self.main_peak.setData(data["main_peak_hist_sweep_s"], 1000 * data["main_peak_hist_dist"])
        self.minor_peaks.setData(
            data["minor_peaks_hist_sweep_s"], 1000 * data["minor_peaks_hist_dist"]
        )
        self.first_distance_above_threshold.setData(
            data["above_thres_hist_sweep_s"], 1000 * data["above_thres_hist_dist"]
        )
        
        if data["found_peaks"] is not None:
            peaks = np.take(self.r, data["found_peaks"])* 1000.0
            for i, line in enumerate(self.peak_lines):
                try:
                    peak = peaks[i]
                except (TypeError, IndexError):
                    line.hide()
                else:
                    line.setPos(peak)
                    line.show()
            

            if len(peaks)>1:
                sorted_peaks = sorted(peaks)
                diconstant = self.constant
                difference_peaks1 = (sorted_peaks[1] - sorted_peaks[0])

                material_peaks1 = difference_peaks1 / diconstant
                text = f"Peak One: {sorted_peaks[0]:.2f} mm Peak Two: {sorted_peaks[1]:.2f} mm Uncorrected Depth: {difference_peaks1:.2f} mm Material Depth: {material_peaks1:.2f} "
                text = f"Peak One: {sorted_peaks[0]:.2f} mm Peak Two: {sorted_peaks[1]:.2f} mm Uncorrected Depth: {difference_peaks1:.2f} mm Material Depth: {material_peaks1:.2f} mm"
            elif len(peaks) == 1:
                text = f"{peaks[0]:.2f} mm"
            else:
                text = "-"

            self.peak_text.setText(text)
            
