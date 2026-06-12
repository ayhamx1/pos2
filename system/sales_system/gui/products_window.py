import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QPushButton, QMessageBox, QInputDialog, QDialog, QFormLayout,
                               QLineEdit, QDoubleSpinBox, QSpinBox)
from PySide6.QtCore import Qt
from database.connection import get_connection


class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة منتج جديد")
        self.setFixedSize(300, 200)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 10000)
        self.price_input.setDecimals(2)
        self.qty_input = QSpinBox()
        self.qty_input.setRange(0, 10000)
        
        layout.addRow("اسم المنتج:", self.name_input)
        layout.addRow("السعر:", self.price_input)
        layout.addRow("الكمية:", self.qty_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        cancel_btn = QPushButton("إلغاء")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)

    def get_data(self):
        return (
            self.name_input.text().strip(),
            self.price_input.value(),
            self.qty_input.value()
        )


class ProductsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("إدارة المنتجات - نظام المبيعات")
        self.setGeometry(150, 100, 900, 550)
        self.setLayoutDirection(Qt.RightToLeft)

        main_layout = QVBoxLayout()

        # العنوان
        title = QLabel("📦 إدارة المنتجات")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; padding: 10px;")
        main_layout.addWidget(title)

        # أزرار التحكم
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ إضافة منتج جديد")
        self.btn_refresh = QPushButton("🔄 تحديث")
        self.btn_delete = QPushButton("🗑️ حذف المحدد")

        self.btn_add.setStyleSheet("padding: 8px; font-size: 16px;")
        self.btn_refresh.setStyleSheet("padding: 8px; font-size: 16px;")
        self.btn_delete.setStyleSheet("padding: 8px; font-size: 16px;")

        self.btn_add.clicked.connect(self.add_product)
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_delete.clicked.connect(self.delete_product)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_delete)
        main_layout.addLayout(btn_layout)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["كود", "اسم المنتج", "السعر (جنيه)", "الكمية"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("font-size: 15px;")
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)
        self.load_data()

    def load_data(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, name, price, qty FROM products ORDER BY id;")
            rows = cur.fetchall()

            self.table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)
            
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")

    def add_product(self):
        dialog = AddProductDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, price, qty = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "تحذير", "يجب إدخال اسم المنتج")
                return
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO products (name, price, qty) VALUES (%s, %s, %s)",
                           (name, price, qty))
                conn.commit()
                cur.close()
                conn.close()
                QMessageBox.information(self, "نجح", "تم إضافة المنتج بنجاح")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def delete_product(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تحذير", "اختر منتج أولاً")
            return

        product_id = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()

        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف المنتج:\n{name} ؟",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
                conn.commit()
                cur.close()
                conn.close()
                self.load_data()
                QMessageBox.information(self, "تم", "تم حذف المنتج")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProductsWindow()
    window.show()
    sys.exit(app.exec())