import csv
from glob import glob
from collections import defaultdict
import pandas as pd

path_data_collection_csv = 'raw_tables/aibl_adni_confirmed_11_09_2023.csv'
path_data_searched_csv = 'raw_tables/aibl_search_baseline.csv'

# This script is modified from "https://github.com/vkola-lab/ncomms2022/blob/main/lookupcsv/dataset_table/AIBL/AIBL.py"
class TableData:
    def __init__(self):
        self.datasetName = 'AIBL'
        self.imageDir = '/media/flik/seagate_basic/alzheimer_dataset/AIBL_raw/'
        self.imageFileNameList, self.RIDList, self.imgIDList, self.manufacturerList = self.get_filenames_and_IDs(self.imageDir)
        self.columnNames = []
        self.content = defaultdict(dict)  # dictionary of dictionary; {RID: {colname1: val1, colname2: val2, ...}}
        # self.time_table = self.get_time_table()

    def get_filenames_and_IDs(self, path):
        fullpathList = glob(path + '*.nii')
        fileNameList = [fullpath.split('/')[-1].replace('.nii', '') for fullpath in fullpathList]

        RIDList = [filename.split('_')[0] for filename in fileNameList]
        manufacturerList = [filename.split('_')[1].split('.')[0] for filename in fileNameList]  # 使用dim2niix时，将扫描仪信息提取到名称中
        df = pd.read_csv(path_data_collection_csv, dtype={'Subject': str} )
        df = df.set_index('Subject')
        df = df.loc[RIDList]
        imgIDList = df['Image Data ID'].values
        return fileNameList, RIDList, imgIDList, manufacturerList

    def addColumns_path_filename(self):
        self.columnNames.extend(['filename', 'image_id', 'diagnosis_id', 'visit', 'scanner'])
        for idx, rid in enumerate(self.RIDList):
            # self.content[rid]['path'] = self.imageDir
            self.content[rid]['filename'] = self.imageFileNameList[idx]  # filename
            self.content[rid]['image_id'] = self.imgIDList[idx]
            self.content[rid]['diagnosis_id'] = rid
            self.content[rid]['scanner'] = self.manufacturerList[idx]
            self.content[rid]['visit'] = 'bl' #baseline



    def get_time_table(self):
        convert = {'1': 'Base', '2': 'm18', '3': 'm36', '4': 'm54'}
        time_table = {} # the time_table maps image ID to visit code
        with open(path_data_collection_csv) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                time_table[row['Image Data ID']] = convert[row['Visit']]
        return time_table

    def addColumns_diagnosis(self):
        variables = ['NC', 'MCI', 'DE', 'COG', 'AD', 'PD', 'FTD', 'VD', 'DLB', 'PDD', 'ADD', 'OTHER', 'status']
        self.columnNames.extend(variables)
        targetTable = 'raw_tables/aibl_pdxconv_01-Jun-2018.csv'
        targetTable = self.readcsv(targetTable)
        for row in targetTable:
            if row['RID'] in self.content and row['VISCODE'] == self.content[row['RID']]['visit']:
                if row['DXCURREN'] == '1':# NL healthy control
                    self.content[row['RID']]['status'] = 'NL'
                    for var in ['MCI', 'DE', 'AD', 'FTD', 'VD', 'DLB', 'PDD', 'OTHER']: # Note that PD is not included here, since all DXPARK=-4
                        self.content[row['RID']][var] = 0   # 0 means no
                    self.content[row['RID']]['NC'] = 1      # 1 means yes
                    self.content[row['RID']]['COG'] = 0
                elif row['DXCURREN'] == '2':# MCI patient
                    self.content[row['RID']]['status'] = 'MCI'
                    for var in ['NC', 'DE', 'AD', 'FTD', 'VD', 'DLB', 'PDD', 'OTHER']: # Note that PD is not included here, since all DXPARK=-4
                        self.content[row['RID']][var] = 0
                    self.content[row['RID']]['MCI'] = 1
                    self.content[row['RID']]['COG'] = 1
                elif row['DXCURREN'] == '3':
                    self.content[row['RID']]['status'] = 'AD'
                    self.content[row['RID']]['COG'] = 2
                    self.content[row['RID']]['ADD'] = 1
                    for var in ['NC', 'MCI']:
                        self.content[row['RID']][var] = 0
                    for var in ['AD', 'DE']:
                        self.content[row['RID']][var] = 1
                else:
                    self.content[row['RID']]['status'] = 'else'



    def addColumns_mmse(self):
        self.columnNames.extend(['mmse'])
        targetTable = 'raw_tables/aibl_mmse_01-Jun-2018.csv'
        targetTable = self.readcsv(targetTable)
        for row in targetTable:
            if row['RID'] in self.content and row['VISCODE'] == self.content[row['RID']]['visit']:
                self.content[row['RID']]['mmse'] = row['MMSCORE']

    def addColumns_cdr(self):
        self.columnNames.extend(['cdr'])
        targetTable = 'raw_tables/aibl_cdr_01-Jun-2018.csv'
        targetTable = self.readcsv(targetTable)
        for row in targetTable:
            if row['RID'] in self.content and row['VISCODE'] == self.content[row['RID']]['visit']:
                self.content[row['RID']]['cdr'] = row['CDGLOBAL']

    def addColumns_lm(self):
        self.columnNames.extend(['lm_imm', 'lm_del'])
        targetTable = 'raw_tables/aibl_neurobat_01-Jun-2018.csv'
        targetTable = self.readcsv(targetTable)
        for row in targetTable:
            if row['RID'] in self.content and row['VISCODE'] == self.content[row['RID']]['visit']:
                self.content[row['RID']]['lm_imm'] = row['LIMMTOTAL']
                self.content[row['RID']]['lm_del'] = row['LDELTOTAL']

    def addColumns_demograph(self):
        self.columnNames.extend(['age', 'gender', 'scan_date'])
        targetTable = path_data_collection_csv
        targetTable = self.readcsv(targetTable)
        for row in targetTable:
            if row['Subject'] in self.content:
                self.content[row['Subject']]['age'] = int(row['Age'])
                self.content[row['Subject']]['gender'] = 1 if row['Sex'] == 'M' else 0
                self.content[row['Subject']]['scan_date'] = row['Acq Date']

    def addColumns_apoe(self):
        self.columnNames.extend(['apoe'])
        targetTable = 'raw_tables/aibl_apoeres_01-Jun-2018.csv'  # to get age and gender which table you need to look into
        targetTable = self.readcsv(targetTable)
        for row in targetTable:
            if row['RID'] in self.content:
                if (row['APGEN1'], row['APGEN2']) in [('3', '4'), ('4', '4')]:
                    self.content[row['RID']]['apoe'] = 1
                else:
                    self.content[row['RID']]['apoe'] = 0

    # def addColumns_tesla(self):
    #     T15Table = self.readcsv('raw_tables/aibl_mrimeta_01-Jun-2018.csv')
    #     T3Table = self.readcsv('raw_tables/aibl_mri3meta_01-Jun-2018.csv')
    #     self.columnNames.extend(['Tesla'])
    #     self.content['135']['Tesla'] = 3.0 # manually checked
    #     self.content['448']['Tesla'] = 1.5  # manually checked
    #     self.content['653']['Tesla'] = 1.5  # manually checked
    #     self.content['340']['Tesla'] = 1.5  # manually checked
    #     for row in T15Table:
    #         if row['RID'] in self.content and row['VISCODE'] == self.content[row['RID']]['visit']:
    #             self.content[row['RID']]['Tesla'] = 1.5
    #     for row in T3Table:
    #         if row['RID'] in self.content and row['VISCODE'] == self.content[row['RID']]['visit']:
    #             self.content[row['RID']]['Tesla'] = 3.0

    def addColumns_tesla(self):
        self.columnNames.extend(['tesla'])
        df_search_baseline = pd.read_csv(path_data_searched_csv, dtype={'Subject ID': str})
        df_search_baseline = df_search_baseline.set_index('Subject ID')
        df_search_baseline = df_search_baseline.loc[self.RIDList]
        # Acquisition Plane=SAGITTAL;Mfg Model=TrioTim;Slice Thickness=1.2;Matrix Z=160.0;Acquisition Type=3D;Field Strength=3.0;Manufacturer=SIEMENS;Weighting=T1
        protocol_list = df_search_baseline['Imaging Protocol'].values

        for idx, rid in enumerate(self.RIDList):
            self.content[rid]['tesla'] = float(protocol_list[idx].split(";")[-3].split("=")[-1])

    def writeTable(self):
        self.addColumns_path_filename()
        self.addColumns_demograph()
        self.addColumns_apoe()
        self.addColumns_diagnosis()
        self.addColumns_mmse()
        self.addColumns_cdr()
        self.addColumns_lm()
        self.addColumns_tesla()
        with open('aibl_baseline.csv', 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.columnNames)
            writer.writeheader()
            for rid in self.content:
                # 极个别数据的status为空，删除该行
                if self.content[rid]['status'] == 'else':
                    continue
                writer.writerow(self.content[rid])

    def readcsv(self, csv_file):
        csvfile = open(csv_file, 'r')
        return csv.DictReader(csvfile)


if __name__ == "__main__":
    obj = TableData()
    obj.writeTable()
