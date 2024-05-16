"""
将下载后的数据与csv数据匹配
删除没有T1w的记录
"""
import csv
import os
import shutil
def get_csv_list():
    record_list = []
    with open("../../lookupcsv/OASIS3.csv", 'r') as file:
        reader = csv.reader(file)

        header = next(reader)

        for record in reader:
            record_list.append(record[0])

    return record_list

def get_mr_scan_list():
    with open('raw_tables/OASIS3_MR_json.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)
        # 定义筛选条件
        # MagneticFieldStrength = 1.5 && scan category = T1W
        filter_condition = lambda row: float(row[7]) == 3 and row[4] == 'T1w'

        # 使用列表推导式筛选记录
        filtered_records = [row for row in reader if filter_condition(row)]
        return list(filtered_records)


def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
        print(f"文件夹 {folder_path} 删除成功")
    except OSError as e:
        print(f"文件夹 {folder_path} 删除失败：{e}")

def traverse_folders(root_folder):
    folders = []
    for folder_name in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, folder_name)
        if os.path.isdir(folder_path):
            folders.append(folder_path)
    return folders

# 删除小于55岁的人
def delete_young_record():
    # 指定要遍历的目录路径
    directory_path = '/home/flik/workspace/datasets/OASIS3'

    traverse_folders(directory_path)
    record_list = get_csv_list()
    folders = traverse_folders()
    for folder in folders:
        # print(f"遍历到文件夹：{folder_path}")
        label = folder.split('/')[-1]
        if label not in record_list:
            delete_folder(folder)

"""
下载下的数据中有些不包含T1w
将这部分数据在dataset记录中删除
"""
def delete_noT1w_record():
    directory_path = '/home/flik/workspace/datasets/OASIS3'
    oasis_csv_path = '../../lookupcsv/OASIS3.csv'
    dataset_records = get_csv_list()
    folders = traverse_folders(directory_path)

    for folder_idx in range(len(folders)):
        folders[folder_idx] = folders[folder_idx].split('/')[-1]


    delete_records = []
    for record in dataset_records:
        if record not in folders:
            delete_records.append(record)

    # 打开CSV文件并读取数据
    with open(oasis_csv_path, 'r') as file:
        reader = csv.reader(file)

        header = next(reader)

        data = list(reader)

    # 遍历数据并删除符合条件的行
    filtered_data = [row for row in data if row[0] not in delete_records]

    #保存修改后的数据回CSV文件
    with open(oasis_csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(filtered_data)

# 检查文件名中没有“run-0x”的扫描图像质量
def check_no_runtask_scan():
    dataset_records = get_csv_list()
    mr_scan_records = get_mr_scan_list()

    with open("../../lookupcsv/OASIS3.csv", 'r') as file:
        reader = csv.reader(file)
        next(reader)

        for record in dataset_records:
            for mr_scan in mr_scan_records:
                if record == mr_scan[1]:
                    if "run-" not in mr_scan[5]:
                        print(mr_scan)

#delete_noT1w_record()
check_no_runtask_scan()