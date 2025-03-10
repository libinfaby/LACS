import sys
import random
import time
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QComboBox, QPushButton, QTabWidget, QRadioButton,
                            QLineEdit, QCheckBox, QTextEdit, QProgressBar, QGroupBox,
                            QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
                            QSplitter, QMessageBox, QScrollArea, QSpacerItem, QSizePolicy,
                            QStackedWidget, QFrame, QListWidget, QListWidgetItem, QToolButton, QTabBar)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDateTime, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QPalette
from src.ui.lis_tab import LISTab
from src.ui.sample_tab import SampleTab
from src.ui.result_tab import ResultTab
from src.ui.tester_tab import TesterTab
from src.database.db_manger import DatabaseManager

class LabSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laboratory Analyzer Simulator")
        self.setMinimumSize(1000, 700)
        
        # Setup the database
        # self.create_database()

        # Initialize database
        self.db_manager = DatabaseManager()
        self.db_manager.create_database()        
        
        # Setup the UI
        self.setup_ui()
        
        # Load analyzer list
        self.load_analyzers()
    
    def setup_ui(self):
        # Set up main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Apply stylesheet from resources
        # with open("../../resources/stylesheet.qss", "r") as f:
        #     self.setStyleSheet(f.read())
        
        # Top section - Analyzer selector
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(10, 10, 10, 5)
        
        analyzer_label = QLabel("Analyzer:")
        analyzer_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.analyzer_combo = QComboBox()
        self.analyzer_combo.setFixedWidth(200)
        self.analyzer_combo.setFont(QFont("Arial", 10))
        
        set_button = QPushButton("Set")
        set_button.setFixedWidth(80)
        set_button.clicked.connect(self.set_analyzer)
        
        connection_status = QLabel("LIS Connection Not Established")
        connection_status.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        connection_status.setStyleSheet("color: #ff4444;")
        
        top_layout.addWidget(analyzer_label)
        top_layout.addWidget(self.analyzer_combo)
        top_layout.addWidget(set_button)
        top_layout.addStretch()
        top_layout.addWidget(connection_status)
        
        self.main_layout.addWidget(top_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create the three tabs
        # self.lis_tab = QWidget()
        self.lis_tab = LISTab(self)
        # self.sample_tab = QWidget()
        self.sample_tab = SampleTab(self)
        # self.result_tab = QWidget()
        self.result_tab = ResultTab(self)
        self.tester_tab = TesterTab(self)
        
        self.tab_widget.addTab(self.lis_tab, "LIS")
        self.tab_widget.addTab(self.sample_tab, "Sample/Analyze")
        self.tab_widget.addTab(self.result_tab, "Results")
        self.tab_widget.addTab(self.tester_tab, "Communication Tester")  

        # Connect any signals from the LIS tab to the main window
        # self.lis_tab.connection_status_changed.connect(self.update_status_bar) # for example only    
        
        # Setup LIS Tab
        # self.setup_lis_tab()
        
        # Setup Sample/Analyze Tab
        # self.setup_sample_tab()
        
        # Setup Results Tab
        # self.setup_result_tab()
        
        # Add status bar for logs
        self.statusBar().showMessage("Ready")
        
        # Add a log viewer at the bottom
        log_group = QGroupBox("Connection Logs")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        self.main_layout.addWidget(log_group)
        
        
        # LabSimulator.toggle_socket_type(self) was in LISSetUpUI
                
    def load_analyzers(self):
        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM analyzers")
            analyzers = cursor.fetchall()
            conn.close()
            
            self.analyzer_combo.clear()
            self.analyzer_combo.addItem('', -1)
            for analyzer in analyzers:
                self.analyzer_combo.addItem(analyzer[1], analyzer[0])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load analyzers: {str(e)}")

    def get_analyzer_combo(self):
        return self.analyzer_combo            
    
    def set_analyzer(self):
        analyzer_id = self.analyzer_combo.currentData()
        analyzer_name = self.analyzer_combo.currentText()
        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT connection_type, socket_type, analyzer_address, analyzer_port, 
                       lis_address, lis_port, serial_port, baud_rate, data_bits, 
                       stop_bits, parity, auto_result_sending, request_sample_info,
                       sample_id_delay, result_sending_delay 
                FROM connection_settings 
                WHERE analyzer_id = ?
            """, (analyzer_id,))
            
            settings = cursor.fetchone()
            if settings:
                if settings[0] == "TCP/IP":
                    self.tcp_radio.setChecked(True)
                    if settings[1] == "Server":
                        self.server_radio.setChecked(True)
                    else:
                        self.client_radio.setChecked(True)
                    self.analyzer_address.setText(settings[2] or "")
                    self.analyzer_port.setText(settings[3] or "")
                    self.lis_address.setText(settings[4] or "")
                    self.lis_port.setText(settings[5] or "")
                else:
                    self.serial_radio.setChecked(True)
                    self.serial_port.setCurrentText(settings[6] or "COM1")
                    self.baud_rate.setText(settings[7] or "9600")
                    self.data_bits.setText(settings[8] or "8")
                    self.stop_bits.setText(settings[9] or "1")
                    self.parity.setCurrentText(settings[10] or "No")
                
                self.auto_result.setChecked(bool(settings[11]))
                self.request_sample.setChecked(bool(settings[12]))
                self.sample_delay.setText(str(settings[13] or "0"))
                self.result_delay.setText(str(settings[14] or "0"))
            
            cursor.execute("""
                SELECT template_type, template_content 
                FROM astm_templates 
                WHERE analyzer_id = ?
            """, (analyzer_id,))
            
            templates = cursor.fetchall()
            for template in templates:
                if template[0] == "sample_info":
                    pass
                elif template[0] == "result_send":
                    pass
            
            cursor.execute("""
                SELECT test_code, unit, lower_range, upper_range 
                FROM tests 
                WHERE analyzer_id = ?
            """, (analyzer_id,))
            
            tests = cursor.fetchall()
            self.test_table.setRowCount(len(tests))
            for i, test in enumerate(tests):
                self.test_table.setItem(i, 0, QTableWidgetItem(test[0]))
                self.test_table.setItem(i, 1, QTableWidgetItem(test[1]))
                self.test_table.setItem(i, 2, QTableWidgetItem(str(test[2])))
                self.test_table.setItem(i, 3, QTableWidgetItem(str(test[3])))
            
            conn.close()
            
            QMessageBox.information(self, "Success", f"Analyzer '{analyzer_name}' selected successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load analyzer settings: {str(e)}")  