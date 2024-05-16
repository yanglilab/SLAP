"""
根据数据集的名称，返回不好的文件名列表
"""
import os
import pandas as pd

not_good_csv = "not_good_scans.csv"

def get_not_good_filenames(dataset_name):
    # 读取CSV文件
    df = pd.read_csv(not_good_csv)

    # 筛选出与给定数据集匹配的行
    filtered_df = df[df['dataset'] == dataset_name]

    # 将'filename'列转换为列表并返回
    filenames = filtered_df['filename'].tolist()

    return filenames

# 查找在执行mni152匹配失败后的文件
def find_process_fail_files():
    folder_a = "/media/flik/seagate_basic/alzheimer_dataset/oasis3_unzip"
    folder_b = "/media/flik/seagate_basic/alzheimer_dataset/oasis3_step1"
    # folder_a = "/media/flik/seagate_basic/alzheimer_dataset/nacc_unzip"
    # folder_b = "/media/flik/seagate_basic/alzheimer_dataset/nacc_step1"

    # 获取文件夹A和B中的所有文件名
    files_a = os.listdir(folder_a)
    files_b = os.listdir(folder_b)

    # 将文件名存储在set中
    set_a = set(files_a)
    set_b = set(files_b)

    # 找出存在于文件夹A但不存在于文件夹B的文件
    unique_files = set_a.difference(set_b)

    # 将结果转换为列表并返回
    for fail_file in  list(unique_files):
        print(fail_file)

if __name__ == "__main__":
    pass