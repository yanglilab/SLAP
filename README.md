# HSGO
The MRI file IDs used in the experiment are stored in `#{dataset_name}/raw_tables/#{dataset_name}_baseline.csv`. 
To obtain the raw data in this experiment, please:
1. Apply for each of the following datasets: ADNI, AIBL, ANMerge, NACC, OASIS3, OASIS4.
2. Follow the instructions in `#{dataset_name}/raw_tables/tables.txt` to place these files into `dataset_name/raw_tables`.
3. Run `get_#{dataset_name}_scans_baseline.py`.
4. Delete the files listed in `not_good_files.csv`.

The remaining code for this experiment will be uploaded after the paper is accepted.
