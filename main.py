# main.py
import multiprocessing
import sys
import json
import os

from PySide6.QtCore import QTranslator, QCoreApplication
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.main_window import MainWindow
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
    },
    "action-def": {
        "AffectedElement": "    action def Collide {\n        in CollideCondition = true;\n        out DamageCondition = true;\n        out Casualty = true;\n    }\n    action def Spill {\n        out SpillCondition = true;\n        out PullotedCondition = true;\n        out DetachedCondition = true;\n    }\n    action def Explode {\n        out ExplodeCondition = true;\n    }",
        "EnvironmentElement": "",
        "HazardElement": "    action def Collide{\n        in CollideCondition = true;\n        out DamageCondition = true;\n        out Casualty = true;\n    }\n    action def Spill{\n        out SpillCondition = true;\n        out PullotedCondition = true;\n        out DetachedCondition = true;\n    }\n    action def Explode{\n        out ExplodeCondition = true;\n    }",
        "ResponsePlanElement": "    action def Action{\n        out implementationCondition;\n        out startTime;\n        out endTime;\n    }"

    },
    "state-def": {
        "AffectedElement": "    state def AffectedStates{\n        entry; then DrivingState;\n        state DrivingState;\n        accept Collide\n            then CollidedState;\n        state CollidedState;\n        accept Explode\n            then ExplodeState;\n        state ExplodeState;\n    }",
        "EnvironmentElement": "",
        "HazardElement": "    state def HazardStates{\n        entry; then DriveState;\n        state DriveState;\n        accept Collide\n            then CollideState;\n        state CollideState;\n        accept Spill\n            then SpillState;\n        state SpillState;\n    }",
        "ResponsePlanElement": "    state def aidStates{\n        entry; then idleState;\n        state idleState;\n        accept Aid:Action\n            then implementState;\n        state implementState;\n    }\n    state def firefightingStates{\n        entry; then idleState;\n        state idleState;\n        accept FireFighting:Action\n            then implementState;\n        state implementState;\n    }\n    state def towStates{\n        entry; then idleState;\n        state idleState;\n        accept Tow:Action\n            then implementState;\n        state implementState;\n    }\n    state def rescueStates{\n        entry; then idleState;\n        state idleState;\n        accept Rescue:Action\n            then implementState;\n        state implementState;\n    }"
    },
    "emergency_speed": 60,
    "llm": {
        "enable": False,
        "default_model": "DeepSeek-V3",
        "prompt_without_plan_data": "请回答以下应急管理相关问题。如果问题与应急管理无关，请礼貌说明问题不在应急管理领域，并建议用户提出相关问题。用户问题：{user_input}",
        "prompt_with_plan_data": "你是一位应急管理专家。请基于以下信息完成两个任务：1. 首先，判断用户问题是否与应急预案和应急响应相关。如果不相关，请直接回复：'您的问题与应急预案和应急响应无关，请提出相关问题以便我提供专业帮助。'2. 如果相关，请提供两部分回答：- 第一部分：针对用户问题的直接回答 - 第二部分：基于所有预案信息的分析和优化建议当前可用的应急预案信息如下：{plan_data}用户问题：{user_input}请确保回答专业、实用且针对性强。",
        "user_color": "",
        "model_list": [
            {
                "model_name": "ChatGPT-4o",
                "model_version": "gpt-4o",
                "provider": "openai",
                "model_color": "#27AE60",
                "model_api_key": "",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "top_p": 1
                }
            },
            {
                "model_name": "Claude-3.7-Sonnet",
                "model_version": "claude-3-7-sonnet-20250219",
                "provider": "anthropic",
                "model_color": "#9B59B6",
                "model_api_key": "",
                "endpoint": "https://api.anthropic.com/v1/messages",
                "parameters": {
                    "temperature": 0.5,
                    "max_tokens": 1500
                }
            },
            {
                "model_name": "DeepSeek-V3",
                "model_version": "deepseek-chat",
                "provider": "DeepSeek",
                "model_color": "#5DADE2",
                "model_api_key": "",
                "endpoint": "https://api.deepseek.com/chat/completions",
                "parameters": {
                    "temperature": 0.5,
                    "max_tokens": 1500
                }
            }
        ],
        "fallback_policy": "sequential",
        "rate_limit": {
            "requests_per_minute": 60,
            "retry_attempts": 3
        }
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
        print(f"未发现 config.json，准备创建默认配置文件")
        CustomErrorDialog("错误", f"无法连接到数据库：{message}", parent=None).show_dialog()
        sys.exit(1)

    # 启动应用程序的事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()

    if sys.platform.startswith('win'):
        # On Windows, use 'spawn' which is the default anyway
        multiprocessing.set_start_method('spawn', force=True)
    if sys.platform.startswith('win'):
        # This helps hide console windows in subprocesses
        import subprocess
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main(app)

