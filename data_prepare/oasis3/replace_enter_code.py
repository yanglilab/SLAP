import csv

with open('../oasis4/raw_tables/download_selected_scan.csv') as f:
  reader = csv.reader(f)
  lines = list(reader)

with open('../oasis4/raw_tables/download_selected_scan_encode.csv', 'w', newline='') as f:
  writer = csv.writer(f)
  for line in lines:
    line = [cell.replace('\r', '') for cell in line]
    writer.writerow(line)
