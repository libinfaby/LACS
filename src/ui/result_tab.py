from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGroupBox, 
                             QRadioButton, QFormLayout, QLineEdit, QComboBox, QCheckBox, 
                             QPushButton, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QTabWidget, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import sqlite3

class ResultTab(QWidget):
    # Define signals if needed
    # connection_status_changed = Signal(bool, str) # for example only

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        result_layout = QVBoxLayout(self)
        
        # Split view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        result_layout.addWidget(splitter)
        
        # Left side - Sample list
        sample_list_group = QGroupBox("Samples")
        sample_list_layout = QVBoxLayout(sample_list_group)
        
        self.sample_list = QTableWidget()
        self.sample_list.setColumnCount(3)
        self.sample_list.setHorizontalHeaderLabels(["Sample No.", "Patient ID", "Patient Name"])
        self.sample_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sample_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sample_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.sample_list.selectionModel().selectionChanged.connect(self.load_sample_results)
        
        sample_list_layout.addWidget(self.sample_list)
        
        # Right side - Result details
        result_details_group = QGroupBox("Results")
        result_details_layout = QVBoxLayout(result_details_group)
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["Test Code", "Result", "Unit", "Normal Range", "Sent"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        result_details_layout.addWidget(self.result_table)
        
        # Buttons for sending results
        button_layout = QHBoxLayout()
        
        send_selected_button = QPushButton("Send Selected Results")
        send_selected_button.clicked.connect(self.send_selected_results)
        
        send_all_button = QPushButton("Send All Results")
        send_all_button.clicked.connect(self.send_all_results)
        
        button_layout.addWidget(send_selected_button)
        button_layout.addWidget(send_all_button)
        
        result_details_layout.addLayout(button_layout)
        
        # Add widgets to splitter
        splitter.addWidget(sample_list_group)
        splitter.addWidget(result_details_group)
        splitter.setSizes([300, 700])  # Initial sizes

    def send_selected_results(self):
        selected = self.result_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select results to send")
            return
        
        rows = set()
        for item in selected:
            rows.add(item.row())
        
        result_ids = []
        for row in rows:
            result_id = self.result_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            result_ids.append(result_id)
        
        self.send_results(result_ids)        

    def send_all_results(self):
        result_ids = []
        for row in range(self.result_table.rowCount()):
            result_id = self.result_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            result_ids.append(result_id)
        
        self.send_results(result_ids)     

    def send_results(self, result_ids):
        if not result_ids:
            return
        
        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            for result_id in result_ids:
                cursor.execute("UPDATE results SET sent = 1 WHERE id = ?", (result_id,))
            
            conn.commit()
            conn.close()
            
            self.load_sample_results()
            
            self.log_text.append(f"Sent {len(result_ids)} results to LIS")
            QMessageBox.information(self, "Success", f"{len(result_ids)} results sent successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send results: {str(e)}")        

    def load_sample_results(self):
        selected = self.sample_list.selectedItems()
        if not selected:
            return
        
        sample_db_id = self.sample_list.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)

        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT patient_id, patient_name
                FROM samples
                WHERE id = ?
            """, (sample_db_id,))
            
            patient = cursor.fetchone()
            self.patient_id_label.setText(patient[0])
            self.patient_name_label.setText(patient[1])
            
            cursor.execute("""
                SELECT r.id, t.test_code, r.result_value, t.unit, t.lower_range, t.upper_range, r.sent
                FROM results r
                JOIN tests t ON r.test_id = t.id
                WHERE r.sample_id = ?
            """, (sample_db_id,))
            
            results = cursor.fetchall()
            
            self.result_table.setRowCount(len(results))
            for i, result in enumerate(results):
                result_id, test_code, result_value, unit, lower_range, upper_range, sent = result
                
                normal_range = f"{lower_range} - {upper_range}"
                sent_text = "Yes" if sent else "No"
                
                self.result_table.setItem(i, 0, QTableWidgetItem(test_code))
                self.result_table.setItem(i, 1, QTableWidgetItem(str(result_value)))
                self.result_table.setItem(i, 2, QTableWidgetItem(unit))
                self.result_table.setItem(i, 3, QTableWidgetItem(normal_range))
                self.result_table.setItem(i, 4, QTableWidgetItem(sent_text))
                
                self.result_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, result_id)
                
                if result_value < lower_range or result_value > upper_range:
                    for col in range(5):
                        item = self.result_table.item(i, col)
                        item.setBackground(QColor(80, 0, 0))
            
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sample results: {str(e)}")        