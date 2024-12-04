# scenario_manager.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout,
    QMessageBox, QLineEdit, QListWidgetItem, QFrame, QLabel, QDialog, QTextEdit
)
from PySide6.QtGui import QIcon, QFont, QCursor
from PySide6.QtCore import Signal, Slot, Qt, QTimer, QPoint


class ScenarioDialog(QDialog):
    def __init__(self, parent=None, scenario=None):
        super().__init__(parent)
        self.setWindowTitle("情景信息")
        self.scenario = scenario
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 描述输入
        desc_layout = QVBoxLayout()
        desc_label = QLabel("描述:")
        self.desc_input = QTextEdit()
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)

        # 按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 连接信号
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # 如果是编辑模式，填充现有数据
        if self.scenario:
            self.name_input.setText(self.scenario['name'])
            self.desc_input.setText(self.scenario['description'])

    def get_data(self):
        """获取输入的数据"""
        name = self.name_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        return name, description


class CustomToolTip(QLabel):
    def __init__(self, text, parent=None, duration=3000):
        super().__init__(parent)

        # 设置提示框的文本
        self.setText(text)

        # 设置样式表，定义圆角、背景色、阴影等
        self.setStyleSheet("""
            QLabel {
                background-color: #f7f7f7;
                color: #333333;
                border: none;             /* 去掉边框 */
                border-radius: 8px;       /* 圆角 */
                padding: 8px;             /* 内边距 */
                font-size: 11pt;          /* 字体大小 */
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.15); /* 添加轻微阴影 */
            }
        """)

        # 设置窗口类型为 ToolTip，无边框和阴影
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

        # 创建定时器，用于控制提示框的显示时间
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # 只触发一次
        self.timer.timeout.connect(self.hide)  # 超时后隐藏提示框
        self.timer.start(duration)  # 设置显示时长（毫秒）

    def show_at(self, pos):
        """显示提示框在指定位置"""
        self.move(pos)  # 移动到指定位置
        self.show()  # 显示提示框


class ScenarioManager(QWidget):
    scenario_selected = Signal(int, str, str)
    add_requested = Signal()
    edit_requested = Signal(int)    # 支持单选编辑
    delete_requested = Signal(int)  # 支持单选删除

    def __init__(self):
        super().__init__()

        self.setObjectName("ScenarioManager")
        self.init_ui()
        self.current_tooltip = None  # 用于追踪当前显示的 ToolTip
        self.list_widget.setFocusPolicy(Qt.NoFocus)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # 减少整体边距
        layout.setSpacing(5)  # 减少整体间距

        # 搜索功能
        self.init_search(layout)

        # 分隔线
        self.init_separator(layout)

        # 操作按钮组
        self.init_buttons(layout)

        # 情景列表
        self.init_list_widget(layout)

    def init_search(self, parent_layout):
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入情景名称进行查找...")
        self.search_input.setFont(QFont("Segoe UI", 10))
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self.real_time_search)  # 实现实时搜索

        search_layout.addWidget(self.search_input)
        parent_layout.addLayout(search_layout)

    def init_separator(self, parent_layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(2)  # 确保分隔线有足够的高度显示
        line.setStyleSheet("""
            QFrame {
                background-color: #dcdcdc;  /* 设置分隔线颜色 */
            }
        """)
        parent_layout.addWidget(line)

    def init_buttons(self, parent_layout):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)  # 减少按钮之间的间距
        button_layout.setContentsMargins(0, 5, 0, 5)  # 减少按钮组的边距

        # 使用辅助方法创建按钮
        self.add_button = self.create_button("➕ 增加", "resources/icons/add.png", self.on_add_requested)
        self.edit_button = self.create_button("✏️ 修改", "resources/icons/edit.png", self.on_edit_requested)
        self.delete_button = self.create_button("❌ 删除", "resources/icons/delete.png", self.on_delete_requested)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        parent_layout.addLayout(button_layout)

    def create_button(self, text, icon_path, callback):
        button = QPushButton(text)
        button.setIcon(QIcon(icon_path))
        button.setToolTip(text)
        button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        button.setFixedHeight(35)  # 调整按钮高度
        button.clicked.connect(callback)
        return button

    def init_list_widget(self, parent_layout):
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ScenarioList")
        self.list_widget.setMouseTracking(True)  # 开启鼠标追踪以支持悬浮提示
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)  # 支持单选
        parent_layout.addWidget(self.list_widget)

        # 信号与槽
        self.list_widget.itemClicked.connect(self.select_scenario)
        self.list_widget.itemEntered.connect(self.show_tooltip)  # 悬浮显示描述

        # 启用项悬浮事件
        self.list_widget.setMouseTracking(True)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("""
            QListWidget::item:hover {
                background-color: #e6f7ff;
            }
            QListWidget::item:selected {
                border: none; /* 移除选中时的边框 */
                background-color: #cceeff; /* 选中项背景色 */
            }
        """)

    @Slot(QListWidgetItem)
    def select_scenario(self, item):
        scenario_id = item.data(Qt.UserRole)
        scenario_name = item.text().split(" - ")[0]  # 仅获取名称部分
        scenario_description = item.data(Qt.UserRole + 1)

        reply = QMessageBox.question(
            self, '确认选择', f'您确定要选择情景 "{scenario_name}" 吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.scenario_selected.emit(scenario_id, scenario_name, scenario_description)
        else:
            QMessageBox.information(self, "取消选择", "您已取消选择情景。")

    @Slot(list)
    def populate_scenarios(self, scenarios):
        """填充情景列表"""
        self.list_widget.clear()
        self.scenarios = scenarios  # 存储完整的情景数据以支持查找功能
        for scenario in scenarios:
            description = scenario.description
            # 如果描述超过8个字，用 "..." 替代
            if len(description) > 8:
                description = description[:8] + "..."
            item = QListWidgetItem(f"{scenario.name} - {description}")
            item.setData(Qt.UserRole, scenario.id)
            item.setData(Qt.UserRole + 1, scenario.description)
            self.list_widget.addItem(item)

    @Slot(str)
    def real_time_search(self, text):
        """实时搜索情景"""
        query = text.strip().lower()
        self.list_widget.clear()
        for scenario in self.scenarios:
            if query in scenario['name'].lower():  # 忽略大小写匹配
                description = scenario['description']
                if len(description) > 8:
                    description = description[:8] + "..."
                item = QListWidgetItem(f"{scenario['name']} - {description}")
                item.setData(Qt.UserRole, scenario['id'])
                item.setData(Qt.UserRole + 1, scenario['description'])
                self.list_widget.addItem(item)

        if self.list_widget.count() == 0 and query:
            QMessageBox.information(self, "无结果", "未找到匹配的情景，请尝试其他关键字。")

    @Slot(QListWidgetItem)
    def show_tooltip(self, item):
        """鼠标悬浮显示完整描述"""
        if item:
            full_description = item.data(Qt.UserRole + 1)  # 获取完整描述

            # 隐藏上一个提示框
            if self.current_tooltip:
                self.current_tooltip.hide()
                self.current_tooltip.deleteLater()  # 删除之前的提示框

            # 计算显示位置（鼠标下方偏移一点）
            mouse_pos = QCursor.pos()  # 获取全局鼠标位置
            offset_pos = QPoint(mouse_pos.x() + 10, mouse_pos.y() + 20)  # 向右和向下偏移

            # 创建新的 ToolTip
            self.current_tooltip = CustomToolTip(full_description, self, duration=5000)  # 显示 5 秒
            self.current_tooltip.show_at(offset_pos)

    def leaveEvent(self, event):
        """鼠标离开时隐藏提示框"""
        if self.current_tooltip:
            self.current_tooltip.hide()
            self.current_tooltip.deleteLater()
            self.current_tooltip = None
        super().leaveEvent(event)

    @Slot()
    def on_add_requested(self):
        """处理增加情景的逻辑"""
        dialog = ScenarioDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "输入错误", "情景名称不能为空。")
                return
            # 检查是否有重复名称
            for scenario in self.scenarios:
                if scenario['name'] == name:
                    QMessageBox.warning(self, "重复情景", "该情景名称已存在。")
                    return
            # 添加情景
            scenario_id = self.add_scenario(name, description)
            QMessageBox.information(self, "添加成功", f"情景 '{name}' 已成功添加。")
            self.populate_scenarios(self.get_all_scenarios())
            # 发射信号
            self.add_requested.emit()

    @Slot(int)
    def on_edit_requested(self, scenario_id):
        """处理编辑情景的逻辑"""
        scenario = self.get_scenario_by_id(scenario_id)
        if scenario:
            dialog = ScenarioDialog(self, scenario)
            if dialog.exec() == QDialog.Accepted:
                name, description = dialog.get_data()
                if not name:
                    QMessageBox.warning(self, "输入错误", "情景名称不能为空。")
                    return
                # 检查是否有重复名称
                for s in self.scenarios:
                    if s['name'] == name and s['id'] != scenario_id:
                        QMessageBox.warning(self, "重复情景", "该情景名称已存在。")
                        return
                # 编辑情景
                self.edit_scenario(scenario_id, name, description)
                QMessageBox.information(self, "修改成功", f"情景 '{name}' 已成功修改。")
                self.populate_scenarios(self.get_all_scenarios())
                # 发射信号
                self.edit_requested.emit(scenario_id)
        else:
            QMessageBox.warning(self, "错误", "未找到要编辑的情景。")

    @Slot(int)
    def on_delete_requested(self, scenario_id):
        """处理删除情景的逻辑"""
        scenario = self.get_scenario_by_id(scenario_id)
        if scenario:
            reply = QMessageBox.question(
                self, '确认删除',
                f'您确定要删除情景 "{scenario["name"]}" 吗?',
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.delete_scenario(scenario_id)
                QMessageBox.information(self, "删除成功", "情景已成功删除。")
                self.populate_scenarios(self.get_all_scenarios())
                # 发射信号
                self.delete_requested.emit(scenario_id)
        else:
            QMessageBox.warning(self, "错误", "未找到要删除的情景。")

    def add_scenario(self, name, description):
        """添加情景并返回新情景的ID"""
        new_id = max([s['id'] for s in self.scenarios], default=0) + 1
        new_scenario = {'id': new_id, 'name': name, 'description': description}
        self.scenarios.append(new_scenario)
        return new_id

    def edit_scenario(self, scenario_id, name, description):
        """编辑指定ID的情景"""
        for scenario in self.scenarios:
            if scenario['id'] == scenario_id:
                scenario['name'] = name
                scenario['description'] = description
                break

    def delete_scenario(self, scenario_id):
        """删除指定ID的情景"""
        self.scenarios = [s for s in self.scenarios if s['id'] != scenario_id]

    def get_all_scenarios(self):
        """返回所有情景"""
        return self.scenarios

    def get_scenario_by_id(self, scenario_id):
        """根据ID获取情景"""
        for scenario in self.scenarios:
            if scenario['id'] == scenario_id:
                return scenario
        return None