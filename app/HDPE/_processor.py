from enum import Enum

##From DD

from copy import copy
from typing import Optional

import numpy as np

import acconeer.exptool as et

from .calibration import EnvelopeCalibration
from .calibration2 import DistanceDetectorCalibration

PEAK_MERGE_LIMIT_M = 0.005

def get_sensor_config():
    config = et.a111.EnvelopeServiceConfig()
    config.range_interval = [0.02, 0.5]
    config.profile = config.Profile.PROFILE_1
    config.hw_accelerated_average_samples = 15
    config.update_rate = 30
    config.gain = 0.7
    return config

class ProcessingConfiguration(et.configbase.ProcessingConfig):
    VERSION = 1

    class BackgroundMode(Enum):
        SUBTRACT = "Subtract"
        LIMIT = "Limit"

    show_peak_depths = et.configbase.BoolParameter(
        label="Show peak distances",
        default_value=True,
        updateable=True,
        order=-10,
    )

    bg_buffer_length = et.configbase.IntParameter(
        default_value=50,
        limits=(1, 200),
        label="Background buffer length",
        order=0,
    )

    bg_mode = et.configbase.EnumParameter(
        label="Background mode",
        default_value=BackgroundMode.SUBTRACT,
        enum=BackgroundMode,
        updateable=True,
        order=20,
    )

    history_length = et.configbase.IntParameter(
        default_value=100,
        limits=(10, 1000),
        label="History length",
        order=30,
    )




class Processor:
    def __init__(self, sensor_config, processing_config, session_info, calibration=None):
        self.processing_config = processing_config

        self.session_info = session_info
        self.num_depths = self.session_info["data_length"]
        self.last_mean_sweep = np.full(self.num_depths, np.nan)
        self.depths = et.a111.get_range_depths(sensor_config, session_info)
        num_depths = self.depths.size
        num_sensors = len(sensor_config.sensor)
        self.dr = self.depths[1] - self.depths[0]
        buffer_length = self.processing_config.bg_buffer_length
        self.bg_buffer = np.zeros([buffer_length, num_sensors, num_depths])

        history_length = self.processing_config.history_length
        self.history = np.zeros([history_length, num_sensors, num_depths])

        self.data_index = 0
        self.calibration = calibration




    def process(self, data, data_info):
        new_calibration = None
        bg = None
        output_data = data

        if self.calibration is None:
            if self.data_index < self.bg_buffer.shape[0]:
                self.bg_buffer[self.data_index] = data
            if self.data_index == self.bg_buffer.shape[0] - 1:
                new_calibration = EnvelopeCalibration(self.bg_buffer.mean(axis=0))
        else:
            if self.processing_config.bg_mode == ProcessingConfiguration.BackgroundMode.SUBTRACT:
                output_data = np.maximum(0, data - self.calibration.background)
            else:
                output_data = np.maximum(data, self.calibration.background)

            bg = self.calibration.background


        peak_ampls = [np.max(sweep) for sweep in output_data]
        peak_ampls2 = [np.max(sweep) for sweep in output_data]
        peak_depths = [self.depths[np.argmax(sweep)] for sweep in output_data]
        peak_depths2 = [self.depths[np.argmax(sweep)] for sweep in output_data]
        filtered_peak_depths = [d if a > 200 else None for d, a in zip(peak_depths, peak_ampls)]
        filtered_peak_depths2 = [d if a > 200 else None for d, a in zip(peak_depths2, peak_ampls2)]
        output = {
            "output_data": output_data,
            "bg": bg,
            "history": self.history,
            "peak_depths1": filtered_peak_depths,
            "peak_depths2": filtered_peak_depths2,
        }
        if new_calibration is not None:
            output["new_calibration"] = new_calibration

        self.data_index += 1

        return output



    def update_calibration(self, new_calibration: EnvelopeCalibration):
        self.calibration = new_calibration
        self.data_index = 0
