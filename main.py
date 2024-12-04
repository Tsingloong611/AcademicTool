# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:09 AM
# @FileName: main.py
# @Software: PyCharm

import sys

from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from controllers.scenario_controller import ScenarioController
from database.db_config import Base, engine, SessionLocal
from models.scenario import Scenario

def main():
    # 创建所有表
    Base.metadata.create_all(engine)

    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)  # 使用微软雅黑或其他清晰字体
    font.setHintingPreference(QFont.PreferNoHinting)  # 避免字体模糊
    font.setStyleStrategy(QFont.PreferAntialias)      # 抗锯齿
    app.setFont(font)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)  # 启用高 DPI 支持
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)  # 使图标适配高 DPI

    # 创建主窗口
    window = MainWindow()

    # 获取情景管理器、状态栏和标签页实例
    scenario_manager = window.scenario_manager
    status_bar = window.status_bar_widget
    tab_widget = window.tab_widget

    db = SessionLocal()

    # 创建控制器并连接
    controller = ScenarioController(scenario_manager, status_bar, tab_widget,db)


    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()