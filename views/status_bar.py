# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: status_bar.py
# @Software: PyCharm

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox
from PySide6.QtCore import Qt

class StatusBar(QWidget):
    """
    自定义状态栏，用于显示用户信息、情景状态（包括描述和更新时间）。
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("StatusBarWidget")

        # 设置较小的最小高度，使状态栏占据较小的空间
        self.setMinimumHeight(238)  # 根据需要调整该值

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 20)
        main_layout.setSpacing(10)

        # 用户信息分组
        user_group = QGroupBox("用户信息")
        user_group.setObjectName("UserInfoGroup")
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(5, 5, 5, 5)
        user_layout.setSpacing(5)

        self.user_label = QLabel("当前用户: 无")
        self.user_label.setObjectName("UserLabel")
        user_layout.addWidget(self.user_label)

        self.database_label = QLabel("当前数据库: 无")
        self.database_label.setObjectName("DatabaseLabel")
        user_layout.addWidget(self.database_label)

        user_group.setLayout(user_layout)

        # 情景状态分组
        scenario_group = QGroupBox("情景状态")
        scenario_group.setObjectName("ScenarioStatusGroup")
        scenario_layout = QVBoxLayout()
        scenario_layout.setContentsMargins(5, 5, 5, 5)
        scenario_layout.setSpacing(5)

        self.current_scenario_label = QLabel("当前情景: 等待情景加载")
        self.current_scenario_label.setObjectName("CurrentScenarioLabel")
        scenario_layout.addWidget(self.current_scenario_label)

        self.owl_status_label = QLabel("OWL 文件状态: 等待情景加载")
        self.owl_status_label.setObjectName("OwlStatusLabel")
        scenario_layout.addWidget(self.owl_status_label)

        self.bayes_status_label = QLabel("贝叶斯网络状态: 等待情景加载")
        self.bayes_status_label.setObjectName("BayesStatusLabel")
        scenario_layout.addWidget(self.bayes_status_label)

        self.scenario_description_label = QLabel("情景描述: 等待情景加载")
        self.scenario_description_label.setObjectName("ScenarioDescriptionLabel")
        scenario_layout.addWidget(self.scenario_description_label)

        self.scenario_update_time_label = QLabel("情景更新时间: 等待情景加载")
        self.scenario_update_time_label.setObjectName("ScenarioUpdateTimeLabel")
        scenario_layout.addWidget(self.scenario_update_time_label)

        scenario_group.setLayout(scenario_layout)

        main_layout.addWidget(user_group)
        main_layout.addWidget(scenario_group)

    def set_label_text_with_tooltip(self, label, text, max_length=30):
        """
        设置 QLabel 的文本，超过 max_length 时截断，并添加工具提示。

        :param label: 要设置的 QLabel 对象
        :param text: 完整的文本内容
        :param max_length: 最大显示字符数，超过则截断
        """
        if len(text) > max_length:
            truncated_text = text[:max_length - 3] + '...'
        else:
            truncated_text = text

        label.setText(truncated_text)
        label.setToolTip(text)  # 设置工具提示为完整文本

    def update_status(self, username, database, host, port, scenario_name, owl_status, bayes_status, scenario_description, update_time):
        """
        更新状态栏内容。
        """
        # 更新用户信息
        full_user_text = f"当前用户: {username}"
        self.set_label_text_with_tooltip(self.user_label, full_user_text, max_length=40)

        full_database_text = f"当前数据库: {database}"
        self.set_label_text_with_tooltip(self.database_label, full_database_text, max_length=50)

        # 更新情景状态
        if not scenario_description:
            scenario_description = "无"

        truncated_description = (scenario_description[:8] + "…") if len(scenario_description) > 8 else scenario_description
        self.scenario_description_label.setText(f"情景描述: {truncated_description}")
        self.scenario_description_label.setToolTip(scenario_description)

        self.current_scenario_label.setText(f"当前情景: {scenario_name}")
        self.current_scenario_label.setToolTip(scenario_name)

        self.owl_status_label.setText(f"OWL 文件状态: {owl_status}")
        self.owl_status_label.setToolTip(owl_status)

        self.bayes_status_label.setText(f"贝叶斯网络状态: {bayes_status}")
        self.bayes_status_label.setToolTip(bayes_status)

        self.scenario_update_time_label.setText(f"情景更新时间: {update_time}")
        self.scenario_update_time_label.setToolTip(update_time)

    def update_user_info(self, username, database, host, port):
        """
        更新用户部分信息。
        """
        full_user_text = f"当前用户: {username}"
        self.set_label_text_with_tooltip(self.user_label, full_user_text, max_length=40)

        full_database_text = f"当前数据库: {database}"
        self.set_label_text_with_tooltip(self.database_label, full_database_text, max_length=50)
