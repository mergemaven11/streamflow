import os
import sys
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, 
    QHBoxLayout, QWidget, QGridLayout, QScrollArea, QDialog, QFormLayout, 
    QLineEdit, QFileDialog, QDialogButtonBox, QComboBox, QLabel, QListWidgetItem, QGroupBox, QCheckBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot, Qt, QSize
import handlers

scriptDir = os.path.dirname(os.path.realpath(__file__))

class CategoryDialog(QDialog):
    def __init__(self, category, buttons, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'{category} Buttons')
        self.layout = QVBoxLayout(self)

        for btn_data in buttons:
            btn_checkbox = QCheckBox(btn_data['label'])
            btn_checkbox.setChecked(True)  # By default, buttons are enabled
            self.layout.addWidget(btn_checkbox)
        


class GalleryDialog(QDialog):
    def __init__(self, categories, buttons_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Button Gallery')
        self.setStyleSheet(
            "QDialog { background-color: #262525; border: 2px solid #e5e5e5; border-radius: 10px; }"
            "QPushButton { background-color: #4285F4; border: 1px solid #4285F4; padding: 10px; margin: 8px; font-size: 14px; color: #ffffff; border-radius: 5px; }"
            "QPushButton:hover { background-color: #3c78d8; }"
            "QVBoxLayout { margin: 10px; padding: 10; }"
            "QCheckBox { font-size: 14px; }"
            "QListWidget {background-color: #404040; border: none; color: #c4c2c2; font-weight: bold; padding: 20px; text-decoration: none !important; }"  # list items
            "QListWidget::item { padding: 10px; margin: 2px; text-decoration: none !important; }"
            "QListWidget::item:selected { background-color: #ffffff; color: #404040; border-radius: 10px; text-decoration: none !important; }"
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Navigation bar layout
        nav_bar_layout = QHBoxLayout()
        nav_bar_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_label.setPixmap(QIcon(f'{scriptDir}\\icons\\logo.png').pixmap(55, 55)) 
        nav_bar_layout.addWidget(logo_label)

        nav_bar_layout.addStretch(1)

        gallery_button = QPushButton('Gallery')
        gallery_button.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; font-size: 18px; color: #ffffff; font-weight: bold; }"
        )
        nav_bar_layout.addWidget(gallery_button)

        nav_bar_layout.addStretch(1)

        settings_button = QPushButton()
        settings_button.setIcon(QIcon(f'{scriptDir}\\icons\\settings.png'))
        settings_button.setIconSize(QSize(24, 24))
        settings_button.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; }"
        )
        settings_button.clicked.connect(self.open_settings)
        nav_bar_layout.addWidget(settings_button)

        main_layout.addLayout(nav_bar_layout)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(content_layout)

        # Sidebar layout for categories
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.setSpacing(10)
        content_layout.addLayout(sidebar_layout)

        # Categories list
        self.categories_list = QListWidget()
        for category in categories:
            item = QListWidgetItem(category)
            self.categories_list.addItem(item)
        self.categories_list.currentRowChanged.connect(self.show_category_buttons)  # Connect signal to slot
        sidebar_layout.addWidget(self.categories_list)

        # Main content layout for buttons
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(20)
        content_layout.addLayout(self.content_layout)

        # Add buttons to the main content layout
        self.buttons_dict = buttons_dict

        self.buttons_area = QWidget()
        self.buttons_scroll_area = QScrollArea()
        self.buttons_scroll_area.setWidgetResizable(True)
        self.buttons_scroll_area.setWidget(self.buttons_area)
        self.content_layout.addWidget(self.buttons_scroll_area)

        self.show_category_buttons(0)  # Show buttons for the first category initially

    def show_category_buttons(self, index):
        category = self.categories_list.item(index).text()

        # Clear existing buttons
        existing_layout = self.buttons_area.layout()
        if existing_layout is not None:
            for i in reversed(range(existing_layout.count())):
                existing_layout.itemAt(i).widget().deleteLater()

        # Add buttons for the selected category
        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignTop)
        buttons_layout.setSpacing(10)

        buttons = self.buttons_dict.get(category, [])
        for btn_data in buttons:
            btn = QPushButton(btn_data['label'])
            btn.setStyleSheet(
                "background-color: #4285F4; border: none; padding: 10px; font-size: 16px; color: #ffffff; border-radius: 5px; margin: 5px;"
            )
            btn.clicked.connect(lambda _, data=btn_data: self.open_button_settings(data))
            buttons_layout.addWidget(btn)

        self.buttons_area.setLayout(buttons_layout)

    def open_button_settings(self, btn_data):
        dialog = ButtonSettingsDialog(btn_data, self)
        dialog.exec_()

    def open_settings(self):
        # Handle settings button click
        print("Settings button clicked")


class ButtonSettingsDialog(QDialog):
    def __init__(self, button_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Button Settings')
        self.layout = QFormLayout(self)

        self.label_input = QLineEdit(button_data['label'])
        self.command_input = QLineEdit(button_data['command'])
        self.icon_input = QLineEdit(button_data['icon'])

        self.layout.addRow('Label:', self.label_input)
        self.layout.addRow('Command:', self.command_input)
        self.layout.addRow('Icon Path:', self.icon_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        return {
            'label': self.label_input.text(),
            'command': self.command_input.text(),
            'icon': self.icon_input.text()
        }




class StreamFlow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('StreamFlow')
        self.resize(800, 600)  # Set initial window size

        # Load configuration
        try:
            with open('src/config.json', 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {'buttons': []}

        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        main_layout = QVBoxLayout(main_widget)

        # Top bar layout
        top_bar_layout = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QIcon(f'{scriptDir}\\icons\\logo.png').pixmap(72, 72))  # Replace with your logo path
        top_bar_layout.addWidget(logo)

        top_bar_layout.addStretch(1)  # Pushes the gallery button to the right

        self.gallery_button = QPushButton('Gallery')
        self.gallery_button.clicked.connect(self.open_gallery)
        top_bar_layout.addWidget(self.gallery_button)

        # Add the top bar to the main layout
        main_layout.addLayout(top_bar_layout)

        # Main content layout (sidebar + buttons area)
        content_layout = QHBoxLayout()

        # Categories sidebar
        self.categories_list = QListWidget()
        self.categories_list.addItems(['Applications', 'Audio', 'Video', 'Messages', 'More'])
        self.categories_list.currentItemChanged.connect(self.load_buttons)

        # Create a scroll area for the categories list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.categories_list)
        scroll_area.setFixedWidth(150)  # Set fixed width for the sidebar

        content_layout.addWidget(scroll_area)

        # Buttons area
        self.buttons_layout = QGridLayout()
        self.buttons_widget = QWidget()
        self.buttons_widget.setLayout(self.buttons_layout)
        buttons_scroll_area = QScrollArea()
        buttons_scroll_area.setWidgetResizable(True)
        buttons_scroll_area.setWidget(self.buttons_widget)

        content_layout.addWidget(buttons_scroll_area)

        # Add content layout to main layout
        main_layout.addLayout(content_layout)

        # Set default category and load buttons
        self.categories_list.setCurrentRow(0)
        self.load_buttons()

    @Slot()
    def load_buttons(self):
        # Clear existing buttons
        for i in reversed(range(self.buttons_layout.count())):
            self.buttons_layout.itemAt(i).widget().deleteLater()

        # Check if a category is selected
        current_item = self.categories_list.currentItem()
        if current_item is None:
            return

        category = current_item.text()
        buttons = [btn for btn in self.config['buttons'] if btn['category'] == category]

        # Add buttons to the grid layout
        max_buttons = 16  # Maximum number of buttons (4x4 grid)
        for idx, button_data in enumerate(buttons[:max_buttons]):
            button = QPushButton(button_data['label'])
            button.setStyleSheet("padding: 10px; font-size: 16px;")  # Customize button style
            if button_data['icon']:
                button.setIcon(QIcon(button_data['icon']))
                button.setIconSize(button.sizeHint())
            button.clicked.connect(lambda _, cmd=button_data['command']: handlers.execute_command(cmd))
            row = idx // 4
            col = idx % 4
            self.buttons_layout.addWidget(button, row, col)

        # Fill remaining slots with empty widgets to maintain the grid structure
        for idx in range(len(buttons), max_buttons):
            row = idx // 4
            col = idx % 4
            self.buttons_layout.addWidget(QWidget(), row, col)

    @Slot()
    def open_gallery(self):
        categories = ['Applications', 'Audio', 'Video', 'Messages', 'More']
        buttons_dict = {}
        for btn in self.config['buttons']:
            category = btn['category']
            if category not in buttons_dict:
                buttons_dict[category] = []
            buttons_dict[category].append(btn)

        gallery_dialog = GalleryDialog(categories, buttons_dict, self)
        gallery_dialog.resize(800, 600)  # Set the size of the gallery dialog
        gallery_dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StreamFlow()
    window.show()
    sys.exit(app.exec())
