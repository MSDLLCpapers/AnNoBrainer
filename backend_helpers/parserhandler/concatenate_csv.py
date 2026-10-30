import csv
import os

target_file = "data/concatenated.csv"
source_folder = "data/out"

with open(target_file, "w") as csv_write_file:
    csv_write = csv.writer(csv_write_file, delimiter=",")
    for csv_file in os.listdir(source_folder):
        if not csv_file.endswith(".csv"):
            continue
        with open(os.path.join(source_folder, csv_file)) as csv_open_file:
            csv_read = csv.reader(csv_open_file, delimiter=",")
            for row in csv_read:
                csv_write.writerow(row)
