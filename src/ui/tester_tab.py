from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGroupBox, 
                             QRadioButton, QFormLayout, QLineEdit, QComboBox, QCheckBox, 
                             QPushButton, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QTabWidget, QMessageBox, QGridLayout, QFileDialog)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor
import socket
import serial
import json
from datetime import datetime

class CommThread(QThread):
    data_received = Signal(str)
    status_update = Signal(str)

    def __init__(self, protocol, connection_type, settings, auto_response=False):
        super().__init__()
        self.protocol = protocol
        self.connection_type = connection_type
        self.settings = settings
        self.running = False
        self.conn = None
        self.auto_response = auto_response

    def run(self):
        self.running = True
        try:
            if self.connection_type == "TCP/IP":
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self.settings.get("mode") == "Client":
                    self.conn.connect((self.settings["host"], int(self.settings["port"])))
                    self.status_update.emit("Connected via TCP/IP (Client)")
                else:  # Server
                    self.conn.bind(("", int(self.settings["port"])))
                    self.conn.listen(1)
                    self.status_update.emit("Server started, waiting for connection...")
                    self.conn, addr = self.conn.accept()
                    self.status_update.emit(f"Connected to {addr}")
            elif self.connection_type == "Serial":
                self.conn = serial.Serial(
                    port=self.settings["port"],
                    baudrate=int(self.settings["baudrate"]),
                    timeout=1
                )
                self.status_update.emit("Connected via Serial")

            while self.running:
                if self.connection_type == "TCP/IP":
                    data = self.conn.recv(1024).decode('utf-8')
                else:
                    data = self.conn.readline().decode('utf-8')
                if data:
                    self.data_received.emit(data)
                    if self.auto_response:
                        response = "ACK" if self.protocol == "ASTM" else "MSH|^~\&|SIM||LIS||20250225||ACK|||2.5"
                        self.send(response)

        except Exception as e:
            self.status_update.emit(f"Error: {str(e)}")
            self.running = False

    def send(self, message):
        if self.conn and self.running:
            if self.protocol == "ASTM":
                message = f"\x02{message}\x03"  # STX and ETX for ASTM
            elif self.protocol == "HL7":
                message = f"\x0B{message}\x1C\x0D"  # VT, FS, CR for HL7
            try:
                if self.connection_type == "TCP/IP":
                    self.conn.send(message.encode('utf-8'))
                else:
                    self.conn.write(message.encode('utf-8'))
                self.status_update.emit(f"Sent: {message}")
            except Exception as e:
                self.status_update.emit(f"Send error: {str(e)}")

    def stop(self):
        self.running = False
        if self.conn:
            if self.connection_type == "TCP/IP":
                self.conn.close()
            else:
                self.conn.close()
        self.status_update.emit("Connection closed")

class TesterTab(QWidget):
    # Define signals if needed
    # connection_status_changed = Signal(bool, str) # for example only

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create main layout
        main_layout = QHBoxLayout(self)
        
        # Split view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
         # Left: Settings Panel
        settings_panel = QGroupBox("Settings")
        settings_layout = QVBoxLayout()

        # Connection Status
        self.status_indicator = QLabel("Disconnected")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
        settings_layout.addWidget(self.status_indicator)

        # Protocol Selection
        settings_layout.addWidget(QLabel("Protocol:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["ASTM", "HL7"])
        settings_layout.addWidget(self.protocol_combo)

        # Connection Type
        settings_layout.addWidget(QLabel("Connection Type:"))
        self.conn_type_combo = QComboBox()
        self.conn_type_combo.addItems(["TCP/IP", "Serial"])
        self.conn_type_combo.currentTextChanged.connect(self.toggle_connection_fields)
        settings_layout.addWidget(self.conn_type_combo)

        # Mode Selection (Client/Server) - Side by side
        mode_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Mode:"))
        self.client_radio = QRadioButton("Client")
        self.server_radio = QRadioButton("Server")
        self.client_radio.setChecked(True)
        self.client_radio.toggled.connect(self.toggle_mode_fields)
        self.server_radio.toggled.connect(self.toggle_mode_fields)
        mode_layout.addWidget(self.client_radio)
        mode_layout.addWidget(self.server_radio)
        mode_layout.addStretch()
        settings_layout.addLayout(mode_layout)

        # Connection Settings
        self.conn_settings_grid = QGridLayout()
        self.host_label = QLabel("Host:")
        self.host_input = QLineEdit("localhost")
        self.port_label = QLabel("Port:")
        self.port_input = QLineEdit("5000")
        self.baud_label = QLabel("Baud Rate:")
        self.baud_input = QLineEdit("9600")
        
        self.conn_settings_grid.addWidget(self.host_label, 0, 0)
        self.conn_settings_grid.addWidget(self.host_input, 0, 1)
        self.conn_settings_grid.addWidget(self.port_label, 1, 0)
        self.conn_settings_grid.addWidget(self.port_input, 1, 1)
        self.conn_settings_grid.addWidget(self.baud_label, 2, 0)
        self.conn_settings_grid.addWidget(self.baud_input, 2, 1)
        settings_layout.addLayout(self.conn_settings_grid)

        # Auto-Response Checkbox
        self.auto_response_check = QCheckBox("Auto-Response")
        settings_layout.addWidget(self.auto_response_check)

        # Lab Machine Selector
        settings_layout.addWidget(QLabel("Lab Machine:"))
        self.machine_combo = QComboBox()
        self.machine_combo.addItems(["Analyzer A", "Analyzer B", "Centrifuge", "Custom"])
        settings_layout.addWidget(self.machine_combo)

        # Connect/Disconnect Buttons
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_to_lis)
        settings_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_from_lis)
        self.disconnect_btn.setEnabled(False)
        settings_layout.addWidget(self.disconnect_btn)

        # Save/Load Settings Buttons
        settings_btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.load_btn = QPushButton("Load Settings")
        self.load_btn.clicked.connect(self.load_settings)
        settings_btn_layout.addWidget(self.save_btn)
        settings_btn_layout.addWidget(self.load_btn)
        settings_layout.addLayout(settings_btn_layout)

        settings_layout.addStretch()
        settings_panel.setLayout(settings_layout)
        settings_panel.setFixedWidth(300)
        
        # Right panel - IO panel
        io_widget = QWidget()
        io_panel = QVBoxLayout(io_widget)

        # Input Window (Received Data)
        input_group = QGroupBox("Input (Received from LIS)")
        input_layout = QVBoxLayout()
        self.input_window = QTextEdit()
        self.input_window.setReadOnly(True)
        input_layout.addWidget(self.input_window)
        self.clear_input_btn = QPushButton("Clear Input")
        self.clear_input_btn.clicked.connect(lambda: self.input_window.clear())
        input_layout.addWidget(self.clear_input_btn)
        input_group.setLayout(input_layout)
        io_panel.addWidget(input_group, stretch=2)

        # Output Window (Sent Data)
        output_group = QGroupBox("Output (Sent to LIS)")
        output_layout = QVBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.addItems(["Custom", "ASTM ACK", "HL7 ACK", "Sample Result"])
        self.template_combo.currentTextChanged.connect(self.load_template)
        output_layout.addWidget(self.template_combo)
        self.output_window = QTextEdit()
        output_layout.addWidget(self.output_window)
        output_btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send Output")
        self.send_btn.clicked.connect(self.send_output)
        self.send_btn.setEnabled(False)
        self.clear_output_btn = QPushButton("Clear Output")
        self.clear_output_btn.clicked.connect(lambda: self.output_window.clear())
        output_btn_layout.addWidget(self.send_btn)
        output_btn_layout.addWidget(self.clear_output_btn)
        output_layout.addLayout(output_btn_layout)
        output_group.setLayout(output_layout)
        io_panel.addWidget(output_group, stretch=2)

        # Status Log
        status_group = QGroupBox("Status Log")
        status_layout = QVBoxLayout()
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        status_layout.addWidget(self.status_log)
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(lambda: self.status_log.clear())
        status_layout.addWidget(self.clear_log_btn)
        status_group.setLayout(status_layout)
        io_panel.addWidget(status_group, stretch=1)

        # Initial State
        self.thread = None
        self.toggle_connection_fields("TCP/IP")
        self.toggle_mode_fields()
        self.status_log.append(f"Simulator started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add widgets to main layout
        splitter.addWidget(settings_panel)
        splitter.addWidget(io_widget)
        splitter.setSizes([300, 700])  # Initial sizes
        main_layout.addWidget(splitter)

    def toggle_connection_fields(self, conn_type):
        if conn_type == "TCP/IP":
            self.host_label.show()
            self.host_input.show()
            self.port_label.setText("Port:")
            self.port_label.show()
            self.port_input.show()
            self.baud_label.hide()
            self.baud_input.hide()
            self.toggle_mode_fields()
        else:  # Serial
            self.host_label.hide()
            self.host_input.hide()
            self.port_label.setText("Serial Port:")
            self.port_label.show()
            self.port_input.setText("COM1")
            self.port_input.show()
            self.baud_label.show()
            self.baud_input.show()

    def toggle_mode_fields(self):
        if self.conn_type_combo.currentText() == "TCP/IP":
            if self.client_radio.isChecked():
                self.host_label.setEnabled(True)
                self.host_input.setEnabled(True)
            elif self.server_radio.isChecked():
                self.host_label.setEnabled(False)
                self.host_input.setEnabled(False)

    def connect_to_lis(self):
        self.status_indicator.setText("Connecting")
        self.status_indicator.setStyleSheet("color: yellow; font-weight: bold;")
        settings = {
            "host": self.host_input.text(),
            "port": self.port_input.text(),
            "baudrate": self.baud_input.text(),
            "mode": "Client" if self.client_radio.isChecked() else "Server"
        }
        protocol = self.protocol_combo.currentText()
        conn_type = self.conn_type_combo.currentText()

        self.thread = CommThread(protocol, conn_type, settings, self.auto_response_check.isChecked())
        self.thread.data_received.connect(self.update_input_window)
        self.thread.status_update.connect(self.update_status_log)
        self.thread.start()

        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.send_btn.setEnabled(True)

    def disconnect_from_lis(self):
        if self.thread:
            self.thread.stop()
            self.thread.wait()
            self.thread = None
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.status_indicator.setText("Disconnected")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")

    def send_output(self):
        if self.thread and self.thread.running:
            message = self.output_window.toPlainText().strip()
            if message:
                self.thread.send(message)
                self.output_window.clear()
            else:
                QMessageBox.warning(self, "Empty Message", "Please enter data to send.")

    def update_input_window(self, data):
        self.input_window.append(f"[{datetime.now().strftime('%H:%M:%S')}] {data}")

    def update_status_log(self, message):
        self.status_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        if "Connected" in message:
            self.status_indicator.setText("Connected")
            self.status_indicator.setStyleSheet("color: green; font-weight: bold;")
        elif "Error" in message or "closed" in message.lower():
            self.status_indicator.setText("Disconnected")
            self.status_indicator.setStyleSheet("color: red; font-weight: bold;")

    def save_settings(self):
        settings = {
            "protocol": self.protocol_combo.currentText(),
            "conn_type": self.conn_type_combo.currentText(),
            "mode": "Client" if self.client_radio.isChecked() else "Server",
            "host": self.host_input.text(),
            "port": self.port_input.text(),
            "baudrate": self.baud_input.text(),
            "machine": self.machine_combo.currentText(),
            "auto_response": self.auto_response_check.isChecked()
        }
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Settings", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'w') as f:
                json.dump(settings, f)
            self.status_log.append(f"Settings saved to {file_name}")

    def load_settings(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Settings", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r') as f:
                settings = json.load(f)
                self.protocol_combo.setCurrentText(settings["protocol"])
                self.conn_type_combo.setCurrentText(settings["conn_type"])
                self.client_radio.setChecked(settings["mode"] == "Client")
                self.server_radio.setChecked(settings["mode"] == "Server")
                self.host_input.setText(settings["host"])
                self.port_input.setText(settings["port"])
                self.baud_input.setText(settings["baudrate"])
                self.machine_combo.setCurrentText(settings["machine"])
                self.auto_response_check.setChecked(settings["auto_response"])
                self.toggle_connection_fields(settings["conn_type"])
                self.toggle_mode_fields()
            self.status_log.append(f"Settings loaded from {file_name}")

    def load_template(self, template):
        if template == "ASTM ACK":
            self.output_window.setText("ACK")
        elif template == "HL7 ACK":
            self.output_window.setText("MSH|^~\&|SIM||LIS||20250225||ACK|||2.5")
        elif template == "Sample Result":
            if self.protocol_combo.currentText() == "ASTM":
                self.output_window.setText("H|\^&|||SIM|||||||20250225\rP|1\rO|1||^^^GLU||20250225||||||A\rR|1|^^^GLU|5.5|mmol/L||||F")
            else:  # HL7
                self.output_window.setText("MSH|^~\&|SIM||LIS||20250225||ORU^R01|||2.5\rPID|1||12345||Doe^John\rOBR|1|||^GLUCOSE\rOBX|1|NM|^GLUCOSE||5.5|mmol/L|||F")
        else:
            self.output_window.clear()