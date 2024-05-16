import csv
import pandas as pd
import numpy as np

"""
将需要下载的数据的label写入csv
"""

ALZ_DIAGNOSIS = [
    'AD+Non Neurodegenerative',
    'AD/Vascular',
    'Alzheimer Disease Dementia',
    'Cognitively Normal',
    'Early Onset AD',
    'MCI'
]


path_diagnosis = 'raw_tables/OASIS4_data_clinical.csv'

path_mri_lookup = 'raw_tables/OASIS4_json_information.csv'

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
def extract_days(image_id):
    # OAS30001_ClinicalData_d0370
    return int(image_id.split('d')[1])




# 根据临床诊断结果和匹配到的MRI记录，生成数据集项
#filename,diagnosis_id,image_id,colport,status,age,gender,mmse,apoe,site,race,tesla,sequence,scanner,scan_date
def get_oasis4_dataset_record(diagnosis, mr_scan, diagnosis_result):
    # Create a dictionary with the data
    data = {
        'filename': mr_scan[2].replace('.json', ''),
        'diagnosis_id': diagnosis[1],
        'image_id': mr_scan[1],
        'colport': None,
        'status': diagnosis_result,
        'age': float(diagnosis[3]),
        'gender': 1 if diagnosis[2] == 1 else 0,
        'mmse': None,
        'apoe': None,
        'site': 'CENTRAL05',
        'race': race_key[diagnosis[4]],
        'tesla': mr_scan[17],  # MagneticFieldStrength
        'sequence': mr_scan[37],  # SeriesDescription
        'scanner': mr_scan[31],
        'scan_date': None
    }
    return data

# filename,diagnosis_id,image_id,colport,status,age,gender,mmse,apoe,site,race,tesla,sequence,scanner,scan_date
def write_record_to_csv(record_list, location):
    with open(location, "w", newline='') as f:
        header = ['filename', 'diagnosis_id', 'image_id','colport', 'status', 'age', 'gender',  'mmse', 'apoe', 'site', 'race', 'tesla', 'sequence','scanner','scan_date']

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

    df_mr = pd.read_csv(path_mri_lookup)

    condition1 = df_mr['scan_type'] == "anat"
    condition2 = df_mr['InPlanePhaseEncodingDirectionDICOM'] == "ROW"
    condition3 = df_mr['MRAcquisitionType'] == "3D"
    condition4 = df_mr['filename'].str.contains('T1w')

    df_mr = df_mr[condition1 & condition2 & condition3 & condition4]

    for record in df_mr.values:
        subject_id = record[0]  # subject_id

        # 判断该subject_id 是否在字典
        if subject_id not in mr_scan_dictionary:
            mr_scan_dictionary[subject_id] = []

        mr_scan_dictionary[subject_id].append(record)

    # # 筛选run数字最大的记录
    # for _subject_id, mr_records in mr_scan_dictionary.items():
    #     # 如果只有一个record，则跳过
    #     if len(mr_records) == 1:
    #         continue
    #
    #     # 初始化最大的run number和对应的record
    #     max_run_number = -1
    #     max_run_record = None
    #
    #     for record in mr_records:
    #         # 检查record[4]是否包含"_run-"
    #         if "_run-" in record[2]:
    #             # 提取出_run-后面的数字
    #             run_number = int(record[2].split('_run-')[1].split('_')[0])
    #
    #             # 如果当前的run number大于已知的最大run number，则更新最大的run number和对应的record
    #             if run_number > max_run_number:
    #                 max_run_number = run_number
    #                 max_run_record = record
    #
    #     # 如果找到了最大的run number，则将mr_records更新为只包含最大run number的record的列表
    #     if max_run_record is not None:
    #         mr_scan_dictionary[_subject_id] = [max_run_record]

    return mr_scan_dictionary


def get_excluded_diagnosis():
    diagnosis_dictionary = {}

    filter_columns = [
        'oasis_id', 'demographics_id', 'sex', 'age', 'race', 'final_dx']

    df = pd.read_csv(path_diagnosis,usecols=filter_columns)
    df = df.replace(np.nan, None)

    # 定义筛选条件
    # 筛选与阿尔茨海默病相关的诊断记录
    condition = df['final_dx'].isin(ALZ_DIAGNOSIS)

    filtered_records = df[condition].values

    for record in filtered_records:

        subject_id = record[0]  # oasis_id
        # 判断该subject_id 是否在字典Al
        if subject_id not in diagnosis_dictionary:
            diagnosis_dictionary[subject_id] = []

        diagnosis_dictionary[subject_id].append(record)


    return diagnosis_dictionary



# 判断记录是否在前后6个月内
def check_in_6months(diagnosis, mr_list):

    # 由于仅有单个mri，因此取第0条记录即可
    mr_scan = mr_list[0]

    DAYS_RANGE = 184
    
    _days = abs(extract_days(mr_scan[1]) - 3000) # 所有的诊断基线都从第3000天开始
    
    return _days < DAYS_RANGE


def check_for_diagnosis(diagnosis):
    # 将cdr=0.5标记为MCI
    if diagnosis[5] == 'Cognitively Normal':
        return 'NL'
    elif diagnosis[5] == 'MCI':
        return 'MCI'
    else:
        return 'AD'


if __name__ == "__main__":
    mr_scan_dictionary = get_mr_scan_dict()
    mr_scan_subjects = mr_scan_dictionary.keys()

    diagnosis_dictionary = get_excluded_diagnosis()

    # 需要写入数据集文件的列表
    oasis4_data_list = []

    for subject_id, diagnosis_records in diagnosis_dictionary.items():
        diagnosis_record = diagnosis_records[0]  # 只使用baseline

        # 如果mr记录中没有该subject，则直接跳过
        if subject_id not in mr_scan_subjects:
            continue

        diagnosis_result = check_for_diagnosis(diagnosis_record)

        # 检查mri是否在诊断的前后6个月内
        match = check_in_6months(diagnosis_record, mr_scan_dictionary[subject_id])

        if not match:
            # 未匹配成功
            # print("函数返回了None")
            continue
        else:
            # 匹配成功
            # print("函数返回了数据")
            # 进一步处理返回的数据
            target_diagnosis = diagnosis_record
            target_mr_scan = mr_scan_dictionary[subject_id][0]

            dataset_record = get_oasis4_dataset_record(target_diagnosis, target_mr_scan, diagnosis_result)

            oasis4_data_list.append(dataset_record)

    # 将列表转换为DataFrame
    df_all = pd.DataFrame(oasis4_data_list)

    # 将DataFrame写入CSV文件
    df_all.to_csv('oasis4_baseline.csv', index=False)
