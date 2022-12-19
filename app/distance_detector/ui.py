import numpy as np
from PySide6 import QtGui
import pyqtgraph as pg

import acconeer.exptool as et


class PGUpdater:
    def __init__(self, sensor_config, processing_config, session_info):
        self.sensor_config = sensor_config
        self.processing_config = processing_config
        self.depth_res = session_info["step_length_m"]

        self.r = et.a111.get_range_depths(sensor_config, session_info)

        self.setup_is_done = False

    def update_processing_config(self, processing_config=None):
        if processing_config is None:
            processing_config = self.processing_config
        else:
            self.processing_config = processing_config

        if not self.setup_is_done:
            return

        self.show_peaks = processing_config.show_peak_depths

    def setup(self, win):
        win.setWindowTitle("Acconeer Distance Detector")

        # Sweep Plot
        self.sweep_plot = win.addPlot(title="Sweep and threshold")
        self.sweep_plot.setMenuEnabled(False)
        self.sweep_plot.setMouseEnabled(x=False, y=False)
        self.sweep_plot.hideButtons()
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

        win.nextRow()


        rate = self.sensor_config.update_rate
        xlabel = "Sweeps" if rate is None else "Time (s)"
        x_scale = 1.0 if rate is None else 1.0 / rate
        y_scale = self.depth_res
        x_offset = -self.processing_config.history_length * x_scale
        y_offset = self.r[0] - 0.5 * self.depth_res
        is_single_sensor = len(self.sensor_config.sensor) == 1

        self.history_plots = []
        self.history_ims = []
        for i, sensor_id in enumerate(self.sensor_config.sensor):
            title = None if is_single_sensor else "Sensor {}".format(sensor_id)
            plot = win.addPlot(row=1, col=i, title=title)
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

        self.setup_is_done = True
        self.update_processing_config()

    def update(self, data):
        self.sweep_curve.setData(1000.0 * self.r, data["sweep"])
        self.mean_sweep_curve.setData(1000.0 * self.r, data["last_mean_sweep"])
        self.threshold_curve.setData(1000.0 * self.r, data["threshold"])
        histories = data["history"]
        sweeps = data["sweep"]

        for i, _ in enumerate(self.sensor_config.sensor):
            peak = data["sweep"][i]
            if peak is not None and self.show_peaks:
                self.peak_lines[i].setPos(peak)
                self.peak_lines[i].show()
            else:
                self.peak_lines[i].hide()


        im = self.history_ims[i]
        history = histories[:, i]
        im.updateImage(history, levels=(0, 1.05 * history.max()))

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
            peaks = np.take(self.r, data["found_peaks"]) * 1000.0
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
                text = f"{sorted_peaks[0]:.2f} cm {sorted_peaks[1]:.2f} cm"
            elif len(peaks) == 1:
                text = f"{peaks[0]:.2f} cm"
            else:
                text = "-"
            #if data["found_peaks"]:
            #    amplitude = data["sweep"][data["found_peaks"][0]]
            #    text = "{:.2f} mm, {:.1f}".format(peaks[0], amplitude)
            #else:
            #    text = "-"
 
            self.peak_text.setText(text)
