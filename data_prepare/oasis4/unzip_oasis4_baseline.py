import os
import shutil
import glob
import gzip
import pandas as pd


# 导出OASIS3_baseline.csv中的filename列表，如#sub-OAS30001_ses-d0129_run-02_T1w.nii
def get_selected_nii_filename():
    df_oasis4_baseline = pd.read_csv("oasis4_baseline.csv")
    _filename_list = df_oasis4_baseline["filename"].tolist()
    return _filename_list


# sub-OAS42120_sess-d3028_run-01_T1w（无法下载）（已删除）
# sub-OAS42212_sess-d3011_run-01_T1w（成像质量差）（已删除）
# sub-OAS42345_sess-d3000_run-01_T1w（未下载）（已重新下载并手动放入）
# sub-OAS42392_sess-d3012_run-01_T1w（未下载）（已重新下载并手动放入）
# sub-OAS42460_sess-d3056_run-01_T1w（未下载）（已重新下载并手动放入）
# 应有349条记录
def select_nii_from_baseline_csv(source_dir):
    filename_list = get_selected_nii_filename()
    all_files = []

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".nii.gz"):
                archived_file_name = file.replace(".nii.gz", "")
                # 判断是否是要找的文件
                if archived_file_name in filename_list:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
                    unzip_nii(file_path)  # 解压至指定目录
                    filename_list.remove(archived_file_name)


    for remaining_file in filename_list:
        print(remaining_file)

def unzip_nii(input_nii_path):
    # 定义输入和输出路径
    output_directory = '/media/flik/seagate_basic/alzheimer_dataset/oasis4_unzip_n'

    # 获取文件名
    file_name = os.path.basename(input_nii_path)

    # 将 nii.gz 文件解压到指定目录
    with gzip.open(input_nii_path, 'rb') as f_in:
        with open(os.path.join(output_directory, file_name.replace('.nii.gz', '.nii')), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    # # 重命名解压后的文件
    # new_file_path = os.path.join(output_directory, file_name.replace('.nii.gz', '.nii'))
    # os.rename(os.path.join(output_directory, file_name), new_file_path)


if __name__ == "__main__":
    source = "/media/flik/seagate_basic/alzheimer_dataset/oasis4"  # 源目录路径
    # get_fail_downloaded_files(source_dir)
    select_nii_from_baseline_csv(source)

