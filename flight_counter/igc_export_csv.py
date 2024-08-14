import os.path as path
from jsonargparse import CLI
from typing import Optional, List, TextIO
from flight_counter.igc_parser import load_igc_file, Igc
import csv


def igc_to_csv(
        igc: Igc,
        csv_file: Optional[TextIO]
):
    csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
    for i, record in enumerate(igc.records):
        csv_writer.writerow([igc.header.track_date + record.timestamp,
                             record.latitude, record.longitude,
                             record.validity,
                             record.altitude_pression, record.altitude_gnss,
                             record.extra])


def igc_file_to_csv_file(
        igc_file_path: str,
        csv_file_path: Optional[str]
):
    igc = load_igc_file(igc_file_path)
    # todo: optimize avoiding igc full load
    if not csv_file_path:
        csv_file_path = path.splitext(igc_file_path)[0] + '.csv'
    with open(csv_file_path, 'w', newline='') as csv_file:
        igc_to_csv(igc, csv_file)


if __name__ == "__main__":
    CLI(igc_file_to_csv_file)
