import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QScrollArea, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QSizePolicy, QMessageBox, QApplication, QDialog,
    QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont


class CustomInformationDialog(QMessageBox):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(message)
        self.setIcon(QMessageBox.Information)
        self.setStandardButtons(QMessageBox.Ok)


class CustomWarningDialog(QMessageBox):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(message)
        self.setIcon(QMessageBox.Warning)
        self.setStandardButtons(QMessageBox.Ok)


class ZoomableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.scale_factor = 1.0
        self.pixmap_original = None

    def setPixmap(self, pixmap):
        self.pixmap_original = pixmap
        self.update_pixmap()

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1
        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
        self.update_pixmap()

    def update_pixmap(self):
        if self.pixmap_original:
            scaled_pixmap = self.pixmap_original.scaled(
                self.pixmap_original.size() * self.scale_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            super().setPixmap(scaled_pixmap)

    def mousePressEvent(self, event):
        if not self.pixmap_original:
            CustomWarningDialog("提示", "未选择图像，请选择图像").exec()
        else:
            super().mousePressEvent(event)


class ModelTransformationTab(QWidget):
    set_inference_request = Signal()
    """推演模型转换选项卡"""

    def __init__(self):
        super().__init__()
        self.node_data = {
            "节点A": [("状态1", 0.3), ("状态2", 0.7)],
            "节点B": [("状态1", 0.5), ("状态2", 0.5)],
            "节点C": [("状态1", 0.2), ("状态2", 0.8)],
            "节点D": [("状态1", 0.6), ("状态2", 0.4)],
        }  # 预定义的节点状态和概率数据
        self.init_ui()

    def init_ui(self):
        self.set_stylesheet()
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 左侧 - 贝叶斯网络展示
        main_layout.addWidget(self.create_bayesian_network_group_box(), 2)

        # 右侧 - 先验概率部分
        right_layout = QVBoxLayout()
        prior_group_box = self.create_prior_probability_group_box()

        # 上下布局：上方为prior_group_box（包含节点选择和表格区域）
        # 下方为按钮框
        upper_layout = QVBoxLayout()
        upper_layout.addWidget(prior_group_box)

        lower_layout = QVBoxLayout()
        button_box = self.create_button_box()  # 创建按钮框
        lower_layout.addLayout(button_box)

        right_layout.addLayout(upper_layout)
        right_layout.addLayout(lower_layout)

        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)
        self.node_group_box.setStyleSheet("""QGroupBox {
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-top: 10px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0px 0px;
    font-weight: bold;
    color: #333333;
    background-color: #ffffff;
}""")

    def set_stylesheet(self):
        """设置整体样式表"""
        self.setStyleSheet("""
QGroupBox {
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-top: 10px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    font-weight: bold;
    color: #333333;
    background-color: #E8E8E8; /* 设置圆角灰色背景 */
    border-radius: 10px; /* 圆角效果 */
    border-bottom-left-radius: 0px; /* 左下角无圆角 */
}
            QLabel {
                color: #333333;
                background-color: #ffffff;
            }
            QCheckBox {
                color: #333333;
                background-color: #ffffff;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QScrollArea {
                background-color: #ffffff;
                border: none;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: #f1f1f1;
                width: 8px;
                height: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #c1c1c1;
                min-width: 20px;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
                width: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }

            QLabel#placeholder{
                color: gray;
                font-size: 20pt;
                border-radius: 10px;
                border: 0px solid #c0c0c0;
                background-color: #ffffff;
            }

            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black; 
                background-color: #ffffff;
            }
            QHeaderView::section {
                border-top: 1px solid black;   
                border-bottom: 1px solid black; 
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
            QTableWidget::item {
                border: none; 
                padding: 5px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
                color: black;
                border: none;
            }
            QTableWidget:focus {
                outline: none;
            }

            QPushButton {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #ffffff;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)

    def create_bayesian_network_group_box(self):
        group_box = QGroupBox("贝叶斯网络")
        group_box.setObjectName("BayesianNetworkGroupBox")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                background-color: #ffffff;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # 图像加载区域
        self.bayesian_network_label = ZoomableLabel()
        self.bayesian_network_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bayesian_network_label.setText("贝叶斯网络图像加载区")
        self.bayesian_network_label.setStyleSheet("background-color: #ffffff;")

        # 默认图片路径，可以替换为实际路径
        default_png = os.path.join(os.path.dirname(__file__), "combined_bn.png")

        if os.path.exists(default_png):
            pixmap = QPixmap(default_png)
            self.bayesian_network_label.setPixmap(pixmap)
        else:
            self.bayesian_network_label.setText("无法加载贝叶斯网络图像")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.bayesian_network_label)
        scroll_area.setStyleSheet("QScrollArea {border: none; background-color: #ffffff;}")
        layout.addWidget(scroll_area)

        group_box.setLayout(layout)
        return group_box

    def create_prior_probability_group_box(self):
        """创建先验概率部分"""
        group_box = QGroupBox("先验概率")
        group_box.setObjectName("PriorProbabilityGroupBox")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                background-color: #ffffff;
            }
        """)

        outer_layout = QVBoxLayout(group_box)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(15)

        # 使用垂直布局将节点选择在上，表格/提示在下
        main_v_layout = QVBoxLayout()
        main_v_layout.setSpacing(20)
        main_v_layout.setContentsMargins(0, 0, 0, 0)

        # 上面：节点选择区域
        self.node_group_box = QGroupBox("节点选择")
        self.node_group_box.setStyleSheet("""
            QGroupBox {
    border: 1px solid #d0d0d0;

    border-radius: 10px;
    margin-top: 14px;
            }
        """)

        scroll_for_checkboxes = QScrollArea()
        scroll_for_checkboxes.setWidgetResizable(True)
        scroll_for_checkboxes.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_for_checkboxes.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_for_checkboxes.setStyleSheet("background-color: #ffffff; border:none;")

        grid_layout = QGridLayout()
        self.node_checkboxes = {}
        nodes = list(self.node_data.keys())
        for i, node in enumerate(nodes):
            checkbox = QCheckBox(node)
            checkbox.setStyleSheet("background-color: #ffffff;")
            checkbox.stateChanged.connect(self.on_checkbox_state_changed)
            self.node_checkboxes[node] = checkbox
            row = i // 2
            col = i % 2
            grid_layout.addWidget(checkbox, row, col, alignment=Qt.AlignCenter)

        self.node_group_box.setLayout(grid_layout)
        scroll_for_checkboxes.setWidget(self.node_group_box)

        # 下方：展示区域
        self.display_area = QVBoxLayout()
        self.display_area.setContentsMargins(0, 0, 0, 0)

        self.prior_table = QTableWidget()
        self.prior_table.setColumnCount(3)
        self.prior_table.setHorizontalHeaderLabels(["节点", "状态", "概率"])
        self.prior_table.horizontalHeader().setFont(QFont("SimSun", 16, QFont.Bold))
        self.prior_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.prior_table.horizontalHeader().setStretchLastSection(True)
        self.prior_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.prior_table.verticalHeader().setVisible(False)
        self.prior_table.setAlternatingRowColors(True)
        self.prior_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.prior_table.setShowGrid(False)
        self.prior_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply_table_style(self.prior_table)

        self.placeholder_label = QLabel("请选择节点")
        self.placeholder_label.setObjectName("placeholder")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        # 默认全部不选
        for node, checkbox in self.node_checkboxes.items():
            checkbox.setChecked(False)
        self.update_prior_table()

        self.display_area.addWidget(self.placeholder_label)
        self.display_area.addWidget(self.prior_table)

        # 将两个区域按1:4比例分配(节点选择:展示)
        # 使用setStretch来控制比例
        main_v_layout.addWidget(scroll_for_checkboxes, 1)
        main_v_layout.addLayout(self.display_area, 4)

        outer_layout.addLayout(main_v_layout)

        return group_box

    def apply_table_style(self, table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black; 
                background-color: #ffffff;
            }
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
            QTableWidget::item {
                border: none; 
                padding: 5px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
                color: black;
                border: none;
            }
            QTableWidget:focus {
                outline: none;
            }
        """)
        self.force_refresh_table_headers(table)

    def force_refresh_table_headers(self, table: QTableWidget):
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
        """)
        table.horizontalHeader().repaint()

    def create_button_box(self):
        button_box = QVBoxLayout()
        self.set_condition_button = QPushButton("设置推演条件")
        self.set_condition_button.clicked.connect(self.set_inference_conditions)
        button_box.addWidget(self.set_condition_button)
        return button_box

    def set_inference_conditions(self):
        self.set_inference_request.emit()

    def on_checkbox_state_changed(self, state):
        self.update_prior_table()

    def update_prior_table(self):
        selected_nodes = [node for node, cb in self.node_checkboxes.items() if cb.isChecked()]
        self.prior_table.setRowCount(0)

        if not selected_nodes:
            # 没有选中任何节点，显示“请选择节点”
            self.prior_table.hide()
            self.placeholder_label.show()
        else:
            # 有选中节点，显示表格数据
            self.placeholder_label.hide()
            self.prior_table.show()
            for node in selected_nodes:
                if node in self.node_data:
                    for state_name, prob in self.node_data[node]:
                        row_position = self.prior_table.rowCount()
                        self.prior_table.insertRow(row_position)
                        self.prior_table.setItem(row_position, 0, QTableWidgetItem(node))
                        self.prior_table.setItem(row_position, 1, QTableWidgetItem(state_name))
                        self.prior_table.setItem(row_position, 2, QTableWidgetItem(f"{prob:.4f}"))

    def reset_inputs(self):
        pass


class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("推演模型转换界面")
        self.resize(1200, 800)
        layout = QVBoxLayout(self)

        model_transformation_tab = ModelTransformationTab()
        layout.addWidget(model_transformation_tab)

        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
