# -*- coding: utf-8 -*-
# @Time    : 2/7/2025 1:36 AM
# @FileName: missing_data_dialog.py
# @Software: PyCharm
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QDialog, QPushButton, \
    QHeaderView


def get_missing_rows(df):
    """
    返回一个 DataFrame，包含原始 DataFrame 中存在缺失值的所有行，
    同时新增一列 'Excel行号' 用于显示该行在 Excel 中的行号（从 1 开始）。
    """
    # 筛选出含缺失值的行
    missing_df = df[df.isnull().any(axis=1)].copy()
    # 新增 Excel 行号（假设原 df 的索引对应 Excel 行号减去表头行）
    missing_df.insert(0, '行号', missing_df.index + 1)
    return missing_df


class MissingDataDialog(QDialog):
    """
    对话框：展示包含缺失值的完整行数据，
    用户点击“确定”后返回 accept()，后续流程可删除含缺失值的行。
    """

    def __init__(self, missing_df):
        super().__init__()
        self.setWindowTitle("缺失值信息")
        self.resize(900, 600)

        layout = QVBoxLayout()
        tip_label = QLabel("以下行存在缺失值，已跳过：")
        layout.addWidget(tip_label)

        # 创建一个 QTableWidget 展示缺失数据（包含 Excel 行号和所有列）
        table = QTableWidget()
        rows, cols = missing_df.shape
        table.setRowCount(rows)
        table.setColumnCount(cols)
        # 设置表头（列名）
        table.setHorizontalHeaderLabels(missing_df.columns.tolist())

        # 填充表格
        for i in range(rows):
            for j, col in enumerate(missing_df.columns):
                # 如果数据为 NaN，显示为空字符串
                cell_data = missing_df.iloc[i, j]
                table.setItem(i, j, QTableWidgetItem("缺失" if pd.isna(cell_data) else str(cell_data)))
        table.resizeColumnsToContents()
        layout.addWidget(table)

        # 添加一个确认按钮
        confirm_btn = QPushButton("确定")
        # 按钮居中,使用Qt.AlignCenter
        # 固定宽度
        confirm_btn.setFixedWidth(110)
        confirm_btn.clicked.connect(self.accept)
        layout.addWidget(confirm_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.apply_three_line_table_style(table)

        table.verticalHeader().setVisible(False)
        # 表格宽度自适应
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)



    def apply_three_line_table_style(self, table: QTableWidget):
        """应用三线表样式到表格"""
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
        """强制刷新表头样式"""
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