
"""
Author: guozq

Create Date: 2022/5/20

Description:

"""
import pandas as pd
import numpy as np
import os
import datetime
import csv
from typing import Dict, List, Set, Tuple, Type, Any, Callable

from btc_model.core.util.hash_util import HashUtil
from btc_model.core.util.file_util import FileUtil
from btc_model.core.util.io_util import io_pickle

from btc_model.core.common.const import PROJECT_NAME

class FileCacheUtil:

    @staticmethod
    def load_cached_data(params: List[str]):
        """

        """
        hash_str = HashUtil.get_hash_str(params)
        file_dir = str(FileUtil.get_project_dir(project_name=PROJECT_NAME, sub_dir='cache'))
        file_path = file_dir + f'/{hash_str}.cache'

        if os.path.exists(file_path):
            cached_data = io_pickle.load_file(file_path)
            return cached_data, file_path, '|'.join(params)
        else:
            return None, file_path, '|'.join(params)

    @staticmethod
    def save_cached_data(file_path: str, file_desc: str, object_to_save):
        """

        """
        io_pickle.save_file(object_to_save, file_path)

        # 定义说明文件的路径
        desc_file_path = os.path.dirname(file_path) + '/file_desc.csv'

        # 检查说明文件是否存在，如果不存在则创建并写入表头
        if not os.path.exists(desc_file_path):
            with open(desc_file_path, mode='w', newline='') as csvfile:
                fieldnames = ['file_name', 'desc', 'modify_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

        with open(desc_file_path, mode='a', newline='') as csvfile:
            fieldnames = ['file_name', 'desc', 'modify_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # 写入文件路径和描述信息
            writer.writerow({'file_name': os.path.basename(file_path),
                             'desc': file_desc,
                             'modify_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                             })