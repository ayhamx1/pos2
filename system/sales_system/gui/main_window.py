import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFrame, QMessageBox,
    QGridLayout
)
from PySide6.QtCore import Qt

try:
    from gui.products_window import ProductsWindow
except ModuleNotFoundError:
    from products_window import ProductsWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.setWindowTitle("نظام إدارة المبيعات والمخازن")
        self.setGeometry(100, 100, 1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ==============================
        # الهيدر
        # ==============================
        header = QFrame()
        header.setFixedHeight(85)
        header.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 12px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title_label = QLabel("نظام إدارة المبيعات والمخازن")
        title_label.setStyleSheet("""
            color: white;
            font-size: 26px;
            font-weight: bold;
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.lbl_user = QLabel("غير مسجل")
        self.lbl_user.setStyleSheet("""
            color: #ecf0f1;
            font-size: 16px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.lbl_user)

        btn_logout = QPushButton("خروج")
        btn_logout.setFixedHeight(40)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_logout.clicked.connect(self.logout)
        header_layout.addWidget(btn_logout)

        main_layout.addWidget(header)

        # ==============================
        # الأزرار الرئيسية
        # ==============================
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        self.btn_sales = self.create_menu_button("شاشة الكاشير", "#27ae60")
        self.btn_products = self.create_menu_button("إدارة المنتجات", "#2980b9")
        self.btn_returns_report = self.create_menu_button("تقرير المرتجعات", "#d35400")
        self.btn_reports = self.create_menu_button("التقارير", "#8e44ad")
        self.btn_settings = self.create_menu_button("الإعدادات", "#7f8c8d")

        grid_layout.addWidget(self.btn_sales, 0, 0)
        grid_layout.addWidget(self.btn_products, 0, 1)
        grid_layout.addWidget(self.btn_returns_report, 0, 2)
        grid_layout.addWidget(self.btn_reports, 1, 0)
        grid_layout.addWidget(self.btn_settings, 1, 1)

        main_layout.addWidget(grid_widget)

        # ==============================
        # الفوتر
        # ==============================
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
            }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 5, 15, 5)

        self.footer = QLabel("الحالة: متصل بقاعدة البيانات")
        self.footer.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        footer_layout.addWidget(self.footer)

        footer_layout.addStretch()

        main_layout.addWidget(footer)

        # ==============================
        # ربط الأزرار
        # ==============================
        self.btn_products.clicked.connect(self.open_products)
        self.btn_sales.clicked.connect(self.open_sales)
        self.btn_returns_report.clicked.connect(self.open_returns_report)
        self.btn_reports.clicked.connect(self.open_reports)
        self.btn_settings.clicked.connect(self.open_settings)

    def set_user(self, user_data):
        """استقبال بيانات المستخدم من شاشة الدخول"""
        self.current_user = user_data
        role_ar = "مدير" if user_data.get('role') == 'admin' else "موظف"
        self.lbl_user.setText(f"{user_data.get('full_name', '')} ({role_ar})")
        self.footer.setText(f"الحالة: متصل | المستخدم: {user_data.get('username', '')}")

    def create_menu_button(self, text, color):
        btn = QPushButton(text)
        btn.setFixedHeight(150)
        btn.setMinimumWidth(260)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: white;
                color: {color};
                border: 3px solid {color};
            }}
        """)
        return btn

    def open_products(self):
        self.products_win = ProductsWindow()
        self.products_win.show()

    def open_sales(self):
        """فتح شاشة الكاشير"""
        try:
            from gui.pos_window import POSWindow
        except ImportError:
            from pos_window import POSWindow

        self.pos_win = POSWindow(self.current_user if self.current_user else {})
        self.pos_win.show()

    def open_returns_report(self):
        """فتح شاشة تقرير المرتجعات"""
        try:
            from gui.returns_report_window import ReturnsReportWindow
        except ImportError:
            from returns_report_window import ReturnsReportWindow

        self.returns_report_win = ReturnsReportWindow()
        self.returns_report_win.show()

    def open_reports(self):
        """فتح شاشة التقارير"""
        try:
            from gui.reports_window import ReportsWindow
        except ImportError:
            QMessageBox.information(self, "التقارير", "شاشة التقارير لم يتم إنشاؤها بعد.")
            return

        self.reports_win = ReportsWindow()
        self.reports_win.show()

    def open_settings(self):
        """فتح شاشة الإعدادات"""
        try:
            from gui.settings_window import SettingsWindow
        except ImportError:
            QMessageBox.information(self, "الإعدادات", "شاشة الإعدادات لم يتم إنشاؤها بعد.")
            return

        self.settings_win = SettingsWindow()
        self.settings_win.show()

    def logout(self):
        """تسجيل الخروج والعودة لشاشة الدخول"""
        reply = QMessageBox.question(
            self,
            "تسجيل الخروج",
            "هل تريد تسجيل الخروج؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                from gui.login_window import LoginWindow
            except ImportError:
                from login_window import LoginWindow

            self.login_win = LoginWindow()
            self.login_win.show()
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())