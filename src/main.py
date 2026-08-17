from __future__ import annotations

import copy
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

import handlers
from config_store import get_user_config_path, load_config, save_config

SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLED_CONFIG = SCRIPT_DIR / "config.json"
ICON_DIR = SCRIPT_DIR / "icons"

APP_STYLE = """
QMainWindow, QDialog, QWidget { background-color: #202124; color: #f1f3f4; }
QPushButton { background-color: #3c4043; border: 1px solid #5f6368; border-radius: 8px; padding: 8px 12px; color: #f1f3f4; }
QPushButton:hover { background-color: #4b4f52; }
QPushButton#deckButton { background-color: #303134; font-size: 15px; font-weight: 600; min-width: 120px; min-height: 78px; }
QPushButton#primaryButton { background-color: #1a73e8; border-color: #1a73e8; }
QListWidget, QLineEdit, QComboBox { background-color: #303134; border: 1px solid #5f6368; border-radius: 6px; padding: 6px; color: #f1f3f4; }
QListWidget::item { padding: 8px; }
QListWidget::item:selected { background-color: #1a73e8; }
QScrollArea { border: none; }
QStatusBar { color: #bdc1c6; }
"""

ACTION_CHOICES = [
    ("Open website", "url"), ("Launch application", "app"), ("Run command", "cmd"),
    ("Run shell command", "shell"), ("Mute / unmute audio", "mute"),
    ("Volume up", "volume_up"), ("Volume down", "volume_down"),
]
PREFIX_ACTIONS = {"url", "app", "cmd", "shell"}


def resolve_icon(icon_value: str) -> Path | None:
    if not icon_value:
        return None
    candidate = Path(icon_value).expanduser()
    if candidate.is_file():
        return candidate
    bundled = ICON_DIR / icon_value
    return bundled if bundled.is_file() else None


def decode_command(command: str) -> tuple[str, str]:
    command = (command or "").strip()
    for prefix in PREFIX_ACTIONS:
        token = f"{prefix}:"
        if command.startswith(token):
            return prefix, command[len(token):]
    if command in {"mute", "volume_up", "volume_down"}:
        return command, ""
    if command == "chrome":
        return "url", "https://www.google.com"
    return "cmd", command


class ButtonEditorDialog(QDialog):
    def __init__(self, button_data=None, categories=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Button" if button_data else "Add Button")
        self.resize(520, 260)
        self.button_data = button_data or {}
        categories = categories or []
        form = QFormLayout(self)
        self.label_input = QLineEdit(self.button_data.get("label", ""))
        form.addRow("Label", self.label_input)
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(categories)
        self.category_input.setCurrentText(self.button_data.get("category", categories[0] if categories else "More"))
        form.addRow("Category", self.category_input)
        self.action_input = QComboBox()
        for label, action in ACTION_CHOICES:
            self.action_input.addItem(label, action)
        form.addRow("Action", self.action_input)
        value_row = QHBoxLayout()
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("URL, application path, or command")
        value_row.addWidget(self.value_input)
        self.browse_button = QPushButton("Browse…")
        self.browse_button.clicked.connect(self.browse_application)
        value_row.addWidget(self.browse_button)
        form.addRow("Value", value_row)
        icon_row = QHBoxLayout()
        self.icon_input = QLineEdit(self.button_data.get("icon", ""))
        icon_row.addWidget(self.icon_input)
        icon_button = QPushButton("Icon…")
        icon_button.clicked.connect(self.browse_icon)
        icon_row.addWidget(icon_button)
        form.addRow("Icon", icon_row)
        self.enabled_input = QCheckBox("Show this button")
        self.enabled_input.setChecked(self.button_data.get("enabled", True))
        form.addRow("Enabled", self.enabled_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        action, value = decode_command(self.button_data.get("command", ""))
        action_index = self.action_input.findData(action)
        if action_index >= 0:
            self.action_input.setCurrentIndex(action_index)
        self.value_input.setText(value)
        self.action_input.currentIndexChanged.connect(self.update_action_state)
        self.update_action_state()

    def update_action_state(self):
        action = self.action_input.currentData()
        self.value_input.setEnabled(action in PREFIX_ACTIONS)
        self.browse_button.setVisible(action == "app")

    def browse_application(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose application")
        if path:
            self.value_input.setText(path)

    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose icon", filter="Images (*.png *.jpg *.jpeg *.svg *.ico);;All files (*)")
        if path:
            self.icon_input.setText(path)

    def validate_and_accept(self):
        if not self.label_input.text().strip():
            QMessageBox.warning(self, "Missing label", "Give the button a label.")
            return
        if not self.category_input.currentText().strip():
            QMessageBox.warning(self, "Missing category", "Choose or enter a category.")
            return
        action = self.action_input.currentData()
        if action in PREFIX_ACTIONS and not self.value_input.text().strip():
            QMessageBox.warning(self, "Missing value", "This action needs a value.")
            return
        self.accept()

    def get_button_data(self):
        action = self.action_input.currentData()
        value = self.value_input.text().strip()
        return {
            "label": self.label_input.text().strip(),
            "category": self.category_input.currentText().strip(),
            "command": f"{action}:{value}" if action in PREFIX_ACTIONS else action,
            "icon": self.icon_input.text().strip(),
            "enabled": self.enabled_input.isChecked(),
        }


class ManageButtonsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Deck")
        self.resize(760, 520)
        self.config = copy.deepcopy(config)
        layout = QVBoxLayout(self)
        intro = QLabel("Add, edit, remove, or reorder StreamFlow buttons. Changes are saved locally.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _: self.edit_selected())
        layout.addWidget(self.list_widget)
        actions = QHBoxLayout()
        for label, callback in (("Add", self.add_button), ("Edit", self.edit_selected), ("Delete", self.delete_selected)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch(1)
        up_button = QPushButton("Move Up")
        up_button.clicked.connect(lambda: self.move_selected(-1))
        actions.addWidget(up_button)
        down_button = QPushButton("Move Down")
        down_button.clicked.connect(lambda: self.move_selected(1))
        actions.addWidget(down_button)
        layout.addLayout(actions)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.reload()

    def reload(self, selected_index=None):
        self.list_widget.clear()
        for index, button in enumerate(self.config["buttons"]):
            status = "" if button.get("enabled", True) else " [hidden]"
            item = QListWidgetItem(f"{button['category']}  •  {button['label']}{status}\n{button['command']}")
            item.setData(Qt.UserRole, index)
            self.list_widget.addItem(item)
        if selected_index is not None and self.list_widget.count():
            self.list_widget.setCurrentRow(max(0, min(selected_index, self.list_widget.count() - 1)))

    def selected_index(self):
        item = self.list_widget.currentItem()
        return None if item is None else item.data(Qt.UserRole)

    def add_button(self):
        editor = ButtonEditorDialog(categories=self.config["categories"], parent=self)
        if editor.exec() == QDialog.Accepted:
            button = editor.get_button_data()
            self.config["buttons"].append(button)
            if button["category"] not in self.config["categories"]:
                self.config["categories"].append(button["category"])
            self.reload(len(self.config["buttons"]) - 1)

    def edit_selected(self):
        index = self.selected_index()
        if index is None:
            return
        editor = ButtonEditorDialog(self.config["buttons"][index], self.config["categories"], self)
        if editor.exec() == QDialog.Accepted:
            button = editor.get_button_data()
            self.config["buttons"][index] = button
            if button["category"] not in self.config["categories"]:
                self.config["categories"].append(button["category"])
            self.reload(index)

    def delete_selected(self):
        index = self.selected_index()
        if index is None:
            return
        button = self.config["buttons"][index]
        answer = QMessageBox.question(self, "Delete button", f"Delete '{button['label']}'?", QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            del self.config["buttons"][index]
            self.reload(index)

    def move_selected(self, offset):
        index = self.selected_index()
        if index is None:
            return
        new_index = index + offset
        if new_index < 0 or new_index >= len(self.config["buttons"]):
            return
        buttons = self.config["buttons"]
        buttons[index], buttons[new_index] = buttons[new_index], buttons[index]
        self.reload(new_index)


class StreamFlow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamFlow")
        self.resize(980, 680)
        self.setStyleSheet(APP_STYLE)
        self.config_path = get_user_config_path()
        self.config = load_config(self.config_path, BUNDLED_CONFIG)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(18, 18, 18, 12)
        main_layout.setSpacing(14)
        header = QHBoxLayout()
        logo = QLabel()
        logo_path = ICON_DIR / "logo.png"
        if logo_path.is_file():
            logo.setPixmap(QIcon(str(logo_path)).pixmap(64, 64))
        header.addWidget(logo)
        title_box = QVBoxLayout()
        title = QLabel("StreamFlow")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        subtitle = QLabel("Your local, customizable virtual stream deck")
        subtitle.setStyleSheet("color: #bdc1c6;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        add_button = QPushButton("+ Add Button")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_button)
        header.addWidget(add_button)
        manage_button = QPushButton("Manage Deck")
        manage_button.clicked.connect(self.open_manager)
        header.addWidget(manage_button)
        main_layout.addLayout(header)
        content = QHBoxLayout()
        self.categories_list = QListWidget()
        self.categories_list.setFixedWidth(180)
        self.categories_list.currentItemChanged.connect(self.load_buttons)
        content.addWidget(self.categories_list)
        self.buttons_layout = QGridLayout()
        self.buttons_layout.setSpacing(12)
        self.buttons_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.buttons_widget = QWidget()
        self.buttons_widget.setLayout(self.buttons_layout)
        buttons_scroll = QScrollArea()
        buttons_scroll.setWidgetResizable(True)
        buttons_scroll.setWidget(self.buttons_widget)
        content.addWidget(buttons_scroll, 1)
        main_layout.addLayout(content, 1)
        self.refresh_categories()
        self.statusBar().showMessage(f"Config: {self.config_path}")

    def refresh_categories(self, preferred=None):
        current = preferred
        if current is None and self.categories_list.currentItem():
            current = self.categories_list.currentItem().text()
        self.categories_list.blockSignals(True)
        self.categories_list.clear()
        self.categories_list.addItems(self.config["categories"])
        self.categories_list.blockSignals(False)
        if self.categories_list.count() == 0:
            return
        target_row = 0
        if current:
            matches = self.categories_list.findItems(current, Qt.MatchExactly)
            if matches:
                target_row = self.categories_list.row(matches[0])
        self.categories_list.setCurrentRow(target_row)
        self.load_buttons()

    def _clear_grid(self):
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @Slot()
    def load_buttons(self, *_):
        self._clear_grid()
        item = self.categories_list.currentItem()
        if item is None:
            return
        category = item.text()
        visible = [(index, button) for index, button in enumerate(self.config["buttons"]) if button["category"] == category and button.get("enabled", True)]
        if not visible:
            empty = QLabel("No buttons here yet. Use '+ Add Button' to create one.")
            empty.setStyleSheet("color: #9aa0a6; padding: 18px;")
            self.buttons_layout.addWidget(empty, 0, 0)
            return
        for position, (index, button_data) in enumerate(visible):
            button = QPushButton(button_data["label"])
            button.setObjectName("deckButton")
            button.setToolTip(button_data["command"] or "No action configured")
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button, idx=index: self.open_button_menu(btn, pos, idx))
            icon_path = resolve_icon(button_data.get("icon", ""))
            if icon_path:
                button.setIcon(QIcon(str(icon_path)))
                button.setIconSize(QSize(36, 36))
            button.clicked.connect(lambda checked=False, cmd=button_data["command"]: self.run_action(cmd))
            row, col = divmod(position, 4)
            self.buttons_layout.addWidget(button, row, col)

    def run_action(self, command):
        result = handlers.execute_command(command)
        self.statusBar().showMessage(result.message, 6000)
        if not result.success:
            QMessageBox.warning(self, "Action failed", result.message)

    def open_button_menu(self, button_widget, position, index):
        menu = QMenu(self)
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_button(index))
        menu.addAction(edit_action)
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_button(index))
        menu.addAction(delete_action)
        menu.exec(button_widget.mapToGlobal(position))

    def add_button(self):
        current = self.categories_list.currentItem()
        seed = {"category": current.text()} if current else None
        editor = ButtonEditorDialog(seed, self.config["categories"], self)
        if editor.exec() != QDialog.Accepted:
            return
        button = editor.get_button_data()
        self.config["buttons"].append(button)
        if button["category"] not in self.config["categories"]:
            self.config["categories"].append(button["category"])
        self.persist_and_refresh(button["category"])

    def edit_button(self, index):
        if index < 0 or index >= len(self.config["buttons"]):
            return
        editor = ButtonEditorDialog(self.config["buttons"][index], self.config["categories"], self)
        if editor.exec() != QDialog.Accepted:
            return
        button = editor.get_button_data()
        self.config["buttons"][index] = button
        if button["category"] not in self.config["categories"]:
            self.config["categories"].append(button["category"])
        self.persist_and_refresh(button["category"])

    def delete_button(self, index):
        if index < 0 or index >= len(self.config["buttons"]):
            return
        button = self.config["buttons"][index]
        answer = QMessageBox.question(self, "Delete button", f"Delete '{button['label']}'?", QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            category = button["category"]
            del self.config["buttons"][index]
            self.persist_and_refresh(category)

    def open_manager(self):
        dialog = ManageButtonsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.config
            self.persist_and_refresh()

    def persist_and_refresh(self, preferred_category=None):
        try:
            save_config(self.config, self.config_path)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save config", str(exc))
            return
        self.refresh_categories(preferred_category)
        self.statusBar().showMessage(f"Saved to {self.config_path}", 5000)

    def closeEvent(self, event):
        try:
            save_config(self.config, self.config_path)
        except OSError:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StreamFlow")
    window = StreamFlow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
