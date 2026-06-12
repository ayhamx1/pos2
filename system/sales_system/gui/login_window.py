import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bcrypt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from database.connection import get_connection


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.user_data = None

        self.setWindowTitle("تسجيل الدخول - نظام المبيعات")
        self.setFixedSize(450, 550)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("background-color: #ecf0f1;")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        # العنوان
        title = QLabel("نظام إدارة المبيعات")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        subtitle = QLabel("سجل دخولك للمتابعة")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # اسم المستخدم
        lbl_user = QLabel("اسم المستخدم:")
        lbl_user.setStyleSheet("font-size: 16px; color: #34495e;")
        layout.addWidget(lbl_user)

        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("ادخل اسم المستخدم")
        self.input_username.setStyleSheet("""
            padding: 12px;
            font-size: 16px;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            background-color: white;
        """)
        self.input_username.returnPressed.connect(self.focus_password)
        layout.addWidget(self.input_username)

        # كلمة المرور
        lbl_pass = QLabel("كلمة المرور:")
        lbl_pass.setStyleSheet("font-size: 16px; color: #34495e;")
        layout.addWidget(lbl_pass)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("ادخل كلمة المرور")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setStyleSheet("""
            padding: 12px;
            font-size: 16px;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            background-color: white;
        """)
        self.input_password.returnPressed.connect(self.login)
        layout.addWidget(self.input_password)

        layout.addSpacing(20)

        # زر الدخول
        btn_login = QPushButton("دخول")
        btn_login.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_login.clicked.connect(self.login)
        layout.addWidget(btn_login)

        # زر الخروج
        btn_exit = QPushButton("خروج")
        btn_exit.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e74c3c;
                font-size: 14px;
                padding: 8px;
                border: none;
            }
            QPushButton:hover {
                color: #c0392b;
            }
        """)
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

        # تلميح
        hint = QLabel("افتراضياً: admin / admin123")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #95a5a6; margin-top: 10px;")
        layout.addWidget(hint)

        self.setLayout(layout)
        self.input_username.setFocus()

    def focus_password(self):
        self.input_password.setFocus()

    def login(self):
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "تنبيه", "من فضلك ادخل اسم المستخدم وكلمة المرور")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, username, password, full_name, role
                FROM users
                WHERE username = %s
            """, (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if not user:
                QMessageBox.critical(self, "خطأ", "اسم المستخدم غير موجود")
                return

            stored_password = user[2].encode("utf-8")

            if bcrypt.checkpw(password.encode("utf-8"), stored_password):
                self.user_data = {
                    "id": user[0],
                    "username": user[1],
                    "full_name": user[3],
                    "role": user[4]
                }
                self.open_main_window()
            else:
                QMessageBox.critical(self, "خطأ", "كلمة المرور غير صحيحة")
                self.input_password.clear()
                self.input_password.setFocus()

        except Exception as e:
            QMessageBox.critical(self, "خطأ في الاتصال", str(e))

    def open_main_window(self):
        role = self.user_data.get("role", "user")

        if role == "admin":
            try:
                from gui.main_window import MainWindow
            except ImportError:
                from main_window import MainWindow

            self.main_win = MainWindow()
            if hasattr(self.main_win, "set_user"):
                self.main_win.set_user(self.user_data)
            self.main_win.show()
            self.close()
            return

        # الموظف: لازم يفتح وردية أو يكون عنده وردية مفتوحة
        try:
            from gui.shift_manager import get_open_shift, OpenShiftDialog
        except ImportError:
            from shift_manager import get_open_shift, OpenShiftDialog

        cashier_name = self.user_data.get("full_name", "")
        shift_id = get_open_shift(cashier_name)

        if not shift_id:
            dialog = OpenShiftDialog(self.user_data, self)
            dialog.exec()

            # إعادة التحقق بعد غلق شاشة فتح الوردية
            shift_id = get_open_shift(cashier_name)

            if not shift_id:
                QMessageBox.warning(self, "تنبيه", "لا يمكن الدخول بدون فتح وردية!")
                return

        try:
            from gui.pos_window import POSWindow
        except ImportError:
            from pos_window import POSWindow

        self.pos_win = POSWindow(self.user_data)
        self.pos_win.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())