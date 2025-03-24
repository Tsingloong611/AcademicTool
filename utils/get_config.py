# -*- coding: utf-8 -*-
# @Time    : 2025/3/8 19:23
# @FileName: get_config.py
# @Software: PyCharm

import os
import sys
import json

def get_cfg():
    # 获取当前文件的绝对路径
    current_path = os.path.abspath(__file__)
    # 获取当前文件的父目录
    father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
    # 获取父目录的父目录
    father_father_path = os.path.abspath(os.path.dirname(father_path) + os.path.sep + ".")
    # 获取配置文件的路径
    config_file_path = os.path.join(father_father_path, "config.json")
    # 读取配置文件
    with open(config_file_path, "r", encoding='utf-8') as f:
        config = json.load(f)
    return config

