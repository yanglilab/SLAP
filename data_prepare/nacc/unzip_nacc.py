import re
import zipfile
import os
import csv
import json

# 定义要匹配的模式列表，按照优先级顺序排列
series_patterns = ["3D_SAG", "MPRAGE", "MP-RAGE", "FSPGR", "SPGR", "COR_GRADIENT_T1", "3D_CORO_T1",
                   "3D_Saggital_T1", "3DT1_CORON", "3D_CORONAL", "RAGE_REPEAT", "t1_mpr", "MPRAGE_GRAPPA2",
                   "T1w_MPR", "FSPGR_COR_3D", "3D_Coronal_T1", "SAG_3D_MPR", "SAG_MPR_ISO"]

"""
1.从nacc原格式的zip文件中，寻找SAG或者FSPGR序列的图像nii
2.该nii文件重命名为NACC.csv中对应的文件名（去除"_"后的部分）,并解压至NACC_raw文件夹
3.修改NACC.csv记录中的文件名
"""


def unzip_nacc_raw():
    # 指定要解压的zip文件所在的文件夹
    zip_folder = "/media/flik/seagate_basic/alzheimer_dataset/nacc"
    out_folder = "/media/flik/seagate_basic/alzheimer_dataset/nacc_unzip"
    # 遍历zip文件夹下的所有zip文件
    for file_name in os.listdir(zip_folder):
        # 该变量用来判断该zip文件中是否有指定扫描序列的nii文件
        found_current_nii = False

        if file_name.endswith(".zip"):
            # 获取zip文件的路径
            zip_path = os.path.join(zip_folder, file_name)
            # 打开zip文件并解压到当前文件夹下
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 遍历该zip文件
                for sub_file_name in zip_ref.namelist():
                    if sub_file_name.endswith(".json") and not found_current_nii:
                        # series_description = extract_series_from_json(sub_file_name)
                        # 在zip中打开该json文件
                        with zip_ref.open(sub_file_name) as json_file:
                            # 部分json可能解析失败，这里需要捕获异常
                            try:
                                json_data = json.load(json_file)
                                # 获取SeriesDescription字段值
                                series_description = json_data.get('SeriesDescription')
                            except Exception as e:
                                print("文件{}的{}解析失败".format(file_name, sub_file_name))
                                series_description = None
                        if series_description is not None:
                            for series in series_patterns:
                                if re.search(series, series_description):
                                    # 同一个扫描文件的nii与json文件名相同
                                    # 获取该扫描文件
                                    nii_file_name = sub_file_name.replace(".json", ".nii")
                                    # 将该文件解压至out_folder
                                    zip_ref.extract(nii_file_name, out_folder)
                                    # 修改nii文件名 (1.3.6.1.4.1.5962.99.1.1182900812.2138722620.1482946650700.188.0_i00001.nii ----> mri6514.nii)

                                    os.rename(os.path.join(out_folder, nii_file_name),
                                              os.path.join(out_folder, file_name.replace("ni.zip", ".nii")))
                                    # print("修改文件{}--->{}".format(os.path.join(out_folder, sub_file_name),
                                    #                                 os.path.join(out_folder,
                                    #                                              file_name.replace("ni.zip", ".nii"))))

                                    # 写入NACC.csv
                                    match_record(file_name)
                                    found_current_nii = True
                                    break

            if found_current_nii:
                continue
            else:
                print("{}没有发现合适的序列文件".format(file_name))


def extract_series_from_json(json_path):
    try:
        with open(json_path) as json_file:
            json_data = json.load(json_file)
            series_description = json_data.get('SeriesDescription')

            return series_description  # or None

    except json.JSONDecodeError:
        print(f"文件内容不是合法的JSON格式：{json_path}")

    except KeyError:
        print("JSON数据中缺少SeriesDescription字段。")


"""
根据nacc的zip文件名称，匹配NACC.csv中对应的属性值
并将结果写入新的NACC_custom.csv
例如：mri1266ni.zip -----> mri1266ni_s002a1000 -> mri1266
"""


def match_record(zip_name):
    zip_name = zip_name.replace("ni.zip", "")
    with open("nacc_baseline.csv", "r") as f:
        f_csv = csv.reader(f)
        headers = next(f_csv)
        for row in f_csv:

            # if zip_name == row[0].split("_")[0]:
            if zip_name == row[0]:
                row[0] = zip_name
                # 将改行写入新的NACC.csv文件中
                save_record_to_csv(row)
                break


def save_record_to_csv(new_row):
    with open("NACC_baseline.csv", "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(new_row)

        # print("写入：{}".format(new_row))


if __name__ == "__main__":
    pass
