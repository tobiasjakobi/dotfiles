#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

from __future__ import annotations

import sys

from dataclasses import dataclass
from os.path import isdir, isfile, islink, join as pjoin
from os import listdir
from re import compile as rcompile

from sysfs_helper import read_sysfs, get_parent_device


##########################################################################################
# Class definitions
##########################################################################################

@dataclass(frozen=True)
class SensorDevice:
    vendor_id: int
    device_id: int

@dataclass(frozen=True)
class SensorDescription:
    driver: str
    label: str
    device: SensorDevice

@dataclass(frozen=True)
class SensorDeviceInfo:
    value_path: str
    parent_path: str


##########################################################################################
# Constants
##########################################################################################

_sysfs_base = '/sys/class/hwmon/'

_hwmon_re = rcompile('^hwmon[0-9]+$')
_label_re = rcompile('^temp[0-9]+_label$')

sensor_descs = {
    # AMD Ryzen 7 4800H
    'CPU': SensorDescription(driver = 'k10temp', label = 'Tctl', device = SensorDevice(0x1022, 0x144b)),

    # Primary 512GB NVME SSD (PM991 NVMe Samsung 512GB).
    'NVME0': SensorDescription(driver = 'nvme', label = 'Sensor 1', device = SensorDevice(0x144d, 0xa808)),

    # Secondary 1TB NVME SSD (Samsung SSD 970 EVO 1TB).
    'NVME1': SensorDescription(driver = 'nvme', label = 'Sensor 1', device = SensorDevice(0x144d, 0xa809)),

    # Integrated AMD Renoir GPU.
    'iGPU': SensorDescription(driver= 'amdgpu', label = 'edge', device = SensorDevice(0x1002, 0x1636)),

    # Dedicated AMD Navi10 GPU.
    'dGPU': SensorDescription(driver= 'amdgpu', label = 'junction', device = SensorDevice(0x1002, 0x731f)),
}


##########################################################################################
# Internal functions
##########################################################################################

def _is_sensor_online(info: SensorDeviceInfo) -> bool:
    runtime_status = read_sysfs(pjoin(info.parent_path, 'power/runtime_status'))
    if runtime_status is None:
        return False

    return runtime_status == 'active'

def _is_matching_device(path: str, sdev: SensorDevice) -> bool:
    try:
        device_id = int(read_sysfs(pjoin(path, 'device')), 16)
        vendor_id = int(read_sysfs(pjoin(path, 'vendor')), 16)

    except Exception:
        return False

    return vendor_id == sdev.vendor_id and device_id == sdev.device_id

def _lookup_label(path: str, label: str) -> str:
    for arg in listdir(path):
        res = _label_re.findall(arg)
        if len(res) == 0:
            continue

        sensor_label = read_sysfs(pjoin(path, arg))
        if sensor_label == label:
            return arg

    return None

def _identify_sensor(path: str, desc: SensorDescription) -> SensorDeviceInfo:
    sensor_driver = read_sysfs(pjoin(path, 'name'))
    if sensor_driver != desc.driver:
        return None

    parent_device = get_parent_device(path)
    if not _is_matching_device(parent_device, desc.device):
        return None

    label_node = _lookup_label(path, desc.label)
    if label_node is None:
        return None

    try:
        prefix, _ = label_node.rsplit('_', maxsplit=1)
        sensor_input = f'{prefix}_input'

    except Exception:
        return None

    value_path = pjoin(path, sensor_input)

    return SensorDeviceInfo(value_path, parent_device)

def _read_sensor_internal(info: SensorDeviceInfo) -> str:
    '''
    Internal helper to read the sensor value.

    Arguments:
        info - the sensor device info to use
    '''

    content = read_sysfs(info.value_path)

    if content is None or not content.isdigit():
        return 'Error'
    else:
        value = int(content)

    return '{0:6.2f}°C'.format(float(value) / 1000.0)


##########################################################################################
# Functions
##########################################################################################

def get_sensor(desc: SensorDescription) -> SensorDeviceInfo:
    '''
    Lookup a sensor using a sensor description.

    Arguments:
        desc - the sensor description to use

    Returns a SensorDeviceInfo object, or None if the sensors does not exist.
    '''

    if not isdir(_sysfs_base):
        return None

    for arg in listdir(_sysfs_base):
        res = _hwmon_re.findall(arg)
        if len(res) == 0:
            continue

        p = pjoin(_sysfs_base, arg)
        if not islink(p):
            continue

        info = _identify_sensor(p, desc)
        if info is not None:
            return info

    return None

def read_sensor(info: SensorDeviceInfo) -> str:
    '''
    Read current sensor value.

    Arguments:
        info - the sensor device info to use
    '''

    if not _is_sensor_online(info):
        return 'N/A'

    return _read_sensor_internal(info)

def gpu_busy(info: SensorDeviceInfo) -> int:
    '''
    Read the GPU busy ratio of the sensor's parent device.

    Arguments:
        info - the sensor device info to use

    Reading the busy ratio is only supported if the parent device is a GPU.
    '''

    if not _is_sensor_online(info):
        return None

    gpu_busy_percent = read_sysfs(pjoin(info.parent_path, 'gpu_busy_percent'))
    if gpu_busy_percent is None:
        return None

    return int(gpu_busy_percent)


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    if len(args) < 2:
        return 0

    sensor = args[1]

    try:
        desc = sensor_descs[sensor]

    except Exception as exc:
        print(f'error: unknown sensor requested: {sensor}: {exc}', file=sys.stderr)

        return 1

    info = get_sensor(desc)
    if info is None:
        print('error: sensor not found', file=sys.stderr)

        return 2

    sensor_value = read_sensor(info)

    print(f'Sensor {sensor}: {sensor_value}', file=sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
