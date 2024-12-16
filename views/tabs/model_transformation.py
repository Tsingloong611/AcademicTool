# model_transformation.py

import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QScrollArea, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QSizePolicy, QMessageBox, QApplication, QDialog,
    QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFont, QIcon

from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.tabs.condition_setting import CustomTableWidget

# Constants Definition
ZOOM_IN_ICON = "resources/icons/zoom_in.png"   # 确保路径正确
ZOOM_OUT_ICON = "resources/icons/zoom_out.png" # 确保路径正确

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
        self.scale_factor = max(self.scale_factor, 0.1)
        self.scale_factor = min(self.scale_factor, 10.0)
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
        """Initialize UI components and layout."""
        self.set_stylesheet()

        # 主布局改为垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 0, 20, 10)  # Adjusted bottom margin for better spacing


        # -------------------
        # 底部布局 - 分左右
        # -------------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        # 先验概率部分（左侧，比例1）
        prior_group_box = self.create_prior_probability_group_box()
        bottom_layout.addWidget(prior_group_box, stretch=1)

        # 贝叶斯网络展示部分（右侧，比例3）
        bayesian_network_group_box = self.create_bayesian_network_group_box()
        bottom_layout.addWidget(bayesian_network_group_box, stretch=3)


        # 将底部布局添加到主布局
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

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

        # 整体布局
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(5)

        # ====== 顶部按钮布局（固定在右上角） ======
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        button_layout.addStretch()  # 把按钮推到右边

        # 放大和缩小按钮
        self.zoom_in_button = self.create_zoom_button(ZOOM_IN_ICON, "放大图像(按住 Ctrl 并滚动鼠标滚轮)", self.zoom_in)
        self.zoom_out_button = self.create_zoom_button(ZOOM_OUT_ICON, "缩小图像(按住 Ctrl 并滚动鼠标滚轮)", self.zoom_out)

        # 连接信号
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.set_condition_button = QPushButton("设置推演条件")
        # 设置最大宽度
        self.set_condition_button.setFixedWidth(110)
        self.set_condition_button.clicked.connect(self.set_inference_conditions)
        button_layout.addWidget(self.set_condition_button)


        button_layout.addWidget(self.zoom_in_button)
        button_layout.addWidget(self.zoom_out_button)

        # ====== 中部：可滚动图像区域 ======
        self.bayesian_network_label = ZoomableLabel()
        self.bayesian_network_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bayesian_network_label.setText("贝叶斯网络图像加载区")
        self.bayesian_network_label.setStyleSheet("background-color: #ffffff;")

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

        # ====== 把按钮布局和滚动区域加入 group_box 的布局 ======
        group_layout.addLayout(button_layout)   # 按钮固定在顶部
        group_layout.addWidget(scroll_area, 1)  # 滚动区域在下面

        return group_box

    def create_zoom_button(self, icon_path, tooltip, callback):
        """Create Zoom Button"""
        button = QPushButton()
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            button.setText("缩放")
        button.setToolTip(tooltip)
        button.setFixedSize(QSize(24, 24))
        button.clicked.connect(callback)
        return button

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
        main_v_layout.setSpacing(0)
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
        self.display_area.setContentsMargins(0, 10, 0, 0)

        self.prior_table = CustomTableWidget()
        self.prior_table.setColumnCount(3)
        self.prior_table.setHorizontalHeaderLabels(["节点", "状态", "概率"])
        self.apply_table_style(self.prior_table)

        self.prior_table.horizontalHeader().setFont(QFont("SimSun", 16, QFont.Bold))
        self.prior_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.prior_table.horizontalHeader().setStretchLastSection(True)
        self.prior_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.prior_table.verticalHeader().setVisible(False)
        self.prior_table.setAlternatingRowColors(True)
        self.prior_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.prior_table.setShowGrid(False)
        self.prior_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prior_table.setSelectionMode(QTableWidget.SingleSelection)
        self.prior_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
                    background-color: white;
    alternate-background-color: #e9e7e3;
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
                        item_node = QTableWidgetItem(node)
                        item_state = QTableWidgetItem(state_name)
                        item_prob = QTableWidgetItem(f"{prob:.4f}")

                        # 设置文本居中
                        item_node.setTextAlignment(Qt.AlignCenter)
                        item_state.setTextAlignment(Qt.AlignCenter)
                        item_prob.setTextAlignment(Qt.AlignCenter)

                        self.prior_table.setItem(row_position, 0, item_node)
                        self.prior_table.setItem(row_position, 1, item_state)
                        self.prior_table.setItem(row_position, 2, item_prob)

    def zoom_in(self):
        """放大图像"""
        if self.bayesian_network_label.pixmap_original:
            self.bayesian_network_label.scale_factor *= 1.1
            self.bayesian_network_label.scale_factor = min(self.bayesian_network_label.scale_factor, 10.0)
            self.bayesian_network_label.update_pixmap()

    def zoom_out(self):
        """缩小图像"""
        if self.bayesian_network_label.pixmap_original:
            self.bayesian_network_label.scale_factor /= 1.1
            self.bayesian_network_label.scale_factor = max(self.bayesian_network_label.scale_factor, 0.1)
            self.bayesian_network_label.update_pixmap()

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
