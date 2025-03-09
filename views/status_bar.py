# status_bar.py
from PySide6.QtGui import QFont
# -*- coding: utf-8 -*-
# @FileName: status_bar.py
# @Software: PyCharm
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox
from PySide6.QtCore import Qt


class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("StatusBarWidget")
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 0)
        main_layout.setSpacing(10)

        user_group = QGroupBox(self.tr("用户信息"))
        user_group.setObjectName("UserInfoGroup")
        user_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
            }
        """)
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(5, 5, 5, 5)
        user_layout.setSpacing(5)


        self.user_label = QLabel(self.tr("当前用户: 无"))
        self.user_label.setObjectName("UserLabel")
        user_layout.addWidget(self.user_label)

        self.database_label = QLabel(self.tr("当前数据库: 无"))
        self.database_label.setObjectName("DatabaseLabel")
        user_layout.addWidget(self.database_label)

        user_group.setLayout(user_layout)

        scenario_group = QGroupBox(self.tr("情景状态"))
        scenario_group.setObjectName("ScenarioStatusGroup")
        # 加粗，16
        scenario_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                /* 加粗字体 */
                font-weight: bold;
            }
        """)
        scenario_layout = QVBoxLayout()
        scenario_layout.setContentsMargins(5, 5, 5, 5)
        scenario_layout.setSpacing(5)

        self.current_scenario_label = QLabel(self.tr("当前情景: 等待情景加载"))
        self.current_scenario_label.setObjectName("CurrentScenarioLabel")
        scenario_layout.addWidget(self.current_scenario_label)

        self.owl_status_label = QLabel(self.tr("OWL 文件状态: 等待情景加载"))
        self.owl_status_label.setObjectName("OwlStatusLabel")
        scenario_layout.addWidget(self.owl_status_label)

        self.bayes_status_label = QLabel(self.tr("贝叶斯网络状态: 等待情景加载"))
        self.bayes_status_label.setObjectName("BayesStatusLabel")
        scenario_layout.addWidget(self.bayes_status_label)

        self.scenario_description_label = QLabel(self.tr("情景描述: 等待情景加载"))
        self.scenario_description_label.setObjectName("ScenarioDescriptionLabel")
        scenario_layout.addWidget(self.scenario_description_label)

        self.scenario_update_time_label = QLabel(self.tr("情景更新时间: 等待情景加载"))
        self.scenario_update_time_label.setObjectName("ScenarioUpdateTimeLabel")
        scenario_layout.addWidget(self.scenario_update_time_label)

        scenario_group.setLayout(scenario_layout)

        main_layout.addWidget(user_group)
        main_layout.addWidget(scenario_group)

        self.user_label.setObjectName("UserLabel")
        self.database_label.setObjectName("DatabaseLabel")
        self.current_scenario_label.setObjectName("CurrentScenarioLabel")
        self.owl_status_label.setObjectName("OwlStatusLabel")
        self.bayes_status_label.setObjectName("BayesStatusLabel")
        self.scenario_description_label.setObjectName("ScenarioDescriptionLabel")
        self.scenario_update_time_label.setObjectName("ScenarioUpdateTimeLabel")

    def set_label_text_with_tooltip(self, label, text, max_length=30):
        if len(text) > max_length:
            truncated_text = text[:max_length - 3] + '...'
        else:
            truncated_text = text
        label.setText(self.tr(text) if isinstance(text, str) else text)
        label.setToolTip(text)

    def update_status(self, username, database, scenario_name, owl_status, bayes_status, scenario_description, update_time):
        full_user_text = self.tr('当前用户: {username}').format(username=username)
        self.set_label_text_with_tooltip(self.user_label, full_user_text, max_length=40)

        full_database_text = self.tr('当前数据库: {database}').format(database=database)
        self.set_label_text_with_tooltip(self.database_label, full_database_text, max_length=50)

        if not scenario_description:
            scenario_description = self.tr("无")

        truncated_description = (self.tr(scenario_description[:8] + "…") if len(scenario_description) > 8 else self.tr(scenario_description))
        self.scenario_description_label.setText(self.tr("情景描述: ") + truncated_description)
        self.scenario_description_label.setToolTip(self.tr(scenario_description))

        self.current_scenario_label.setText(self.tr("当前情景: ") + self.tr(scenario_name))
        self.current_scenario_label.setToolTip(self.tr(scenario_name))

        self.owl_status_label.setText(self.tr("OWL 文件状态: ") + self.tr(owl_status))
        self.owl_status_label.setToolTip(self.tr(owl_status))

        self.bayes_status_label.setText(self.tr("贝叶斯网络状态: ") + self.tr(bayes_status))
        self.bayes_status_label.setToolTip(self.tr(bayes_status))

        self.scenario_update_time_label.setText(self.tr("情景更新时间: ") + self.tr(update_time))
        self.scenario_update_time_label.setToolTip(self.tr(update_time))

    def update_user_info(self, username, database):
        full_user_text = self.tr('当前用户: {username}').format(username=username)
        self.set_label_text_with_tooltip(self.user_label, full_user_text, max_length=40)

        full_database_text = self.tr('当前数据库: {database}').format(database=database)
        self.set_label_text_with_tooltip(self.database_label, full_database_text, max_length=50)
