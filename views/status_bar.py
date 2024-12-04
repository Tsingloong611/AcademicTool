# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: status_bar.py
# @Software: PyCharm

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer, QDateTime


class StatusBar(QWidget):
    """
    自定义状态栏，用于显示用户信息、情景状态（包括描述和更新时间）。
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("StatusBarWidget")  # 设置 objectName 以便样式表应用
        self.init_ui()

        self.setFixedHeight(200)  # 固定高度

    def init_ui(self):
        """
        初始化用户界面组件。
        """
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 减少整体边距
        main_layout.setSpacing(10)  # 减少整体间距

        # 用户信息分组
        user_group = QGroupBox("用户信息")
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(5, 5, 5, 5)  # 减少分组内边距
        user_layout.setSpacing(5)  # 减少分组内间距

        self.user_label = QLabel("当前用户: 无")
        self.user_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # 减小字体
        user_layout.addWidget(self.user_label)

        self.database_label = QLabel("当前数据库: 无")
        self.database_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # 减小字体
        user_layout.addWidget(self.database_label)

        user_group.setLayout(user_layout)

        # 情景状态分组
        scenario_group = QGroupBox("情景状态")
        scenario_layout = QVBoxLayout()
        scenario_layout.setContentsMargins(5, 5, 5, 5)  # 减少分组内边距
        scenario_layout.setSpacing(5)  # 减少分组内间距

        self.current_scenario_label = QLabel("当前情景: 无")
        self.current_scenario_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # 减小字体
        scenario_layout.addWidget(self.current_scenario_label)

        self.owl_status_label = QLabel("OWL 文件状态: 无")
        self.owl_status_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # 减小字体
        scenario_layout.addWidget(self.owl_status_label)

        self.bayes_status_label = QLabel("贝叶斯网络状态: 无")
        self.bayes_status_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # 减小字体
        scenario_layout.addWidget(self.bayes_status_label)

        self.scenario_description_label = QLabel("情景描述: 无")
        self.scenario_description_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # 减小字体
        scenario_layout.addWidget(self.scenario_description_label)

        self.scenario_update_time_label = QLabel("情景更新时间: 无")
        self.scenario_update_time_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # 减小字体
        scenario_layout.addWidget(self.scenario_update_time_label)

        scenario_group.setLayout(scenario_layout)

        # 添加到主布局
        main_layout.addWidget(user_group)
        main_layout.addWidget(scenario_group)

        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-size: 10pt;  /* 减小分组标题字体 */
                font-weight: bold;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #0066CC;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;  /* 减少标题内边距 */
            }
            QLabel {
                color: #333;
                font-size: 8pt;  /* 减小标签字体 */
            }
        """)



    def update_status(self, user_name, database_name, scenario_name, owl_status, bayes_status, scenario_description):
        """
        更新状态栏内容。

        :param user_name: 当前用户名。
        :param database_name: 当前数据库名称。
        :param scenario_name: 当前情景名称。
        :param owl_status: OWL 文件状态。
        :param bayes_status: 贝叶斯网络状态。
        :param scenario_description: 当前情景描述。
        """
        self.user_label.setText(f"当前用户: {user_name}")
        self.database_label.setText(f"当前数据库: {database_name}")
        self.current_scenario_label.setText(f"当前情景: {scenario_name}")
        self.owl_status_label.setText(f"OWL 文件状态: {owl_status}")
        self.bayes_status_label.setText(f"贝叶斯网络状态: {bayes_status}")

        # 处理情景描述，超过8个字显示“...”
        if len(scenario_description) > 8:
            truncated_description = scenario_description[:8] + "…"
        else:
            truncated_description = scenario_description
        self.scenario_description_label.setText(f"情景描述: {truncated_description}")
