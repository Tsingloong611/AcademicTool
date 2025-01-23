# model_transformation.py

import sys
import os

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QScrollArea, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QSizePolicy, QMessageBox, QApplication, QDialog,
    QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFont, QIcon, QWheelEvent, QPainter

from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.tabs.condition_setting import CustomTableWidget

# Constants Definition
ZOOM_IN_ICON = "resources/icons/zoom_in.png"
ZOOM_OUT_ICON = "resources/icons/zoom_out.png"

class ZoomableLabel(QLabel):
    """Label supporting zoom functionality for displaying SVG images."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.renderer = QSvgRenderer()
        self.scale_factor = 1.0
        self.image_loaded = False

    def set_svg(self, svg_path):
        """Set and load the SVG image."""
        if not self.renderer.load(svg_path):
            self.setText(self.tr("无法加载图像"))
            self.image_loaded = False
            return
        self.scale_factor = 1.0
        self.image_loaded = True
        self.update_pixmap()

    def wheelEvent(self, event: QWheelEvent):
        """Implement zoom with Ctrl + mouse wheel."""
        if self.image_loaded and event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.scale_factor *= 1.1
            else:
                self.scale_factor /= 1.1
            self.scale_factor = max(0.1, min(self.scale_factor, 10.0))  # Limit zoom factor
            self.update_pixmap()
        else:
            super().wheelEvent(event)

    def update_pixmap(self):
        """Update the displayed image based on the zoom factor."""
        if self.renderer.isValid() and self.image_loaded:
            size = self.renderer.defaultSize() * self.scale_factor
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            self.renderer.render(painter)
            painter.end()

            super().setPixmap(pixmap)

    def mousePressEvent(self, event):
        """Handle mouse click events to prompt user if image not loaded."""
        if not self.image_loaded and event.button() == Qt.LeftButton:
            pass
        else:
            super().mousePressEvent(event)



class ModelTransformationTab(QWidget):
    set_inference_request = Signal()
    """推演模型转换选项卡"""

    def __init__(self):
        super().__init__()
        self.node_data = {
            "节点A": [["状态1", 0.3], ["状态2", 0.7]],
            "节点B": [["状态1", 0.5], ["状态2", 0.5]],
            "节点C": [["状态1", 0.2], ["状态2", 0.8]],
            "节点D": [["状态1", 0.6], ["状态2", 0.4]],
        }
        self.node_checkboxes = {}
        self.init_ui()

    def init_ui(self):
        """Initialize UI components and layout."""
        self.set_stylesheet()

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 0, 20, 10)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        prior_group_box = self.create_prior_probability_group_box()
        bottom_layout.addWidget(prior_group_box, stretch=1)

        bayesian_network_group_box = self.create_bayesian_network_group_box()
        bottom_layout.addWidget(bayesian_network_group_box, stretch=3)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def set_stylesheet(self):
        # 去除表格单元格的边框，并为后面添加悬浮显示工具提示做准备
        self.setStyleSheet(self.tr("""
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
    background-color: #E8E8E8;
    border-radius: 10px;
    border-bottom-left-radius: 0px;
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
        border: none;
        background: transparent;
    }
    QAbstractScrollArea::corner {
        background: transparent;  /* 或者改成 #ffffff，与主背景相同 */
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

/* ---- 这里去除单元格本身的边框 ---- */
QTableWidget {
    border: none;
    font-size: 14px;
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
"""))

    def create_bayesian_network_group_box(self):
        group_box = QGroupBox(self.tr("贝叶斯网络"))
        group_box.setObjectName("BayesianNetworkGroupBox")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                background-color: #ffffff;
            }
        """)

        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(5)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        button_layout.addStretch()

        self.zoom_in_button = self.create_zoom_button(ZOOM_IN_ICON, self.tr("放大图像(按住 Ctrl 并滚动鼠标滚轮)"), self.zoom_in)
        self.zoom_out_button = self.create_zoom_button(ZOOM_OUT_ICON, self.tr("缩小图像(按住 Ctrl 并滚动鼠标滚轮)"), self.zoom_out)

        self.set_condition_button = QPushButton(self.tr("设置推演条件"))
        self.set_condition_button.setFixedWidth(110)
        self.set_condition_button.clicked.connect(self.set_inference_conditions)
        button_layout.addWidget(self.set_condition_button)

        button_layout.addWidget(self.zoom_in_button)
        button_layout.addWidget(self.zoom_out_button)

        self.bayesian_network_label = ZoomableLabel()
        self.bayesian_network_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bayesian_network_label.setText(self.tr("贝叶斯网络图像加载区"))
        self.bayesian_network_label.setStyleSheet("background-color: #ffffff;")

        default_svg = os.path.join(os.path.dirname(__file__), "combined_bn.png")
        if os.path.exists(default_svg):
            self.bayesian_network_label.set_svg(default_svg)
        else:
            self.bayesian_network_label.setText(self.tr("无法加载贝叶斯网络图像"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.bayesian_network_label)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
        background: transparent;
            }
            QAbstractScrollArea::corner {
                background: transparent;  /* 或者改成 #ffffff，与主背景相同 */
                border: none;
            }
        """)

        group_layout.addLayout(button_layout)
        group_layout.addWidget(scroll_area, 1)

        return group_box

    def create_zoom_button(self, icon_path, tooltip, callback):
        button = QPushButton()
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            button.setText(self.tr("缩放"))
        button.setToolTip(tooltip)
        button.setFixedSize(QSize(24, 24))
        button.clicked.connect(callback)
        return button

    def create_prior_probability_group_box(self):
        group_box = QGroupBox(self.tr("先验概率"))
        group_box.setObjectName("PriorProbabilityGroupBox")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                background-color: #ffffff;
                padding: 10px;
            }
        """)

        outer_layout = QVBoxLayout(group_box)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(15)

        # Create node selection area
        self.node_group_box = QGroupBox(self.tr("节点选择"))
        self.node_group_box.setMinimumWidth(300)
        self.node_group_box.setFixedHeight(200)
        self.node_group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f0f0f0;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Create scroll area
        scroll_area = QScrollArea(self.node_group_box)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        # 横纵向都需要在内容超出时才出现滚动条
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create content widget for checkboxes
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.grid_layout = QGridLayout(content_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # 设置每列弹性伸缩，保证复选框文本可完整显示
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)

        # 添加复选框
        self.node_checkboxes = {}
        nodes = list(self.node_data.keys())
        for i, node in enumerate(nodes):
            checkbox = QCheckBox(self.tr(node))
            checkbox.setStyleSheet("""
                QCheckBox {
                    background-color: #ffffff;
                    padding: 5px;
                    text-align: left;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    margin-right: 5px;
                    subcontrol-position: left center;
                }
            """)
            checkbox.setText(node)
            checkbox.setToolTip(node)  # 鼠标悬浮提示
            # 使复选框在水平方向可扩展
            checkbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            checkbox.stateChanged.connect(self.on_checkbox_state_changed)
            self.node_checkboxes[node] = checkbox
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(checkbox, row, col)

        scroll_area.setWidget(content_widget)
        node_layout = QVBoxLayout(self.node_group_box)
        node_layout.addWidget(scroll_area)

        # 创建并设置先验表格
        self.prior_table = CustomTableWidget()
        self.prior_table.setColumnCount(3)
        self.prior_table.setHorizontalHeaderLabels([self.tr("节点"), self.tr("状态"), self.tr("概率")])
        self.prior_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prior_table.setSelectionMode(QTableWidget.SingleSelection)
        self.prior_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.prior_table.setAlternatingRowColors(True)
        # 去除表格边框
        self.prior_table.setShowGrid(False)

        self.apply_table_style(self.prior_table)

        header = self.prior_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignCenter)
        self.prior_table.verticalHeader().setVisible(False)

        self.placeholder_label = QLabel(self.tr("请选择节点"))
        self.placeholder_label.setObjectName("placeholder")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel#placeholder {
                color: gray;
                font-size: 20pt;
                background-color: #ffffff;
                padding: 20px;
            }
        """)

        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self.placeholder_label)
        table_layout.addWidget(self.prior_table)

        outer_layout.addWidget(self.node_group_box)
        outer_layout.addWidget(table_container, 4)

        # Initialize display state
        self.prior_table.hide()
        self.placeholder_label.show()

        return group_box

    def apply_table_style(self, table: QTableWidget):
        # 此处保留对表格样式的基础设置，已去除单元格外边框
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
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
            self.prior_table.hide()
            self.placeholder_label.show()
        else:
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

                        # 设置文本居中 & 鼠标悬浮提示
                        for item in (item_node, item_state, item_prob):
                            item.setTextAlignment(Qt.AlignCenter)
                            item.setToolTip(item.text())

                        self.prior_table.setItem(row_position, 0, item_node)
                        self.prior_table.setItem(row_position, 1, item_state)
                        self.prior_table.setItem(row_position, 2, item_prob)

    def zoom_in(self):
        self.bayesian_network_label.scale_factor *= 1.1
        self.bayesian_network_label.scale_factor = min(self.bayesian_network_label.scale_factor, 10.0)
        self.bayesian_network_label.update_pixmap()

    def zoom_out(self):

        self.bayesian_network_label.scale_factor /= 1.1
        self.bayesian_network_label.scale_factor = max(self.bayesian_network_label.scale_factor, 0.1)
        self.bayesian_network_label.update_pixmap()

    def reset_inputs(self):
        # Clear existing checkboxes
        for checkbox in self.node_checkboxes.values():
            checkbox.setChecked(False)

        # Update the node selection grid with new node_data
        self.update_node_selection_grid()

        # Update the prior probability table
        self.update_prior_table()

    def update_node_selection_grid(self):
        # 移除旧的复选框
        for checkbox in self.node_checkboxes.values():
            checkbox.setParent(None)
        self.node_checkboxes.clear()

        nodes = list(self.node_data.keys())
        for i, node in enumerate(nodes):
            checkbox = QCheckBox(self.tr(node))
            checkbox.setStyleSheet("background-color: #ffffff;")
            checkbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            checkbox.stateChanged.connect(self.on_checkbox_state_changed)
            self.node_checkboxes[node] = checkbox
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(checkbox, row, col, alignment=Qt.AlignLeft)

    def set_node_data(self, new_node_data):
        """Update node_data and refresh the UI"""
        self.node_data = new_node_data
        self.reset_inputs()

    def set_bayesian_network_image(self, image_path):
        """Set the image of the Bayesian network"""
        if os.path.exists(image_path):
            self.bayesian_network_label.set_svg(image_path)
        else:
            self.bayesian_network_label.setText(self.tr("无法加载贝叶斯网络图像"))