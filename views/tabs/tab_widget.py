# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:11 AM
# @FileName: tab_widget.py
# @Software: PyCharm

from PySide6.QtWidgets import QStackedWidget, QWidget, QLabel, QVBoxLayout, QTabWidget, QSizePolicy
from PySide6.QtCore import Qt
from views.tabs.element_setting import ElementSettingTab
from views.tabs.model_generation import ModelGenerationTab
from views.tabs.model_transformation import ModelTransformationTab
from views.tabs.condition_setting import ConditionSettingTab

class TabWidget(QStackedWidget):
    def __init__(self, root):
        super().__init__()

        self.setObjectName("MainRightArea")  # 为整个区域设置对象名，便于QSS统一管理

        # 页面 0：占位页面
        self.placeholder = QWidget()
        self.placeholder.setObjectName("RightArea")  # 设置对象名
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)

        self.placeholder_label = QLabel("")
        self.placeholder_label.setObjectName("PlaceholderLabel")  # 为占位标签设置对象名
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(self.placeholder_label)
        self.addWidget(self.placeholder)

        self.root = root

        # 页面 1：功能区标签页
        self.tab_widget_inner = QTabWidget()
        self.tab_widget_inner.setObjectName("MainTabWidget")  # 设置对象名
        self.tab_widget_inner.setTabPosition(QTabWidget.North)
        self.tab_widget_inner.setTabShape(QTabWidget.Rounded)
        self.tab_widget_inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.addWidget(self.tab_widget_inner)

        # 添加四个标签页
        self.element_setting_tab = ElementSettingTab()
        self.model_generation_tab = ModelGenerationTab()
        self.model_transformation_tab = ModelTransformationTab()
        self.condition_setting_tab = ConditionSettingTab()

        self.tab_widget_inner.addTab(self.element_setting_tab, "情景要素设定")
        self.tab_widget_inner.addTab(self.model_generation_tab, "情景模型生成")
        self.tab_widget_inner.addTab(self.model_transformation_tab, "推演模型转换")
        self.tab_widget_inner.addTab(self.condition_setting_tab, "推演条件设定")

        # 初始化时锁定所有标签页
        self.setCurrentWidget(self.placeholder)
        self.lock_tabs()

    def lock_tabs(self):
        for index in range(self.tab_widget_inner.count()):
            self.tab_widget_inner.setTabEnabled(index, False)

    def unlock_tabs(self):
        for index in range(self.tab_widget_inner.count()):
            self.tab_widget_inner.setTabEnabled(index, True)
        self.setCurrentWidget(self.tab_widget_inner)
        self.tab_widget_inner.setCurrentIndex(0)

    def show_placeholder(self, has_scenarios: bool):
        self.setCurrentWidget(self.placeholder)
        self.lock_tabs()
        self.set_placeholder_text(has_scenarios)

    def show_tabs(self):
        self.unlock_tabs()

    def set_placeholder_text(self, has_scenarios: bool):
        if has_scenarios:
            self.placeholder_label.setText("请选择或新建情景")
        else:
            self.placeholder_label.setText("请新建情景")

    def update_placeholder_style(self, border_color: str = "#0078d7", background_color: str = "#f0f8ff"):
        pass