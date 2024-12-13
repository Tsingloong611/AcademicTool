import sys
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QGridLayout, QHeaderView, QDialog, QFormLayout,
    QDialogButtonBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QUrl, QObject
from PySide6.QtGui import QIntValidator
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.tabs.element_setting import CustomInformationDialog




# 通信桥接类，用于与 JavaScript 交互
class MapBridge(QObject):
    location_selected = Signal(str)

    @Slot(str)
    def sendLocation(self, location):
        self.location_selected.emit(location)


# 地图选择对话框
class MapSelectionDialog(QDialog):
    location_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择位置")
        self.resize(800, 600)
        self.bridge = MapBridge()
        self.bridge.location_selected.connect(self.on_location_selected)
        self.selected_location = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 设置 QWebEngineView
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        # 设置 QWebChannel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.map_view.page().setWebChannel(self.channel)

        # 加载内嵌的 HTML 地图
        self.map_view.setHtml(self.get_map_html(), QUrl("qrc:///"))

        # 确认和取消按钮
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("确认选择")
        self.confirm_button.setEnabled(False)  # 初始禁用，直到选择位置
        self.cancel_button = QPushButton("取消")
        button_layout.addStretch()
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_map_html(self):
        # 使用 Leaflet.js 创建交互式地图
        # 通过 QWebChannel 发送点击位置到 Python
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>地图选择</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                  integrity="sha256-sA+e2A5QnpF+4S2vXwXoBw6lgXHI7fVGM3e3z+oA64E="
                  crossorigin=""/>
            <style>
                html, body, #map { height: 100%; margin: 0; padding: 0; }
            </style>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                    integrity="sha256-o9N1jv0FQJmH+v8XkLG0+ZPrunfZzE9sThnjG+uHaxE="
                    crossorigin=""></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([39.915, 116.404], 12); // 默认北京

                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);

                var marker;

                // Initialize QWebChannel
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.bridge = channel.objects.bridge;
                });

                map.on('click', function(e) {
                    var lat = e.latlng.lat.toFixed(6);
                    var lng = e.latlng.lng.toFixed(6);
                    var location = lat + "," + lng;
                    if (marker) {
                        map.removeLayer(marker);
                    }
                    marker = L.marker(e.latlng).addTo(map);
                    bridge.sendLocation(location);
                });
            </script>
        </body>
        </html>
        """

    @Slot(str)
    def on_location_selected(self, location):
        self.selected_location = location
        self.confirm_button.setEnabled(True)
        CustomInformationDialog("位置选择", f"已选择位置: {location}").exec()

    def accept(self):
        if self.selected_location:
            self.location_selected.emit(self.selected_location)
            super().accept()
        else:
            CustomWarningDialog("提示", "请先选择一个位置。").exec()


# 资源管理对话框
class ResourceManagementDialog(QDialog):
    resource_updated = Signal(list)  # Signal to emit the updated resource list

    # 定义资源类型的枚举
    RESOURCE_TYPES = {
        "人员": ["救援人员", "医疗人员", "后勤人员"],
        "物资": ["医疗物资", "食品", "饮用水"],
        "车辆": ["救护车", "消防车", "运输车"]
    }

    def __init__(self, resources=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("资源管理")
        self.resources = resources if resources else []
        self.init_ui()
        self.resize(800, 600)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 资源表格
        self.resource_table = QTableWidget(0, 4)
        self.resource_table.setHorizontalHeaderLabels(["资源", "类型", "数量", "位置"])
        self.apply_three_line_table_style(self.resource_table)
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止直接编辑
        self.resource_table.verticalHeader().setVisible(False)  # 隐藏行号
        layout.addWidget(self.resource_table)

        self.load_resources()

        # 按钮布局
        button_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        edit_btn = QPushButton("修改")
        delete_btn = QPushButton("删除")
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        layout.addLayout(button_layout)

        add_btn.clicked.connect(self.add_resource)
        edit_btn.clicked.connect(self.edit_resource)
        delete_btn.clicked.connect(self.delete_resource)

        # 确认和取消按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_changes)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def load_resources(self):
        self.resource_table.setRowCount(0)
        for resource in self.resources:
            self.add_resource_to_table(resource)

    def add_resource_to_table(self, resource):
        row_position = self.resource_table.rowCount()
        self.resource_table.insertRow(row_position)
        self.resource_table.setItem(row_position, 0, QTableWidgetItem(resource["资源"]))
        self.resource_table.setItem(row_position, 1, QTableWidgetItem(resource["类型"]))
        self.resource_table.setItem(row_position, 2, QTableWidgetItem(str(resource["数量"])))
        self.resource_table.setItem(row_position, 3, QTableWidgetItem(resource["位置"]))

    def add_resource(self):
        dialog = SingleResourceDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            resource = dialog.get_resource()
            self.resources.append(resource)
            self.add_resource_to_table(resource)

    def edit_resource(self):
        selected_items = self.resource_table.selectedItems()
        if not selected_items:
            CustomWarningDialog("提示", "请选择要修改的资源。").exec()
            return
        row = selected_items[0].row()
        resource = {
            "资源": self.resource_table.item(row, 0).text(),
            "类型": self.resource_table.item(row, 1).text(),
            "数量": int(self.resource_table.item(row, 2).text()),
            "位置": self.resource_table.item(row, 3).text()
        }
        dialog = SingleResourceDialog(resource, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated_resource = dialog.get_resource()
            self.resources[row] = updated_resource
            self.resource_table.setItem(row, 0, QTableWidgetItem(updated_resource["资源"]))
            self.resource_table.setItem(row, 1, QTableWidgetItem(updated_resource["类型"]))
            self.resource_table.setItem(row, 2, QTableWidgetItem(str(updated_resource["数量"])))
            self.resource_table.setItem(row, 3, QTableWidgetItem(updated_resource["位置"]))

    def delete_resource(self):
        selected_items = self.resource_table.selectedItems()
        if not selected_items:
            CustomWarningDialog("提示", "请选择要删除的资源。").exec()
            return
        row = selected_items[0].row()
        confirm = CustomQuestionDialog("确认删除", "确定要删除选中的资源吗？").ask()
        if confirm:
            self.resource_table.removeRow(row)
            del self.resources[row]

    def accept_changes(self):
        self.resource_updated.emit(self.resources)
        self.accept()

    def apply_three_line_table_style(self, table: QTableWidget):
        """应用三线表样式到指定的表格并动态调整列宽"""
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black; /* 底部线 */
            }
            QHeaderView::section {
                border-top: 1px solid black;    /* 表头顶部线 */
                border-bottom: 1px solid black; /* 表头底部线 */
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center; /* 表头内容居中 */
            }
            QTableWidget::item {
                border: none; /* 中间行无边框 */
                padding: 5px;
                text-align: center; /* 单元格内容居中 */
            }
            /* 设置选中行的样式 */
            QTableWidget::item:selected {
                background-color: #cce5ff; /* 选中背景颜色 */
                color: black;             /* 选中文字颜色 */
                border: none;             /* 选中时无边框 */
            }
            QTableWidget:focus {
                outline: none; /* 禁用焦点边框 */
            }
        """)
        # 动态调整列宽
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)


# 单个资源添加/编辑对话框
class SingleResourceDialog(QDialog):
    def __init__(self, resource=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加资源" if resource is None else "修改资源")
        self.resource = resource
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.resource_combo = QComboBox()
        self.resource_combo.addItems(["人员", "物资", "车辆"])
        form_layout.addRow("资源:", self.resource_combo)

        # 类型根据资源类型枚举
        self.type_combo = QComboBox()
        self.update_type_options(self.resource_combo.currentText())
        form_layout.addRow("类型:", self.type_combo)

        # 连接资源类型下拉框变化信号，动态更新类型选项
        self.resource_combo.currentTextChanged.connect(self.update_type_options)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1000)
        form_layout.addRow("数量:", self.quantity_spin)

        self.location_input = QLineEdit()
        self.location_input.setReadOnly(True)
        self.location_button = QPushButton("选择位置")
        self.location_button.clicked.connect(self.select_location)
        location_layout = QHBoxLayout()
        location_layout.addWidget(self.location_input)
        location_layout.addWidget(self.location_button)
        form_layout.addRow("位置:", location_layout)

        layout.addLayout(form_layout)

        # 确认和取消按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        if self.resource:
            self.resource_combo.setCurrentText(self.resource["资源"])
            self.type_combo.setCurrentText(self.resource["类型"])
            self.quantity_spin.setValue(self.resource["数量"])
            self.location_input.setText(self.resource["位置"])

    def update_type_options(self, resource_type):
        self.type_combo.clear()
        if resource_type in ResourceManagementDialog.RESOURCE_TYPES:
            self.type_combo.addItems(ResourceManagementDialog.RESOURCE_TYPES[resource_type])
        else:
            self.type_combo.addItem("未知类型")

    def select_location(self):
    # dialog = MapSelectionDialog(self)
    # dialog.location_selected.connect(self.set_location)
    # dialog.exec()
        # 手动输入地址
        self.location_input.setText(QInputDialog.getText(self, "手动输入地址", "请输入地址：")[0])
        # 设置地址
        self.set_location(self.location_input.text())


    @Slot(str)
    def set_location(self, location):
        self.location_input.setText(location)

    def validate_and_accept(self):
        resource = self.resource_combo.currentText()
        type_ = self.type_combo.currentText().strip()
        quantity = self.quantity_spin.value()
        location = self.location_input.text().strip()

        if not type_:
            CustomWarningDialog("提示", "类型不能为空。").exec()
            return
        if not location:
            CustomWarningDialog("提示", "位置不能为空。").exec()
            return

        self.resource = {
            "资源": resource,
            "类型": type_,
            "数量": quantity,
            "位置": location
        }
        self.accept()

    def get_resource(self):
        return self.resource


# 主界面类
class ConditionSettingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("应急预案设置")
        self.init_ui()

    def init_ui(self):
        self.set_stylesheet()
        main_layout = QVBoxLayout()

        # 应急行为设置
        behavior_group = QGroupBox("应急行为设置")
        behavior_layout = QGridLayout()

        self.behaviors = ["救助", "牵引", "抢修", "消防"]
        self.behavior_duration = {}

        for i, behavior in enumerate(self.behaviors):
            label = QLabel(f"{behavior}时长：")
            hour_spin = QSpinBox()
            hour_spin.setRange(0, 23)
            hour_spin.setSuffix(" 小时")
            hour_spin.setValue(0)
            hour_spin.setFocusPolicy(Qt.StrongFocus)  # 允许键盘输入
            hour_spin.setWrapping(False)
            hour_spin.wheelEvent = lambda event: None  # 禁用滚轮

            minute_spin = QSpinBox()
            minute_spin.setRange(0, 59)
            minute_spin.setSuffix(" 分钟")
            minute_spin.setValue(0)
            minute_spin.setFocusPolicy(Qt.StrongFocus)  # 允许键盘输入
            minute_spin.setWrapping(False)
            minute_spin.wheelEvent = lambda event: None  # 禁用滚轮

            # 连接分钟变化信号，自动增加小时
            minute_spin.valueChanged.connect(
                lambda value, b=behavior, m_spin=minute_spin, h_spin=hour_spin: self.handle_minute_change(b, value, m_spin, h_spin)
            )

            self.behavior_duration[behavior] = (hour_spin, minute_spin)
            behavior_layout.addWidget(label, i, 0)
            behavior_layout.addWidget(hour_spin, i, 1)
            behavior_layout.addWidget(minute_spin, i, 2)

        behavior_group.setLayout(behavior_layout)
        main_layout.addWidget(behavior_group)

        # 应急资源设置
        resource_group = QGroupBox("应急资源设置")
        resource_layout = QVBoxLayout()

        # 资源表格
        self.resource_table = QTableWidget(0, 4)
        self.resource_table.setHorizontalHeaderLabels(["资源", "类型", "数量", "位置"])
        self.apply_three_line_table_style(self.resource_table)
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止直接编辑
        self.resource_table.verticalHeader().setVisible(False)  # 隐藏行号
        self.resource_table.setAlternatingRowColors(True)
        resource_layout.addWidget(self.resource_table)

        # 设置资源按钮
        set_resource_btn = QPushButton("设置资源")
        set_resource_btn.clicked.connect(self.open_resource_dialog)
        resource_layout.addWidget(set_resource_btn)

        resource_group.setLayout(resource_layout)
        main_layout.addWidget(resource_group)

        # 保存预案，执行推演按钮
        execute_btn = QPushButton("保存预案，执行推演")
        execute_btn.clicked.connect(self.save_and_execute)
        main_layout.addWidget(execute_btn)

        # 证据更新区域
        evidence_group = QGroupBox("证据更新")
        evidence_layout = QVBoxLayout()
        self.evidence_table = QTableWidget(0, 3)
        self.evidence_table.setHorizontalHeaderLabels(["要素节点", "状态", "概率"])
        self.apply_three_line_table_style(self.evidence_table)
        self.evidence_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止直接编辑
        self.evidence_table.verticalHeader().setVisible(False)  # 隐藏行号
        self.evidence_table.setAlternatingRowColors(True)
        evidence_layout.addWidget(self.evidence_table)
        evidence_group.setLayout(evidence_layout)
        main_layout.addWidget(evidence_group)

        # 推演结果区域
        simulation_group = QGroupBox("推演结果")
        simulation_layout = QVBoxLayout()
        self.simulation_table = QTableWidget(0, 7)
        # 列头: 预案名字, 推演前较好, 推演前中等, 推演前较差, 推演后较好, 推演后中等, 推演后较差
        self.simulation_table.setHorizontalHeaderLabels([
            "预案名字",
            "推演前-较好", "推演前-中等", "推演前-较差",
            "推演后-较好", "推演后-中等", "推演后-较差"
        ])
        self.apply_three_line_table_style(self.simulation_table)
        self.simulation_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止直接编辑
        self.simulation_table.verticalHeader().setVisible(False)  # 隐藏行号
        self.simulation_table.setAlternatingRowColors(True)
        simulation_layout.addWidget(self.simulation_table)
        simulation_group.setLayout(simulation_layout)
        main_layout.addWidget(simulation_group)

        self.setLayout(main_layout)

    def handle_minute_change(self, behavior, value, m_spin, h_spin):
        if value >= 60:
            m_spin.setValue(0)
            if h_spin.value() < 23:
                h_spin.setValue(h_spin.value() + 1)
            else:
                h_spin.setValue(23)

    def set_stylesheet(self):
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                font-weight: bold;
                color: #333333;
            }
            QLabel {
                color: #333333;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QTableWidget {
                border: none;
                font-size: 14px;
                background-color: white;
            }
            QHeaderView::section {
                border: 1px solid #ccc;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
                color: black;
            }
            QTableWidget:focus {
                outline: none;
            }
        """)

    def apply_three_line_table_style(self, table: QTableWidget):
        """应用三线表样式到指定的表格并动态调整列宽"""
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black; /* 底部线 */
            }
            QHeaderView::section {
                border-top: 1px solid black;    /* 表头顶部线 */
                border-bottom: 1px solid black; /* 表头底部线 */
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center; /* 表头内容居中 */
            }
            QTableWidget::item {
                border: none; /* 中间行无边框 */
                padding: 5px;
                text-align: center; /* 单元格内容居中 */
            }
            /* 设置选中行的样式 */
            QTableWidget::item:selected {
                background-color: #cce5ff; /* 选中背景颜色 */
                color: black;             /* 选中文字颜色 */
                border: none;             /* 选中时无边框 */
            }
            QTableWidget:focus {
                outline: none; /* 禁用焦点边框 */
            }
        """)
        # 动态调整列宽
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

        # 设置交替行颜色
        table.setAlternatingRowColors(True)

    def open_resource_dialog(self):
        dialog = ResourceManagementDialog(self.get_current_resources(), self)
        dialog.resource_updated.connect(self.update_resource_table)
        dialog.exec()

    def get_current_resources(self):
        resources = []
        for row in range(self.resource_table.rowCount()):
            resource = {
                "资源": self.resource_table.item(row, 0).text(),
                "类型": self.resource_table.item(row, 1).text(),
                "数量": int(self.resource_table.item(row, 2).text()),
                "位置": self.resource_table.item(row, 3).text()
            }
            resources.append(resource)
        return resources

    def update_resource_table(self, resources):
        self.resource_table.setRowCount(0)
        for resource in resources:
            self.add_resource_to_table(resource)

    def add_resource_to_table(self, resource):
        row_position = self.resource_table.rowCount()
        self.resource_table.insertRow(row_position)
        self.resource_table.setItem(row_position, 0, QTableWidgetItem(resource["资源"]))
        self.resource_table.setItem(row_position, 1, QTableWidgetItem(resource["类型"]))
        self.resource_table.setItem(row_position, 2, QTableWidgetItem(str(resource["数量"])))
        self.resource_table.setItem(row_position, 3, QTableWidgetItem(resource["位置"]))

    def save_and_execute(self):
        # 获取应急行为设置
        behavior_settings = {}
        for behavior, (hour_spin, minute_spin) in self.behavior_duration.items():
            total_minutes = hour_spin.value() * 60 + minute_spin.value()
            behavior_settings[behavior] = total_minutes
        print("应急行为设置:", behavior_settings)

        # 获取应急资源设置
        resources = self.get_current_resources()
        print("应急资源设置:", resources)

        # 这里应保存预案并执行推演，更新证据更新和推演结果
        # 这里只是示例，实际逻辑需要根据需求实现

        # 更新证据更新表格
        self.update_evidence_table()

        # 更新推演结果表格
        self.update_simulation_table()

        CustomInformationDialog("成功", "预案已保存并执行推演。").exec()

    def update_evidence_table(self):
        self.evidence_table.setRowCount(0)
        # 示例数据，实际应根据推演结果获取
        evidence_data = [
            {"要素节点": "节点1", "状态": "正常", "概率": "80%"},
            {"要素节点": "节点2", "状态": "异常", "概率": "20%"},
        ]
        for data in evidence_data:
            row_position = self.evidence_table.rowCount()
            self.evidence_table.insertRow(row_position)
            self.evidence_table.setItem(row_position, 0, QTableWidgetItem(data["要素节点"]))
            self.evidence_table.setItem(row_position, 1, QTableWidgetItem(data["状态"]))
            self.evidence_table.setItem(row_position, 2, QTableWidgetItem(data["概率"]))

    def update_simulation_table(self):
        self.simulation_table.setRowCount(0)
        # 示例数据，实际应根据推演结果获取
        simulation_data = [
            {
                "预案名字": "预案A",
                "推演前-较好": "30%",
                "推演前-中等": "50%",
                "推演前-较差": "20%",
                "推演后-较好": "60%",
                "推演后-中等": "30%",
                "推演后-较差": "10%",
            },
            {
                "预案名字": "预案B",
                "推演前-较好": "25%",
                "推演前-中等": "55%",
                "推演前-较差": "20%",
                "推演后-较好": "50%",
                "推演后-中等": "35%",
                "推演后-较差": "15%",
            },
        ]
        for data in simulation_data:
            row_position = self.simulation_table.rowCount()
            self.simulation_table.insertRow(row_position)
            self.simulation_table.setItem(row_position, 0, QTableWidgetItem(data["预案名字"]))
            self.simulation_table.setItem(row_position, 1, QTableWidgetItem(data["推演前-较好"]))
            self.simulation_table.setItem(row_position, 2, QTableWidgetItem(data["推演前-中等"]))
            self.simulation_table.setItem(row_position, 3, QTableWidgetItem(data["推演前-较差"]))
            self.simulation_table.setItem(row_position, 4, QTableWidgetItem(data["推演后-较好"]))
            self.simulation_table.setItem(row_position, 5, QTableWidgetItem(data["推演后-中等"]))
            self.simulation_table.setItem(row_position, 6, QTableWidgetItem(data["推演后-较差"]))

    def reset_inputs(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConditionSettingTab()
    window.resize(1000, 800)
    window.show()
    sys.exit(app.exec())
