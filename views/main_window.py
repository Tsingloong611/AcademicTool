# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: main_window.py
# @Software: PyCharm

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QDockWidget, QLabel, QFrame
from PySide6.QtCore import Qt, Slot
from views.scenario_manager import ScenarioManager
from views.status_bar import StatusBar
from views.tabs.tab_widget import TabWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("情景管理系统")
        self.resize(1200, 600)

        # 设置样式
        self.load_styles()

        # 创建中央部件：标签页
        self.tab_widget = TabWidget()
        self.setCentralWidget(self.tab_widget)

        # 创建情景管理器的 QDockWidget
        self.create_scenario_manager_dock()

        # 创建状态栏的 QDockWidget
        self.create_status_bar_dock()



    def create_scenario_manager_dock(self):
        # 创建 QDockWidget
        dock = QDockWidget("情景管理器", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable)

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
        dock.setWidget(frame)

        # 将 QDockWidget 添加到主窗口的左侧
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        # 连接信号
        self.scenario_manager.scenario_selected.connect(self.on_scenario_selected)

    def create_status_bar_dock(self):
        # 创建 QDockWidget
        dock_status = QDockWidget("状态栏", self)
        dock_status.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_status.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable)

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
        dock_status.setWidget(frame_status)

        # 使用 splitDockWidget 将状态栏 dock 分割到情景管理器 dock 的下方
        scenario_dock = self.findChild(QDockWidget, "情景管理器")
        if scenario_dock:
            self.splitDockWidget(scenario_dock, dock_status, Qt.BottomDockWidgetArea)
        else:
            # 如果情景管理器未找到，直接添加
            self.addDockWidget(Qt.LeftDockWidgetArea, dock_status)

    @Slot(int, str, str)
    def on_scenario_selected(self, scenario_id, scenario_name, scenario_description):
        # 更新状态栏显示情景名称、状态和描述
        self.status_bar_widget.update_status(scenario_name, "正常", scenario_description)

    def load_styles(self):
        try:
            with open("resources/styles/style.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading style.qss: {e}")
