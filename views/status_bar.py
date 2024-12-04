# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: status_bar.py
# @Software: PyCharm

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QVBoxLayout, QGroupBox
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, QTimer, QDateTime

# status_bar.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("StatusBarWidget")  # 设置 objectName
        self.init_ui()
        self.init_timer()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 用户信息分组
        user_group = QGroupBox("用户信息")
        user_layout = QVBoxLayout()
        self.user_label = QLabel("当前用户: 无")
        self.user_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        user_layout.addWidget(self.user_label)
        self.database_label = QLabel("当前数据库: 无")
        self.database_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        user_layout.addWidget(self.database_label)
        user_group.setLayout(user_layout)

        # 情景状态分组
        scenario_group = QGroupBox("情景状态")
        scenario_layout = QVBoxLayout()
        self.current_scenario_label = QLabel("当前情景: 无")
        self.current_scenario_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        scenario_layout.addWidget(self.current_scenario_label)
        self.owl_status_label = QLabel("OWL 文件状态: 无")
        self.owl_status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        scenario_layout.addWidget(self.owl_status_label)
        self.bayes_status_label = QLabel("贝叶斯网络状态: 无")
        self.bayes_status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        scenario_layout.addWidget(self.bayes_status_label)
        scenario_group.setLayout(scenario_layout)

        # 最后更新时间分组
        time_group = QGroupBox("更新时间")
        time_layout = QVBoxLayout()
        self.last_update_label = QLabel("最后更新时间: 无")
        self.last_update_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        time_layout.addWidget(self.last_update_label)
        time_group.setLayout(time_layout)

        # 添加到主布局
        main_layout.addWidget(user_group)
        main_layout.addWidget(scenario_group)
        main_layout.addWidget(time_group)

        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-size: 14pt;
                font-weight: bold;
                margin-top: 15px;
            }
            QGroupBox::title {
                color: #0066CC;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
            }
            QLabel {
                color: #333;
                font-size: 12pt;
            }
        """)

    def init_timer(self):
        # 初始化定时器，用于动态更新时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新一次

    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.last_update_label.setText(f"最后更新时间: {current_time}")

    def update_status(self, user_name, database_name, scenario_name, owl_status, bayes_status):
        # 更新状态栏内容
        self.user_label.setText(f"当前用户: {user_name}")
        self.database_label.setText(f"当前数据库: {database_name}")
        self.current_scenario_label.setText(f"当前情景: {scenario_name}")
        self.owl_status_label.setText(f"OWL 文件状态: {owl_status}")
        self.bayes_status_label.setText(f"贝叶斯网络状态: {bayes_status}")