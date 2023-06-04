import os
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QComboBox, QPushButton, QTextEdit, QMessageBox, QHBoxLayout
import sys

# Get the current working directory
current_dir = os.getcwd()

# exefile directory path
exefile_dir = os.path.join(current_dir, "exefile")

# List to store .exe files
exe_files = []

# Recursively explore the files in the exefile directory
for root, dirs, files in os.walk(exefile_dir):
    if root == exefile_dir or root.startswith(exefile_dir + os.sep) and root.count(os.sep) <= exefile_dir.count(os.sep) + 1:
        for file in files:
            if file.endswith(".exe"):
                # Get the file name
                file_name = file
                # Add the file name to the list
                exe_files.append(file_name)

# Store the suffix notes for each option
option_suffixes = {
    "default": "/S",
    "Microsoft Windows Installer": "/QB REBOOT=Suppress",
    "Inno setup": "/verysilent sp-",
    "Ni-VISA": "--quiet --accept-eulas --prevent-reboot"
}

# Read external text file to get specific dropdown option settings
def read_option_settings(file_path):
    option_settings = {}

    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line:
                keyword, option = line.split("=")
                option_settings[keyword] = option

    return option_settings

# Store specific dropdown option settings
option_settings = read_option_settings("options.txt")

# Custom window class
class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Installer Selection")
        self.resize(400, 400)  # Adjust window size

        # Store the selected files and suffix notes
        self.selected_files = {}

        # Store the completed files and result messages
        self.completed_files = {}

        # Create a vertical layout
        self.layout = QVBoxLayout()

        # Create checkboxes and comboboxes
        for file in exe_files:
            checkbox = QCheckBox(file)
            combobox = QComboBox()
            combobox.addItems(["default", "Microsoft Windows Installer", "Inno setup", "Ni-VISA"])

            # Check if the file name contains keywords and set the default option
            for keyword, option in option_settings.items():
                if keyword in file:
                    combobox.setCurrentText(option)
                    break

            hbox_layout = QHBoxLayout()
            hbox_layout.addWidget(checkbox)
            hbox_layout.addWidget(combobox)

            self.layout.addLayout(hbox_layout)

            # Connect checkbox and combobox to update the selection
            checkbox.stateChanged.connect(lambda state, cb=combobox: cb.setEnabled(state))
            combobox.currentTextChanged.connect(lambda text, cb=checkbox, f=file: self.update_selection(cb, text, f))

            # Set the checkbox to checked by default
            checkbox.setChecked(True)

        # Create a button
        self.button = QPushButton("Confirm")
        self.button.clicked.connect(self.check_selection)
        self.layout.addWidget(self.button)

        # Create a QTextEdit for displaying completed files
        self.completed_files_textedit = QTextEdit()
        self.completed_files_textedit.setReadOnly(True)
        self.layout.addWidget(self.completed_files_textedit)

        self.setLayout(self.layout)

    # Update the selected files and suffix notes
    def update_selection(self, combobox, option, file):
        if option != "None":
            self.selected_files[file] = option
        elif file in self.selected_files:
            del self.selected_files[file]

    # Check the checkbox state and store the selection
    def check_selection(self):
        for i in range(0, self.layout.count()):
            layout_item = self.layout.itemAt(i)
            if isinstance(layout_item, QHBoxLayout):
                checkbox = layout_item.itemAt(0).widget()
                combobox = layout_item.itemAt(1).widget()
                if checkbox.isChecked() and combobox.currentText() != "None":
                    file = checkbox.text()
                    option = combobox.currentText()
                    self.selected_files[file] = option

        if len(self.selected_files) == 0:
            QMessageBox.warning(self, "Error", "Please select files and options to install")
        else:
            QMessageBox.information(self, "Selection Complete", f"Selected files and options: {', '.join(self.selected_files.keys())}")
            self.install_files()
            self.show_completed_files()

    # Execute the selected .exe files
    def install_files(self):
        for file, option in self.selected_files.items():
            file_path = os.path.join(exefile_dir, file)
            command_suffix = option_suffixes[option]
            command = f'"{file_path}" {command_suffix}'

            result = subprocess.run(command, shell=True)
            exit_code = result.returncode

            if exit_code == 0:
                self.completed_files[file] = "Installation successful"
                if "pyth" in file:
                    # Check if the PATH environment variable contains the string "python"
                    path_env = os.environ.get("PATH")
                    if "python" in path_env:
                        self.completed_files[file] = "Installation successful. 'python' is included in the PATH"
                    else:
                        self.completed_files[file] = "Installation successful. 'python' is not included in the PATH"
                        if sys.executable is None:
                            self.completed_files[file] = "Python is not installed"
                        else:
                            self.completed_files[file] = "Python is installed. Path: " + sys.executable
                            # Get the path of the Python interpreter
                            python_exe = sys.executable
                            # Get the parent directory path
                            parent_dir = os.path.abspath(os.path.join(python_exe, os.pardir))
                            # Get the current PATH value
                            current_path = os.environ.get('PATH')

                            # Target folder paths
                            python_dir = os.path.join(parent_dir, 'Python311')
                            scripts_dir = os.path.join(parent_dir, 'Python311', 'Scripts')
                            new_path = os.pathsep.join([python_dir, scripts_dir, current_path])
                            os.environ['PATH'] = new_path
                            print("Added target folder paths to PATH")

            elif exit_code == -125071:
                self.completed_files[file] = "Installation successful. System restart required"
            else:
                self.completed_files[file] = "Installation failed"

        # Clear the selected files/options
        self.selected_files = {}

    # Show the completed files and result messages
    def show_completed_files(self):
        self.completed_files_textedit.clear()
        for file, message in self.completed_files.items():
            if message == "Installation successful":
                self.completed_files_textedit.append(f"{file}: {message} ")
            elif message == "Installation successful. System restart required":
                self.completed_files_textedit.append(f"{file}: {message} ")
            else:
                self.completed_files_textedit.append(f"{file}: {message}")

# Create the application and window
app = QApplication([])
window = InstallerWindow()
window.show()

# Start the application event loop
app.exec_()
