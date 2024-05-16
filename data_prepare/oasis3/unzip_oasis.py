import os
import shutil
import glob
import gzip

source_dir = "/home/flik/workspace/datasets/OASIS3(archive)"  # 源目录路径
output_dir = "/home/flik/workspace/datasets/OASIS3_raw"  # 输出目录路径
# 获取所有以OAS开头的文件夹
oas_folders = glob.glob(os.path.join(source_dir, "OAS*"))

for oas_folder in oas_folders:
    # 获取当前OAS文件夹下的所有anat文件夹
    anat_folders = glob.glob(os.path.join(oas_folder, "anat*"))
    if not anat_folders:
        continue

    # 根据数字大小对anat文件夹进行排序，并选择第一个文件夹
    sorted_anat_folders = sorted(anat_folders)
    selected_anat_folder = sorted_anat_folders[0]

    # 查找.gz压缩包文件
    gz_files = glob.glob(os.path.join(selected_anat_folder, "*.gz"))
    if not gz_files:
        continue

    # 获取压缩包中的.nii文件路径
    gz_file_path = gz_files[0]
    nii_file_path = os.path.join(selected_anat_folder, os.path.basename(gz_file_path).replace(".gz", ".nii"))

    # 解压缩.gz文件到.nii文件
    with gzip.open(gz_file_path, "rb") as gz_file:
        with open(nii_file_path, "wb") as nii_file:
            shutil.copyfileobj(gz_file, nii_file)

    # 生成新文件名
    new_file_name = os.path.basename(oas_folder) + ".nii"
    output_path = os.path.join(output_dir, new_file_name)

    # 将文件复制到指定目录，并重命名
    shutil.copyfile(nii_file_path, output_path)
    print(f"已提取和重命名文件：{new_file_name}   ")