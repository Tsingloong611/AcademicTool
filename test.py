from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGroupBox, QHeaderView, QSizePolicy, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt


class CompoundAttributeEditor(QDialog):
    """复合属性编辑窗口"""

    def __init__(self, attribute_name, attribute_type, selected_entities, parent=None):
        super().__init__(parent)
        self.setWindowTitle("复合属性编辑")
        self.resize(800, 600)

        # 当前正在编辑的属性信息
        self.attribute_name = attribute_name
        self.attribute_type = attribute_type

        # 当前复合属性已经选中的实体
        self.selected_entities = selected_entities

        self.init_ui()

    def init_ui(self):
        # 创建复合属性分组框
        resource_group = QGroupBox("复合属性编辑")
        resource_layout = QVBoxLayout()
        resource_layout.setContentsMargins(10, 10, 10, 10)

        # 创建顶部描述信息
        label_layout = QHBoxLayout()
        self.current_behavior_label = QLabel(f"当前正在编辑复合属性：{self.attribute_name}，属性类型：{self.attribute_type}")
        self.current_behavior_label.setAlignment(Qt.AlignCenter)
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:gray;")
        label_layout.addWidget(self.current_behavior_label)

        resource_layout.addLayout(label_layout)

        # 创建表格
        self.resource_table = QTableWidget(0, 5)
        self.resource_table.setHorizontalHeaderLabels(["选中", "实体名称", "类型", "值", "备注"])
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resource_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resource_table.setSelectionMode(QTableWidget.SingleSelection)
        self.resource_table.verticalHeader().setVisible(False)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resource_table.setShowGrid(False)
        self.resource_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply_table_style(self.resource_table)

        # 加载初始实体数据并默认勾选
        self.load_entities()

        resource_layout.addWidget(self.resource_table)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        self.add_resource_btn = QPushButton("增加")
        self.edit_resource_btn = QPushButton("修改")
        self.delete_resource_btn = QPushButton("删除")

        self.add_resource_btn.setFixedWidth(110)
        self.edit_resource_btn.setFixedWidth(110)
        self.delete_resource_btn.setFixedWidth(110)

        button_layout.addWidget(self.add_resource_btn)
        button_layout.addWidget(self.edit_resource_btn)
        button_layout.addWidget(self.delete_resource_btn)

        resource_layout.addLayout(button_layout)

        resource_group.setLayout(resource_layout)

        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(resource_group)
        self.setLayout(main_layout)

        # 绑定按钮事件
        self.add_resource_btn.clicked.connect(self.add_resource)
        self.edit_resource_btn.clicked.connect(self.edit_resource)
        self.delete_resource_btn.clicked.connect(self.delete_resource)

    def apply_table_style(self, table):
        """应用表格样式"""
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdcdc;
                gridline-color: #dcdcdc;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
        """)

    def load_entities(self):
        """加载初始实体数据并默认勾选"""
        for entity in self.selected_entities:
            row_count = self.resource_table.rowCount()
            self.resource_table.insertRow(row_count)

            # 创建复选框，并默认勾选当前已经选择的实体
            checkbox = QCheckBox()
            checkbox.setChecked(entity.get("selected", False))
            self.resource_table.setCellWidget(row_count, 0, checkbox)

            self.resource_table.setItem(row_count, 1, QTableWidgetItem(entity["name"]))
            self.resource_table.setItem(row_count, 2, QTableWidgetItem(entity["type"]))
            self.resource_table.setItem(row_count, 3, QTableWidgetItem(entity["value"]))
            self.resource_table.setItem(row_count, 4, QTableWidgetItem(entity["remarks"]))

    def add_resource(self):
        """增加新实体"""
        print("增加新实体")
        new_entity = {
            "name": "新实体",
            "type": "默认类型",
            "value": "默认值",
            "remarks": "默认备注",
            "selected": True  # 新增实体默认选中
        }
        self.selected_entities.append(new_entity)
        self.add_entity_to_table(new_entity)

    def add_entity_to_table(self, entity):
        """将实体添加到表格"""
        row_count = self.resource_table.rowCount()
        self.resource_table.insertRow(row_count)

        # 创建复选框，并设置选中状态
        checkbox = QCheckBox()
        checkbox.setChecked(entity.get("selected", False))
        self.resource_table.setCellWidget(row_count, 0, checkbox)

        self.resource_table.setItem(row_count, 1, QTableWidgetItem(entity["name"]))
        self.resource_table.setItem(row_count, 2, QTableWidgetItem(entity["type"]))
        self.resource_table.setItem(row_count, 3, QTableWidgetItem(entity["value"]))
        self.resource_table.setItem(row_count, 4, QTableWidgetItem(entity["remarks"]))

    def edit_resource(self):
        """修改实体"""
        print("修改实体")
        selected_items = self.resource_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            entity_name = self.resource_table.item(row, 1).text()

            # 弹出对话框编辑实体
            QMessageBox.information(self, "修改实体", f"修改实体：{entity_name}")
            self.resource_table.setItem(row, 3, QTableWidgetItem("修改后的值"))
            self.resource_table.setItem(row, 4, QTableWidgetItem("修改后的备注"))

    def delete_resource(self):
        """删除实体"""
        print("删除实体")
        selected_items = self.resource_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            entity_name = self.resource_table.item(row, 1).text()
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除实体“{entity_name}”吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.resource_table.removeRow(row)
                del self.selected_entities[row]


# 测试窗口
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    # 示例初始数据
    selected_entities = [
        {"name": "实体1", "type": "类型A", "value": "值1", "remarks": "备注1", "selected": True},
        {"name": "实体2", "type": "类型B", "value": "值2", "remarks": "备注2", "selected": False},
        {"name": "实体3", "type": "类型C", "value": "值3", "remarks": "备注3", "selected": True},
    ]
    dialog = CompoundAttributeEditor("行车道数", "int", selected_entities)
    dialog.exec()
