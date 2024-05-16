import os
import shutil
import glob
import gzip
import pandas as pd


# 获取下载失败的文件列表，并写入"download_fail_scan.csv"
def get_fail_downloaded_files(src_dir):
    downloaded_files = os.listdir(src_dir)
    download_fail_files = []
    with open("download_selected_scan.csv", "r") as dl_file:
        for _file_name in dl_file:
            file_name = _file_name.replace("\n", "")
            if file_name not in downloaded_files:
                download_fail_files.append(file_name)

    with open("download_fail_scan.csv", "w") as download_fail_scan:
        for fail_file in download_fail_files:
            download_fail_scan.write(fail_file + "\n")


# 导出OASIS3_baseline.csv中的filename列表，如#sub-OAS30001_ses-d0129_run-02_T1w.nii
def get_selected_nii_filename():
    df_oasis3_baseline = pd.read_csv("OASIS3_baseline.csv")
    _filename_list = df_oasis3_baseline["filename"].tolist()
    return _filename_list


# 根据OASIS3_baseline.csv中的filename，从source文件夹中挑选nii
def select_nii_from_baseline_csv(source_dir, output_dir):
    filename_list = get_selected_nii_filename()
    all_files = []  # 620个文件

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".nii.gz"):
                archived_file_name = file.replace(".nii.gz", ".nii")
                # 判断是否是要找的文件
                if archived_file_name in filename_list:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
                    unzip_nii(file_path)  # 解压至指定目录


def unzip_nii(input_nii_path):
    # 定义输入和输出路径
    output_directory = '/home/flik/workspace/datasets/OASIS3_out'

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
    source = "/home/flik/workspace/datasets/OASIS3_archive"  # 源目录路径
    output = "/home/flik/workspace/datasets/OASIS3_out"  # 输出目录路径
    # get_fail_downloaded_files(source_dir)
    # select_nii_from_baseline_csv(source, output)

