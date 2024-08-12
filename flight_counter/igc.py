import os
import os.path as path
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

""" header looks like :
AXSDUB4963
HFDTE090824
HFPLTPILOTINCHARGE:JuM
HFCM2CREW2:NIL
HFGTYGLIDERTYPE:photon
HFGIDGLIDERID:NKN
HFCIDCOMPETITIONID:NKN
HFDTMGPSDATUM:WGS84
HFRFWFIRMWAREVERSION:2023-11-29:87e22e5a
HFRHWHARDWAREVERSION:ULTRABIP 1.0
HFFTYFRTYPE:STODEUS,ULTRABIP
HFGPSRECEIVER:GOTOP,GT1110SN,22,18000
HFTZNTIMEZONE:2
HFPRSPRESSALTSENSOR:INFINEON,DPS310,7000
HFALGALTGPS:GEO
HFALPALTPRESSURE:ISA
LMMMGPSPERIOD1000MSEC
I023638FXA3940SIU
"""


@dataclass
class IgcHeader:
    file_path: str
    track_date: date = date
    glider_type: str = ''
    glider_id: str = ''
    pilot_name: str = ''
    hardware_type: str = ''


def load_igc_header(file_path: str) -> Optional[IgcHeader]:
    """

    https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_HFDTE
    :param file_path:
    :return:
    """
    header = IgcHeader(file_path)
    with open(file_path, 'r', encoding='utf-8') as file:
        # A Record is always the first in the file
        a_record = file.readline()
        if not a_record.startswith('A'):
            return

        for record in file.readlines():
            record = record.strip()  # remove any end of line
            try:
                if not record.startswith('H'):
                    break
                if record.startswith('HFDTE'):  # UTC date this file was recorded
                    # format : HFDTEDDMMYY
                    dd, mm, yy = int(record[5:7]), int(record[7:9]), int(record[9:11])
                    # year is only 2 digits, make it full year on simple assumption
                    yy += 1900 if yy > 80 else 2000
                    header.track_date = date(day=dd, month=mm, year=yy)
                if record.startswith('HFPLTPILOTINCHARGE:'):  # Name of the competing pilot
                    header.pilot_name = record[len('HFPLTPILOTINCHARGE:'):]
                if record.startswith('HFGTYGLIDERTYPE:'):  # glider model
                    header.glider_type = record[len('HFGTYGLIDERTYPE:'):]
                if record.startswith('HFGIDGLIDERID:'):  # glider model
                    header.glider_id = record[len('HFGIDGLIDERID:'):]
                if record.startswith('HFFTYFRTYPE:'):  # glider model
                    header.hardware_type = record[len('HFFTYFRTYPE:'):]

            except Exception as e:
                print(f'fail to parse line: {record[0:10]}...')

    return header


@dataclass
class Records:
    times: List[timedelta] = field(default_factory=lambda: [])
    longitudes: List[float] = field(default_factory=lambda: [])
    latitudes: List[float] = field(default_factory=lambda: [])
    validity: List[float] = field(default_factory=lambda: [])
    altitudes_pression: List[float] = field(default_factory=lambda: [])
    altitudes_gnss: List[float] = field(default_factory=lambda: [])

    def append(self, time, longitude, latitude, validity, altitudes_press, altitudes_gnss):
        pass


def str_to_wgs84(igs_coord: str):
    degrees = int(igs_coord[0:2])
    minutes = int(igs_coord[2:4])
    decimal_minutes = int(igs_coord[4:7])
    hemisphere = igs_coord[7]
    # Convert everything to a float representing degrees
    coord = degrees + (minutes + decimal_minutes / 1000.0) / 60.0
    if hemisphere in ['S', 'W']:
        coord = -coord
    return coord


def load_igc_track(file_path: str) -> List[str]:
    """
    https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_4.1
    :param file_path:
    :return:
    """
    # B H H M M S S D D M MM MM N D D D M MM MM E V P P P P P G G G G G CR LF
    records = Records()
    with open(file_path, 'r', encoding='utf-8') as file:
        for record in file.readlines():
            if not record.startswith('B'):
                continue
            record = record.strip()  # remove any end of line
            hh, mm, ss = int(record[1:3]), int(record[3:5]), int(record[5:7])
            timestamp = timedelta(hours=hh, minutes=mm, seconds=ss)
            latitude = str_to_wgs84(record[7:15])
            longitude = str_to_wgs84(record[16:24])
            records.times.append(timestamp)
            records.latitudes.append(latitude)
            records.longitudes.append(longitude)
            records.validity.append(record[24])
            if len(record) >= 30:
                records.altitudes_pression.append(float(record[25:30]))
            if len(record) >= 35:
                records.altitudes_gnss.append(float(record[30:35]))
    return records


def igc_file_iterator(
        dir_path: str
) -> List[str]:
    """
    Returns an iterable on all igc files contained in dir_path.
    :param dir_path: path of root directory containing igc files.
    :return:
    """
    file_iterator = (path.join(dp, fn) for dp, _, fs in os.walk(dir_path) for fn in fs)
    file_iterator = (filepath for filepath in file_iterator if path.splitext(filepath)[1].upper() == '.IGC')
    return file_iterator

