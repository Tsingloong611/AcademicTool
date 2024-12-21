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
        self.ModelGenerationTab.generate_request.connect(self.generate_bayes)
        self.ModelTransformationTab.set_inference_request.connect(self.set_inference_conditions)


    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_buttons_widget = QWidget()
        self.tab_buttons_widget.setObjectName("TabButtonsWidget")
        self.tab_buttons_layout = QHBoxLayout(self.tab_buttons_widget)
        self.tab_buttons_layout.setSpacing(0)
        self.tab_buttons_layout.setContentsMargins(0, 0, 0, 0)


        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.ElementSettingTab = ElementSettingTab()
        self.ModelGenerationTab = ModelGenerationTab()
        self.ModelTransformationTab = ModelTransformationTab()
        self.ConditionSettingTab = ConditionSettingTab()

        self.tabs = []
        self.add_tab(self.tr("情景要素设定"), self.ElementSettingTab)
        self.add_tab(self.tr("情景模型生成"), self.ModelGenerationTab)
        self.add_tab(self.tr("推演模型转换"), self.ModelTransformationTab)
        self.add_tab(self.tr("推演条件设定"), self.ConditionSettingTab)



        self.placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
    border-radius: 10px; /* 圆角边框 */
    """)

        self.placeholder_label = QLabel("")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setObjectName("PlaceholderLabel")

        placeholder_layout.addWidget(self.placeholder_label)

        self.content_stack.addWidget(self.placeholder)
        self.content_stack.setCurrentWidget(self.placeholder)

        main_layout.addWidget(self.tab_buttons_widget)
        main_layout.addWidget(self.content_stack)

        self.tab_buttons_widget.setVisible(False)

    def set_border(self):
        """设置边框样式"""
        self.content_stack.setStyleSheet("""QStackedWidget {
    border: 2px solid dark; /* 边框颜色 */
    border-radius: 10px; /* 圆角边框 */
}""")

    def add_tab(self, tab_name, content_widget):
        button = QPushButton(self.tr(tab_name))
        button.setObjectName(f"{tab_name}Button")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setCheckable(True)
        button.clicked.connect(lambda checked, idx=len(self.tabs)+1: self.switch_tab(idx))
        # 设置固定高度以保持一致性
        button.setFixedHeight(32)
        # 样式根据 tab_name 判断，但这些判断字符串并非直接展示给用户，仅用于条件判断，不添加 tr()
        if tab_name in [self.tr("情景模型生成")]:
            button.setStyleSheet("""
                border: 2px solid dark; /* 边框颜色 */
                border-radius: 10px; /* 圆角边框 */
                background-color: transparent; /* 背景透明 */
                color: #333333; /* 文字颜色 */
                font-size: 18px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
                    padding: 5px;
                border-top-left-radius: 0px; /* 左上角直角 */
                border-top-right-radius: 0px; /* 右上角直角 */
                border-bottom: none; /* 下方没有边框 */
                border-bottom-left-radius: 0; /* 左下角直角 */
                border-bottom-right-radius: 0; /* 右下角直角 */
            }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */}
            """)
        elif tab_name in [self.tr("推演模型转换")]:
            button.setStyleSheet("""
                            border: 2px solid dark; /* 边框颜色 */
                            border-radius: 10px; /* 圆角边框 */
                            background-color: transparent; /* 背景透明 */
                            color: #333333; /* 文字颜色 */
                            font-size: 18px; /* 文字大小 */
                            font-weight: bold; /* 文字加粗 */
                            border-top-left-radius: 0px; /* 左上角直角 */
                                padding: 5px;
                            border-top-right-radius: 0px; /* 右上角直角 */
                            border-bottom: none; /* 下方没有边框 */
                            border-left: none; /* 左侧没有边框 */
                            border-bottom-left-radius: 0; /* 左下角直角 */
                            border-bottom-right-radius: 0; /* 右下角直角 */
                        }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */}
                        """)
        elif tab_name in [self.tr("情景要素设定")]:
            button.setStyleSheet("""
                border: 2px solid dark; /* 边框颜色 */
                border-radius: 10px; /* 圆角边框 */
                background-color: transparent; /* 背景透明 */
                color: #333333; /* 文字颜色 */
                font-size: 18px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
                    padding: 5px;
                border-top-right-radius: 0px; /* 右上角直角 */
                border-right: none; /* 右侧没有边框 */
                border-bottom: none; /* 下方没有边框 */
                border-bottom-left-radius: 0; /* 左下角直角 */
                border-bottom-right-radius: 0; /* 右下角直角 */
            }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-right: none; /* 右侧没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-right: none; /* 右侧没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */
                border-right: none; /* 右侧没有边框 */}
            """)
        elif tab_name in [self.tr("推演条件设定")]:
            button.setStyleSheet("""
                border: 2px solid dark; /* 边框颜色 */
                border-radius: 10px; /* 圆角边框 */
                background-color: transparent; /* 背景透明 */
                color: #333333; /* 文字颜色 */
                font-size: 18px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
                    padding: 5px;
                border-top-left-radius: 0px; /* 右上角直角 */
                border-left: none; /* 右侧没有边框 */
                border-bottom: none; /* 下方没有边框 */
                border-bottom-left-radius: 0; /* 左下角直角 */
                border-bottom-right-radius: 0; /* 右下角直角 */
            }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */}
            """)

        self.tab_buttons_layout.addWidget(button)
        self.tabs.append(button)
        self.content_stack.addWidget(content_widget)

    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index - 1)
        self.tab_changed.emit(index - 1)

        for i, button in enumerate(self.tabs):
            button.setChecked(i + 1 == index)

        self.content_stack.setStyleSheet("""QStackedWidget {
    border: 2px solid dark; /* 边框颜色 */
    border-top: none; /* 上方没有边框 */
    border-bottom-left-radius: 10px; /* 左下角圆角 */
    border-bottom-right-radius: 10px; /* 右下角圆角 */
    background-color:#E8E8E8; /* 淡灰色 */
}
""")

    def show_placeholder(self, show=True, message=None):
        if message is None:
            message = self.tr("请选择或新建情景")
        if show:
            self.content_stack.setCurrentWidget(self.placeholder)
            self.placeholder_label.setText(self.tr(message))
            for button in self.tabs:
                button.setChecked(False)
            self.tab_buttons_widget.setVisible(False)
        else:
            self.tab_buttons_widget.setVisible(True)
            self.reset_all_inputs()
            for button in self.tabs:
                self.lock_tabs(self.tabs.index(button) + 1)
            if self.tabs:
                self.unlock_tabs(1)
                self.switch_tab(1)

    def reset_all_inputs(self):
        self.ElementSettingTab.reset_inputs()
        self.ModelGenerationTab.reset_inputs()
        self.ModelTransformationTab.reset_inputs()
        self.ConditionSettingTab.reset_inputs()

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

    def set_inference_conditions(self):
        self.unlock_tabs(4)
        self.switch_tab(4)
