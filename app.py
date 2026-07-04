import sys
import os
import csv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon
from pipeline import find_dcm_files, group_by_series, sort_into_folders
from extract import classify_series

class WorkerThread(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(dict)
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def __init__(self, folder_path, output_folder):
        super().__init__()
        self.folder_path = folder_path
        self.output_folder = output_folder

    def run(self):
        dcm_files = find_dcm_files(self.folder_path)
        groups = group_by_series(dcm_files)
        total = len(groups)
        self.status.emit(f"Found {len(dcm_files)} files in {total} series")

        for i, (uid, files) in enumerate(groups.items()):
            try:
                result = classify_series(files[0])
                result["file_count"] = len(files)
                self.result.emit(result)
            except Exception as e:
                self.result.emit({
                    "series_uid": uid,
                    "series_description": "Error",
                    "label": "unknown",
                    "confidence": 0.0,
                    "decision_path": "error",
                    "file_count": len(files)
                })
            self.progress.emit(int((i + 1) / total * 100))

        sort_into_folders(self.folder_path, self.output_folder)
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GridSift")
        self.setMinimumSize(800, 600)

        # Set window icon
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "gridsift.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.folder_path = None
        self.output_folder = None
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("GridSift")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Automatically classify and sort DICOM series from any hospital export")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        folder_layout.addWidget(self.folder_label)

        select_btn = QPushButton("Select Folder")
        select_btn.setFixedWidth(130)
        select_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(select_btn)
        layout.addLayout(folder_layout)

        # Output folder selection
        output_layout = QHBoxLayout()
        self.output_label = QLabel("No output folder selected")
        self.output_label.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        output_layout.addWidget(self.output_label)

        output_btn = QPushButton("Select Output")
        output_btn.setFixedWidth(130)
        output_btn.clicked.connect(self.select_output)
        output_layout.addWidget(output_btn)
        layout.addLayout(output_layout)

        # Study name input
        study_layout = QHBoxLayout()
        study_label = QLabel("Study Name:")
        study_label.setFixedWidth(90)
        study_layout.addWidget(study_label)
        self.study_name_input = __import__('PyQt6.QtWidgets', fromlist=['QLineEdit']).QLineEdit()
        self.study_name_input.setPlaceholderText("e.g. Study_001 (optional)")
        self.study_name_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        study_layout.addWidget(self.study_name_input)
        layout.addLayout(study_layout)

        # Run button
        self.run_btn = QPushButton("Run Classification")
        self.run_btn.setFixedHeight(44)
        self.run_btn.setEnabled(False)
        self.run_btn.setStyleSheet("background-color: #2E6DA4; color: white; font-size: 15px; border-radius: 6px;")
        self.run_btn.clicked.connect(self.run_classification)
        layout.addWidget(self.run_btn)

        # Export button
        self.export_btn = QPushButton("Export Results as CSV")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setVisible(False)
        self.export_btn.setStyleSheet("background-color: #27AE60; color: white; font-size: 14px; border-radius: 6px;")
        self.export_btn.clicked.connect(self.export_csv)
        layout.addWidget(self.export_btn)

        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Series Description", "Label", "Confidence", "Decision", "Files"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(folder)
            self.check_ready()

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_label.setText(folder)
            self.check_ready()

    def check_ready(self):
        if self.folder_path and self.output_folder:
            self.run_btn.setEnabled(True)

    def run_classification(self):
        self.run_btn.setEnabled(False)
        self.export_btn.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.table.setRowCount(0)

        study_name = self.study_name_input.text().strip()
        if study_name:
            final_output = os.path.join(self.output_folder, study_name)
        else:
            final_output = self.output_folder
        self.worker = WorkerThread(self.folder_path, final_output)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.result.connect(self.add_result_row)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def add_result_row(self, result):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(result.get("series_description", ""))))
        self.table.setItem(row, 1, QTableWidgetItem(str(result.get("label", ""))))
        self.table.setItem(row, 2, QTableWidgetItem(str(result.get("confidence", ""))))
        self.table.setItem(row, 3, QTableWidgetItem(str(result.get("decision_path", ""))))
        self.table.setItem(row, 4, QTableWidgetItem(str(result.get("file_count", ""))))

        if result.get("confidence", 0) == 0.0:
            for col in range(5):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QColor(255, 220, 220))

    def on_finished(self):
        self.status_label.setText(f"Done. Files sorted to: {self.output_folder}")
        self.run_btn.setEnabled(True)
        self.export_btn.setVisible(True)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "results.csv", "CSV Files (*.csv)")
        if path:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Series Description", "Label", "Confidence", "Decision", "Files"])
                for row in range(self.table.rowCount()):
                    writer.writerow([
                        self.table.item(row, col).text() if self.table.item(row, col) else ""
                        for col in range(5)
                    ])
            self.status_label.setText(f"CSV saved to: {path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())