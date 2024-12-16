import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Signal, Slot, QUrl
from networkx.algorithms.distance_measures import center


# 定义桥梁类，用于 JavaScript 与 Python 通信
class LocationBridge(QObject):
    locationSelected = Signal(float, float)

    @Slot(float, float)
    def sendLocationToQt(self, lat, lng):
        """
        JS 调用此函数，将经纬度传回 Python。
        """
        self.locationSelected.emit(lat, lng)

# 定义地图对话框
class MapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高德地图选择")
        self.resize(800, 600)

        self.selected_lat = 0.0
        self.selected_lng = 0.0

        # 设置布局
        layout = QVBoxLayout(self)

        # 创建 QWebEngineView
        self.webview = QWebEngineView(self)
        layout.addWidget(self.webview, stretch=1)

        # 创建按钮布局
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 设置 WebChannel
        self.channel = QWebChannel(self.webview.page())
        self.bridge = LocationBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        # 连接信号
        self.bridge.locationSelected.connect(self.on_location_selected)
        self.ok_btn.clicked.connect(self.on_ok_clicked)
        self.cancel_btn.clicked.connect(self.reject)
        center_lat ,center_lng = self.get_current_location()

        # 定义 HTML 内容
        js_api_key = "f5c6bd77acf4d4a715e9cd57c1eef006"  # 替换为 JavaScript API 的 Key
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>高德地图选择</title>
            <style>
                html, body, #mapContainer {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}
            </style>
            <!-- 引入高德地图 API -->
            <script src="https://webapi.amap.com/maps?v=2.0&key={js_api_key}"></script>
            <!-- 引入 Qt WebChannel -->
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script type="text/javascript">
                var bridge = null;
                var map = null;
                var marker = null;

                function initMap() {{
                    // 初始化 WebChannel
                    new QWebChannel(qt.webChannelTransport, function(channel) {{
                        bridge = channel.objects.bridge;
                    }});

                    // 创建地图实例
                    map = new AMap.Map('mapContainer', {{
                        resizeEnable: true,
                        center: [{center_lng}, {center_lat}], // 设置地图中心点
                        zoom: 13
                    }});

                    // 添加点击事件
                    map.on('click', function(e) {{
                        var lnglat = e.lnglat;
                        var lng = lnglat.getLng();
                        var lat = lnglat.getLat();

                        // 清除之前的标注
                        if (marker) {{
                            map.remove(marker);
                        }}

                        // 添加新的标注
                        marker = new AMap.Marker({{
                            position: lnglat
                        }});
                        marker.setMap(map);

                        // 调用桥梁对象的方法，将坐标传回Python
                        if (bridge) {{
                            bridge.sendLocationToQt(lat, lng);
                        }}
                    }});
                }}

                window.onload = initMap;
            </script>
        </head>
        <body>
            <div id="mapContainer"></div>
        </body>
        </html>
        """

        # 加载 HTML 内容
        self.webview.setHtml(html_content, QUrl("qrc:///"))

    @Slot(float, float)
    def on_location_selected(self, lat, lng):
        """
        接收来自JS的经纬度。
        """
        self.selected_lat = lat
        self.selected_lng = lng

    def on_ok_clicked(self):
        """
        用户点击“确定”按钮，关闭对话框。
        """
        if self.selected_lat == 0.0 and self.selected_lng == 0.0:
            QMessageBox.warning(self, "未选择位置", "请在地图上选择一个位置。")
            return
        self.accept()

    def get_selected_coordinates(self):
        """
        返回选定的经纬度。
        """
        return self.selected_lat, self.selected_lng

    def get_current_location(self, default_lat=39.0, default_lng=116.0):
        """
        获取用户当前的经纬度。若获取失败，则返回默认经纬度。
        """
        web_service_key = "a5c30cf29633446ba3ad37bcefd1a0fb"  # 替换为高德 Web 服务 API 的 Key
        url = f"https://restapi.amap.com/v3/ip?key={web_service_key}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1" and "rectangle" in data:
                    # 使用返回的 rectangle 获取中心坐标
                    rectangle = data["rectangle"]
                    # 根据分号分隔进行解析
                    coords = rectangle.split(';')
                    if len(coords) == 2:
                        lng_min, lat_min = map(float, coords[0].split(','))
                        lng_max, lat_max = map(float, coords[1].split(','))
                        center_lat = (lat_min + lat_max) / 2
                        center_lng = (lng_min + lng_max) / 2
                        return center_lat, center_lng
        except Exception as e:
            print(f"获取当前位置失败: {e}")
        # 若失败，返回默认位置（北京）
        return default_lat, default_lng


# 逆地理编码函数（使用 Web服务 API）
def reverse_geocode(lat, lng):
    web_service_key = "a5c30cf29633446ba3ad37bcefd1a0fb"  # 替换为 Web服务 API 的 Key
    url = f"https://restapi.amap.com/v3/geocode/regeo?location={lng},{lat}&key={web_service_key}&radius=1000&extensions=all"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "1" and "regeocode" in data:
            return data["regeocode"]["formatted_address"]
    return "未知地址"

# 定义主窗口
class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("高德地图最小测试案例")
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        # 标签显示选择结果
        self.result_label = QLabel("尚未选择位置。")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        # 打开地图选择按钮
        self.open_map_btn = QPushButton("选择位置")
        layout.addWidget(self.open_map_btn)

        self.setLayout(layout)

        # 绑定按钮点击事件
        self.open_map_btn.clicked.connect(self.open_map_dialog)

    def open_map_dialog(self):
        """
        打开地图对话框，获取位置数据。
        """
        map_dialog = MapDialog(parent=self)
        if map_dialog.exec() == QDialog.Accepted:
            lat, lng = map_dialog.get_selected_coordinates()
            address = reverse_geocode(lat, lng)
            self.result_label.setText(f"地址: {address}\n纬度: {lat}\n经度: {lng}")
        else:
            self.result_label.setText("选择位置被取消。")

# 主程序入口
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
