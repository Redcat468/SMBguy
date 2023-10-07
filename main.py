# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from PyQt5.QtWidgets import QApplication, QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, QLabel,QLayout, QWidget, QTextEdit, QMessageBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap
import sys
import win32wnet
import win32net
import win32netcon
import win32file
import win32api
import string
import os

def get_shares(server, username, password):
    global share_info
    share_info = {}
    
    try:
        net_resource = win32wnet.NETRESOURCE()
        net_resource.lpRemoteName = f"\\\\{server}"
        net_resource.lpProvider = None
        net_resource.dwType = win32netcon.RESOURCETYPE_DISK
        win32wnet.WNetAddConnection2(net_resource, password, username)

        shares, _, _ = win32net.NetShareEnum(server, 0)
        # Remove IPC$ share if it exists
        shares = [share for share in shares if share['netname'] != 'IPC$']
        
        # Initialize share_info with all shares set to 'Not Mounted'
        for share in shares:
            share_info[share['netname']] = {'is_mounted': False, 'mount_letter': None}

        drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]


        for drive in drives:
            try:
                # This will give the UNC path of the share
                remote_name = win32wnet.WNetGetConnection(drive[:-1])
                
                # Remove leading '\\' from the UNC path and split
                remote_server, remote_share = remote_name[2:].split('\\', 1)
                
                if remote_server.lower() == server.lower():
                    if remote_share in share_info:
                        share_info[remote_share] = {'is_mounted': True, 'mount_letter': drive[:-1]}

            except Exception as e:
                # Likely an error due to the drive not being a network share
                pass
        
        
    except Exception as e:
        if e.winerror == 1219:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("You are already connected to this server with different credentials. Do you want to disconnect and change the login?")
            msg_box.setWindowTitle("Connection Error")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            
            return_value = msg_box.exec()
            if return_value == QMessageBox.Yes:
                import subprocess
                subprocess.run(["net", "use", "*", "/delete", "/y"])
                get_shares(server, username, password)
            else:
                os.execv(sys.executable, ['python'] + sys.argv)

        else:
            print(f"Failed to get shares: {e}")
            QMessageBox.warning(None, 'Failed to get shares', f"Failed to get shares: {e}")
            print("Relaunching the program...")
            os.execv(sys.executable, ['python'] + sys.argv)

    return share_info

def get_available_drive_letters():
    global all_drive_letters
    all_drive_letters = {}
    # All possible drive letters from A to Z
    all_drive_letters = set(string.ascii_uppercase)
    global used_drive_letters
    used_drive_letters = {}
    # Get currently used drive letters
    used_drive_letters = set([drive[0].upper() for drive in win32api.GetLogicalDriveStrings().split('\x00')[:-1]])
    global available_drive_letters
    available_drive_letters = {}
    # Calculate available drive letters
    available_drive_letters = sorted(list(all_drive_letters - used_drive_letters))

    return available_drive_letters

class SMBClient(QWidget):
    def __init__(self):
        super().__init__()
        self.tray_icon = None
        self.initUI()
        self.setWindowTitle('SMBGuy')
        self.setWindowIcon(QIcon('logo.ico'))
        self.click_count = 0
        self.text_editor = None
        
    def settings_clicked(self, event):
            self.text_editor = TextEditor()
            self.text_editor.show()
            self.hide()

    def initUI(self):
        
        # Initialisation du QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('path_to_your_icon.png'))

        # Création du menu pour le QSystemTrayIcon
        tray_menu = QMenu()

        restore_action = QAction("Restore", self)
        quit_action = QAction("Exit", self)

        restore_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quit_application)

        tray_menu.addAction(restore_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        
        self.layout = QHBoxLayout()
        self.layout.setSpacing(10)

        # Create a QVBoxLayout to stack the logo and configure servers button
        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.setSpacing(0)
        self.vertical_layout.setSizeConstraint(QLayout.SetMaximumSize)
        # Column 1: Logo
        self.logo_button = QPushButton(self)
        self.logo_button.setIcon(QIcon('logo.png'))
        self.logo_button.setIconSize(QSize(190, 190))
        self.logo_button.setStyleSheet("background-color: transparent;")
        self.vertical_layout.addWidget(self.logo_button)
        
        # Configure Servers Button
        self.configure_servers_button = QPushButton('Configure servers', self)
        self.configure_servers_button.setFont(QFont('Arial', 10, QFont.Bold))
        self.configure_servers_button.setIcon(QIcon('settings.png'))
        self.configure_servers_button.clicked.connect(self.settings_clicked)
        self.configure_servers_button.setFixedSize(210, 30)
        self.vertical_layout.addWidget(self.configure_servers_button)

        # Add the QVBoxLayout to the QHBoxLayout
        self.layout.addLayout(self.vertical_layout)
        
        column_layout = QVBoxLayout()

        label = QLabel('Select a server :  ', self)
        label.setFont(QFont('Arial', 10, QFont.Bold))
        self.server_input = QComboBox(self)
        self.server_input.setFixedSize(300, 30)
        self.server_input.setFont(QFont('Arial', 10, QFont.Bold))
        # Add server list from servers.ini to the ComboBox
        with open('servers.ini', 'r') as file:
            servers = [line.split(',')[1].strip() for line in file.readlines()]
            self.server_input.addItems(servers)

        column_layout.addWidget(label)
        column_layout.addWidget(self.server_input, 0, Qt.AlignTop)

        label_credentials = QLabel('Connect as : ', self)
        label_credentials.setFont(QFont('Arial', 10, QFont.Bold))
        column_layout.addWidget(label_credentials)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText('Enter Username')
        self.username_input.setFont(QFont('Arial', 10, QFont.Bold))
        column_layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Enter Password')
        self.password_input.setFont(QFont('Arial', 10, QFont.Bold))
        self.password_input.setEchoMode(QLineEdit.Password)
        column_layout.addWidget(self.password_input)        

        column_layout.addSpacing(5)

        self.connect_button = QPushButton('Connect to selected server', self)
        self.connect_button.setFont(QFont('Arial', 10, QFont.Bold))
        self.connect_button.setIcon(QIcon('login.png'))
        self.connect_button.clicked.connect(self.connect)
        self.connect_button.setFixedSize(210, 30)

        self.disconnect_button = QPushButton('Disconnect ALL', self)
        self.disconnect_button.setFont(QFont('Arial', 10, QFont.Bold))
        self.disconnect_button.setIcon(QIcon('logout.png'))
        self.disconnect_button.clicked.connect(self.disconnect)
        self.disconnect_button.setFixedSize(140, 30)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)

        column_layout.addLayout(button_layout)

        self.layout.addLayout(column_layout)

        # Fix the main window size based on its content
        self.setFixedSize(600, 250)
        self.setLayout(self.layout)
              
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.connect()
            
    def connect(self): 
        global server
        global username
        global password
        
        with open('servers.ini', 'r') as file:
            for line in file:
                if self.server_input.currentText() in line:
                    server = line.split(',')[0].strip()
                    break
        username = self.username_input.text()
        password = self.password_input.text()
    
        get_shares(server,username,password)
        get_available_drive_letters()
        share_table = ShareTable(share_info, available_drive_letters)
        share_table.show()
        self.hide()
        self.tray_icon.hide()

    def disconnect(self):     
        try:
            import subprocess
            subprocess.run(["net", "use", "*", "/delete", "/y"])
            QMessageBox.information(self, 'Success', 'All network connections have been disconnected.')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to disconnect network connections: {str(e)}')
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('logo_tray.ico'))
        self.tray_icon.show()
        self.tray_icon.showMessage(
            "SMBguy",
            "Application was minimized to Tray",
            QIcon('logo_tray.ico'),
            2000
        )
        self.tray_icon.activated.connect(self.tray_icon_clicked)
            # Création du menu pour le QSystemTrayIcon
        tray_menu = QMenu()

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()
            self.tray_icon.hide()

    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()
        
class TextEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SMBGuy Server list Editor')
        self.setWindowIcon(QIcon('logo.ico'))
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        banner_image = QLabel(self)
        pixmap = QPixmap('bandeau.png')
        pixmap = pixmap.scaledToWidth(300)
        banner_image.setPixmap(pixmap)
        banner_image.setAlignment(Qt.AlignCenter)
        layout.addWidget(banner_image)
        
        instruction_label = QLabel("You can configure the list of available servers below.", self)
        instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction_label)
        instruction_label2 = QLabel("Enter the server's IP address and the name you wish to display for this server on the same line.", self)
        instruction_label2.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction_label2)
        instruction_label3 = QLabel("Separate the address and the name with a comma.", self)
        instruction_label3.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction_label3)

        # Créer le widget QTextEdit pour l'édition du fichier
        self.text_edit = QTextEdit(self)
        layout.addWidget(self.text_edit)

        # Charger le contenu du fichier servers.ini dans le QTextEdit
        with open('servers.ini', 'r') as file:
            content = file.read()
            self.text_edit.setText(content)

        # Boutton Save
        self.save_btn = QPushButton('Save and reload', self)
        self.save_btn.clicked.connect(self.saveToFile)
        layout.addWidget(self.save_btn)

        # Boutton Cancel
        self.cancel_btn = QPushButton('Cancel', self)
        self.cancel_btn.clicked.connect(self.cancel_edition)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)
        self.resize(400, 500)
        self.show()

    def saveToFile(self):
        with open('servers.ini', 'w') as file:
            content = self.text_edit.toPlainText()
            file.write(content)
        self.close()
        
    def cancel_edition(self):
        self.close()

    def closeEvent(self, event):
        # Lorsque la fenêtre est fermée, relancez l'application
        os.execv(sys.executable, ['python'] + sys.argv)
                               
class ShareTable(QWidget):
    def __init__(self, share_info, available_drive_letters):
        super().__init__()
        self.share_info = share_info
        self.available_drive_letters = available_drive_letters
        self.setWindowTitle('SMBGuy')
        self.setWindowIcon(QIcon('logo.ico'))
        self.initUI()
    
    def initUI(self):
        
        # Initialisation du QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('path_to_your_icon.png'))

        # Création du menu pour le QSystemTrayIcon
        tray_menu = QMenu()

        restore_action = QAction("Restore", self)
        quit_action = QAction("Exit", self)

        restore_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quit_application)

        tray_menu.addAction(restore_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    
        self.layout = QVBoxLayout()
        banner_image = QLabel(self)
        pixmap = QPixmap('bandeau.png')
        pixmap = pixmap.scaledToWidth(300)
        banner_image.setPixmap(pixmap)
        banner_image.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(banner_image)
        spacer = QLabel(self)
        spacer.setFixedHeight(30)
        self.layout.addWidget(spacer)
        self.table = QTableWidget()
        self.table.setShowGrid(False)        
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent; 
                border: none;
            }
            QTableWidget::item {
                border: 0px solid transparent;
            }
            QTableWidget QHeaderView::section {
                background-color: transparent;
                border: 0px solid transparent;
                border-bottom: 0px solid;  
            }
            QTableWidget::verticalHeader {
                border: 0px solid transparent;
                border-right: 0px solid;  
            }
            QTableWidget::horizontalHeader {
                border: 0px solid transparent;
                text-align: left;
            }
        """)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Share Name', 'Current letter', 'Change letter', 'Mount', 'Unmount'])
        
        self.table.setRowCount(len(self.share_info))
        
        for row, (share_name, info) in enumerate(self.share_info.items()):
            # Column 1: Share Name
            self.table.setItem(row, 0, QTableWidgetItem(share_name))
            # Check if share is mounted and set font to bold if it is
            if info.get('is_mounted', False):
                font = self.table.item(row, 0).font()
                font.setWeight(QFont.Bold)
                self.table.item(row, 0).setFont(font)
                # Refresh the table when the mount button is clicked
                self.table.itemClicked.connect(self.refresh_table)
            
            # Column 2: Current Drive Letter
            current_drive_letter = info.get('mount_letter', '')
            item = QTableWidgetItem(current_drive_letter)
            item.setFont(QFont("Arial", weight=QFont.Bold))
            self.table.setItem(row, 1, item)

            
            # Column 3: Available Drive Letters (ComboBox)
            combo = QComboBox()
            combo.setStyleSheet("background-color: normal; text-align: center;")
            for letter in self.available_drive_letters:
                combo.addItem(letter)
            self.table.setCellWidget(row, 2, combo)
            
            # Column 4: Mount Button
            mount_button = QPushButton('Mount')
            mount_button = QPushButton('Mount')
            mount_button.setStyleSheet("background-color: normal;")
            mount_button.clicked.connect(lambda _, row=row: self.mount_share(row))
            self.table.setCellWidget(row, 3, mount_button)
            
            # Column 5: Unmount Button
            unmount_button = QPushButton('Unmount')
            unmount_button.setStyleSheet("background-color: normal;")
            unmount_button.clicked.connect(lambda _, row=row: self.unmount_share(row))
            self.table.setCellWidget(row, 4, unmount_button)
        
        self.layout.addWidget(self.table)
        # Button: Log out or switch server
        self.unmount_all_button = QPushButton('Log out or switch server', self)
        self.unmount_all_button.clicked.connect(self.switch_server)
        self.layout.addWidget(self.unmount_all_button)
        
        self.setLayout(self.layout)
        self.setMinimumSize(540, 500)

    def refresh_table(self):
        get_shares(server, username, password)
        get_available_drive_letters()
        self.table.setRowCount(len(share_info))
        
        for row, (share_name, info) in enumerate(share_info.items()):
            # Column 1: Share Name
            self.table.setItem(row, 0, QTableWidgetItem(share_name))
            # Check if share is mounted and set font to bold if it is
            if info.get('is_mounted', False):
                font = self.table.item(row, 0).font()
                font.setWeight(QFont.Bold)
                self.table.item(row, 0).setFont(font)
                # Refresh the table when the mount button is clicked
                self.table.itemClicked.connect(self.refresh_table)
            
            # Column 2: Current Drive Letter
            current_drive_letter = info.get('mount_letter', '')
            item = QTableWidgetItem(current_drive_letter)
            item.setFont(QFont("Arial", weight=QFont.Bold))
            self.table.setItem(row, 1, item)
            
            # Column 3: Available Drive Letters (ComboBox)
            combo = QComboBox()
            combo.clear()
            combo.setStyleSheet("background-color: normal;")
            for letter in available_drive_letters:
                combo.addItem(letter)
            combo.addItem('')            
            self.table.setCellWidget(row, 2, combo)
            
            # Column 4: Mount Button
            mount_button = QPushButton('Mount')
            mount_button.setStyleSheet("background-color: normal;")
            mount_button.clicked.connect(lambda _, row=row: self.mount_share(row))
            self.table.setCellWidget(row, 3, mount_button)
            
            # Column 5: Unmount Button
            unmount_button = QPushButton('Unmount')
            unmount_button.setStyleSheet("background-color: normal;")
            unmount_button.clicked.connect(lambda _, row=row: self.unmount_share(row))
            self.table.setCellWidget(row, 4, unmount_button)

    def mount_share(self, row):

        share_name = self.table.item(row, 0).text()
        drive_letter = self.table.cellWidget(row, 2).currentText().replace(":", "")
        network_path = f"\\\\{server}\\{share_name}"

        try:
            net_resource = win32wnet.NETRESOURCE()
            net_resource.lpRemoteName = network_path
            net_resource.lpLocalName = f"{drive_letter}:"
            net_resource.lpProvider = None
            net_resource.dwType = win32netcon.RESOURCETYPE_DISK

            win32wnet.WNetAddConnection2(net_resource, password, username)
            print(f"Successfully mounted {network_path} to {drive_letter}:")

        except Exception as e:
            QMessageBox.warning(self, 'Error', f"Failed to mount drive: {e}")
        
        self.refresh_table()

    def unmount_share(self, row):
        drive_letter = self.table.item(row, 1).text()# Utilisez la lettre de la colonne 'Mount Status'
        try:
            win32wnet.WNetCancelConnection2(f"{drive_letter}", 0, 0)

        except win32wnet.error as e:
            error_code, _, error_message = e.args
            print(f"Failed to unmount drive: ({error_code}, 'WNetCancelConnection2', '{error_message}')")
            QMessageBox.warning(self, 'Error', f"Failed to unmount drive: ({error_code}, 'WNetCancelConnection2', '{error_message}')")
        
        self.refresh_table()

    def switch_server(self):
        self.smb_client = SMBClient()
        self.smb_client.show()
        self.hide()
        self.tray_icon.hide()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('logo_tray.ico'))
        self.tray_icon.show()
        self.tray_icon.showMessage(
            "SMBguy",
            "Application was minimized to Tray",
            QIcon('logo_tray.ico'),
            2000
        )
        self.tray_icon.activated.connect(self.tray_icon_clicked)
            # Création du menu pour le QSystemTrayIcon
        tray_menu = QMenu()

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()
            self.tray_icon.hide()

    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SMBClient()
    ex.show()
    sys.exit(app.exec_())
