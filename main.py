import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import LabSimulator

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load stylesheet
    with open("resources/stylesheet.qss", "r") as f:
        app.setStyleSheet(f.read())

    window = LabSimulator()
    window.show()
    sys.exit(app.exec())