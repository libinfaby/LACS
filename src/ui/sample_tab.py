import random
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QComboBox, QPushButton, QTabWidget, QRadioButton,
                            QLineEdit, QCheckBox, QTextEdit, QProgressBar, QGroupBox,
                            QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
                            QSplitter, QMessageBox, QScrollArea, QSpacerItem, QSizePolicy,
                            QStackedWidget, QFrame, QListWidget, QListWidgetItem, QToolButton)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDateTime, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QPalette
import sqlite3

class SampleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        sample_layout = QVBoxLayout(self)
        
        # Sample number input area
        sample_group = QGroupBox("Sample Input")
        sample_input_layout = QVBoxLayout(sample_group)
        
        # Sample number widget that can dynamically add more
        self.sample_widget = QWidget()
        self.sample_layout = QVBoxLayout(self.sample_widget)
        self.sample_layout.setContentsMargins(0, 0, 0, 0)
        
        # Initial sample input
        self.add_sample_input()
        
        # sample_input_layout.addWidget(self.sample_widget)
        # Create a scroll area and add the sample widget to it
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Important - this allows the widget to resize
        scroll_area.setWidget(self.sample_widget)

        # Add the scroll area to the sample input layout
        sample_input_layout.addWidget(scroll_area)
        
        # Add more samples button
        add_sample_button = QPushButton("Add More Samples")
        add_sample_button.clicked.connect(self.add_sample_input)
        sample_input_layout.addWidget(add_sample_button)

        # Now set the layout on the group box
        sample_group.setLayout(sample_input_layout)

        sample_layout.addWidget(sample_group)
        
        # Start analysis button
        start_button = QPushButton()
        start_button.setIcon(QIcon.fromTheme("media-playback-start"))
        start_button.setText("Start Analysis")
        start_button.setIconSize(QSize(24, 24))
        start_button.setStyleSheet("font-size: 16px; padding: 10px;")
        start_button.clicked.connect(self.start_analysis)
        sample_layout.addWidget(start_button)
        
        # Progress section
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        current_sample_layout = QHBoxLayout()
        current_sample_layout.addWidget(QLabel("Current Sample:"))
        self.current_sample_label = QLabel("None")
        current_sample_layout.addWidget(self.current_sample_label)
        current_sample_layout.addStretch()
        progress_layout.addLayout(current_sample_layout)
        
        sample_layout.addWidget(progress_group)
        
        # Patient info section
        patient_group = QGroupBox("Patient Information")
        patient_layout = QFormLayout(patient_group)
        
        self.patient_id_label = QLabel("Not Available")
        self.patient_name_label = QLabel("Not Available")
        
        patient_layout.addRow("Patient ID:", self.patient_id_label)
        patient_layout.addRow("Patient Name:", self.patient_name_label)
        
        # Test details
        test_details_group = QGroupBox("Test Details")
        test_details_layout = QVBoxLayout(test_details_group)
        
        self.test_list = QListWidget()
        test_details_layout.addWidget(self.test_list)
        
        patient_layout.addRow("Tests:", test_details_group)
        
        sample_layout.addWidget(patient_group)
        
        # Add a spacer at the bottom
        sample_layout.addStretch()

    def add_sample_input(self):
        sample_row = QWidget()
        sample_row_layout = QHBoxLayout(sample_row)
        sample_row_layout.setContentsMargins(0, 0, 0, 0)
        
        sample_label = QLabel("Sample Number:")
        sample_input = QLineEdit()
        sample_input.setPlaceholderText("Enter sample ID")
        
        patient_label = QLabel("Patient ID:")
        patient_input = QLineEdit()
        patient_input.setPlaceholderText("Enter patient ID")
        
        patient_name_label = QLabel("Patient Name:")
        patient_name_input = QLineEdit()
        patient_name_input.setPlaceholderText("Enter patient name")
        
        sample_row_layout.addWidget(sample_label)
        sample_row_layout.addWidget(sample_input)
        sample_row_layout.addWidget(patient_label)
        sample_row_layout.addWidget(patient_input)
        sample_row_layout.addWidget(patient_name_label)
        sample_row_layout.addWidget(patient_name_input)
        
        remove_button = QToolButton()
        remove_button.setText("X")
        remove_button.clicked.connect(lambda: self.remove_sample_input(sample_row))
        sample_row_layout.addWidget(remove_button)
        
        self.sample_layout.addWidget(sample_row)

    def remove_sample_input(self, sample_row):
        sample_row.deleteLater()        

    def start_analysis(self):
        sample_ids = []
        patient_ids = []
        patient_names = []
        
        for i in range(self.sample_layout.count()):
            widget = self.sample_layout.itemAt(i).widget()
            if widget:
                layout = widget.layout()
                sample_input = layout.itemAt(1).widget()
                patient_input = layout.itemAt(3).widget()
                patient_name_input = layout.itemAt(5).widget()
                
                if sample_input.text():
                    sample_ids.append(sample_input.text())
                    patient_ids.append(patient_input.text())
                    patient_names.append(patient_name_input.text())
        
        if not sample_ids:
            QMessageBox.warning(self, "Warning", "Please enter at least one sample ID")
            return
        
        self.store_samples(sample_ids, patient_ids, patient_names)
        self.generate_results(sample_ids)
        self.load_sample_list()
        
        self.progress_bar.setMaximum(len(sample_ids))
        self.progress_bar.setValue(0)
        
        self.current_sample_index = 0
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(lambda: self.update_progress(sample_ids))
        self.progress_timer.start(1000)
        
        QMessageBox.information(self, "Started", "Analysis started for {} samples".format(len(sample_ids)))                

    def update_progress(self, sample_ids):
        if self.current_sample_index < len(sample_ids):
            self.progress_bar.setValue(self.current_sample_index + 1)
            self.current_sample_label.setText(sample_ids[self.current_sample_index])
            self.current_sample_index += 1
        else:
            self.progress_timer.stop()
            self.current_sample_label.setText("Completed")
            QMessageBox.information(self, "Completed", "Analysis completed for all samples")
    
    def store_samples(self, sample_ids, patient_ids, patient_names):
        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for i, sample_id in enumerate(sample_ids):
                cursor.execute("SELECT id FROM samples WHERE sample_number = ?", (sample_id,))
                existing = cursor.fetchone()
                
                patient_id = patient_ids[i] if i < len(patient_ids) else ""
                patient_name = patient_names[i] if i < len(patient_names) else ""
                
                if existing:
                    cursor.execute("""
                        UPDATE samples SET
                        patient_id = ?,
                        patient_name = ?,
                        date_time = ?
                        WHERE sample_number = ?
                    """, (patient_id, patient_name, now, sample_id))
                else:
                    cursor.execute("""
                        INSERT INTO samples
                        (sample_number, patient_id, patient_name, date_time)
                        VALUES (?, ?, ?, ?)
                    """, (sample_id, patient_id, patient_name, now))
            
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to store samples: {str(e)}")
    
    def generate_results(self, sample_ids):
        try:
            analyzer_id = self.analyzer_combo.currentData()
            if not analyzer_id:
                return
            
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, test_code, lower_range, upper_range
                FROM tests
                WHERE analyzer_id = ?
            """, (analyzer_id,))
            
            tests = cursor.fetchall()
            if not tests:
                conn.close()
                return
            
            for sample_id in sample_ids:
                cursor.execute("SELECT id FROM samples WHERE sample_number = ?", (sample_id,))
                sample_db_id = cursor.fetchone()[0]
                
                for test in tests:
                    test_id, test_code, lower_range, upper_range = test
                    
                    result_value = round(random.uniform(lower_range, upper_range), 3)
                    
                    cursor.execute("""
                        SELECT id FROM results
                        WHERE sample_id = ? AND test_id = ?
                    """, (sample_db_id, test_id))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute("""
                            UPDATE results SET
                            result_value = ?,
                            sent = 0
                            WHERE sample_id = ? AND test_id = ?
                        """, (result_value, sample_db_id, test_id))
                    else:
                        cursor.execute("""
                            INSERT INTO results
                            (sample_id, test_id, result_value, sent)
                            VALUES (?, ?, ?, 0)
                        """, (sample_db_id, test_id, result_value))
            
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate results: {str(e)}")      

    def load_sample_list(self):
        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, sample_number, patient_id, patient_name
                FROM samples
                ORDER BY date_time DESC
            """)
            
            samples = cursor.fetchall()
            
            self.sample_list.setRowCount(len(samples))
            for i, sample in enumerate(samples):
                sample_id, sample_number, patient_id, patient_name = sample
                
                self.sample_list.setItem(i, 0, QTableWidgetItem(sample_number))
                self.sample_list.setItem(i, 1, QTableWidgetItem(patient_id))
                self.sample_list.setItem(i, 2, QTableWidgetItem(patient_name))
                self.sample_list.item(i, 0).setData(Qt.ItemDataRole.UserRole, sample_id)
            
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sample list: {str(e)}")
