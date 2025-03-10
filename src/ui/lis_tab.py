from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QComboBox, QPushButton, QTabWidget, QRadioButton,
                            QLineEdit, QCheckBox, QTextEdit, QProgressBar, QGroupBox,
                            QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
                            QSplitter, QMessageBox, QScrollArea, QSpacerItem, QSizePolicy,
                            QStackedWidget, QFrame, QListWidget, QListWidgetItem, QToolButton)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDateTime, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QPalette
import sqlite3

class LISTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        lis_layout = QHBoxLayout(self)
        
        # Create left and right splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        lis_layout.addWidget(splitter)
        
        # Left side - Connection settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Connection type selection
        conn_type_group = QGroupBox("Connection Type")
        conn_type_layout = QHBoxLayout(conn_type_group)
        
        self.tcp_radio = QRadioButton("TCP/IP")
        self.serial_radio = QRadioButton("Serial")
        self.tcp_radio.setChecked(True)
        
        conn_type_layout.addWidget(self.tcp_radio)
        conn_type_layout.addWidget(self.serial_radio)
        
        left_layout.addWidget(conn_type_group)
        
        # TCP/IP settings
        self.tcp_widget = QWidget()
        tcp_layout = QFormLayout(self.tcp_widget)
        
        # Socket type
        socket_layout = QHBoxLayout()
        self.server_radio = QRadioButton("Server")
        self.client_radio = QRadioButton("Client")
        self.server_radio.setChecked(True)
        socket_layout.addWidget(self.server_radio)
        socket_layout.addWidget(self.client_radio)
        tcp_layout.addRow("Socket Type:", socket_layout)
        
        # Analyzer address and port
        self.analyzer_address = QLineEdit("")
        self.analyzer_address.setPlaceholderText("")
        tcp_layout.addRow("Analyzer Address:", self.analyzer_address)
        
        self.analyzer_port = QLineEdit("")
        self.analyzer_port.setPlaceholderText("0 - 65535")
        tcp_layout.addRow("Analyzer Port:", self.analyzer_port)
        
        # LIS address and port
        self.lis_address = QLineEdit("")
        self.lis_address.setPlaceholderText("")
        tcp_layout.addRow("LIS Address:", self.lis_address)
        
        self.lis_port = QLineEdit("")
        self.lis_port.setPlaceholderText("0 - 65535")
        tcp_layout.addRow("LIS Port:", self.lis_port)
        
        left_layout.addWidget(self.tcp_widget)
        
        # Serial settings
        self.serial_widget = QWidget()
        self.serial_widget.setVisible(False)  # Hide initially
        serial_layout = QFormLayout(self.serial_widget)
        
        # Serial port
        self.serial_port = QComboBox()
        self.serial_port.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9"])
        serial_layout.addRow("Serial Port:", self.serial_port)
        
        # Baud rate
        self.baud_rate = QLineEdit("9600")
        self.baud_rate.setPlaceholderText("2400, 4800, 9600, 19200")
        serial_layout.addRow("Baud Rate:", self.baud_rate)
        
        # Data bits
        self.data_bits = QLineEdit("8")
        serial_layout.addRow("Data Bits:", self.data_bits)
        
        # Stop bits
        self.stop_bits = QLineEdit("1")
        self.stop_bits.setPlaceholderText("1 or 2")
        serial_layout.addRow("Stop Bits:", self.stop_bits)
        
        # Parity
        self.parity = QComboBox()
        self.parity.addItems(["Even", "Odd", "No", "Space", "Mark"])
        self.parity.setCurrentText("No")
        serial_layout.addRow("Parity:", self.parity)
        
        left_layout.addWidget(self.serial_widget)
        
        # Common settings
        common_group = QGroupBox("Common Settings")
        common_layout = QVBoxLayout(common_group)
        
        self.auto_result = QCheckBox("Automatic Result Sending")
        self.request_sample = QCheckBox("Request Sample Info")
        common_layout.addWidget(self.auto_result)
        common_layout.addWidget(self.request_sample)
        
        sample_delay_layout = QHBoxLayout()
        sample_delay_layout.addWidget(QLabel("Sample ID Sending Delay (ms):"))
        self.sample_delay = QLineEdit("0")
        sample_delay_layout.addWidget(self.sample_delay)
        common_layout.addLayout(sample_delay_layout)
        
        result_delay_layout = QHBoxLayout()
        result_delay_layout.addWidget(QLabel("Result Sending Delay (ms):"))
        self.result_delay = QLineEdit("0")
        result_delay_layout.addWidget(self.result_delay)
        common_layout.addLayout(result_delay_layout)
        
        left_layout.addWidget(common_group)
        
        # Save connection settings button
        save_button = QPushButton("Save Connection Settings")
        save_button.clicked.connect(self.save_connection_settings)
        left_layout.addWidget(save_button)
        
        # Connect button
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.connect_to_lis)
        left_layout.addWidget(connect_button)
        
        left_layout.addStretch()
        
        # Right side - ASTM Message Templates
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Create tab widget for ASTM templates
        astm_tabs = QTabWidget()
        
        # Sample Info Request Template Tab
        sample_info_tab = QWidget()
        sample_info_layout = QVBoxLayout(sample_info_tab)
        
        sample_info_text = QTextEdit()
        sample_info_text.setPlaceholderText("Enter ASTM message template for sample info request...")
        sample_info_text.setText("Send: <ENQ>\nRead: <ACK>\n\nSend: <STX>1H|\\^&|||1^Analyzer_1^|||||||||P||20101118101825<CR><ETX>A1\nRead: <ACK>\n\nSend: <STX>2Q|1|^SampleID_03^^||^^^ALL^||||||O<CR><ETX>FF\n\nRead: <ACK>\n\nSend: <STX>3L|1|N<CR><ETX>06\n\nRead: <ACK>\n\nSend: < EOT >")
        
        # Field selector UI for sample info
        field_group = QGroupBox("Add Field")
        field_layout = QHBoxLayout(field_group)
        
        field_selector = QComboBox()
        field_selector.addItems(["ENQ", "ACK", "STX", "ETX", "H", "P", "O", "Q", "R"])
        field_layout.addWidget(field_selector)
        
        field_text = QLineEdit()
        field_layout.addWidget(field_text)
        
        field_direction = QComboBox()
        field_direction.addItems(["Send", "Read"])
        field_layout.addWidget(field_direction)
        
        add_field_button = QPushButton("Add")
        field_layout.addWidget(add_field_button)
        
        sample_info_layout.addWidget(sample_info_text)
        sample_info_layout.addWidget(field_group)
        
        # Result Sending Template Tab
        result_send_tab = QWidget()
        result_send_layout = QVBoxLayout(result_send_tab)
        
        result_send_text = QTextEdit()
        result_send_text.setPlaceholderText("Enter ASTM message template for result sending...")
        result_send_text.setText("send: <ENQ>\nread: <ACK>\nsend: <STX>1H]\\Aé|[]1 Analyzer 1^7.0]||||||||P|]20190801124640<CR><EXT>E4\nread: <ACK>\n\nsend: <STX>2P|1|PatientID_07|||Patient Name_7|||U|||||||||||||||||||<CR><EXT>67\nread: <ACK>\n\nsend: <STX>3O|1|SampleID_07^0.0^5^1|||^^^Test_1^0.0|R||||||X|||3|||||||1|F<CR><EXT>2C\nread: <ACK>\n\nsend: <STX>4R|1|^^^Test_1^0.0|2.4|mmol/l||N||F||<root user>||20190801124608|Analyzer 1<CR><EXT>3F\nread: <ACK>\n\nsend: <STX>5O|2|SampleID_07^0.0^5^1|||^^^Photo_reflex_test^0.0|R||||||X|||3|||||||1|F<CR><EXT>0D\nread: <ACK>\n\nsend: <STX>6R|1|^^^Photo_reflex_test^0.0|3.205|mmol/l||N||F||<root user>||20190801124606|Analyzer 1<CR><EXT>81\nread: <ACK>\n\nsend: <STX>7O|3|SampleID_07^0.0^5^1|||^^^Photometric_test^0.0|R||||||X|||3|||||||1|F<CR><EXT>AF\nread: <ACK>\n\nsend: <STX>0R|1|^^^Photometric_test^0.0|0.06|mmol/l||N||F||<root user>||20190801124607|Analyzer 1<CR><EXT>E7\nread: <ACK>\n\nsend: <STX>1L|1|N<CR><EXT>04\nread")
        
        # Field selector UI for result sending
        result_field_group = QGroupBox("Add Field")
        result_field_layout = QHBoxLayout(result_field_group)
        
        result_field_selector = QComboBox()
        result_field_selector.addItems(["ENQ", "ACK", "STX", "ETX", "H", "P", "O", "Q", "R"])
        result_field_layout.addWidget(result_field_selector)
        
        result_field_text = QLineEdit()
        result_field_layout.addWidget(result_field_text)
        
        result_field_direction = QComboBox()
        result_field_direction.addItems(["Send", "Read"])
        result_field_layout.addWidget(result_field_direction)
        
        result_add_field_button = QPushButton("Add")
        result_field_layout.addWidget(result_add_field_button)
        
        result_send_layout.addWidget(result_send_text)
        result_send_layout.addWidget(result_field_group)
        
        # Add tabs to the ASTM templates tab widget
        astm_tabs.addTab(sample_info_tab, "Sample Info Request Template")
        astm_tabs.addTab(result_send_tab, "Result Sending Template")
        
        right_layout.addWidget(astm_tabs)
        
        # Test Master table
        test_group = QGroupBox("Test Master")
        test_layout = QVBoxLayout(test_group)
        
        self.test_table = QTableWidget()
        self.test_table.setColumnCount(4)
        self.test_table.setHorizontalHeaderLabels(["Test Code", "Unit", "Lower Range", "Upper Range"])
        self.test_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        test_button_layout = QHBoxLayout()
        add_test_button = QPushButton("Add Test")
        add_test_button.clicked.connect(self.add_test)
        edit_test_button = QPushButton("Edit Test")
        edit_test_button.clicked.connect(self.edit_test)
        delete_test_button = QPushButton("Delete Test")
        delete_test_button.clicked.connect(self.delete_test)
        
        test_button_layout.addWidget(add_test_button)
        test_button_layout.addWidget(edit_test_button)
        test_button_layout.addWidget(delete_test_button)
        
        test_layout.addWidget(self.test_table)
        test_layout.addLayout(test_button_layout)
        
        right_layout.addWidget(test_group)
        
        # Save templates button
        save_templates_button = QPushButton("Save Templates and Test Data")
        save_templates_button.clicked.connect(self.save_templates)
        right_layout.addWidget(save_templates_button)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])  # Initial sizes
        
        # Connect connection type radio buttons
        self.tcp_radio.toggled.connect(self.toggle_connection_type)
        self.serial_radio.toggled.connect(self.toggle_connection_type)
        
        # Connect socket type radio buttons
        self.server_radio.toggled.connect(self.toggle_socket_type)
        self.client_radio.toggled.connect(self.toggle_socket_type)
        
        # Connect field selector buttons
        add_field_button.clicked.connect(lambda: self.add_field(field_selector, field_text, field_direction, sample_info_text))
        result_add_field_button.clicked.connect(lambda: self.add_field(result_field_selector, result_field_text, result_field_direction, result_send_text))

    def save_connection_settings(self):
        # analyzer_id = self.analyzer_combo.currentData()
        analyzer_id = self.parent().get_analyzer_combo().currentData()
        if not analyzer_id:
            QMessageBox.warning(self, "Warning", "Please select an analyzer first")
            return
        
        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM connection_settings WHERE analyzer_id = ?", (analyzer_id,))
            existing = cursor.fetchone()
            
            connection_type = "TCP/IP" if self.tcp_radio.isChecked() else "Serial"
            socket_type = "Server" if self.server_radio.isChecked() else "Client"
            analyzer_address = self.analyzer_address.text()
            analyzer_port = self.analyzer_port.text()
            lis_address = self.lis_address.text()
            lis_port = self.lis_port.text()
            serial_port = self.serial_port.currentText()
            baud_rate = self.baud_rate.text()
            data_bits = self.data_bits.text()
            stop_bits = self.stop_bits.text()
            parity = self.parity.currentText()
            auto_result = 1 if self.auto_result.isChecked() else 0
            request_sample = 1 if self.request_sample.isChecked() else 0
            sample_delay = self.sample_delay.text()
            result_delay = self.result_delay.text()
            
            if existing:
                cursor.execute("""
                    UPDATE connection_settings 
                    SET connection_type = ?, socket_type = ?, analyzer_address = ?,
                        analyzer_port = ?, lis_address = ?, lis_port = ?,
                        serial_port = ?, baud_rate = ?, data_bits = ?,
                        stop_bits = ?, parity = ?, auto_result_sending = ?,
                        request_sample_info = ?, sample_id_delay = ?,
                        result_sending_delay = ?
                    WHERE analyzer_id = ?
                """, (connection_type, socket_type, analyzer_address, analyzer_port,
                     lis_address, lis_port, serial_port, baud_rate, data_bits,
                     stop_bits, parity, auto_result, request_sample,
                     sample_delay, result_delay, analyzer_id))
            else:
                cursor.execute("""
                    INSERT INTO connection_settings 
                    (analyzer_id, connection_type, socket_type, analyzer_address,
                     analyzer_port, lis_address, lis_port, serial_port, baud_rate,
                     data_bits, stop_bits, parity, auto_result_sending,
                     request_sample_info, sample_id_delay, result_sending_delay)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (analyzer_id, connection_type, socket_type, analyzer_address,
                     analyzer_port, lis_address, lis_port, serial_port, baud_rate,
                     data_bits, stop_bits, parity, auto_result, request_sample,
                     sample_delay, result_delay))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Success", "Connection settings saved successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save connection settings: {str(e)}")

    def connect_to_lis(self):
        analyzer_id = self.analyzer_combo.currentData()
        if not analyzer_id:
            QMessageBox.warning(self, "Warning", "Please select an analyzer first")
            return
        
        self.log_text.append("Connecting to LIS...")
        QTimer.singleShot(1000, lambda: self.log_text.append("Connected successfully"))
        self.statusBar().showMessage("Connected")            

    def add_test(self):
        row = self.test_table.rowCount()
        self.test_table.insertRow(row)
        self.test_table.setItem(row, 0, QTableWidgetItem("New Test"))
        self.test_table.setItem(row, 1, QTableWidgetItem("Unit"))
        self.test_table.setItem(row, 2, QTableWidgetItem("0.0"))
        self.test_table.setItem(row, 3, QTableWidgetItem("0.0"))
    
    def edit_test(self):
        selected = self.test_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select a test to edit")
            return
        
        QMessageBox.information(self, "Info", "Test editing not implemented yet")
    
    def delete_test(self):
        selected = self.test_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select a test to delete")
            return
        
        row = selected[0].row()
        test_code = self.test_table.item(row, 0).text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Are you sure you want to delete test '{test_code}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.test_table.removeRow(row)        

    def save_templates(self):
        analyzer_id = self.analyzer_combo.currentData()
        if not analyzer_id:
            QMessageBox.warning(self, "Warning", "Please select an analyzer first")
            return
        
        try:
            conn = sqlite3.connect('analyzersim.db')
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM tests WHERE analyzer_id = ?", (analyzer_id,))
            
            for row in range(self.test_table.rowCount()):
                test_code = self.test_table.item(row, 0).text()
                unit = self.test_table.item(row, 1).text()
                lower_range = float(self.test_table.item(row, 2).text())
                upper_range = float(self.test_table.item(row, 3).text())
                
                cursor.execute("""
                    INSERT INTO tests (analyzer_id, test_code, unit, lower_range, upper_range)
                    VALUES (?, ?, ?, ?, ?)
                """, (analyzer_id, test_code, unit, lower_range, upper_range))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Success", "Templates and test data saved successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save templates and test data: {str(e)}")
                
    def toggle_connection_type(self):
        if self.tcp_radio.isChecked():
            self.tcp_widget.setVisible(True)
            self.serial_widget.setVisible(False)
        else:
            self.tcp_widget.setVisible(False)
            self.serial_widget.setVisible(True)
    
    def toggle_socket_type(self):
        server_mode = self.server_radio.isChecked()
        self.analyzer_address.setEnabled(True)
        self.analyzer_port.setEnabled(server_mode)
        self.lis_address.setEnabled(True)
        self.lis_port.setEnabled(not server_mode)                

    def add_field(self, selector, text, direction, target):
        field = selector.currentText()
        content = text.text()
        dir_text = direction.currentText()
        
        if field in ["ENQ", "ACK", "STX", "ETX", "EOT"]:
            target.append(f"{dir_text}: <{field}>")
        else:
            target.append(f"{dir_text}: {field} {content}")        