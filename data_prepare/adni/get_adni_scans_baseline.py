import csv
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

import time
from data_prepare.alzheimer_record import AlzheimerRecord
SYMBOL_NC = 'CN'
SYMBOL_MCI = 'MCI'
SYMBOL_AD = 'Dementia'
race_key = {
    'White': 'White',
    'Black': 'Black or African American',
    'Am Indian/Alaskan': 'American Indian or Alaska Native',
    'Asian': 'Asian',
    'More than one': 'More than one'
}

path_diagnosis = "raw_tables/ADNIMERGE_02Nov2023.csv"
path_mri = "raw_tables/MPRAGEMETA_11Nov2023.csv"
path_scanner = "raw_tables/ADSP_PHC_ADNI_T1_1.0_MetaData_11Nov2023.csv"

def write_record_to_csv(filename, data):
    header = ['filename',"diagnosis_id","image_id", "colport", 'status', 'age', 'gender', 'mmse', 'apoe', 'site', 'race', 'tesla','sequence', 'scanner','scan_date']

    file_exists = os.path.isfile(filename)

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)

        if file_exists and os.stat(filename).st_size > 0:
            file.truncate(0)  # 清空文件内容

        writer.writerow(header)  # 写入标题行
        writer.writerows(data)  # 写入内容行

def search_scanner(_rid):
    df_scanner = pd.read_csv(path_scanner,usecols=['RID','COG_VISCODE2','MANUFACTURER'])

    searched = df_scanner.loc[(df_scanner['RID'] == _rid) & (df_scanner['COG_VISCODE2'] == 'bl'), :].values

    if len(searched) > 0:
        return searched[0][2]
    else:
        return None


# 根据临床诊断结果和匹配到的MRI记录，生成数据集项
def get_adni_dataset_record(diagnosis, mr_scan, diagnosis_result):
    record = []  # filename,status,age,gender,mmse,apoe

    filename = 'I' + str(mr_scan[5]) #ImageUID
    # filename = mr_scan[5]


    if diagnosis_result == SYMBOL_NC:
        _status = 'NL'
    elif diagnosis_result == SYMBOL_MCI:
        _status = 'MCI'
    else:
        _status = 'AD'

    gender = 0 if diagnosis[8] == 'Female' else 1  # SEX
    age = float(diagnosis[7])  # EXAMDATE

    # 由于已经将apoe为9的记录过滤，因此apoe的值仅为0,1,2
    apoe = int(diagnosis[13])  # APOE4

    mmse = int(diagnosis[14])  # MMSE

    site = int(diagnosis[3])  # site

    race = diagnosis[11]  # race

    tesla = float(3) if diagnosis[15] == '3 Tesla MRI' else float(1.5)

    record.append(filename)  # filename
    record.append(diagnosis[0])  # diagnosis_id
    record.append(filename)  # image_id
    record.append(mr_scan[6])  # Visit
    record.append(_status)
    record.append(age)
    record.append(gender)
    record.append(mmse)
    record.append(apoe)
    record.append(site)
    record.append(race_key[race])
    record.append(tesla)
    record.append(mr_scan[1])
    record.append(search_scanner(diagnosis[0]))
    record.append(mr_scan[2]) # scan_date

    # # Create a dictionary with the data
    # data = {
    #     'filename': mr_scan[2].replace('.json', ''),
    #     'diagnosis_id': diagnosis[1],
    #     'image_id': mr_scan[1],
    #     'colport': None,
    #     'status': diagnosis_result,
    #     'age': float(diagnosis[3]),
    #     'gender': 1 if diagnosis[2] == 1 else 0,
    #     'mmse': None,
    #     'apoe': None,
    #     'site': 'CENTRAL05',
    #     'race': race_key[diagnosis[4]],
    #     'tesla': mr_scan[17],  # MagneticFieldStrength
    #     'sequence': mr_scan[37],  # SeriesDescription
    #     'scanner': mr_scan[31],
    #     'scan_date': None
    # }
    # return data

    return record


"""
筛选mr_scan记录
并将记录存入字典，
key:subject_id
value:相同subject_id的记录数组
由于筛选条件过多，使用pandas来实现
"""


def get_mr_scan_dict():
    mr_scan_dictionary = {}

    filtered_columns = ['SubjectID', 'Sequence', 'ScanDate', 'StudyID', 'SeriesID', 'ImageUID', 'Visit', 'Orig/Proc']
    df = pd.read_csv(path_mri, usecols=filtered_columns,index_col=False)[filtered_columns]

    condition1 = df['Sequence'].isin(["MPR; GradWarp; B1 Correction; N3; Scaled",
                                      "MPR-R; GradWarp; B1 Correction; N3; Scaled",
                                      "MPR; GradWarp; B1 Correction; N3; Scaled_2",
                                      "MPR-R; GradWarp; B1 Correction; N3; Scaled_2"
                                      ])
    condition2 = df['Orig/Proc'] == 'Processed'

    filtered_df = df[condition1 & condition2]

    filtered_records = filtered_df.values
    # filtered_records = df.values

    for record in filtered_records:
        subject_id = record[0]  # SubjectID

        # 判断该subject_id 是否在字典
        if subject_id not in mr_scan_dictionary:
            mr_scan_dictionary[subject_id] = []

        mr_scan_dictionary[subject_id].append(record)

    return mr_scan_dictionary


def get_excluded_diagnosis_baseline():
    """
    从CLINICALDATA数据中，筛选：
    """
    filter_columns = [
        'RID', 'ORIGPROT', 'PTID', 'SITE', 'VISCODE', 'EXAMDATE', 'DX_bl', 'AGE', 'PTGENDER', 'PTEDUCAT', 'PTETHCAT',
        'PTRACCAT', 'PTMARRY', 'APOE4',
        'MMSE', 'FLDSTRENG', 'IMAGEUID', 'DX'
    ]
    diagnosis_dictionary = {}
    df = pd.read_csv(path_diagnosis, usecols=filter_columns)

    # 定义筛选条件
    # condition1 = df['AGE'] != ''
    condition1 = df['VISCODE'] == 'bl'  # baseline

    condition2 = df['FLDSTRENG'].isin(['3 Tesla MRI', '1.5 Tesla MRI'])   # T=1.5 or 3

    condition3 = (df['MMSE'] >= 0) & (df['MMSE'] <= 30)  # 0 <= NACCMMSE <= 30

    condition4 = df['DX'].isin([SYMBOL_NC, SYMBOL_MCI, SYMBOL_AD])  # AD,MCI,Dementia

    filtered_records = df[condition1 & condition2 & condition3 & condition4].values

    for record in filtered_records:

        subject_id = record[2]  # PTID

        # 判断该subject_id 是否在字典
        if subject_id not in diagnosis_dictionary:
            diagnosis_dictionary[subject_id] = []
        else:
            # 某个PTID只保留它的baseline，因此若存在，则只需要保留一条
            continue

        diagnosis_dictionary[subject_id].append(record)

    # key:126_S_0605, value: 605	ADNI1	ADNI1	126_S_0605...
    # key:126_S_0605, value: 605	ADNI1	ADNI1	126_S_0605...
    return diagnosis_dictionary


"""
双向匹配，获取正确的6个月内扫描记录和对应的诊断
每个subject只会选择一条扫描记录和对应的诊断
"""


def match_date_closet(_diagnosis, mr_list):

    diagnosis_date = datetime.strptime(_diagnosis[5], "%Y-%m-%d")  # EXAMDATE 9/8/2005

    for mr_scan in mr_list:
        mr_scan_date = datetime.strptime(mr_scan[2], "%Y-%m-%d")  # ScanDate 9/8/2005 %m/%d/%Y
        # 计算日期差
        date_difference = mr_scan_date - diagnosis_date
        # 获取相隔的天数
        days_difference = date_difference.days
        # 若在该区间，则匹配成功
        if abs(days_difference) < 184:
            # # 修改实际年龄
            # _diagnosis[6] = round(_diagnosis[6] + (days_difference / 365), 2)  # 保留两位小数
            return _diagnosis, mr_scan

    return None


def check_for_diagnosis(_diagnosis):
    return _diagnosis[17]






if __name__ == "__main__":

    mr_scan_dictionary = get_mr_scan_dict()

    mr_scan_subjects = mr_scan_dictionary.keys()

    diagnosis_dictionary = get_excluded_diagnosis_baseline()

    # 需要写入数据集文件的列表
    adni_all_data_list = []
    adni_data_list = []

    for subject_id, diagnosis_records in diagnosis_dictionary.items():
        diagnosis_record = diagnosis_records[0]  # 只使用baseline

        # 如果mr记录中没有该subject，则直接跳过
        if subject_id not in mr_scan_subjects:
            continue

        diagnosis_result = check_for_diagnosis(diagnosis_record)

        selected_mr_scans = mr_scan_dictionary[subject_id]

        # 将诊断结果与mri记录进行双向匹配
        match = match_date_closet(diagnosis_record, selected_mr_scans)

        if match is None:
            # 未匹配成功
            # print("函数返回了None")
            continue
        else:
            # 匹配成功,进一步处理返回的数据
            target_diagnosis, target_mr_scan = match

            # 生成dataset记录
            dataset_record = get_adni_dataset_record(target_diagnosis, target_mr_scan, diagnosis_result)

            adni_all_data_list.append(dataset_record)

    write_record_to_csv("adni_baseline.csv", adni_all_data_list)
