import matplotlib.pyplot as plt
import h5py
import pandas as pd
import json
import numpy as np
import acconeer.exptool as et
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

filename = ('C:/Users/Ryan.Stakenborghs/AMWi_Scanners-master/working/h5_graph/test.h5')

with h5py.File((filename), 'r') as f:
    print(json.loads(f["session_info"][()]))
    sweeps = f['data']
    time = f['sample_times']
    config = f['sensor_config_dump']
                    
    record = et.a111.recording.load(filename)
    depths = et.a111.get_range_depths(record.sensor_config, record.session_info)
    min_sweep = np.min(sweeps)
    max_sweep = np.max(sweeps)
    data_length = record.session_info['data_length']
    ind_sweep = sweeps[0:]
    
    print(depths)
    print(data_length)
    print(min_sweep)
    print(max_sweep)
    print(sweeps[0])
    print(ind_sweep)