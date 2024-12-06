from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class ThreeLineTable(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("三线表")
        self.setGeometry(100, 100, 800, 400)

        # 创建表格
        self.table = QTableWidget(self)
        self.table.setRowCount(5)  # 数据行数
        self.table.setColumnCount(3)  # 列数
        self.table.setGeometry(20, 20, 760, 360)

        # 设置表头
        self.table.setHorizontalHeaderLabels(["列1", "列2", "列3"])
        self.table.horizontalHeader().setFont(QFont("Arial", 12, QFont.Bold))
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        # 填充数据
        for row in range(5):
            for col in range(3):
                item = QTableWidgetItem(f"数据{row + 1}-{col + 1}")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        # 样式：三线表样式
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 12px;
                border-top: 2px solid black; /* 顶部线 */
                border-bottom: 2px solid black; /* 底部线 */
            }
            QHeaderView::section {
                border-top: 2px solid black; /* 表头底部线 */
                background-color: #f0f0f0;
            }
            QTableWidget::item {
                border: none; /* 中间行无边框 */
            }
            QTableWidget::item:nth-child(even) {
                background-color: #f9f9f9; /* 偶数行背景颜色 */
            }
            QTableWidget::item:nth-child(odd) {
                background-color: #ffffff; /* 奇数行背景颜色 */
            }
        """)

        # 隐藏网格线
        self.table.setShowGrid(False)

        # 调整行高和列宽
        self.table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.table.horizontalHeader().setStretchLastSection(True)  # 最后一列填充
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # 强制刷新表头样式，确保第二条线不被覆盖
        self.force_refresh_headers()

        # 调整表格高度以消除底部空白
        self.adjust_table_height()

    def adjust_table_height(self):
        # 根据内容调整表格的高度，使底部线条贴近内容
        total_row_height = sum(self.table.rowHeight(row) for row in range(self.table.rowCount()))
        header_height = self.table.horizontalHeader().height()
        self.table.setFixedHeight(total_row_height + header_height + 6)  # 微调底部

    def force_refresh_headers(self):
        # 确保表头样式刷新，防止表头下的线丢失
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-bottom: 2px solid black;
                background-color: #f0f0f0;
            }
        """)

if __name__ == "__main__":
    app = QApplication([])
    window = ThreeLineTable()
    window.show()
    app.exec()
