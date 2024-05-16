import os
import shutil

# the output path like "/home/flik/workspace/datasets/ADNI_out"
path_adni_out = ""


def rename_to_image_id():
    # 遍历源文件夹下的所有文件和文件夹
    for root, dirs, files in os.walk(path_adni_out):
        # 遍历当前文件夹下的所有文件

        for file in files:
            allowed_suffix = [".jpg", ".npy"]
            suffix = '.' + file.split(".")[1]
            if suffix not in allowed_suffix:
                continue

            if file.startswith("ADNI_"):
                file_id = file.split(suffix)[0].split("_")[-1]
                source_path = os.path.join(root, file)
                target_path = os.path.join(root, file_id + suffix )
                os.rename(source_path, target_path)



if __name__ == '__main__':
    rename_to_image_id()