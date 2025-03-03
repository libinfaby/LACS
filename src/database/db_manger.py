import sqlite3
from datetime import datetime
import random

class DatabaseManager:
    def __init__(self, db_path='analyzersim.db'):
        self.db_path = db_path

    def create_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create analyzer table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyzers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        ''')
        
        # Create connection settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS connection_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analyzer_id INTEGER,
            connection_type TEXT,
            socket_type TEXT,
            analyzer_address TEXT,
            analyzer_port TEXT,
            lis_address TEXT,
            lis_port TEXT,
            serial_port TEXT,
            baud_rate TEXT,
            data_bits TEXT,
            stop_bits TEXT,
            parity TEXT,
            auto_result_sending INTEGER,
            request_sample_info INTEGER,
            sample_id_delay INTEGER,
            result_sending_delay INTEGER,
            FOREIGN KEY (analyzer_id) REFERENCES analyzers(id)
        )
        ''')
        
        # Create ASTM message templates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS astm_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analyzer_id INTEGER,
            template_type TEXT,
            template_content TEXT,
            FOREIGN KEY (analyzer_id) REFERENCES analyzers(id)
        )
        ''')
        
        # Create tests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analyzer_id INTEGER,
            test_code TEXT,
            unit TEXT,
            lower_range REAL,
            upper_range REAL,
            FOREIGN KEY (analyzer_id) REFERENCES analyzers(id)
        )
        ''')
        
        # Create samples table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_number TEXT,
            patient_id TEXT,
            patient_name TEXT,
            date_time TEXT
        )
        ''')
        
        # Create results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER,
            test_id INTEGER,
            result_value REAL,
            sent INTEGER DEFAULT 0,
            FOREIGN KEY (sample_id) REFERENCES samples(id),
            FOREIGN KEY (test_id) REFERENCES tests(id)
        )
        ''')
        
        # Insert some initial data if needed
        cursor.execute("SELECT COUNT(*) FROM analyzers")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO analyzers (name) VALUES ('Analyzer 1')")
            cursor.execute("INSERT INTO analyzers (name) VALUES ('Analyzer 2')")
            
            # Insert some test examples
            analyzer_id = 1
            tests = [
                ('Test_1', 'mmol/l', 0.5, 5.0),
                ('Photo_reflex_test', 'mmol/l', 1.0, 5.5),
                ('Photometric_test', 'mmol/l', 0.05, 1.2)
            ]
            for test in tests:
                cursor.execute('''
                INSERT INTO tests (analyzer_id, test_code, unit, lower_range, upper_range)
                VALUES (?, ?, ?, ?, ?)
                ''', (analyzer_id, test[0], test[1], test[2], test[3]))
        
        conn.commit()
        conn.close()        