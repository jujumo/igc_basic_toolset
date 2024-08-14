import os
import os.path as path
from datetime import timedelta
from rich.progress import track
from jsonargparse import CLI
from typing import Optional, List
from flight_counter.igc_parser import load_igc_header_stream, load_igc_records_stream, igc_file_iterator, IgcRecord


def get_flight_duration(
        igc_records: List[IgcRecord]
):
    duration = igc_records[-1].timestamp - igc_records[0].timestamp
    return duration


def count(
        flight_directory: str,
        wing_name: Optional[str] = None,
        pilot_name: Optional[str] = None
):
    igc_file_list = sorted(igc_file_iterator(flight_directory))
    print(f'{len(igc_file_list)} igc file found.')
    duration_total = timedelta()
    for igc_file_path in track(igc_file_list):
        with open(igc_file_path, 'r', encoding='utf-8') as igc_file_stream:
            igc_info = load_igc_header_stream(igc_file_stream)
            if igc_info is None:
                continue
            if wing_name and wing_name != igc_info.glider_type:
                # skip it
                continue
            if pilot_name and pilot_name != igc_info.pilot_name:
                # skip it
                continue

            igc_records = load_igc_records_stream(igc_file_stream)
            duration_total += get_flight_duration(igc_records)

    print(f'Total: {duration_total.seconds/3600:6.1f} hours')


if __name__ == "__main__":
    CLI(count)
