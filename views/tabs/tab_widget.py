# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:11 AM
# @FileName: tab_widget.py
# @Software: PyCharm

from PySide6.QtWidgets import QStackedWidget, QWidget, QLabel, QVBoxLayout, QTabWidget
from PySide6.QtCore import Slot, Qt
from views.tabs.element_setting import ElementSettingTab
from views.tabs.model_generation import ModelGenerationTab
from views.tabs.model_transformation import ModelTransformationTab
from views.tabs.condition_setting import ConditionSettingTab



class TabWidget(QStackedWidget):
    def __init__(self):
        super().__init__()

        # 页面 0：占位页面，提示用户选择情景
        self.placeholder = QWidget()
        self.placeholder.setObjectName("RightArea")  # 设置 objectName
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_label = QLabel("请选择情景")
        placeholder_layout.addWidget(placeholder_label)
        self.addWidget(self.placeholder)

        # 页面 1：功能区标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)
        self.tab_widget.setObjectName("MainTabWidget")  # 设置 objectName
        self.addWidget(self.tab_widget)

        # 添加四个标签页
        self.element_setting_tab = ElementSettingTab()
        self.model_generation_tab = ModelGenerationTab()
        self.model_transformation_tab = ModelTransformationTab()
        self.condition_setting_tab = ConditionSettingTab()

        self.tab_widget.addTab(self.element_setting_tab, "情景要素设定")
        self.tab_widget.addTab(self.model_generation_tab, "情景模型生成")
        self.tab_widget.addTab(self.model_transformation_tab, "推演模型转换")
        self.tab_widget.addTab(self.condition_setting_tab, "推演条件设定")

        # 初始化时锁定所有标签页
        self.setCurrentWidget(self.placeholder)
        self.lock_tabs()

    def lock_tabs(self):
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(index, False)

    def unlock_tabs(self):
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(index, True)
        self.setCurrentWidget(self.tab_widget)
        self.tab_widget.setCurrentIndex(0)

    def show_placeholder(self):
        self.setCurrentWidget(self.placeholder)
        self.lock_tabs()

    def show_tabs(self):
        self.unlock_tabs()