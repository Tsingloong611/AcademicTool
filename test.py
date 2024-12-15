import sys
from PySide6.QtWidgets import (
    QApplication, QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class MultiHeaderTableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多行表头的QTableWidget示例")
        self.resize(800, 400)
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setRowCount(3)  # 两行表头 + 一行数据
        self.table.setColumnCount(7)

        # 第一行合并单元格
        self.table.setSpan(0, 0, 2, 1)  # "预案名字" 跨两行
        self.table.setItem(0, 0, QTableWidgetItem("预案名字"))

        self.table.setSpan(0, 1, 1, 3)  # "推演前" 跨三列
        self.table.setItem(0, 1, QTableWidgetItem("推演前"))

        self.table.setSpan(0, 4, 1, 3)  # "推演后" 跨三列
        self.table.setItem(0, 4, QTableWidgetItem("推演后"))

        # 设置表头文字居中和加粗
        for row in range(2):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setFont(QFont("SimSun", 12, QFont.Bold))

        # 第二行子表头
        sub_headers = ["", "较好", "中等", "较差", "较好", "中等", "较差"]
        for col, header in enumerate(sub_headers):
            if col == 0:
                continue  # 第一个单元格已合并
            item = QTableWidgetItem(header)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled)  # 设置为不可编辑
            item.setFont(QFont("SimSun", 10, QFont.Bold))
            self.table.setItem(1, col, item)

        # 隐藏垂直表头（行号）
        self.table.verticalHeader().setVisible(False)

        # 隐藏网格线
        self.table.setShowGrid(False)

        # 禁止编辑
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置选择行为
        self.table.setSelectionBehavior(QTableWidget.SelectItems)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # 设置列宽自适应
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 应用样式表
        self.apply_table_style(self.table)

        # 添加示例数据
        data = ["预案1", "30%", "50%", "20%", "60%", "30%", "10%"]
        for col, value in enumerate(data):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(2, col, item)

        layout.addWidget(self.table)

    def apply_table_style(self, table: QTableWidget):
        """应用三线表样式到指定的表格"""
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

        # 确保表头刷新样式
        self.force_refresh_table_headers(table)

    def force_refresh_table_headers(self, table: QTableWidget):
        """确保表头样式刷新，防止表头下的线丢失"""
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-top: 1px solid black;    /* 表头顶部线 */
                border-bottom: 2px solid black; /* 表头底部线，增加粗细 */
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center; /* 表头内容居中 */
            }
        """)
        table.horizontalHeader().repaint()  # 使用 repaint() 确保样式应用

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultiHeaderTableWidget()
    window.show()
    sys.exit(app.exec())
