# -*- coding: utf-8 -*-
# @Time    : 12/10/2024 11:10 AM
# @FileName: main_window.py
# @Software: PyCharm
import os
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSizePolicy, QFrame, QSpacerItem
)
from PySide6.QtCore import Qt

from controllers.scenario_controller import ScenarioController
from views.scenario_manager import ScenarioManager
from views.status_bar import StatusBar
from views.tabs.tab_widget import CustomTabWidget


class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()

        # 设置主窗口标题
        self.setWindowTitle(self.tr("基于认知数字孪生的城市道路应急情景推演工具"))
        self.setObjectName("MainWindow")

        self.db_manager = db_manager  # 保存数据库管理器实例

        # 创建中央部件：左右布局
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        central_layout = QHBoxLayout(central_widget)
        central_layout.setContentsMargins(10, 10, 10, 10)
        central_layout.setSpacing(10)

        # 创建左侧大框架（包含情景管理器和状态栏两个小框架）
        left_container = QFrame()
        left_container.setObjectName("LeftContainer")
        left_layout = QVBoxLayout(left_container)
        # 设置最大宽度
        left_container.setMaximumWidth(365)
        left_layout.setContentsMargins(0, 0, 0, 0)  # 移除容器的外边距
        left_layout.setSpacing(15)  # 设置两个小框架之间的间距
        # 移除左侧大框架的边框，并添加圆角和背景颜色
        left_container.setStyleSheet("""
            QFrame#LeftContainer {
                border: none;
                border-radius: 10px;
            }
        """)

        # 创建情景管理器小框架
        scenario_frame = QFrame()
        scenario_frame.setObjectName("ScenarioFrame")
        scenario_layout = QVBoxLayout(scenario_frame)
        scenario_layout.setContentsMargins(0, 0, 0, 0)  # 设置小框架的内边距
        scenario_layout.setSpacing(0)  # 设置标题与内容之间的间距
        # 场景管理器样式已经在 scenario_manager.qss 中定义，无需再次设置

        # 创建情景管理器标题标签
        scenario_title_label = QLabel(self.tr("情景管理器"))
        scenario_title_label.setObjectName("ScenarioTitleLabel")
        scenario_title_label.setAlignment(Qt.AlignCenter)
        scenario_title_label.setFixedHeight(30)  # 增加高度以容纳圆角

        # 添加标题标签到情景管理器小框架
        scenario_layout.addWidget(scenario_title_label)

        # 添加边框
        underline = QFrame()
        underline.setObjectName("Scenario_Underline")
        underline.setFrameShape(QFrame.HLine)
        underline.setFrameShadow(QFrame.Sunken)
        underline.setFixedHeight(2)
        scenario_layout.addWidget(underline)

        # 创建情景管理器内容区域
        self.scenario_manager = ScenarioManager()
        self.scenario_manager.setObjectName("ScenarioManager")
        self.scenario_manager.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scenario_layout.addWidget(self.scenario_manager)

        # 创建状态栏小框架
        status_frame = QFrame()
        status_frame.setObjectName("StatusFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 10)  # 设置小框架的内边距
        status_layout.setSpacing(0)  # 设置标题与内容之间的间距
        # 状态栏样式已经在 status_bar.qss 中定义，无需再次设置

        # 创建状态栏标题标签
        status_title_label = QLabel(self.tr("状态栏"))
        status_title_label.setObjectName("StatusTitleLabel")
        status_title_label.setAlignment(Qt.AlignCenter)
        status_title_label.setFont(QFont("SimSun", 16, QFont.Bold))  # 设置字体和大小
        status_title_label.setFixedHeight(30)  # 增加高度以容纳圆角

        # 添加标题标签到状态栏小框架
        status_layout.addWidget(status_title_label)

        # 添加边框
        underline = QFrame()
        underline.setObjectName("Status_Underline")
        underline.setFrameShape(QFrame.HLine)
        underline.setFrameShadow(QFrame.Sunken)
        underline.setFixedHeight(2)
        status_layout.addWidget(underline)

        # 创建状态栏内容区域
        self.status_bar_widget = StatusBar()
        self.status_bar_widget.setObjectName("StatusBarWidget")
        self.status_bar_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_layout.addWidget(self.status_bar_widget)

        # 添加情景管理器和状态栏小框架到左侧大框架布局
        left_layout.addWidget(scenario_frame, stretch=3)
        left_layout.addWidget(status_frame, stretch=1)

        # 创建右侧自定义标签页
        self.tab_widget = CustomTabWidget()
        self.tab_widget.setObjectName("CustomTabWidget")
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置右侧布局的边框（如果需要圆角）
        self.tab_widget.set_border()

        # 添加左右布局到中央布局
        central_layout.addWidget(left_container, stretch=1)
        central_layout.addWidget(self.tab_widget, stretch=4)

        # 设置中央部件
        self.setCentralWidget(central_widget)

        # 创建控制器并连接
        self.controller = ScenarioController(
            scenario_manager=self.scenario_manager,
            status_bar=self.status_bar_widget,
            tab_widget=self.tab_widget,
            db_manager=self.db_manager
        )

        # 自动加载情景数据
        self.controller.load_scenarios()

        # 连接标签切换信号，调试
        self.tab_widget.tab_changed.connect(self.on_tab_changed)

        # 加载样式表
        self.load_stylesheets([
            os.path.join(os.path.dirname(__file__), "..", "resources", "styles", "global.qss"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "styles", "scenario_manager.qss"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "styles", "widgets.qss"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "styles", "status_bar.qss")
        ])  # 确保样式表文件位于正确路径

    def load_stylesheets(self, filepaths):
        """加载多个样式表文件，并动态修改图标路径"""
        combined_styles = ""
        for filepath in filepaths:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    style = f.read()

                    # 获取资源路径：区分打包和非打包环境
                    if getattr(sys, 'frozen', False):  # 如果在打包后环境中
                        icon_path = os.path.join(sys._MEIPASS, "resources", "icons")
                    else:  # 本地开发环境
                        icon_path = os.path.join("resources", "icons")

                    # 确保路径格式正确
                    icon_path = icon_path.replace("\\", "/")  # 处理 Windows 路径分隔符

                    # 替换样式表中的图标路径
                    style = style.replace("./resources/icons", icon_path)

                    combined_styles += style + "\n"
            else:
                print(f"样式表文件未找到: {filepath}")

        self.setStyleSheet(combined_styles)

    def on_tab_changed(self, index):
        # 处理标签切换事件
        print(self.tr(f"切换到标签 {index}"))