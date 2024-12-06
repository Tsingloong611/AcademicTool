# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:11 AM
# @FileName: tab_widget.py
# @Software: PyCharm
from PySide6 import QtWidgets
from PySide6.QtWidgets import QStackedWidget, QWidget, QLabel, QVBoxLayout, QTabWidget, QSizePolicy
from PySide6.QtCore import Slot, Qt
from views.tabs.element_setting import ElementSettingTab
from views.tabs.model_generation import ModelGenerationTab
from views.tabs.model_transformation import ModelTransformationTab
from views.tabs.condition_setting import ConditionSettingTab



class TabWidget(QStackedWidget):
    def __init__(self,root):
        super().__init__()

        # 页面 0：占位页面，根据是否有情景显示不同提示
        self.placeholder = QWidget()
        self.placeholder.setObjectName("RightArea")  # 设置 objectName
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        self.placeholder_label = QLabel("")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel {
                border-radius: 8px;
                padding: 10px;
                font-size: 14pt;
                font-weight: bold;
            }
        """)
        placeholder_layout.addWidget(self.placeholder_label)
        self.addWidget(self.placeholder)
        self.root = root

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


        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 为占位页面添加蓝色边框
        self.placeholder.setStyleSheet("""
            QWidget#RightArea {
                border: 2px solid #0078d7; /* 蓝色边框 */
                border-radius: 8px;
                padding: 20px;
                background-color: #f0f8ff; /* 可选：淡蓝色背景 */
            }
        """)
        # 初始化时锁定所有标签页
        self.setCurrentWidget(self.placeholder)
        self.lock_tabs()

        tab_count = self.tab_widget.count()
        tab_width = self.tab_widget.width() // tab_count + 42
        style = f"QTabBar::tab{{width: {tab_width}px;}}"
        self.tab_widget.setStyleSheet(style)

    def lock_tabs(self):
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(index, False)

    def unlock_tabs(self):
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(index, True)
        self.setCurrentWidget(self.tab_widget)
        self.tab_widget.setCurrentIndex(0)

    def show_placeholder(self, has_scenarios: bool):
        self.setCurrentWidget(self.placeholder)
        self.lock_tabs()
        self.set_placeholder_text(has_scenarios)

    def show_tabs(self):
        self.unlock_tabs()

    def set_placeholder_text(self, has_scenarios: bool):
        """
        根据是否存在情景设置占位符文本。
        :param has_scenarios: True 如果存在情景，否则 False。
        """
        if has_scenarios:
            self.placeholder_label.setText("请选择或新建情景")
        else:
            self.placeholder_label.setText("请新建情景")

    def update_placeholder_style(self, border_color: str = "#0078d7", background_color: str = "#f0f8ff"):
        """
        更新占位符标签的样式。
        :param border_color: 边框颜色。
        :param background_color: 背景颜色。
        """
        self.placeholder_label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {border_color}; /* 蓝色边框 */
                border-radius: 8px;
                padding: 10px;
                font-size: 14pt;
                font-weight: bold;
                background-color: {background_color}; /* 淡蓝色背景 */
            }}
        """)