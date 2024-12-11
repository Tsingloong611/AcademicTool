# scenario_manager.py

# -*- coding: utf-8 -*-
# @FileName: scenario_manager.py
# @Software: PyCharm
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout,
    QLineEdit, QListWidgetItem, QFrame, QLabel, QDialog, QTextEdit, QStackedLayout
)
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtCore import Signal, Slot, Qt, QTimer, QPoint, QEvent
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog

class ScenarioDialog(QDialog):
    def __init__(self, parent=None, scenario=None):
        super().__init__(parent)
        self.setWindowTitle("情景信息")
        self.setObjectName("ScenarioDialog")
        self.scenario = scenario
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        name_label.setObjectName("NameLabel")

        self.name_input = QLineEdit()
        self.name_input.setObjectName("NameInput")
        self.name_input.setPlaceholderText("请输入情景名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        desc_layout = QVBoxLayout()
        desc_label = QLabel("描述:")
        desc_label.setObjectName("DescriptionLabel")

        self.desc_input = QTextEdit()
        self.desc_input.setObjectName("DescriptionInput")
        self.desc_input.setPlaceholderText("请输入情景描述")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("SaveButton")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("CancelButton")

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        if self.scenario:
            self.name_input.setText(self.scenario.name)
            self.desc_input.setText(self.scenario.description)

    def get_data(self):
        name = self.name_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        return name, description

class CustomToolTip(QLabel):
    def __init__(self, text, parent=None, duration=3000):
        super().__init__(parent)
        self.text = text.strip() if text and text.strip() else "没有描述信息"
        self.setText(self.text)
        self.setObjectName("CustomToolTip")
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self.installEventFilter(self)

    def show_at(self, pos, duration=3000):
        if not self.text.strip():
            return
        self.move(pos)
        self.show()
        self.timer.start(duration)

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Enter:
                self.timer.stop()
            elif event.type() == QEvent.Leave:
                self.hide()
        return super().eventFilter(obj, event)

class ScenarioManager(QWidget):
    scenario_selected = Signal(int, str, str)
    add_requested = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("ScenarioManager")
        self.current_tooltip = None
        self.init_ui()
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.viewport().installEventFilter(self)
        self.scenarios = []

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.init_buttons(layout)
        self.init_separator(layout)
        self.init_search(layout)
        self.init_list_widget(layout)
        self.search_input.setObjectName("SearchInput")
        self.list_widget.setObjectName("ScenarioList")
        self.placeholder_label.setObjectName("PlaceholderLabel")
        self.no_result_label.setObjectName("NoResultLabel")
        self.add_button.setObjectName("新建Button")
        self.edit_button.setObjectName("修改Button")
        self.delete_button.setObjectName("删除Button")

    def init_search(self, parent_layout):
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("输入情景名称进行查找...")
        self.search_input.textChanged.connect(self.real_time_search)

        search_layout.addWidget(self.search_input)
        parent_layout.addLayout(search_layout)

    def init_separator(self, parent_layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("SeparatorLine")
        parent_layout.addWidget(line)

    def init_buttons(self, parent_layout):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 5, 0, 5)

        self.add_button = self.create_button("新建", "add.png", self.add_requested.emit)
        self.edit_button = self.create_button("修改", "edit.png", self.on_edit_requested)
        self.delete_button = self.create_button("删除", "delete.png", self.on_delete_requested)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        parent_layout.addLayout(button_layout)

    def create_button(self, text, icon_name, callback):
        button = QPushButton(text)
        button.setObjectName(f"{text}Button")
        button.setIcon(QIcon(os.path.join("resources", "icons", icon_name)))
        button.setToolTip(text)
        button.clicked.connect(callback)
        return button

    def init_list_widget(self, parent_layout):
        # 创建列表小部件
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ScenarioList")
        self.list_widget.setMouseTracking(True)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)

        # 创建占位标签
        self.placeholder_label = QLabel("请添加情景")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setObjectName("PlaceholderLabel")
        self.placeholder_label.setStyleSheet("color: gray; font-style: italic;")

        # 创建“无匹配结果”标签
        self.no_result_label = QLabel("无匹配结果")
        self.no_result_label.setAlignment(Qt.AlignCenter)
        self.no_result_label.setObjectName("NoResultLabel")
        # 样式已在 widgets.qss 中定义

        # 创建一个带有 QStackedLayout 的容器小部件，用于在列表和占位标签之间切换
        self.scenario_stack = QStackedLayout()
        self.scenario_stack.setContentsMargins(0, 0, 0, 0)

        scenario_container = QWidget()
        scenario_container.setLayout(self.scenario_stack)
        self.scenario_stack.addWidget(self.list_widget)       # 索引 0
        self.scenario_stack.addWidget(self.placeholder_label) # 索引 1
        self.scenario_stack.addWidget(self.no_result_label)   # 索引 2

        parent_layout.addWidget(scenario_container)

        # 连接列表信号
        self.list_widget.itemClicked.connect(self.select_scenario)
        self.list_widget.itemEntered.connect(self.show_tooltip)

    @Slot(QListWidgetItem)
    def select_scenario(self, item):
        scenario_id = item.data(Qt.UserRole)
        scenario_name = item.text().split(" - ")[0]
        scenario_description = item.data(Qt.UserRole + 1)

        reply = CustomQuestionDialog("确认选择", f'您确定要选择情景 "{scenario_name}" 吗?').ask()

        if reply:
            self.scenario_selected.emit(scenario_id, scenario_name, scenario_description)
        else:
            CustomInformationDialog("取消选择", "您已取消选择情景。").get_result()

    @Slot(list)
    def populate_scenarios(self, scenarios):
        self.list_widget.clear()
        self.scenarios = scenarios
        for scenario in scenarios:
            description = scenario.description
            if len(description) > 8:
                short_desc = description[:8] + "..."
            else:
                short_desc = description
            item = QListWidgetItem(f"{scenario.name} - {short_desc}")
            item.setData(Qt.UserRole, scenario.id)
            item.setData(Qt.UserRole + 1, scenario.description)
            self.list_widget.addItem(item)

        # 根据是否有情景更新堆叠布局
        if self.scenarios:
            self.scenario_stack.setCurrentIndex(0)  # 显示列表
        else:
            self.scenario_stack.setCurrentIndex(1)  # 显示占位标签

    @Slot(str)
    def real_time_search(self, text):
        query = text.strip().lower()
        self.list_widget.clear()
        found = False
        for scenario in self.scenarios:
            if query in scenario.name.lower():
                description = scenario.description
                if len(description) > 8:
                    description = description[:8] + "..."
                item = QListWidgetItem(f"{scenario.name} - {description}")
                item.setData(Qt.UserRole, scenario.id)
                item.setData(Qt.UserRole + 1, scenario.description)
                self.list_widget.addItem(item)
                found = True

        # 根据搜索结果更新堆叠布局
        if found:
            self.scenario_stack.setCurrentIndex(0)  # 显示列表
        elif query:
            self.scenario_stack.setCurrentIndex(2)  # 显示“无匹配结果”
        else:
            if self.scenarios:
                self.scenario_stack.setCurrentIndex(0)  # 显示列表
            else:
                self.scenario_stack.setCurrentIndex(1)  # 显示占位标签

    @Slot(QListWidgetItem)
    def show_tooltip(self, item):
        if item:
            full_description = item.data(Qt.UserRole + 1)
            if self.current_tooltip:
                self.current_tooltip.hide()
                self.current_tooltip.deleteLater()

            if not full_description.strip():
                full_description = "没有描述信息"

            mouse_pos = QCursor.pos()
            offset_pos = QPoint(mouse_pos.x() + 10, mouse_pos.y() + 20)

            self.current_tooltip = CustomToolTip(full_description, None, duration=5000)
            self.current_tooltip.show_at(offset_pos)
            self.current_tooltip.raise_()

    def eventFilter(self, obj, event):
        if obj == self.list_widget.viewport():
            if event.type() == QEvent.MouseMove:
                pos = event.position().toPoint()
                item = self.list_widget.itemAt(pos)
                if not item:
                    if self.current_tooltip:
                        self.current_tooltip.hide()
                        self.current_tooltip.deleteLater()
                        self.current_tooltip = None
            elif event.type() == QEvent.Leave:
                if self.current_tooltip:
                    self.current_tooltip.hide()
                    self.current_tooltip.deleteLater()
                    self.current_tooltip = None
        return super().eventFilter(obj, event)

    @Slot()
    def on_edit_requested(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            CustomWarningDialog("修改失败", "请先选择要修改的情景。").get_result()
            return
        scenario_id = selected_items[0].data(Qt.UserRole)
        self.edit_requested.emit(scenario_id)

    @Slot()
    def on_delete_requested(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            CustomWarningDialog("删除失败", "请先选择要删除的情景。").get_result()
            return

        scenario_names = [item.text().split(" - ")[0] for item in selected_items]
        scenario_id = selected_items[0].data(Qt.UserRole)
        scenario_name = scenario_names[0]
        reply = CustomQuestionDialog("确认删除", f'您确定要删除情景 "{scenario_name}" 吗?').ask()

        if reply:
            self.delete_requested.emit(scenario_id)
            CustomInformationDialog("删除成功", "情景已成功删除。").get_result()
        else:
            CustomInformationDialog("取消删除", "您已取消删除操作。").get_result()

    def add_scenario(self, scenario):
        """添加情景并更新视图。"""
        self.scenarios.append(scenario)
        self.populate_scenarios(self.scenarios)

    def remove_scenario_by_id(self, scenario_id):
        """根据 ID 删除情景并更新视图。"""
        self.scenarios = [s for s in self.scenarios if s.id != scenario_id]
        self.populate_scenarios(self.scenarios)

    def update_scenario(self, updated_scenario):
        """更新情景并刷新视图。"""
        for idx, scenario in enumerate(self.scenarios):
            if scenario.id == updated_scenario.id:
                self.scenarios[idx] = updated_scenario
                break
        self.populate_scenarios(self.scenarios)
