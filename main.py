# main.py

import sys
import json
import os

from PySide6.QtCore import QTranslator, QCoreApplication
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.main_window import MainWindow
# from views.login_dialog import LoginDialog
from database.db_config import DatabaseManager

# 定义默认配置
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


def create_default_config(config_path):
    """
    如果配置文件不存在，创建一个默认配置文件，并提示用户进行修改。
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)

        CustomInformationDialog("配置文件创建", f"默认配置文件已创建在 {config_path}。\n请根据需要进行修改后重新启动应用程序。").exec_()
    except Exception as e:
        CustomErrorDialog("配置文件创建失败", f"无法创建配置文件：{e}", parent=None).show_dialog()
    sys.exit(1)


def load_config(config_path='config.json'):
    """
    加载配置文件。如果不存在，则创建默认配置文件并退出程序。
    """
    if not os.path.exists(config_path):
        create_default_config(config_path)

    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            CustomErrorDialog("配置错误", f"解析配置文件失败：{e}", parent=None).show_dialog()
            sys.exit(1)

    return config


def setup_i18n(app, i18n_config):
    """
    设置国际化选项。
    """
    language = i18n_config.get("language", "en_US")
    available_languages = i18n_config.get("available_languages", ["en_US", "zh_CN"])

    translator = QTranslator()
    translation_file = f"translations/translations_{language}.qm"

    if language not in available_languages:
        language = "zh_CN"  # 默认语言

    if os.path.exists(translation_file):
        if translator.load(translation_file):
            app.installTranslator(translator)
        else:
            print(f"无法加载翻译文件：{translation_file}")
    else:
        print(f"翻译文件不存在：{translation_file}")

    return translator


def main(app):
    """
    主函数，初始化应用程序，加载配置，连接数据库并启动主窗口。
    """
    # 设置宋体九号
    app.setFont("宋体,9")

    # 加载配置文件
    config = load_config()

    # 设置国际化
    translator = setup_i18n(app, config.get("i18n", {}))

    # 初始化数据库管理器
    db_manager = DatabaseManager()

    # 获取数据库配置
    db_config = config.get("database", {})
    username = db_config.get("username")
    password = db_config.get("password")
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 3306)
    database = db_config.get("database")

    # 验证数据库配置是否完整
    if not all([username, password, host, port, database]):
        CustomErrorDialog("配置错误", "数据库配置信息不完整。", parent=None).show_dialog()
        sys.exit(1)

    # 尝试连接数据库
    success, message = db_manager.connect(
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    if success:
        window = MainWindow(db_manager)
        window.showMaximized()
    else:
        CustomErrorDialog("错误", f"无法连接到数据库：{message}", parent=None).show_dialog()
        sys.exit(1)

    # 启动应用程序的事件循环
    sys.exit(app.exec())


if __name__ == '__main__':
    # 创建 QApplication 实例
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 设置全局样式

    # 调用主函数，并传递 QApplication 实例
    main(app)
