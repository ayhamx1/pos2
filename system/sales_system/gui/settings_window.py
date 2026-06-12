import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("الإعدادات")
        self.setGeometry(200, 150, 700, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI';
            }
            QLabel {
                color: #2c3e50;
                background: transparent;
            }
            QPushButton {
                background-color: #1e5378;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #163f5c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QFrame()
        header.setStyleSheet("background-color: #1e5378; border-radius: 10px; padding: 12px;")
        header_layout = QVBoxLayout(header)

        title = QLabel("الإعدادات")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        layout.addWidget(header)

        info = QLabel("دي شاشة إعدادات مبدئية.\nتقدر بعد كده تضيف فيها إعدادات الطابعة، النظام، النسخ الاحتياطي، البيانات، وغيرها.")
        info.setFont(QFont("Segoe UI", 12))
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_printer = QPushButton("إعدادات الطباعة")
        btn_printer.clicked.connect(lambda: QMessageBox.information(self, "الطباعة", "إعدادات الطباعة لم تُنشأ بعد"))
        layout.addWidget(btn_printer)

        btn_backup = QPushButton("النسخ الاحتياطي")
        btn_backup.clicked.connect(lambda: QMessageBox.information(self, "النسخ الاحتياطي", "شاشة النسخ الاحتياطي لم تُنشأ بعد"))
        layout.addWidget(btn_backup)

        btn_db = QPushButton("إعدادات قاعدة البيانات")
        btn_db.clicked.connect(lambda: QMessageBox.information(self, "قاعدة البيانات", "إعدادات قاعدة البيانات لم تُنشأ بعد"))
        layout.addWidget(btn_db)

        btn_close = QPushButton("إغلاق")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        layout.addStretch()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())