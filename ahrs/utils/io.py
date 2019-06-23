#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Input and Output routines

"""

import os
import sys
import scipy.io as sio
import numpy as np

def find_index(header, s):
    for h in header:
        if s in h.lower():
            return header.index(h)
    return None

def load(file_name):
    """
    Load the contents of a file into a dictionary.

    Supported formats, so far, are MAT and CSV files. More to come.

    To Do:
    - Get a better way to find data from keys of dictionary. PLEASE.

    Parameters
    ----------
    file_name : string
        Name of the file
    """
    if not os.path.isfile(file_name):
        sys.exit("[ERROR] The file {} does not exist.".format(file_name))
    file_ext = file_name.strip().split('.')[-1]
    if file_ext == 'mat':
        d = sio.loadmat(file_name)
        d.update({'rads':False})
        return Data(d)
    if file_ext == 'csv':
        with open(file_name, 'r') as f:
            all_lines = f.readlines()
        split_header = all_lines[0].strip().split(';')
        a_idx = find_index(split_header, 'acc')
        g_idx = find_index(split_header, 'gyr')
        m_idx = find_index(split_header, 'mag')
        q_idx = find_index(split_header, 'orient')
        data = np.genfromtxt(all_lines[2:], delimiter=';')
        d = {'time' : data[:, 0],
        'acc' : data[:, a_idx:a_idx+3],
        'gyr' : data[:, g_idx:g_idx+3],
        'mag' : data[:, m_idx:m_idx+3],
        'qts' : data[:, q_idx:q_idx+4]}
        d.update({'rads':True})
        return Data(d)
    return None

def loadETH(path):
    """
    Loads data from a directory containing files of the Event-Camera Dataset
    from the ETH Zurich (http://rpg.ifi.uzh.ch/davis_data.html)

    The dataset includes 4 basic text files with recorded data, plus a file
    listing all images of the recording included in the subfolder 'images.'

    **events.txt**: One event per line (timestamp x y polarity)
    **images.txt**: One image reference per line (timestamp filename)
    **imu.txt**: One measurement per line (timestamp ax ay az gx gy gz)
    **groundtruth.txt**: One ground truth measurements per line (timestamp px py pz qx qy qz qw)
    **calib.txt**: Camera parameters (fx fy cx cy k1 k2 p1 p2 k3)

    Parameters
    ----------
    path : str
        Path of the folder containing the TXT files.

    Returns
    -------
    data : Data
        class Data with the contents of the dataset.

    """
    if os.path.isdir(path):
        data = {}
        files = []
        [files.append(f) for f in os.listdir(path) if f.endswith('.txt')]
        missing = list(set(files).symmetric_difference([
            'events.txt',
            'images.txt',
            'imu.txt',
            'groundtruth.txt',
            'calib.txt']))
        if missing:
            sys.exit("Incomplete data. Missing files:\n{}".format('\n'.join(missing)))
        imu_data = np.loadtxt(os.path.join(path, 'imu.txt'), delimiter=' ')
        data.update({"time_sensors": imu_data[:, 0]})
        data.update({"accs": imu_data[:, 1:4]})
        data.update({"gyros": imu_data[:, 4:7]})
        data.update({"rads": False})
        truth_data = np.loadtxt(os.path.join(path, 'groundtruth.txt'), delimiter=' ')
        data.update({"time_truth": truth_data[:, 0]})
        data.update({"qts": truth_data[:, 4:]})
        return Data(data)
    else:
        sys.exit("Invalid path")

class Data:
    """
    Data to store the arrays of the most common variables.
    """
    def __init__(self, data_dict, **kwargs):
        # Create empty data attributes
        self.qts = None
        data_keys = list(data_dict.keys())
        # Find possible data from keys of dictionary
        time_labels = list(s for s in data_keys if 'time' in s.lower())
        acc_labels = list(s for s in data_keys if 'acc' in s.lower())
        gyr_labels = list(s for s in data_keys if 'gyr' in s.lower())
        mag_labels = list(s for s in data_keys if 'mag' in s.lower())
        qts_labels = list(s for s in data_keys if 'qts' in s.lower())
        rad_labels = list(s for s in data_keys if 'rad' in s.lower())
        self.in_rads = data_dict.get(rad_labels[0], False)
        # Load data into each attribute
        self.time = data_dict.get(time_labels[0], None) if time_labels else None
        if len(time_labels) > 1:
            self.time_ref = data_dict.get(time_labels[1], None) if time_labels else None
        self.acc = data_dict.get(acc_labels[0], None) if acc_labels else None
        self.gyr = data_dict.get(gyr_labels[0], None) if gyr_labels else None
        self.mag = data_dict.get(mag_labels[0], None) if mag_labels else None
        self.q_ref = data_dict.get(qts_labels[0], None) if qts_labels else None
        self.num_samples, self.num_axes = self.acc.shape