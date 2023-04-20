#!/dls/science/groups/i23/pyenvs/carelesspy_3p9/bin/python
import sys
import os
import subprocess
import re
from PyQt5.QtWidgets import (
    QApplication,
    QProgressBar,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QPlainTextEdit,
    QScrollArea,
    QRadioButton,
    QSpinBox,
    QMessageBox,
    QComboBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class RunThread(QThread):
    output_received = pyqtSignal(str)
    finished_running = pyqtSignal()

    def __init__(self, command=None):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(
            self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                self.output_received.emit(output.strip())

        self.finished_running.emit()


class GUImore(QWidget):
    def __init__(self):
        super().__init__()
        self.enable_gpu = True
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        project_layout = QHBoxLayout()
        project_label = QLabel("Project:")
        self.project_edit = QLineEdit()
        self.project_set_btn = QPushButton("Set")
        self.project_set_btn.clicked.connect(self.create_project_folder)

        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_edit)
        project_layout.addWidget(self.project_set_btn)
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
        choices_label_layout = QHBoxLayout()
        data_labels_label = QLabel("Data Labels:")
        self.data_labels_edit = QLineEdit()
        self.data_labels_edit.setReadOnly(True)
        self.normal_radio = QRadioButton("Normal")
        self.normal_radio.setChecked(True)
        self.robust_radio = QRadioButton("Robust")
        self.boost_radio = QRadioButton("Boost")
        dof_label = QLabel("DOF:")
        iter_label = QLabel("Iterations:")
        booster_label = QLabel("Level:")
        self.dof_input = QSpinBox()
        self.dof_input.setMinimum(2)
        self.dof_input.setMaximum(64)
        self.dof_input.setValue(16)
        self.dof_input.setDisabled(True)
        run_careless_btn = QPushButton("Run Careless")
        run_careless_btn.clicked.connect(self.run_careless)
        run_careless_btn.setEnabled(False)
        self.run_careless_btn = run_careless_btn
        self.iterations_input = QSpinBox()
        self.iterations_input.setMinimum(1)
        self.iterations_input.setMaximum(999999)
        self.iterations_input.setValue(30000)

        self.boost_level_box = QComboBox()
        self.boost_level_box.addItem("fast")
        self.boost_level_box.addItem("normal")
        self.boost_level_box.addItem("intense")
        self.boost_level_box.setCurrentText("normal")
        self.boost_level_box.setDisabled(True)

        self.normal_radio.toggled.connect(self.update_boost_level_widgets)
        self.robust_radio.toggled.connect(self.update_boost_level_widgets)
        self.boost_radio.toggled.connect(self.update_boost_level_widgets)

        self.normal_radio.toggled.connect(
            lambda: self.dof_input.setDisabled(self.normal_radio.isChecked())
        )

        data_label_layout.addWidget(data_labels_label)
        data_label_layout.addWidget(self.data_labels_edit)
        choices_label_layout.addWidget(self.normal_radio)
        choices_label_layout.addWidget(self.robust_radio)
        choices_label_layout.addWidget(self.boost_radio)
        choices_label_layout.addWidget(dof_label)
        choices_label_layout.addWidget(self.dof_input)
        choices_label_layout.addWidget(iter_label)
        choices_label_layout.addWidget(self.iterations_input)
        choices_label_layout.addWidget(booster_label)
        choices_label_layout.addWidget(self.boost_level_box)
        choices_label_layout.addWidget(run_careless_btn)
        layout.addLayout(data_label_layout)
        layout.addLayout(choices_label_layout)

        self.output_message_box = QPlainTextEdit()
        self.output_message_box.setReadOnly(True)
        output_message_box_label = QLabel("Careless Output:")
        self.gpu_checkbox = QCheckBox("GPU")
        self.gpu_checkbox.setChecked(True)
        self.gpu_checkbox.stateChanged.connect(self.toggle_gpu)
        layout.addWidget(self.gpu_checkbox)
        layout.addWidget(output_message_box_label)
        layout.addWidget(self.output_message_box)

        self.run_thread = RunThread()
        self.run_thread.output_received.connect(self.handle_command_output)
        # self.run_thread.finished_running.connect(self.show_finished_message)

        # Reset Button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset)
        layout.addWidget(reset_btn)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setWindowTitle("GUImore")
        self.show()

    def create_project_folder(self):
        project_name = self.project_edit.text()
        if not project_name:
            QMessageBox.warning(self, "Warning", "Please enter a project name.")
            return

        try:
            os.makedirs("careless_" + project_name, exist_ok=True)
            self.projname = project_name
            self.project_set_btn.setStyleSheet("background-color: green")
            self.update_run_careless_button()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error creating project directory: {e}")

    def browse_input_file(self):
        file_filter = "MTZ Files (*.mtz);;All Files (*)"
        self.inputfile, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", file_filter
        )
        self.input_edit.setText(self.inputfile)
        if self.inputfile:
            self.mtz_dump_btn.setEnabled(True)
        self.update_run_careless_button()

    def mtz_dump(self):
        progress = QProgressBar(self)
        progress.setRange(0, 0)
        progress.show()
        try:
            output = subprocess.check_output(["rs.mtzdump", self.inputfile]).decode(
                "utf-8"
            )
            self.mtz_output.setPlainText(output)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Error", str(e))
        finally:
            progress.deleteLater()

        # Extract Batch and MTZReal column names
        start_line = "mtz.dtypes:\n"
        start_index = output.index(start_line) + len(start_line)
        mtz_lines = output[start_index:].split("\n")
        self.batch_and_mtzreal_columns = ["dHKL", "Hobs", "Kobs", "Lobs"]

        for line in mtz_lines:
            if "Batch" in line or "MTZReal" in line:
                column_name = line.split()[0]
                self.batch_and_mtzreal_columns.append(column_name)

        # Set data labels
        self.data_labels_edit.setText(", ".join(self.batch_and_mtzreal_columns))
        self.update_run_careless_button()

    def run_careless(self):
        iterations = self.iterations_input.value()
        if self.enable_gpu == True:
            enable_gpu = "--gpu-id=0"
        else:
            enable_gpu = "--disable-gpu"
        mode = (
            "normal"
            if self.normal_radio.isChecked()
            else "robust"
            if self.robust_radio.isChecked()
            else "boost"
        )
        mode_folder = os.path.join("careless_" + self.projname, mode)
        self.mode_folder = mode_folder
        if mode == "boost":
            os.makedirs(mode_folder + "_noanom", exist_ok=True)
            os.makedirs(mode_folder + "_anom", exist_ok=True)
            boost_level = self.boost_level_box.currentText()
            if boost_level == "fast":
                boost_layers = 1
            elif boost_level == "normal":
                boost_layers = 4
            else:
                boost_layers = 16
        else:
            os.makedirs(mode_folder, exist_ok=True)

        if mode == "normal":
            command = [
                "careless",
                "mono",
                "--anomalous",
                f"{enable_gpu}",
                "--disable-image-scales",
                "--merge-half-datasets",
                f"--iterations={iterations}",
                ",".join(self.batch_and_mtzreal_columns),
                self.inputfile,
                f"careless_{self.projname}/normal/{self.projname}",
            ]
        elif mode == "robust":
            dof = self.dof_input.value()
            command = [
                "careless",
                "mono",
                f"--studentt-likelihood-dof={dof}",
                "--anomalous",
                f"{enable_gpu}",
                "--disable-image-scales",
                "--merge-half-datasets",
                f"--iterations={iterations}",
                ",".join(self.batch_and_mtzreal_columns),
                self.inputfile,
                f"careless_{self.projname}/robust/{self.projname}",
            ]
        else:  # Boost mode
            dof = self.dof_input.value()
            command1 = [
                "careless",
                "mono",
                f"--studentt-likelihood-dof={dof}",
                f"{enable_gpu}",
                "--mc-samples=20",
                "--mlp-layers=10",
                f"--image-layers={boost_layers}",
                ",".join(self.batch_and_mtzreal_columns),
                self.inputfile,
                f"careless_{self.projname}/boost_noanom/{self.projname}",
            ]

            command2 = [
                "careless",
                "mono",
                "--freeze-scale",
                f"--scale-file=careless_{self.projname}/boost_noanom/{self.projname}_scale",
                "--anomalous",
                f"--studentt-likelihood-dof={dof}",
                f"{enable_gpu}",
                "--mc-samples=20",
                "--mlp-layers=10",
                f"--image-layers={boost_layers}",
                ",".join(self.batch_and_mtzreal_columns),
                self.inputfile,
                f"careless_{self.projname}/boost_anom/{self.projname}",
            ]

        if mode != "boost":
            self.run_command_thread(command)
        else:
            self.run_thread.finished.connect(self.run_second_command)
            self.second_command = command2
            self.run_command_thread(command1)

        QMessageBox.information(
            self,
            "Initiated",
            "Started running careless... output will appear in the output box shortly.",
        )
        self.output_message_box.appendPlainText("Starting careless, please wait...\n")

    def toggle_gpu(self, state):
        self.enable_gpu = bool(state)

    def update_run_careless_button(self):
        if (
            hasattr(self, "projname")
            and hasattr(self, "inputfile")
            and hasattr(self, "batch_and_mtzreal_columns")
        ):
            self.run_careless_btn.setEnabled(True)
        else:
            self.run_careless_btn.setEnabled(False)

    def update_boost_level_widgets(self):
        if self.boost_radio.isChecked():
            self.iterations_input.setDisabled(True)
            self.boost_level_box.setEnabled(True)
        else:
            self.iterations_input.setEnabled(True)
            self.boost_level_box.setDisabled(True)

    def run_command_thread(self, command):
        command_str = " ".join(command)
        self.output_message_box.appendPlainText(f"Command: {command_str}")

        self.run_thread.command = command
        self.run_thread.start()

    def run_second_command(self):
        self.run_thread.finished.disconnect(self.run_second_command)
        self.run_command_thread(self.second_command)

    def update_progress_bar(self, output):
        percentage_match = re.search(r"(\d+)%", output)
        if percentage_match:
            try:
                percentage = int(percentage_match.group(1))
                self.progress_bar.setValue(percentage)
            except ValueError:
                pass

    def handle_command_output(self, output):
        self.update_progress_bar(output)
        self.output_message_box.appendPlainText(output)

    def show_finished_message(self):
        QMessageBox.information(
            self,
            "Completed",
            f"Careless has finished running. You will find your results here:\n {str(self.mode_folder)}/{self.projname}_0.mtz\n !!! If you are running boost mode, you will see this message twice !!!",
        )

    def reset(self):
        self.project_set_btn.setStyleSheet("")
        self.project_edit.clear()
        self.input_edit.clear()
        self.mtz_output.clear()
        self.output_message_box.clear()
        self.normal_radio.setChecked(True)
        self.dof_input.setValue(16)
        self.iterations_input.setValue(30000)
        self.run_careless_btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUImore()
    sys.exit(app.exec_())
