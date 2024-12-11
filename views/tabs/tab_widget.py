# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:11 AM
# @FileName: tab_widget.py
# @Software: PyCharm
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot
from views.tabs.element_setting import ElementSettingTab
from views.tabs.model_generation import ModelGenerationTab
from views.tabs.model_transformation import ModelTransformationTab
from views.tabs.condition_setting import ConditionSettingTab


class CustomTabWidget(QWidget):
    tab_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.ElementSettingTab.generate_button.clicked.connect(self.generate_model)
        self.ModelGenerationTab.generate_button.clicked.connect(self.generate_bayes)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_buttons_widget = QWidget()
        self.tab_buttons_widget.setObjectName("TabButtonsWidget")
        self.tab_buttons_layout = QHBoxLayout(self.tab_buttons_widget)
        self.tab_buttons_layout.setSpacing(0)
        self.tab_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_buttons_widget.setFont(QFont("宋体", 16, QFont.Bold))  # 设置字体和大小

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.ElementSettingTab = ElementSettingTab()
        self.ModelGenerationTab = ModelGenerationTab()
        self.ModelTransformationTab = ModelTransformationTab()
        self.ConditionSettingTab = ConditionSettingTab()

        self.tabs = []
        self.add_tab("情景要素设定", self.ElementSettingTab)
        self.add_tab("情景模型生成", self.ModelGenerationTab)
        self.add_tab("推演模型转换", self.ModelTransformationTab)
        self.add_tab("推演条件设定", self.ConditionSettingTab)



        self.placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)

        self.placeholder_label = QLabel("")
        self.placeholder_label.setObjectName("PlaceholderLabel")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(self.placeholder_label)

        self.content_stack.addWidget(self.placeholder)
        self.content_stack.setCurrentWidget(self.placeholder)

        main_layout.addWidget(self.tab_buttons_widget)
        main_layout.addWidget(self.content_stack)

        self.tab_buttons_widget.setVisible(False)

    def set_border(self):
        """设置边框样式"""
        self.content_stack.setStyleSheet("""QStackedWidget {
            border: 2px solid #dcdcdc;
        }""")


    def add_tab(self, tab_name, content_widget):
        button = QPushButton(tab_name)
        button.setObjectName(f"{tab_name}Button")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setCheckable(True)
        button.clicked.connect(lambda checked, idx=len(self.tabs)+1: self.switch_tab(idx))
        # 设置固定高度以保持一致性
        button.setFixedHeight(32)
        self.tab_buttons_layout.addWidget(button)
        self.tabs.append(button)
        self.content_stack.addWidget(content_widget)

    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index - 1)
        self.tab_changed.emit(index - 1)

        for i, button in enumerate(self.tabs):
            button.setChecked(i + 1 == index)

        self.content_stack.setStyleSheet("""QStackedWidget {
            border: 1px solid #dcdcdc;
            border-top: none;
        }""")



    def show_placeholder(self, show=True, message="请选择或新建情景"):
        if show:
            self.content_stack.setCurrentWidget(self.placeholder)
            self.placeholder_label.setText(message)
            for button in self.tabs:
                button.setChecked(False)
            self.tab_buttons_widget.setVisible(False)
        else:
            self.tab_buttons_widget.setVisible(True)
            for button in self.tabs:
                self.lock_tabs(self.tabs.index(button) + 1)
            if self.tabs:
                self.unlock_tabs(1)
                self.switch_tab(1)

    def lock_tabs(self, index):
        # 根据索引锁定标签
        for i, button in enumerate(self.tabs):
            if i + 1 == index:
                button.setDisabled(True)

    def unlock_tabs(self, index):
        # 根据索引解锁标签
        for i, button in enumerate(self.tabs):
            if i + 1 == index:
                button.setEnabled(True)

    def generate_model(self):
        self.unlock_tabs(2)
        self.switch_tab(2)

    def generate_bayes(self):
        self.unlock_tabs(3)
        self.switch_tab(3)