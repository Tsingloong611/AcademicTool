# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: main_window.py
# @Software: PyCharm

import os
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QDockWidget, QFrame, QSizePolicy
from PySide6.QtCore import Qt

from controllers import ScenarioController
from views.scenario_manager import ScenarioManager
from views.status_bar import StatusBar
from views.tabs.tab_widget import TabWidget

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()



        # 设置主窗口标题
        self.setWindowTitle("基于认知数字孪生的城市道路应急情景推演工具")
        self.setObjectName("MainWindow")

        self.db_manager = db_manager  # 保存数据库管理器实例

        # 创建中央部件：标签页
        self.tab_widget = TabWidget(self)
        self.tab_widget.setObjectName("TabWidget")
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.tab_widget)

        # 创建情景管理器的 QDockWidget
        self.create_scenario_manager_dock()

        # 创建状态栏的 QDockWidget
        self.create_status_bar_dock()

        # 创建控制器并连接
        self.controller = ScenarioController(
            scenario_manager=self.scenario_manager,
            status_bar=self.status_bar_widget,
            tab_widget=self.tab_widget,
            db_manager=self.db_manager
        )

        # 自动加载情景数据
        self.controller.load_scenarios()

    def create_status_bar_dock(self):
        """创建状态栏的 QDockWidget"""
        self.status_bar_dock = QDockWidget("状态栏", self)
        self.status_bar_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.status_bar_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetFloatable
        )
        self.status_bar_dock.setObjectName("StatusBarDock")

        frame_status = QFrame()
        frame_status.setObjectName("StatusBarFrame")
        layout_status = QVBoxLayout(frame_status)
        layout_status.setContentsMargins(0, 0, 0, 0)
        layout_status.setSpacing(10)

        self.status_bar_widget = StatusBar()
        self.status_bar_widget.setObjectName("StatusBarWidget")
        layout_status.addWidget(self.status_bar_widget)

        self.status_bar_dock.setWidget(frame_status)

        # Ensure the dock widget has a dynamic resizing policy
        self.status_bar_dock.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        # Place the status bar below the scenario manager
        self.splitDockWidget(self.scenario_manager_dock, self.status_bar_dock, Qt.Vertical)

    def create_scenario_manager_dock(self):
        """创建情景管理器的 QDockWidget"""
        self.scenario_manager_dock = QDockWidget("情景管理器", self)
        self.scenario_manager_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.scenario_manager_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetFloatable
        )
        self.scenario_manager_dock.setObjectName("ScenarioManagerDock")

        frame = QFrame()
        frame.setObjectName("ScenarioManagerFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.scenario_manager = ScenarioManager()
        self.scenario_manager.setObjectName("ScenarioManager")
        layout.addWidget(self.scenario_manager)

        self.scenario_manager_dock.setWidget(frame)

        # Ensure the dock widget has a dynamic resizing policy
        self.scenario_manager_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.scenario_manager_dock)
