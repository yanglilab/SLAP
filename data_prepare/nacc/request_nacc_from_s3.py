import boto3
import time
import pandas as pd
from tqdm import tqdm
from botocore.config import Config

BUCKET_NAME = ""

ACCESS_KEY_ID = ""
SECRET_ACCESS_KEY = ""

# 注意: 必须DEBUG检查访问路径，否则可能会出现权限错误
# 访问路径固定为下值
REMOTE_DIRECTORY_PATH = ""  # nifit路径
STORE_DIRECTORY_PATH = ""  # 本地存储路径

REGION = ""


class ProgressPercentage(object):
    def __init__(self, filename, filesize):
        self._filename = filename
        self._size = filesize
        self._seen_so_far = 0
        self._start_time = time.time()
        self._last_print_time = time.time()

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        current_time = time.time()
        if current_time - self._last_print_time > 1:  # 更新打印间隔为1秒
            percentage = (self._seen_so_far / self._size) * 100
            elapsed_time = current_time - self._start_time
            speed = (self._seen_so_far / elapsed_time) / 8  # 以Bytes/s为单位
            print(f"\r{self._filename}: {percentage:.2f}% downloaded, Speed: {speed/1024:.2f} kBytes/s", end="")
            self._last_print_time = current_time



def save_file_names(response):
    # 追加写入
    with open("nacc_file_names.txt", "a") as f:
        for item in response['Contents']:
            name = item['Key'].split("/")[-1]
            f.write(name + "\n")
        f.close()


def save_not_exist_files(list):
    with open("nacc_not_exist.txt", "w") as f:
        for item in list:
            f.write(item + "\n")
        f.close()


def get_file_name_list():
    file_name_list = []
    with open("nacc_file_names.txt", "r") as f:
        for line in f:
            line = line.strip("\n")
            file_name_list.append(line)

        f.close()
    return file_name_list


def list_all_object():
    # 创建 S3 客户端并设置凭据
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY_ID, aws_secret_access_key=SECRET_ACCESS_KEY,
                      region_name=REGION)

    # 列出 S3 存储桶中指定文件夹下的所有文件
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=REMOTE_DIRECTORY_PATH)

    # 输出文件列表
    if 'Contents' in response:
        print("查询出第1页数据")
        save_file_names(response)
        # 如果结果集数量小于 1000，则已经获取到全部结果，退出循环
        if response['IsTruncated'] == False:
            print('获取到全部结果！')
            exit()
        # 如果结果集数量达到 1000，则需要继续请求

        while response['IsTruncated']:
            # 设置 Marker 参数，以便在下次请求时从上一次请求结束处继续获取
            marker = response['Contents'][-1]['Key']

            print("继续发送API中")
            # 继续发送 API 请求
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=REMOTE_DIRECTORY_PATH, StartAfter=marker)
            save_file_names(response)


def check_needs_in_bucket():
    # 获取baseline待下载的数据
    pd_nacc_baseline = pd.read_csv("nacc_baseline.csv")
    filenames = pd_nacc_baseline["filename"].tolist()

    # 获取之前已经下载好的数据
    downloaded_files = pd.read_csv("NACC.csv")["filename"].tolist()

    file_name_list = get_file_name_list()

    # 能下载的数据
    real_needs = []
    not_exist = []
    # 遍历nacc_baseline.csv的filename
    for filename in filenames:
        # real_zip_name = filename.replace(".zip","ni.zip")
        real_zip_name = filename + "ni.zip"

        if real_zip_name not in file_name_list:
            # 若数据不存在于bucket
            not_exist.append(filename)

        else:
            # 若数据存在于bucket，则进一步判断是否已经在之前下载好的旧数据集中
            if filename not in downloaded_files:
                real_needs.append(real_zip_name)
            else:
                print(f"{real_zip_name}已经下载过")
    save_not_exist_files(not_exist)
    return real_needs


def remove_downloaded(filename, txt_path):
    with open(txt_path, "r") as f:
        lines = f.readlines()
    with open(txt_path, "w") as f:
        for line in lines:
            if line.strip("\n") != filename:
                f.write(line)


if __name__ == "__main__":
    # # 预操作，获取可供下载的mri压缩包
    # check_needs_in_bucket()
    my_config = Config(
        region_name=REGION,
        proxies={
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }
    )
    # 创建 S3 客户端并设置凭据
    s3 = boto3.client('s3',
                      aws_access_key_id=ACCESS_KEY_ID,
                      aws_secret_access_key=SECRET_ACCESS_KEY,
                      config=my_config
                      )

    # real_needs = check_needs_in_bucket()
    # # 将real_needs写入txt文件
    # real_needs_txt = "download_list.txt"
    #
    # with open(real_needs_txt, "w") as file:
    #     for item in real_needs:
    #         file.write("%s\n" % item)

    "----------------------------------------------"
    real_needs_txt = "download_list.txt"
    real_needs = []
    with open(real_needs_txt, "r") as f:
        lines = f.readlines()
        for line in lines:
            real_needs.append(line.strip("\n"))

    for file_name in tqdm(real_needs, desc="Downloading files", unit="file"):
        print("开始下载：{}".format(file_name))

        file_key = f'{REMOTE_DIRECTORY_PATH}/{file_name}'
        store_key = f'{STORE_DIRECTORY_PATH}/{file_name}'

        # 获取文件大小
        response = s3.head_object(Bucket=BUCKET_NAME, Key=file_key)
        filesize = response['ContentLength']

        # 下载文件
        s3.download_file(BUCKET_NAME, file_key, store_key, Callback=ProgressPercentage(file_name, filesize))
        print('{}下载完成'.format(file_name))

        # 从txt文件中移除已下载的文件名
        remove_downloaded(file_name, real_needs_txt)
