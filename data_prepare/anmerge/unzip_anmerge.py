import nibabel as nib
import os
import glob
import pandas as pd
import gzip
import shutil
def get_baseline_image_ids():

    return pd.read_csv("anmerge_baseline.csv")['image_id'].tolist()


def unzip_nii_gz(source_directory, target_directory):
    image_ids = get_baseline_image_ids()
    # 确保目标目录存在
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    # 遍历源目录中的所有.nii.gz文件
    for gz_file in glob.glob(os.path.join(source_directory, '*.nii.gz')):
        # # 加载.nii.gz文件
        # nii_image = nib.load(gz_file)

        image_id = gz_file.split('/')[-1].replace('.nii.gz', '')

        if image_id not in image_ids:
            continue

        # 构建目标文件路径
        target_file_path = os.path.join(target_directory, os.path.basename(gz_file).replace('.gz', ''))

        # # 保存为.nii文件
        # nib.save(nii_image, target_file_path)
        # 使用gzip模块打开.gz文件
        with gzip.open(gz_file, 'rb') as f_in:
            # 使用shutil模块将解压后的内容写入新的.nii文件
            with open(target_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Extracted {gz_file} to {target_file_path}")

    print("All files have been extracted.")


# 设置包含.nii.gz文件的源目录
source_directory = ''
# 设置目标目录以存放解压后的.nii文件
target_directory = 'anmerge_unzip'

unzip_nii_gz(source_directory, target_directory)