# tab_widget.py

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTabWidget, QStackedWidget, QFrame
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot, Qt
from views.tabs.element_setting import ElementSettingTab
from views.tabs.model_generation import ModelGenerationTab
from views.tabs.model_transformation import ModelTransformationTab
from views.tabs.condition_setting import ConditionSettingTab


class TabWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 无外边距
        main_layout.setSpacing(0)  # 无间距

        # 带蓝色边框的 QFrame 作为容器
        border_frame = QFrame()
        border_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #0078d7; /* 蓝色边框 */
                border-radius: 8px;
                padding: 20px;
                background-color: #f0f8ff; /* 可选：淡蓝色背景 */
            }
        """)
        border_layout = QVBoxLayout(border_frame)
        border_layout.setContentsMargins(0, 0, 0, 0)
        border_layout.setSpacing(0)

        # QStackedWidget 用于切换占位页面和标签页
        self.stacked_widget = QStackedWidget()

        # 页面 0：占位页面，提示用户选择或新建情景
        self.placeholder = QWidget()
        self.placeholder.setObjectName("RightArea")  # 设置 objectName
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)

        self.placeholder_label = QLabel("请选择或新建情景")  # 默认消息
        self.placeholder_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(self.placeholder_label)

        self.stacked_widget.addWidget(self.placeholder)

        # 页面 1：功能区标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)
        self.tab_widget.setObjectName("MainTabWidget")  # 设置 objectName

        # 添加四个标签页
        self.element_setting_tab = ElementSettingTab()
        self.model_generation_tab = ModelGenerationTab()
        self.model_transformation_tab = ModelTransformationTab()
        self.condition_setting_tab = ConditionSettingTab()

        self.tab_widget.addTab(self.element_setting_tab, "情景要素设定")
        self.tab_widget.addTab(self.model_generation_tab, "情景模型生成")
        self.tab_widget.addTab(self.model_transformation_tab, "推演模型转换")
        self.tab_widget.addTab(self.condition_setting_tab, "推演条件设定")

        self.stacked_widget.addWidget(self.tab_widget)

        # 将 QStackedWidget 添加到 border_layout
        border_layout.addWidget(self.stacked_widget)

        # 将 border_frame 添加到 main_layout
        main_layout.addWidget(border_frame)

        # 初始化时锁定所有标签页并显示占位页面
        self.show_placeholder(has_scenarios=False)

    def lock_tabs(self):
        """锁定所有标签页"""
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(index, False)

    def unlock_tabs(self):
        """解锁所有标签页并显示标签页"""
        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(index, True)
        self.stacked_widget.setCurrentWidget(self.tab_widget)
        self.tab_widget.setCurrentIndex(0)

    def show_placeholder(self, has_scenarios: bool):
        """
        显示占位页面，并设置提示消息。
        """
        self.set_placeholder_text(has_scenarios)
        self.stacked_widget.setCurrentWidget(self.placeholder)
        self.lock_tabs()

    def show_tabs(self):
        """显示标签页并解锁"""
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
