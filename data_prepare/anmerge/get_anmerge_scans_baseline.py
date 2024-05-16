import csv
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

import time
SYMBOL_NC = 'CTL'
SYMBOL_MCI = 'MCI'
SYMBOL_AD = 'AD'

SYMBOL_BASELINE = 'm00'

race_key = {
    'White': 'White',
    'Black': 'Black or African American',
    'Am Indian/Alaskan': 'American Indian or Alaska Native',
    'Asian': 'Asian',
    'More than one': 'More than one'
}

path_diagnosis = "raw_tables/ANMerge_clinical_under_90.csv"
path_mri = "raw_tables/Innomed_AddNeuroMed_ImageLookup.csv"
def write_record_to_csv(filename, data):
    header = ['filename',"diagnosis_id","image_id", "colport", 'status', 'age', 'gender', 'mmse', 'apoe', 'site', 'race', 'tesla','sequence', 'scanner','scan_date']

    file_exists = os.path.isfile(filename)

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)

        if file_exists and os.stat(filename).st_size > 0:
            file.truncate(0)  # 清空文件内容

        writer.writerow(header)  # 写入标题行
        writer.writerows(data)  # 写入内容行


# 根据临床诊断结果和匹配到的MRI记录，生成数据集项
def get_anmerge_dataset_record(diagnosis, mr_scan, diagnosis_result):
    record = []  # filename,status,age,gender,mmse,apoe

    if diagnosis_result == SYMBOL_NC:
        _status = 'NL'
    elif diagnosis_result == SYMBOL_MCI:
        _status = 'MCI'
    else:
        _status = 'AD'

    gender = 0 if diagnosis[6] == 'Female' else 1  # SEX
    age = float(diagnosis[8])  # EXAMDATE

    # 由于已经将apoe为9的记录过滤，因此apoe的值仅为0,1,2

    if diagnosis[9] is np.nan:
        apoe = None
    else:
        apoe = 1 if 'E4' in diagnosis[9] else 0  # APOE4 = E2E2，E2E3，E2E4，E3E3，E3E4，E4E4

    mmse = int(diagnosis[10])  # MMSE

    site = diagnosis[3]  # site

    race = None

    tesla = float(1.5)

    record.append(mr_scan[1])  # filename=image_id
    record.append(diagnosis[0])  # diagnosis_id，与subject_id类似
    record.append(mr_scan[1])  # image_id
    record.append(mr_scan[2])  # colport
    record.append(_status)
    record.append(age)
    record.append(gender)
    record.append(mmse)
    record.append(apoe)
    record.append(site)
    record.append(race)
    record.append(tesla)
    record.append(None)  # sequence
    record.append(mr_scan[5]) # scanner
    record.append(mr_scan[6]) # scan_date
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

    filtered_columns = ['Individual','GUID',  'Timepoint', 'Scan Type', 'Field Strength',  'Scanner', 'Scan date']
    df = pd.read_csv(path_mri, usecols=filtered_columns,index_col=False)[filtered_columns]

    # 直接获取基线记录
    condition1 = df['Timepoint'] == 'm00'

    filtered_df = df[condition1]

    filtered_records = filtered_df.values
    # filtered_records = df.values

    for record in filtered_records:
        subject_id = record[0]  # Individual

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
        'RID', 'Subject_ID', 'Sadman_ID', 'Site', 'Month', 'Visit', 'Sex', 'Diagnosis', 'Age', 'APOE', 'MMSE']
    diagnosis_dictionary = {}
    df = pd.read_csv(path_diagnosis, usecols=filter_columns)

    # 定义筛选条件
    # condition1 = df['AGE'] != ''
    condition1 = df['Visit'] == 1  # baseline

    filtered_records = df[condition1].values

    for record in filtered_records:

        subject_id = record[1]  # Subject_ID

        # 判断该subject_id 是否在字典
        if subject_id not in diagnosis_dictionary:
            diagnosis_dictionary[subject_id] = []
        else:
            # 某个PTID只保留它的baseline，因此若存在，则只需要保留一条
            continue

        diagnosis_dictionary[subject_id].append(record)

    return diagnosis_dictionary


"""
双向匹配，获取正确的6个月内扫描记录和对应的诊断
每个subject只会选择一条扫描记录和对应的诊断
"""


def match_date_closet(_diagnosis, mr_list):

    return _diagnosis, mr_list[0]


def check_for_diagnosis(_diagnosis):
    return _diagnosis[7]






if __name__ == "__main__":

    mr_scan_dictionary = get_mr_scan_dict()

    mr_scan_subjects = mr_scan_dictionary.keys()

    diagnosis_dictionary = get_excluded_diagnosis_baseline()

    # 需要写入数据集文件的列表
    anmerge_all_data_list = []

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
            dataset_record = get_anmerge_dataset_record(target_diagnosis, target_mr_scan, diagnosis_result)

            anmerge_all_data_list.append(dataset_record)

    # for _item in adni_all_data_list:
    #     # print(_item)
    #     image_id = _item[0]
    #     time.sleep(10)
    #     status_code = save_img_to_collect_by_id(image_id)
    #     if status_code != 200:
    #         print("异常，终止请求")
    #         break

    write_record_to_csv("anmerge_baseline.csv", anmerge_all_data_list)
    #
    # for filename in filenames:
    #
    #     time.sleep(10)
    #
    #     status_code = save_img_to_collect_by_id(filename)
    #     if status_code != 200:
    #         print("异常，终止请求")
    #         break
