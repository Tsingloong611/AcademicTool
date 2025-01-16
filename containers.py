# -*- coding: utf-8 -*-
# @Time    : 1/15/2025 7:09 PM
# @FileName: containers.py
# @Software: PyCharm
import sys

from dependency_injector import containers, providers
from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QApplication

import json
import os

from controllers.main_controller import MainController
from views.main_window import MainWindow
from database.db_config import DatabaseManager
from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog

import logging


def setup_logger():
    """配置日志记录器"""
    logger = logging.getLogger("ApplicationLogger")
    logger.setLevel(logging.DEBUG)  # 根据需要设置日志级别
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def load_config(config_path):
    """
    加载配置文件。如果不存在，则创建默认配置文件并退出程序。
    """
    DEFAULT_CONFIG = {
        "database": {
            "username": "your_username",
            "password": "your_password",
            "host": "localhost",
            "port": 3306,
            "database": "your_database"
        },
        "i18n": {
            "language": "zh_CN",
            "available_languages": ["en_US", "zh_CN"]
        },
        "gaode-map": {
            "enable": False,
            "javascript_api_key": "",
            "web_service_key": ""
        }
    }

    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
            # 创建对话框实例
            error_dialog = CustomInformationDialog("配置文件创建", f"默认配置文件已创建在 {config_path}。\n请根据需要进行修改后重新启动应用程序。", parent=None)
            error_dialog.show_dialog()
        except Exception as e:
            error_dialog = CustomErrorDialog("配置文件创建失败", f"无法创建配置文件：{e}", parent=None)
            error_dialog.show_dialog()
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            error_dialog = CustomErrorDialog("配置错误", f"解析配置文件失败：{e}", parent=None)
            error_dialog.show_dialog()
            sys.exit(1)

    return config


class Container(containers.DeclarativeContainer):
    """依赖注入容器，管理项目中的所有依赖关系。"""

    # 配置
    config_path = providers.Configuration()

    # 配置加载器
    config_loader = providers.Factory(
        load_config,
        config_path=config_path
    )

    # 日志记录器
    logger = providers.Singleton(setup_logger)

    # 数据库管理器
    db_manager = providers.Factory(
        DatabaseManager,
    )

    # 控制器
    main_controller = providers.Factory(
        MainController,
        db_manager=db_manager,
        logger=logger
    )

    # 翻译器
    translator = providers.Factory(
        QTranslator
    )

    # 自定义对话框
    custom_error_dialog = providers.Factory(
        CustomErrorDialog
    )

    custom_information_dialog = providers.Factory(
        CustomInformationDialog
    )

    # 主窗口视图
    main_window = providers.Factory(
        MainWindow,
        controller=main_controller,
        db_manager=db_manager,
        translator=translator,
        logger=logger,
        custom_error_dialog=custom_error_dialog,
        custom_information_dialog=custom_information_dialog
    )