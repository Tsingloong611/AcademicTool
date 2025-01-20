# -*- coding: utf-8 -*-
# @Time    : 1/18/2025 10:57 PM
# @FileName: entity_type_select.py
# @Software: PyCharm
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QMessageBox

class EntityTypeDialog(QDialog):
    def __init__(self, entity_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择关联实体类型")
        self.setModal(True)
        self.selected_entity = None

        layout = QVBoxLayout()

        label = QLabel("请选择一个实体类型:")
        layout.addWidget(label)

        self.combo_box = QComboBox()
        # 假设 entity_types 是一个列表的元组 [(id1, name1), (id2, name2), ...]
        for entity_id, entity_name in entity_types:
            self.combo_box.addItem(entity_name, entity_id)
        layout.addWidget(self.combo_box)

        # 添加确定和取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_selected_entity(self):
        return self.combo_box.currentData(), self.combo_box.currentText()
