import os
import os.path as path
from typing import Optional, List, TextIO
from dataclasses import dataclass, field
from datetime import date, timedelta, datetime


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
    track_date: date = date
    glider_type: str = ''
    glider_id: str = ''
    pilot_name: str = ''
    hardware_type: str = ''


def load_igc_header_stream(
        file_stream: TextIO
) -> IgcHeader:
    """

    https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_HFDTE
    :param file_stream:
    :return:
    """
    header = IgcHeader()

    # A Record is always the first in the file
    record = file_stream.readline()
    if not record.startswith('A'):
        return

    while record:
        record = file_stream.readline()
        record = record.strip()  # remove any end of line
        if not record.startswith('H'):
            # rewind to the beginning of the line, allow record parser to start from here:
            pos = file_stream.tell() - len(record) - 2
            file_stream.seek(pos)
            break
        if record.startswith('HFDTE'):  # UTC date this file was recorded
            # format : HFDTEDDMMYY
            dd, mm, yy = int(record[5:7]), int(record[7:9]), int(record[9:11])
            # year is only 2 digits, make it full year on simple assumption
            yy += 1900 if yy > 80 else 2000
            header.track_date = datetime(day=dd, month=mm, year=yy)
        if record.startswith('HFPLTPILOTINCHARGE:'):  # Name of the competing pilot
            header.pilot_name = record[len('HFPLTPILOTINCHARGE:'):]
        if record.startswith('HFGTYGLIDERTYPE:'):  # glider model
            header.glider_type = record[len('HFGTYGLIDERTYPE:'):]
        if record.startswith('HFGIDGLIDERID:'):  # glider model
            header.glider_id = record[len('HFGIDGLIDERID:'):]
        if record.startswith('HFFTYFRTYPE:'):  # glider model
            header.hardware_type = record[len('HFFTYFRTYPE:'):]

    return header


def load_igc_header_file(
        file_path: str
) -> IgcHeader:
    with open(file_path, 'r', encoding='utf-8') as file_stream:
        return load_igc_header_stream(file_stream)


@dataclass
class IgcRecord:
    timestamp: timedelta
    longitude: float
    latitude: float
    validity: float
    altitude_pression: Optional[float] = None
    altitude_gnss:  Optional[float] = None
    extra: Optional[str] = None


def parse_wgs84(
        igs_coord: str
):
    degrees = int(igs_coord[0:2])
    minutes = int(igs_coord[2:4])
    decimal_minutes = int(igs_coord[4:7])
    hemisphere = igs_coord[7]
    # Convert everything to a float representing degrees
    coord = degrees + (minutes + decimal_minutes / 1000.0) / 60.0
    if hemisphere in ['S', 'W']:
        coord = -coord
    return coord


def parse_b_record(
        line: str
) -> IgcRecord:
    """
    https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_4.1
    :param line: input b frame
    :return:
    """
    # B H H M M S S D D M MM MM N D D D M MM MM E V P P P P P G G G G G CR LF
    assert line.startswith('B'), 'this is not B record'
    line = line.strip()  # remove any end of line
    hh, mm, ss = int(line[1:3]), int(line[3:5]), int(line[5:7])
    time_of_day = timedelta(hours=hh, minutes=mm, seconds=ss)
    latitude = parse_wgs84(line[7:15])
    longitude = parse_wgs84(line[16:24])
    validity = line[24]
    altitudes_pression = float(line[25:30]) if len(line) >= 30 else None
    altitudes_gnss = float(line[30:35]) if len(line) >= 35 else None
    extra = line[35:] if len(line) > 35 else None
    return IgcRecord(time_of_day, latitude, longitude, validity, altitudes_pression, altitudes_gnss, extra)


def load_igc_records_stream(
        file_stream: TextIO,
) -> List[IgcRecord]:
    """
    https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_4.1
    :param file_stream: input file stream
    :return:
    """
    # B H H M M S S D D M MM MM N D D D M MM MM E V P P P P P G G G G G CR LF
    records = []
    while True:
        line = file_stream.readline()
        if not line:
            break
        if line.startswith('B'):
            record = parse_b_record(line)
            records.append(record)
    return records


def load_igc_records_file(
        file_path: str,
) -> List[IgcRecord]:
    with open(file_path, 'r', encoding='utf-8') as file_stream:
        igc_records = load_igc_records_stream(file_stream)
    return igc_records


@dataclass
class Igc:
    header: IgcHeader
    records: List[IgcRecord]


def load_igc_file(
        file_path: str
):
    with open(file_path, 'r', encoding='utf-8') as igc_file_stream:
        igc_header = load_igc_header_stream(igc_file_stream)
        igc_records = load_igc_records_stream(igc_file_stream)
    return Igc(igc_header, igc_records)


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

