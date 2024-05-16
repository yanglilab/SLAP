import csv
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from utils import read_txt_line
from data_prepare.not_good_files import get_not_good_filenames

# ftld表中必要的列
ftld_columns = ['NACCID', 'VISITMO', 'VISITDAY', 'VISITYR', 'NACCDAYS', 'SEX', 'RACE', 'NACCMMSE',
                'NACCTMCI', 'NACCALZD', 'PARK', 'NACCAGE', 'NACCUDSD', 'NACCNE4S', 'NACCVNUM', 'NACCALZD', 'NACCTMCI']

SYMBOL_NC = 1
SYMBOL_MCI = 3
SYMBOL_AD = 4

manufacturer_keys = {
    1: 'GE',
    2: 'Siemens',
    3: 'Phillips',
    5: 'Other',
    8: 'Not applicable / no MRI available',
    9: 'Missing / unknown'
}
tesla_keys = {
    1: '1.5',
    2: '3.0',
    5: 'Other',
    7: 'Field strength varies across images',
    8: 'Not applicable / no MRI available',
    9: 'Missing / unknown'
}


def write_record_to_csv(filename, data):
    header = ['filename', 'diagnosis_id', 'image_id', 'colport', 'status', 'age', 'gender', 'mmse', 'apoe', 'scanner',
              'tesla', 'scan_date']

    file_exists = os.path.isfile(filename)

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)

        if file_exists and os.stat(filename).st_size > 0:
            file.truncate(0)  # 清空文件内容

        writer.writerow(header)  # 写入标题行
        writer.writerows(data)  # 写入内容行


def extract_columns():
    """
    精简ftld表，提取必要的列并生成新的csv文件
    """
    # 读取原始CSV文件
    file_path = "raw_tables/investigator_ftldlbd_nacc61.csv"
    df = pd.read_csv(file_path, usecols=ftld_columns)

    # 重新指定列名的顺序，按照ftld_columns的顺序进行排列
    df = df.reindex(columns=ftld_columns)

    # 生成新的CSV文件
    output_file_path = "raw_tables/investigator_ftldlbd_nacc61_extracted.csv"

    df.to_csv(output_file_path, index=False)


# 根据临床诊断结果和匹配到的MRI记录，生成数据集项
def get_nacc_dataset_record(diagnosis, mr_scan, diagnosis_result):
    record = []  # filename,status,age,gender,mmse,apoe

    filename = str(mr_scan[6]).replace(".zip", '')
    image_id = filename
    diagnosis_id = diagnosis[0]

    if diagnosis_result == SYMBOL_NC:
        status = 'NL'
    if diagnosis_result == SYMBOL_MCI:
        status = 'MCI'
    if diagnosis_result == SYMBOL_AD:
        status = 'AD'

    gender = diagnosis[5]  # SEX
    age = int(mr_scan[5])  # NACCMRIA

    apoe = diagnosis[13]

    mmse = diagnosis[7]  # NACCMMSE

    record.append(filename)
    record.append(diagnosis_id)
    record.append(image_id)
    record.append(diagnosis[14])  # colport(visitnum)

    record.append(status)
    record.append(age)
    record.append(gender)
    record.append(mmse)
    record.append(apoe)

    record.append(manufacturer_keys[mr_scan[16]])  # MRIMANU
    record.append(tesla_keys[mr_scan[15]])  # MRIFIELD
    record.append(mr_scan[-1])  # scan_date

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
    df = pd.read_csv("raw_tables/investigator_mri_nacc61.csv")

    # condition1 = df['PARK'] == 0  # PARK = 0
    condition2 = df['NACCNIFT'] == 1  # NACCNIFT = 1
    condition3 = df['MRIT1'] == 1  # MRIT1 = 1
    condition4 = df['MRIFIELD'].isin([1, 2])  # MRIFIELD = 1 （1代表1.5T）

    condition6 = df['MRIOTHER'] == 1  # MRIOTHER = 1 （Other scan type available）重要条件
    condition7 = df['NACCDICO'] == 1  # NACCDICO = 1
    condition8 = df['NACCMRSA'] == 1  # NACCMRSA = 1

    filtered_df = df[condition2 & condition3 & condition4
                     & condition6 & condition7 & condition8]

    filtered_records = filtered_df.iloc[:, :17].values

    for record in filtered_records:
        subject_id = record[1]

        # 判断该subject_id 是否在字典
        if subject_id not in mr_scan_dictionary:
            mr_scan_dictionary[subject_id] = []

        mr_scan_dictionary[subject_id].append(record)

    return mr_scan_dictionary


"""
从CLINICALDATA数据中，筛选：
条件：DX只能是CN 、MCI 、AD这三种
无帕金森确诊
"""


def get_excluded_diagnosis():
    diagnosis_dictionary = {}
    df = pd.read_csv('raw_tables/investigator_ftldlbd_nacc61_extracted.csv')

    # 定义筛选条件
    condition1 = df['PARK'] == 0  # PARK = 0
    # condition2 = df['NACCNE4S'] != 9  # NACCNE4S != 9
    # condition3 = (df['NACCMMSE'] >= 0) & (df['NACCMMSE'] <= 30)  # 0 <= NACCMMSE <= 30
    condition4 = df['NACCUDSD'].isin([SYMBOL_NC, SYMBOL_MCI, SYMBOL_AD])  # NACCUDSD = 1,3,4
    condition5 = df['NACCVNUM'] == 1  # baseline
    # condition5 = (df['NACCUDSD'] == SYMBOL_MCI) & (df['NACCTMCI'] == 4)
    # condition6 = (df['NACCUDSD'] == SYMBOL_AD) & (df['NACCALZD'] == 0)

    filtered_records = df[condition1 & condition4 & condition5].values
    for record in filtered_records:
        # 若NACCUDSD为4，但NACCALZD为0，则表示是非阿尔茨海默病引起的确诊
        if record[12] == SYMBOL_AD and record[15] == 0:
            continue
        if record[12] == SYMBOL_MCI and record[16] == 9:
            continue

        subject_id = record[0]  # NACCID
        # 判断该subject_id 是否在字典
        if subject_id not in diagnosis_dictionary:
            diagnosis_dictionary[subject_id] = []

        diagnosis_dictionary[subject_id].append(record)
    # key:OAS30042, value: OAS30042_ClinicalData_d0000	 OAS30042 ....
    # key:OAS30042, value: OAS30042_ClinicalData_d0406	 OAS30042 ...
    return diagnosis_dictionary


"""
双向匹配，获取正确的6个月内扫描记录和对应的诊断
每个subject只会选择一条扫描记录和对应的诊断
"""


def match_date_closet(diagnosis, mr_list):
    diagnosis_date = datetime(diagnosis[3], diagnosis[1], diagnosis[2])  # MRIYR MRIMO MRIDY

    date_start = diagnosis_date - timedelta(days=6 * 30)
    date_end = diagnosis_date + timedelta(days=6 * 30)

    for mr_scan in mr_list:
        mr_scan_date = datetime(int(mr_scan[4]), int(mr_scan[2]), int(mr_scan[3]))
        # 若在该区间，则匹配成功
        if date_start <= mr_scan_date <= date_end:
            # 将检查日期也放入mr_scan中
            mr_scan = np.append(mr_scan, diagnosis_date.strftime("%Y-%m-%d"))

            return diagnosis, mr_scan

    return None


def check_for_diagnosis(diagnosis):
    return diagnosis[12]


if __name__ == "__main__":
    not_good_files = get_not_good_filenames('NACC')
    # 首次运行，执行该方法，提取必要的列
    # extract_columns()
    mr_scan_dictionary = get_mr_scan_dict()

    mr_scan_subjects = mr_scan_dictionary.keys()

    diagnosis_dictionary = get_excluded_diagnosis()

    exclude_nacc_list = read_txt_line(
        "raw_tables/exclude_nacc_files.txt")
    exclude_mri_list = read_txt_line(
        "raw_tables/exclude_mri_files.txt")

    # 需要写入数据集文件的列表
    nacc_all_data_list = []
    nacc_data_list = []

    for subject_id, diagnosis_records in diagnosis_dictionary.items():
        diagnosis_record = diagnosis_records[0]  # baseline
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
            dataset_record = get_nacc_dataset_record(target_diagnosis, target_mr_scan, diagnosis_result)

            # 部分mri文件不可用，需要剔除
            # exclude_nacc_files.txt中的为手动挑选的不合格的zip文件
            # exclude_mri_list.txt中的为预处理后不合格的mri文件
            if (dataset_record[0] + "ni.zip") not in exclude_nacc_list and dataset_record[0] not in exclude_mri_list:
                if dataset_record[0] not in not_good_files:
                    nacc_all_data_list.append(dataset_record)

    for _item in nacc_all_data_list:
        write_record_to_csv("nacc_baseline.csv",
                            nacc_all_data_list)
