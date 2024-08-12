import os
import os.path as path
from datetime import timedelta
from rich.progress import track
from jsonargparse import CLI
from typing import Optional, List
from flight_counter.igc import load_igc_header, igc_file_iterator, load_igc_track


def get_flight_hours(
        file_path: str,
        wing_name: Optional[str] = None
) -> timedelta:
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # early reject IGC that does not match wing name
    if wing_name:
        igc_wing_name = next(iter(l.split(':')[1].strip().lower()
                                  for l in lines if l.startswith('HFGTYGLIDERTYPE')), None)
        if not igc_wing_name.lower().startswith(wing_name):
            return

    start_time = None
    end_time = None

    for line in lines:
        if line.startswith('B'):
            time = line[1:7]
            if not start_time:
                start_time = time
            end_time = time

    if start_time and end_time:
        try:
            start = timedelta(hours=int(start_time[:2]), minutes=int(start_time[2:4]), seconds=int(start_time[4:]))
            end = timedelta(hours=int(end_time[:2]), minutes=int(end_time[2:4]), seconds=int(end_time[4:]))
            flight_hours = end - start
            # print(f'{wing_name=}, {str(start)}')
            return flight_hours
        except ValueError as e:
            # parsing error
            print(f'error while parsing {file_path}')
            return

    return


def sum_flight_hours(
        dir_path: str,
        wing_name: Optional[str] = None
):
    total_flight_hours = timedelta()
    for file_path in igc_file_iterator(dir_path):
        flight_hours = get_flight_hours(file_path, wing_name=wing_name)
        if flight_hours is not None:
            # print(f'time={str(flight_hours)}')
            total_flight_hours += flight_hours

    return total_flight_hours


def count(
        flight_directory: str,
        wing_name: Optional[str] = None,
        pilot_name: Optional[str] = None
):
    # total_filght_time = sum_flight_hours(flight_directory, wing_name=wing_name)
    # total_hours = total_filght_time.total_seconds() / 3600
    # print(f'Total: {total_hours:6.1f} hours')
    igc_file_list = sorted(igc_file_iterator(flight_directory))
    print(f'{len(igc_file_list)} igc file found.')
    for igc_file_path in igc_file_list:
        igc_info = load_igc_header(igc_file_path)
        if igc_info is None:
            continue
        if wing_name and wing_name != igc_info.glider_type:
            # skip it
            continue
        if pilot_name and pilot_name != igc_info.pilot_name:
            # skip it
            continue

        data = load_igc_track(igc_file_path)
        # print(data.times[-1] - data.times[0])
        print(data.latitudes)
        import matplotlib.pyplot as plt
        plt.plot(data.altitudes_pression)
        plt.plot(data.altitudes_gnss)
        # plt.plot(data.latitudes)
        plt.show()
        exit(1)
    # for file_path in :


if __name__ == "__main__":
    CLI(count)
