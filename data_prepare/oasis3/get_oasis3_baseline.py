import csv
import pandas as pd
import numpy as np
from data_prepare.not_good_files import get_not_good_filenames
"""
将需要下载的数据的label写入csv
"""
count_trans = 0
SYMBOL_NC = 'Cognitively normal'
SYMBOL_AD = 'AD Dementia'
SYMBOL_MCI = 'uncertain dementia'

path_diagnosis = 'raw_tables/OASIS3_ADRC_ClinicalData.csv'

race_key = {
    1: 'White',
    2: 'Black or African American',
    3: 'American Indian or Alaska Native',
    4: 'Native Hawaiian or Other Pacific Islander',
    5: 'Asian',
    50: 'Other (specify)',
    99: '99 = Unknown'
}


# 从id中提取天数
def extract_days(clinical_id):
    # OAS30001_ClinicalData_d0370
    return int(clinical_id.split('d')[1])


# 根据身高判断性别 以补充数据
def predict_sex_by_height(height):
    return 2 if int(height) < 70 else 1


# 将临床数据id匹配至UDS表中，以获取性别
def extract_sex_and_race(diagnosis):
    clinical_id = diagnosis[0]
    # OAS30001_ClinicalData_d0722 -> OAS30001_UDSa2_d0722
    session_label = clinical_id.replace('ClinicalData', 'UDSa2')
    df = pd.read_csv('raw_tables/OASIS3_UDSa2_cs_demo.csv')

    filtered_rows = df[df['OASIS_session_label'] == session_label]

    if len(filtered_rows) > 0:
        record = filtered_rows.values[0]
        return record[4], record[7]
    else:
        return None


# 根据临床诊断结果和匹配到的MRI记录，生成数据集项
def get_oasis3_dataset_record(diagnosis, mr_scan, diagnosis_result):
    age_at_entry = float(diagnosis[5])  # ageAtEntry

    if diagnosis_result == SYMBOL_NC:
        _status = 'NL'
    elif diagnosis_result == SYMBOL_MCI:
        _status = 'MCI'
    else:
        _status = 'AD'

    # gender
    extracted = extract_sex_and_race(diagnosis)
    _gender, _race = None, None

    if extracted:
        gender, race = extracted
        _gender = gender
        # race
        if np.isnan(race):
            _race = None
        else:
            _race = race_key[race]  # 1 = White 2 = Black or African American 3 = American Indian or Alaska Native
                            # 4 = Native Hawaiian or Other Pacific Islander
                            # 5 = Asian
                            # 50 = Other (specify)
                            # 99 = Unknown

    # 创建记录
    record = {
        'filename': mr_scan[5].replace(".json", ""),
        'diagnosis_id': diagnosis[0],
        'image_id': mr_scan[1],
        'colport': None,
        'status': _status,
        'age':  int((extract_days(mr_scan[1]) / 366) + age_at_entry),
        'gender': _gender,
        'mmse': diagnosis[4],
        'apoe': None or str(diagnosis[18]).count('4'),# 34 means apoe4 is positive (1)
        'site': None,
        'race': _race,
        'tesla': mr_scan[7],
        'sequence': None,
        'scanner': mr_scan[8],
        'scan_date': None
    }

    return record




def write_record_to_csv(record_list, location):
    with open(location, "w", newline='') as f:
        header = ['filename', 'diagnosis_id', 'image_id', 'status', 'age', 'gender', 'race', 'mmse', 'apoe', 'site',  'tesla', 'scanner']

        writer = csv.writer(f)
        writer.writerow(header)

        for record in record_list:
            writer.writerow(record)


"""
筛选mr_scan记录，MagneticFieldStrength = 1.5 && scan category = T1W
并将记录存入字典，
key:subject_id
value:相同subject_id的记录数组
"""


def get_mr_scan_dict():
    mr_scan_dictionary = {}

    df_mr = pd.read_csv('raw_tables/OASIS3_MR_json.csv')

    condition1 = df_mr['scan category'] == 'T1w'  # T1w

    filtered_records = df_mr[condition1].values

    for record in filtered_records:
        subject_id = record[0]  # subject_id

        # 判断该subject_id 是否在字典
        if subject_id not in mr_scan_dictionary:
            mr_scan_dictionary[subject_id] = []

        mr_scan_dictionary[subject_id].append(record)

    return mr_scan_dictionary


"""
从ADRCCLINICALDATA数据中，筛选：
dx1 = Cognitively normal 或者 AD Dementia
条件：只能是Cognitively normal 、 Cognitively normal -->  AD Dementia 、 AD Dementia 这三种
"""


def get_excluded_diagnosis():
    diagnosis_dictionary = {}
    df = pd.read_csv(path_diagnosis)
    df = df.replace(np.nan, None)

    # 定义筛选条件
    # baseline
    condition1 = df['ADRC_ADRCCLINICALDATA ID'].str.endswith('d0000')
    condition2 = df['dx1'].isin([SYMBOL_NC, SYMBOL_MCI, SYMBOL_AD])  # AD,MCI,Dementia

    filtered_records = df[condition1 & condition2].values

    for record in filtered_records:

        subject_id = record[1]  # Subject
        # 判断该subject_id 是否在字典
        if subject_id not in diagnosis_dictionary:
            diagnosis_dictionary[subject_id] = []

        diagnosis_dictionary[subject_id].append(record)
    # key:126_S_0605, value: 605	ADNI1	ADNI1	126_S_0605...
    # key:126_S_0605, value: 605	ADNI1	ADNI1	126_S_0605...
    return diagnosis_dictionary


"""
查找举例baseline最近的扫描记录
"""


def match_date_closet(diagnosis, mr_list):
    DAYS_RANGE = 184

    diagnosis_days = extract_days(diagnosis[0])

    date_start = (diagnosis_days - DAYS_RANGE) if diagnosis_days >= DAYS_RANGE else 0
    date_end = (diagnosis_days + DAYS_RANGE)

    for mr_scan in mr_list:
        mr_scan_days = extract_days(mr_scan[1])
        # 若在该区间，则匹配成功
        if date_start <= mr_scan_days <= date_end:
            return diagnosis, mr_scan

    return None


def check_for_diagnosis(diagnosis):
    global count_trans
    # 将cdr=0.5标记为MCI
    if diagnosis[6] == 0.5:
        if diagnosis[8] == SYMBOL_AD:
            count_trans += 1
        return SYMBOL_MCI
    else:
        return diagnosis[8]


if __name__ == "__main__":
    not_good_files = get_not_good_filenames('OASIS3')


    mr_scan_dictionary = get_mr_scan_dict()
    mr_scan_subjects = mr_scan_dictionary.keys()

    diagnosis_dictionary = get_excluded_diagnosis()

    # 需要下载的mr label 列表
    download_scan_list = []

    # 需要写入数据集文件的列表
    oasis3_data_list = []

    for subject_id, diagnosis_records in diagnosis_dictionary.items():
        diagnosis_record = diagnosis_records[0]  # 只使用baseline

        # 如果mr记录中没有该subject，则直接跳过
        if subject_id not in mr_scan_subjects:
            continue

        diagnosis_result = check_for_diagnosis(diagnosis_record)

        # 匹配诊断时间和扫描时间最接近的记录
        # 双向匹配
        # 例如： 某个subject的诊断记录有3条，分别为d0000,d0300,d1000
        # 则他们需要匹配的mr记录的日期范围分别为 [d000,d183] , [d117,d483] ,[d0817,d1183]
        # 在mr记录中寻找是否存在 在这些时间范围内扫描的mr
        # 若存在，则匹配成功

        select_diagnosis_records = []
        selected_mr_scans = mr_scan_dictionary[subject_id]

        # 将诊断结果与mri记录进行双向匹配
        match = match_date_closet(diagnosis_record, selected_mr_scans)

        if match is None:
            # 未匹配成功
            # print("函数返回了None")
            continue
        else:
            # 匹配成功
            # print("函数返回了数据")
            # 进一步处理返回的数据
            target_diagnosis, target_mr_scan = match
            # print(target_diagnosis)
            # print(target_mr_scan)
            # 将MR_label存在代下载的列表
            download_scan_list.append([target_mr_scan[1]])
            # 生成dataset记录
            dataset_record = get_oasis3_dataset_record(target_diagnosis, target_mr_scan, diagnosis_result)

            if dataset_record['filename'] not in not_good_files:
                oasis3_data_list.append(dataset_record)

    # 将列表转换为DataFrame
    df_all = pd.DataFrame(oasis3_data_list)

    # 将DataFrame写入CSV文件
    df_all.to_csv("OASIS3_baseline.csv", index=False)
