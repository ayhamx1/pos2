import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QComboBox, QSpinBox, QMessageBox)
from PySide6.QtCore import Qt
from database.connection import get_connection

class SalesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("شاشة البيع")
        self.setGeometry(150, 100, 900, 600)
        self.setLayoutDirection(Qt.RightToLeft)

        self.cart = [] # سلة التسوق المؤقتة
        self.init_ui()
        self.load_products()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- منطقة اختيار المنتج ---
        top_layout = QHBoxLayout()
        
        self.combo_products = QComboBox()
        self.combo_products.setFixedWidth(300)
        self.combo_products.setStyleSheet("font-size: 18px; padding: 5px;")
        
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 1000)
        self.spin_qty.setStyleSheet("font-size: 18px; padding: 5px;")
        
        btn_add = QPushButton("➕ إضافة للسلة")
        btn_add.setStyleSheet("background-color: #27ae60; color: white; font-size: 18px; padding: 8px;")
        btn_add.clicked.connect(self.add_to_cart)

        top_layout.addWidget(QLabel("المنتج:"))
        top_layout.addWidget(self.combo_products)
        top_layout.addWidget(QLabel("الكمية:"))
        top_layout.addWidget(self.spin_qty)
        top_layout.addWidget(btn_add)
        
        layout.addLayout(top_layout)

        # --- جدول السلة ---
        self.table_cart = QTableWidget()
        self.table_cart.setColumnCount(4)
        self.table_cart.setHorizontalHeaderLabels(["اسم المنتج", "السعر", "الكمية", "الإجمالي"])
        self.table_cart.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_cart)

        # --- الإجمالي وزر الحفظ ---
        bottom_layout = QHBoxLayout()
        self.lbl_total = QLabel("الإجمالي: 0.00 جنيه")
        self.lbl_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c;")
        
        btn_checkout = QPushButton("🛒 إتمام البيع وطباعة")
        btn_checkout.setStyleSheet("background-color: #2c3e50; color: white; font-size: 20px; padding: 15px;")
        btn_checkout.clicked.connect(self.checkout)

        bottom_layout.addWidget(self.lbl_total)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_checkout)
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def load_products(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, name, price, qty FROM products WHERE qty > 0")
            self.db_products = cur.fetchall()
            self.combo_products.clear()
            for p in self.db_products:
                self.combo_products.addItem(f"{p[1]} (متاح: {p[3]})", p)
            cur.close()
            conn.close()
        except Exception as e:
            print("خطأ تحميل المنتجات:", e)

    def add_to_cart(self):
        product_data = self.combo_products.currentData()
        if not product_data: return
        
        qty = self.spin_qty.value()
        if qty > product_data[3]:
            QMessageBox.warning(self, "خطأ", "الكمية المطلوبة أكبر من المتوفر!")
            return

        # إضافة للسلة
        item_total = float(product_data[2]) * qty
        self.cart.append({
            'id': product_data[0],
            'name': product_data[1],
            'price': float(product_data[2]),
            'qty': qty,
            'total': item_total
        })
        self.update_cart_table()

    def update_cart_table(self):
        self.table_cart.setRowCount(len(self.cart))
        total_bill = 0
        for i, item in enumerate(self.cart):
            self.table_cart.setItem(i, 0, QTableWidgetItem(item['name']))
            self.table_cart.setItem(i, 1, QTableWidgetItem(str(item['price'])))
            self.table_cart.setItem(i, 2, QTableWidgetItem(str(item['qty'])))
            self.table_cart.setItem(i, 3, QTableWidgetItem(str(item['total'])))
            total_bill += item['total']
        
        self.lbl_total.setText(f"الإجمالي: {total_bill:.2f} جنيه")

    def checkout(self):
        if not self.cart: return
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            # 1. تسجيل الفاتورة
            total_amount = sum(item['total'] for item in self.cart)
            cur.execute("INSERT INTO sales (total_amount) VALUES (%s) RETURNING id", (total_amount,))
            sale_id = cur.fetchone()[0]

            # 2. تسجيل الأصناف وتحديث المخزن
            for item in self.cart:
                cur.execute("INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                           (sale_id, item['id'], item['qty'], item['price']))
                cur.execute("UPDATE products SET qty = qty - %s WHERE id = %s", (item['qty'], item['id']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            QMessageBox.information(self, "نجاح", "تمت عملية البيع بنجاح!")
            self.cart = []
            self.update_cart_table()
            self.load_products() # لتحديث الكميات المتاحة في القائمة
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))