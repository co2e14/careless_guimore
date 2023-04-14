import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QProgressBar, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QPlainTextEdit, QScrollArea, QRadioButton, QSpinBox, QMessageBox
from PyQt5.QtCore import Qt

class GUImore(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Project Name
        project_layout = QHBoxLayout()
        project_label = QLabel("Project:")
        self.project_edit = QLineEdit()
        project_set_btn = QPushButton("Set")
        project_set_btn.clicked.connect(self.create_project_folder)

        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_edit)
        project_layout.addWidget(project_set_btn)
        layout.addLayout(project_layout)

        # Input File
        input_layout = QHBoxLayout()
        input_label = QLabel("Input File (.mtz):")
        self.input_edit = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_input_file)
        self.mtz_dump_btn = QPushButton("MTZ dump")
        self.mtz_dump_btn.clicked.connect(self.mtz_dump)
        self.mtz_dump_btn.setDisabled(True)

        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(browse_btn)
        input_layout.addWidget(self.mtz_dump_btn)
        layout.addLayout(input_layout)

        # MTZ Dump Output
        self.mtz_output = QPlainTextEdit()
        self.mtz_output.setReadOnly(True)
        scroll = QScrollArea()
        scroll.setWidget(self.mtz_output)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Data Labels, DOF, and Run Careless
        data_label_layout = QHBoxLayout()
        self.datalabels = QLabel()
        self.normal_radio = QRadioButton("Normal")
        self.normal_radio.setChecked(True)
        self.robust_radio = QRadioButton("Robust")
        self.boost_radio = QRadioButton("Boost")
        dof_label = QLabel("DOF:")
        self.dof_input = QSpinBox()
        self.dof_input.setMinimum(2)
        self.dof_input.setMaximum(64)
        self.dof_input.setValue(16)
        self.dof_input.setDisabled(True)
        run_careless_btn = QPushButton("Run Careless")
        run_careless_btn.clicked.connect(self.run_careless)
        self.iterations_input = QSpinBox()
        self.iterations_input.setMinimum(1)
        self.iterations_input.setMaximum(999999)
        self.iterations_input.setValue(30000)

        self.normal_radio.toggled.connect(lambda: self.dof_input.setDisabled(self.normal_radio.isChecked()))

        data_label_layout.addWidget(self.datalabels)
        data_label_layout.addWidget(self.normal_radio)
        data_label_layout.addWidget(self.robust_radio)
        data_label_layout.addWidget(self.boost_radio)
        data_label_layout.addWidget(dof_label)
        data_label_layout.addWidget(self.dof_input)
        data_label_layout.addWidget(run_careless_btn)
        data_label_layout.addWidget(self.iterations_input)
        layout.addLayout(data_label_layout)

        # Reset Button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset)
        layout.addWidget(reset_btn)

        self.setLayout(layout)
        self.setWindowTitle("GUImore")
        self.show()

    def create_project_folder(self):
        self.projname = self.project_edit.text()
        os.makedirs(self.projname + "_careless", exist_ok=True)

    def browse_input_file(self):
        file_filter = "MTZ Files (*.mtz);;All Files (*)"
        self.inputfile, _ = QFileDialog.getOpenFileName(self, "Open File", "", file_filter)
        self.input_edit.setText(self.inputfile)
        if self.inputfile:
            self.mtz_dump_btn.setEnabled(True)

    def mtz_dump(self):
        progress = QProgressBar(self)
        progress.setRange(0, 0)
        progress.show()
        try:
            output = subprocess.check_output(["rs.mtzdump", self.inputfile]).decode("utf-8")
            self.mtz_output.setPlainText(output)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Error", str(e))
        finally:
            progress.deleteLater()

        # Extract Batch and MTZReal column names
        start_line = "mtz.dtypes:\n"
        start_index = output.index(start_line) + len(start_line)
        mtz_lines = output[start_index:].split("\n")
        self.batch_and_mtzreal_columns = []

        for line in mtz_lines:
            if "Batch" in line or "MTZReal" in line:
                column_name = line.split()[0]
                self.batch_and_mtzreal_columns.append(column_name)

        # Set data labels
        self.datalabels.setText(", ".join(["dHKL", "Hobs", "Kobs", "Lobs"] + self.batch_and_mtzreal_columns))

    def run_careless(self):
        iterations = self.iterations_input.value()
        mode = "normal" if self.normal_radio.isChecked() else "robust"
        mode_folder = os.path.join(self.projname + "_careless", mode)
        os.makedirs(mode_folder, exist_ok=True)

        popup = f"Finished running Careless. See {self.projname}_0.mtz"
        if mode == "normal":
            command = ["careless", "mono", "--anomalous", "--disable-image-scales", "--merge-half-datasets",
                       f"--iterations={iterations}", ",".join(self.batch_and_mtzreal_columns), self.inputfile,
                       f"{self.projname}_careless/normal/{self.projname}"]
        elif mode == "robust":
            dof = self.dof_input.value()
            command = ["careless", "mono", f"--studentt-likelihood-dof={dof}", "--anomalous",
                       "--disable-image-scales", "--merge-half-datasets", f"--iterations={iterations}",
                       ",".join(self.batch_and_mtzreal_columns), self.inputfile, f"{self.projname}_careless/robust/{self.projname}"]
        else:  # Boost mode
            dof = self.dof_input.value()
            command1 = ["careless", "mono", f"--studentt-likelihood-dof={dof}", "--mc-samples=20", "--mlp-layers=10", "--image-layers=2",
                    ",".join(self.batch_and_mtzreal_columns), self.inputfile, f"{self.projname}_careless/boost/{self.projname}_noanom"]
            subprocess.call(command1)

            command2 = ["careless", "mono", "--freeze-scale", f"--scale-file=careless/boost/{self.projname}_noanom",
                    f"--studentt-likelihood-dof={dof}", "--mc-samples=20", "--mlp-layers=10", "--image-layers=2",
                    ",".join(self.batch_and_mtzreal_columns), self.inputfile, f"{self.projname}_careless/boost/{self.projname}_anom"]
            subprocess.call(command2)
            popup = f"Finished running Careless. See {self.projname}_anom_0.mtz"

        subprocess.call(command)
        
        QMessageBox.information(self, "Finished", popup)

    def reset(self):
        self.project_edit.clear()
        self.input_edit.clear()
        self.mtz_output.clear()
        self.normal_radio.setChecked(True)
        self.dof_input.setValue(16)
        self.iterations_input.setValue(30000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUImore()
    sys.exit(app.exec_())
