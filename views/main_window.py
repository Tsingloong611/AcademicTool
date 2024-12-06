# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: main_window.py
# @Software: PyCharm
import os


from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QDockWidget, QLabel, QFrame
from PySide6.QtCore import Qt, Slot
from pymysql import connect

from controllers import ScenarioController
from views.scenario_manager import ScenarioManager
from views.status_bar import StatusBar
from views.tabs.tab_widget import TabWidget


class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.setWindowTitle("基于认知数字李生的城市道路应急情景推演工具")
        self.setFixedSize(1197, 600)  # 增大主窗口高度以更好对齐

        self.db_manager = db_manager  # 保存数据库管理器实例

        # 设置样式
        self.load_styles()


        # 创建中央部件：标签页
        self.tab_widget = TabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # 创建情景管理器的 QDockWidget
        self.create_scenario_manager_dock()

        # 创建状态栏的 QDockWidget
        self.create_status_bar_dock()
        self.status_bar_dock.setFixedHeight(225)


        # 创建控制器并连接
        self.controller = ScenarioController(
            scenario_manager=self.scenario_manager,
            status_bar=self.status_bar_widget,
            tab_widget=self.tab_widget,
            db_manager=self.db_manager
        )

        # 自动加载情景数据
        self.controller.load_scenarios()


    def create_scenario_manager_dock(self):
        # 创建 QDockWidget
        self.scenario_manager_dock = QDockWidget("情景管理器", self)
        self.scenario_manager_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.scenario_manager_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetFloatable
        )
        self.scenario_manager_dock.setObjectName("ScenarioManagerDock")

        # 创建一个带阴影和圆角的 QFrame 作为容器
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 设置情景管理器作为 QFrame 的内容
        self.scenario_manager = ScenarioManager()
        layout.addWidget(self.scenario_manager)

        # 将 QFrame 设置为 QDockWidget 的内容
        self.scenario_manager_dock.setWidget(frame)

        # 将 QDockWidget 添加到主窗口的左侧
        self.addDockWidget(Qt.LeftDockWidgetArea, self.scenario_manager_dock)


    def create_status_bar_dock(self):
        # 创建 QDockWidget
        self.status_bar_dock = QDockWidget("状态栏", self)
        self.status_bar_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.status_bar_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetFloatable
        )
        self.status_bar_dock.setObjectName("StatusBarDock")

        # 创建一个带阴影和圆角的 QFrame 作为容器
        frame_status = QFrame()
        frame_status.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
            }
        """)
        layout_status = QVBoxLayout(frame_status)
        layout_status.setContentsMargins(0, 0, 0, 0)
        layout_status.setSpacing(10)

        # 设置状态栏作为 QFrame 的内容
        self.status_bar_widget = StatusBar()
        self.status_bar_widget.setObjectName("StatusBarWidget")  # 用于样式表
        layout_status.addWidget(self.status_bar_widget)

        # 将 QFrame 设置为 QDockWidget 的内容
        self.status_bar_dock.setWidget(frame_status)

        # 使用 splitDockWidget 将状态栏 dock 分割到情景管理器 dock 的下方
        self.splitDockWidget(self.scenario_manager_dock, self.status_bar_dock, Qt.Vertical)

    def load_styles(self):
        """加载拆分后的样式表"""
        styles_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "styles")
        style_files = [
            "global.qss",
            "mainwindow.qss",
            "dockwidget.qss",
            "button.qss",
            "listwidget.qss",
            "tabwidget.qss",
            "tooltip.qss",
            "messagebox.qss",
            "dialog.qss",
            "element_setting.qss"
        ]

        combined_style = ""
        for style_file in style_files:
            path = os.path.join(styles_dir, style_file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    combined_style += f.read() + "\n"
            except Exception as e:
                print(f"Error loading {style_file}: {e}")

        self.setStyleSheet(combined_style)