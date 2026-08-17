from __future__ import annotations

import copy
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

try:
    from . import handlers, obs_client
    from .config_store import (
        create_profile,
        delete_profile,
        export_profile,
        get_active_deck,
        get_user_config_path,
        import_profile,
        load_config,
        rename_profile,
        save_config,
    )
except ImportError:
    import handlers
    import obs_client
    from config_store import (
        create_profile,
        delete_profile,
        export_profile,
        get_active_deck,
        get_user_config_path,
        import_profile,
        load_config,
        rename_profile,
        save_config,
    )


SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLED_CONFIG = SCRIPT_DIR / "config.json"
ICON_DIR = SCRIPT_DIR / "icons"

APP_STYLE = """
* {
    font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background: #0b1020;
    color: #f8fafc;
}
QWidget {
    color: #f8fafc;
}
QFrame#topBar, QFrame#sidebar, QFrame#contentPanel, QFrame#dialogCard {
    background: #111827;
    border: 1px solid #263247;
    border-radius: 16px;
}
QFrame#sidebar {
    background: #0f172a;
}
QLabel#brandTitle {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#brandSubtitle, QLabel#mutedText, QLabel#fieldHint {
    color: #94a3b8;
}
QLabel#eyebrow {
    color: #8b5cf6;
    font-size: 11px;
    font-weight: 700;
}
QLabel#pageTitle {
    font-size: 25px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#emptyIcon {
    font-size: 34px;
    color: #64748b;
}
QLabel#emptyTitle {
    font-size: 17px;
    font-weight: 650;
    color: #e2e8f0;
}
QPushButton {
    background: #172033;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 9px 14px;
    color: #e5e7eb;
    font-weight: 600;
}
QPushButton:hover {
    background: #1d2940;
    border-color: #475569;
}
QPushButton:pressed {
    background: #111827;
}
QPushButton#primaryButton {
    background: #7c3aed;
    border-color: #7c3aed;
    color: #ffffff;
}
QPushButton#primaryButton:hover {
    background: #8b5cf6;
    border-color: #8b5cf6;
}
QPushButton#ghostButton {
    background: transparent;
    border-color: transparent;
    color: #cbd5e1;
    text-align: left;
}
QPushButton#ghostButton:hover {
    background: #172033;
    border-color: #263247;
}
QPushButton#dangerButton {
    color: #fca5a5;
    border-color: #7f1d1d;
    background: #2a1218;
}
QPushButton#deckButton {
    background: #151d2e;
    border: 1px solid #2c3950;
    border-radius: 14px;
    padding: 16px;
    min-width: 150px;
    min-height: 94px;
    color: #f8fafc;
    font-size: 14px;
    font-weight: 650;
    text-align: left;
}
QPushButton#deckButton:hover {
    background: #1b2740;
    border-color: #7c3aed;
}
QPushButton#deckButton:pressed {
    background: #121a29;
}
QListWidget {
    background: transparent;
    border: none;
    outline: none;
    color: #cbd5e1;
}
QListWidget::item {
    border-radius: 9px;
    padding: 10px 12px;
    margin: 2px 0;
}
QListWidget::item:hover {
    background: #172033;
}
QListWidget::item:selected {
    background: #252044;
    color: #ddd6fe;
    border: 1px solid #4c3b78;
}
QLineEdit, QComboBox, QSpinBox {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 9px;
    padding: 8px 10px;
    min-height: 20px;
    color: #f8fafc;
    selection-background-color: #7c3aed;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #8b5cf6;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background: #111827;
    border: 1px solid #334155;
    selection-background-color: #312e81;
    color: #f8fafc;
}
QCheckBox {
    spacing: 8px;
    color: #cbd5e1;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 28px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenu {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 8px 20px;
    border-radius: 6px;
}
QMenu::item:selected {
    background: #252044;
}
QDialogButtonBox {
    background: transparent;
}
QStatusBar {
    background: #0b1020;
    color: #64748b;
    border-top: 1px solid #1e293b;
}
QToolTip {
    background: #111827;
    color: #f8fafc;
    border: 1px solid #334155;
    padding: 6px;
}
"""

ACTION_CHOICES = [
    ("Open website", "url"),
    ("Launch application", "app"),
    ("Run command", "cmd"),
    ("Run shell command", "shell"),
    ("Mute / unmute system audio", "mute"),
    ("System volume up", "volume_up"),
    ("System volume down", "volume_down"),
    ("OBS: Switch scene", "obs_scene"),
    ("OBS: Toggle input mute", "obs_mute"),
    ("OBS: Start / stop recording", "obs_record_toggle"),
    ("OBS: Start / stop streaming", "obs_stream_toggle"),
]
VALUE_ACTIONS = {"url", "app", "cmd", "shell", "obs_scene", "obs_mute"}
ACTION_PLACEHOLDERS = {
    "url": "https://example.com",
    "app": "Application or executable path",
    "cmd": "python --version",
    "shell": "echo hello > output.txt",
    "obs_scene": "Exact OBS scene name, e.g. Gaming",
    "obs_mute": "Exact OBS input name, e.g. Mic/Aux",
}


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
    for prefix in VALUE_ACTIONS:
        token = f"{prefix}:"
        if command.startswith(token):
            return prefix, command[len(token):]
    if command in {
        "mute",
        "volume_up",
        "volume_down",
        "obs_record_toggle",
        "obs_stream_toggle",
    }:
        return command, ""
    if command == "chrome":
        return "url", "https://www.google.com"
    return "cmd", command


def make_dialog_header(title: str, subtitle: str) -> tuple[QVBoxLayout, QLabel]:
    box = QVBoxLayout()
    box.setSpacing(4)
    heading = QLabel(title)
    heading.setObjectName("pageTitle")
    description = QLabel(subtitle)
    description.setObjectName("mutedText")
    description.setWordWrap(True)
    box.addWidget(heading)
    box.addWidget(description)
    return box, heading


def action_summary(command: str) -> str:
    action, value = decode_command(command)
    labels = {
        "url": "Website",
        "app": "Application",
        "cmd": "Command",
        "shell": "Shell command",
        "mute": "System mute",
        "volume_up": "Volume up",
        "volume_down": "Volume down",
        "obs_scene": "OBS scene",
        "obs_mute": "OBS input mute",
        "obs_record_toggle": "OBS recording",
        "obs_stream_toggle": "OBS streaming",
    }
    label = labels.get(action, "Action")
    return f"{label} · {value}" if value else label


class ButtonEditorDialog(QDialog):
    def __init__(self, button_data=None, categories=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Button" if button_data else "Add Button")
        self.resize(600, 390)
        self.setMinimumWidth(560)
        self.button_data = button_data or {}
        categories = categories or []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 20)
        outer.setSpacing(20)
        header, _ = make_dialog_header(
            "Edit action" if button_data else "Create action",
            "Choose what this deck button should do and where it belongs.",
        )
        outer.addLayout(header)

        card = QFrame()
        card.setObjectName("dialogCard")
        form = QFormLayout(card)
        form.setContentsMargins(20, 20, 20, 20)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(14)

        self.label_input = QLineEdit(self.button_data.get("label", ""))
        self.label_input.setPlaceholderText("e.g. Start Recording")
        form.addRow("Label", self.label_input)

        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(categories)
        self.category_input.setCurrentText(
            self.button_data.get("category", categories[0] if categories else "More")
        )
        form.addRow("Category", self.category_input)

        self.action_input = QComboBox()
        for label, action in ACTION_CHOICES:
            self.action_input.addItem(label, action)
        form.addRow("Action", self.action_input)

        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        self.value_input = QLineEdit()
        value_row.addWidget(self.value_input, 1)
        self.browse_button = QPushButton("Browse…")
        self.browse_button.clicked.connect(self.browse_application)
        value_row.addWidget(self.browse_button)
        form.addRow("Value", value_row)

        icon_row = QHBoxLayout()
        icon_row.setSpacing(8)
        self.icon_input = QLineEdit(self.button_data.get("icon", ""))
        self.icon_input.setPlaceholderText("Optional image path")
        icon_row.addWidget(self.icon_input, 1)
        icon_button = QPushButton("Choose…")
        icon_button.clicked.connect(self.browse_icon)
        icon_row.addWidget(icon_button)
        form.addRow("Icon", icon_row)

        self.enabled_input = QCheckBox("Show this button on the deck")
        self.enabled_input.setChecked(self.button_data.get("enabled", True))
        form.addRow("Visible", self.enabled_input)
        outer.addWidget(card)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = buttons.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setObjectName("primaryButton")
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        action, value = decode_command(self.button_data.get("command", ""))
        action_index = self.action_input.findData(action)
        if action_index >= 0:
            self.action_input.setCurrentIndex(action_index)
        self.value_input.setText(value)
        self.action_input.currentIndexChanged.connect(self.update_action_state)
        self.update_action_state()

    def update_action_state(self):
        action = self.action_input.currentData()
        needs_value = action in VALUE_ACTIONS
        self.value_input.setEnabled(needs_value)
        self.value_input.setPlaceholderText(ACTION_PLACEHOLDERS.get(action, "No value needed"))
        self.browse_button.setVisible(action == "app")

    def browse_application(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose application")
        if path:
            self.value_input.setText(path)

    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose icon",
            filter="Images (*.png *.jpg *.jpeg *.svg *.ico);;All files (*)",
        )
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
        if action in VALUE_ACTIONS and not self.value_input.text().strip():
            QMessageBox.warning(self, "Missing value", "This action needs a value.")
            return
        self.accept()

    def get_button_data(self):
        action = self.action_input.currentData()
        value = self.value_input.text().strip()
        return {
            "label": self.label_input.text().strip(),
            "category": self.category_input.currentText().strip(),
            "command": f"{action}:{value}" if action in VALUE_ACTIONS else action,
            "icon": self.icon_input.text().strip(),
            "enabled": self.enabled_input.isChecked(),
        }


class ManageButtonsDialog(QDialog):
    def __init__(self, deck, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Deck")
        self.resize(820, 580)
        self.deck = copy.deepcopy(deck)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)
        header, _ = make_dialog_header(
            "Manage deck",
            "Add, edit, hide, remove, and reorder actions in this profile.",
        )
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _: self.edit_selected())
        layout.addWidget(self.list_widget, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        add_button = QPushButton("＋ Add")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_button)
        actions.addWidget(add_button)
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_selected)
        actions.addWidget(edit_button)
        delete_button = QPushButton("Delete")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_selected)
        actions.addWidget(delete_button)
        actions.addStretch(1)
        up_button = QPushButton("Move up")
        up_button.clicked.connect(lambda: self.move_selected(-1))
        actions.addWidget(up_button)
        down_button = QPushButton("Move down")
        down_button.clicked.connect(lambda: self.move_selected(1))
        actions.addWidget(down_button)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = buttons.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setObjectName("primaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.reload()

    def reload(self, selected_index=None):
        self.list_widget.clear()
        for index, button in enumerate(self.deck["buttons"]):
            status = "" if button.get("enabled", True) else "  ·  Hidden"
            item = QListWidgetItem(
                f"{button['label']}\n{button['category']}  ·  {action_summary(button['command'])}{status}"
            )
            item.setData(Qt.UserRole, index)
            item.setSizeHint(QSize(100, 54))
            self.list_widget.addItem(item)
        if selected_index is not None and self.list_widget.count():
            self.list_widget.setCurrentRow(
                max(0, min(selected_index, self.list_widget.count() - 1))
            )

    def selected_index(self):
        item = self.list_widget.currentItem()
        return None if item is None else item.data(Qt.UserRole)

    def add_button(self):
        editor = ButtonEditorDialog(categories=self.deck["categories"], parent=self)
        if editor.exec() == QDialog.Accepted:
            button = editor.get_button_data()
            self.deck["buttons"].append(button)
            if button["category"] not in self.deck["categories"]:
                self.deck["categories"].append(button["category"])
            self.reload(len(self.deck["buttons"]) - 1)

    def edit_selected(self):
        index = self.selected_index()
        if index is None:
            return
        editor = ButtonEditorDialog(
            self.deck["buttons"][index], self.deck["categories"], self
        )
        if editor.exec() == QDialog.Accepted:
            button = editor.get_button_data()
            self.deck["buttons"][index] = button
            if button["category"] not in self.deck["categories"]:
                self.deck["categories"].append(button["category"])
            self.reload(index)

    def delete_selected(self):
        index = self.selected_index()
        if index is None:
            return
        button = self.deck["buttons"][index]
        answer = QMessageBox.question(
            self,
            "Delete button",
            f"Delete '{button['label']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            del self.deck["buttons"][index]
            self.reload(index)

    def move_selected(self, offset):
        index = self.selected_index()
        if index is None:
            return
        new_index = index + offset
        if new_index < 0 or new_index >= len(self.deck["buttons"]):
            return
        buttons = self.deck["buttons"]
        buttons[index], buttons[new_index] = buttons[new_index], buttons[index]
        self.reload(new_index)


class ProfileManagerDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profiles")
        self.resize(700, 520)
        self.config = copy.deepcopy(config)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)
        header, _ = make_dialog_header(
            "Profiles",
            "Keep separate decks for streaming, work, gaming, or any other workflow.",
        )
        layout.addLayout(header)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        new_button = QPushButton("＋ New")
        new_button.setObjectName("primaryButton")
        new_button.clicked.connect(self.add_profile)
        actions.addWidget(new_button)
        for label, callback in (
            ("Duplicate", self.duplicate_profile),
            ("Rename", self.rename_selected),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        delete_button = QPushButton("Delete")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_selected)
        actions.addWidget(delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        io_actions = QHBoxLayout()
        io_actions.setSpacing(8)
        import_button = QPushButton("Import…")
        import_button.clicked.connect(self.import_profile_file)
        io_actions.addWidget(import_button)
        export_button = QPushButton("Export…")
        export_button.clicked.connect(self.export_selected)
        io_actions.addWidget(export_button)
        io_actions.addStretch(1)
        layout.addLayout(io_actions)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = buttons.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setObjectName("primaryButton")
        buttons.accepted.connect(self.accept_with_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.reload(self.config["active_profile"])

    def reload(self, selected_name=None):
        self.list_widget.clear()
        for name in self.config["profiles"]:
            marker = "  ·  Active" if name == self.config["active_profile"] else ""
            item = QListWidgetItem(f"{name}{marker}")
            item.setData(Qt.UserRole, name)
            item.setSizeHint(QSize(100, 44))
            self.list_widget.addItem(item)
            if name == selected_name:
                self.list_widget.setCurrentItem(item)
        if self.list_widget.currentItem() is None and self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def selected_name(self):
        item = self.list_widget.currentItem()
        return None if item is None else item.data(Qt.UserRole)

    def add_profile(self):
        name, ok = QInputDialog.getText(self, "New profile", "Profile name:")
        if ok and name.strip():
            try:
                created = create_profile(self.config, name.strip())
            except ValueError as exc:
                QMessageBox.warning(self, "Could not create profile", str(exc))
                return
            self.reload(created)

    def duplicate_profile(self):
        source = self.selected_name()
        if not source:
            return
        try:
            created = create_profile(self.config, f"{source} Copy", source_name=source)
        except ValueError as exc:
            QMessageBox.warning(self, "Could not duplicate profile", str(exc))
            return
        self.reload(created)

    def rename_selected(self):
        old_name = self.selected_name()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(
            self, "Rename profile", "Profile name:", text=old_name
        )
        if not ok:
            return
        try:
            renamed = rename_profile(self.config, old_name, new_name)
        except ValueError as exc:
            QMessageBox.warning(self, "Could not rename profile", str(exc))
            return
        self.reload(renamed)

    def delete_selected(self):
        name = self.selected_name()
        if not name:
            return
        answer = QMessageBox.question(
            self,
            "Delete profile",
            f"Delete profile '{name}' and all of its buttons?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            delete_profile(self.config, name)
        except ValueError as exc:
            QMessageBox.warning(self, "Could not delete profile", str(exc))
            return
        self.reload(self.config["active_profile"])

    def import_profile_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import StreamFlow profile", filter="JSON (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            name = import_profile(self.config, Path(path))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return
        self.reload(name)

    def export_selected(self):
        name = self.selected_name()
        if not name:
            return
        default_name = f"{name.lower().replace(' ', '-')}.streamflow.json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export StreamFlow profile",
            default_name,
            "JSON (*.json);;All files (*)",
        )
        if not path:
            return
        try:
            export_profile(self.config, name, Path(path))
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
            return
        QMessageBox.information(self, "Profile exported", f"Saved '{name}' to:\n{path}")

    def accept_with_selection(self):
        selected = self.selected_name()
        if selected:
            self.config["active_profile"] = selected
        self.accept()


class OBSSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OBS Settings")
        self.resize(590, 390)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 20)
        outer.setSpacing(18)
        header, _ = make_dialog_header(
            "OBS connection",
            "Connect StreamFlow directly to OBS WebSocket on this computer or your local network.",
        )
        outer.addLayout(header)

        card = QFrame()
        card.setObjectName("dialogCard")
        form = QFormLayout(card)
        form.setContentsMargins(20, 20, 20, 20)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(14)

        self.host_input = QLineEdit(str(settings.get("host", "127.0.0.1")))
        self.host_input.setPlaceholderText("127.0.0.1")
        form.addRow("Host", self.host_input)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(int(settings.get("port", 4455)))
        form.addRow("Port", self.port_input)

        self.password_input = QLineEdit(str(settings.get("password", "")))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("OBS WebSocket password")
        form.addRow("Password", self.password_input)

        note = QLabel(
            "OBS Studio 28+ includes obs-websocket. You can find its server settings under Tools → WebSocket Server Settings."
        )
        note.setObjectName("fieldHint")
        note.setWordWrap(True)
        form.addRow(note)

        test_button = QPushButton("Test connection")
        test_button.clicked.connect(self.test_obs_connection)
        form.addRow(test_button)
        outer.addWidget(card)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = buttons.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setObjectName("primaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def settings(self):
        return {
            "host": self.host_input.text().strip() or "127.0.0.1",
            "port": self.port_input.value(),
            "password": self.password_input.text(),
        }

    def test_obs_connection(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            message = obs_client.test_connection(self.settings())
        except Exception as exc:
            QMessageBox.warning(self, "OBS connection failed", str(exc))
        else:
            QMessageBox.information(self, "OBS connected", message)
        finally:
            QApplication.restoreOverrideCursor()


class StreamFlow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamFlow")
        self.resize(1180, 760)
        self.setMinimumSize(920, 620)
        self.setStyleSheet(APP_STYLE)

        self.config_path = get_user_config_path()
        self.config = load_config(self.config_path, BUNDLED_CONFIG)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 8)
        root_layout.setSpacing(14)

        root_layout.addWidget(self._build_top_bar())

        body = QHBoxLayout()
        body.setSpacing(14)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_content_panel(), 1)
        root_layout.addLayout(body, 1)

        self.refresh_all()
        self.statusBar().showMessage(f"Config · {self.config_path}")

    def _build_top_bar(self):
        top = QFrame()
        top.setObjectName("topBar")
        layout = QHBoxLayout(top)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        logo = QLabel()
        logo.setFixedSize(48, 48)
        logo_path = ICON_DIR / "logo.png"
        if logo_path.is_file():
            logo.setPixmap(QIcon(str(logo_path)).pixmap(48, 48))
        layout.addWidget(logo)

        brand = QVBoxLayout()
        brand.setSpacing(1)
        title = QLabel("StreamFlow")
        title.setObjectName("brandTitle")
        subtitle = QLabel("Local control deck for your desktop")
        subtitle.setObjectName("brandSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        layout.addLayout(brand)
        layout.addStretch(1)

        profile_hint = QLabel("PROFILE")
        profile_hint.setObjectName("eyebrow")
        layout.addWidget(profile_hint)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(170)
        self.profile_combo.currentTextChanged.connect(self.switch_profile)
        layout.addWidget(self.profile_combo)

        add_button = QPushButton("＋ Add action")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_button)
        layout.addWidget(add_button)

        manage_button = QPushButton("Manage deck")
        manage_button.clicked.connect(self.open_manager)
        layout.addWidget(manage_button)
        return top

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 14)
        layout.setSpacing(8)

        label = QLabel("CATEGORIES")
        label.setObjectName("eyebrow")
        layout.addWidget(label)

        self.categories_list = QListWidget()
        self.categories_list.currentItemChanged.connect(self.load_buttons)
        layout.addWidget(self.categories_list, 1)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #263247; background: #263247; max-height: 1px;")
        layout.addWidget(divider)

        profiles_button = QPushButton("Profiles")
        profiles_button.setObjectName("ghostButton")
        profiles_button.clicked.connect(self.open_profiles)
        layout.addWidget(profiles_button)

        obs_button = QPushButton("OBS connection")
        obs_button.setObjectName("ghostButton")
        obs_button.clicked.connect(self.open_obs_settings)
        layout.addWidget(obs_button)
        return sidebar

    def _build_content_panel(self):
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        heading_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        eyebrow = QLabel("ACTIVE DECK")
        eyebrow.setObjectName("eyebrow")
        self.category_title = QLabel("Applications")
        self.category_title.setObjectName("pageTitle")
        self.category_meta = QLabel("")
        self.category_meta.setObjectName("mutedText")
        title_box.addWidget(eyebrow)
        title_box.addWidget(self.category_title)
        title_box.addWidget(self.category_meta)
        heading_row.addLayout(title_box)
        heading_row.addStretch(1)
        layout.addLayout(heading_row)

        self.buttons_layout = QGridLayout()
        self.buttons_layout.setHorizontalSpacing(12)
        self.buttons_layout.setVerticalSpacing(12)
        self.buttons_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.buttons_widget = QWidget()
        self.buttons_widget.setStyleSheet("background: transparent;")
        self.buttons_widget.setLayout(self.buttons_layout)
        self.buttons_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        buttons_scroll = QScrollArea()
        buttons_scroll.setWidgetResizable(True)
        buttons_scroll.setWidget(self.buttons_widget)
        layout.addWidget(buttons_scroll, 1)
        return panel

    @property
    def deck(self):
        return get_active_deck(self.config)

    def refresh_profile_combo(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(list(self.config["profiles"].keys()))
        self.profile_combo.setCurrentText(self.config["active_profile"])
        self.profile_combo.blockSignals(False)

    def refresh_categories(self, preferred=None):
        current = preferred
        if current is None and self.categories_list.currentItem():
            current = self.categories_list.currentItem().text()

        self.categories_list.blockSignals(True)
        self.categories_list.clear()
        self.categories_list.addItems(self.deck["categories"])
        self.categories_list.blockSignals(False)

        if self.categories_list.count() == 0:
            self._clear_grid()
            self.category_title.setText("No categories")
            self.category_meta.setText("Create an action to get started.")
            return

        target_row = 0
        if current:
            matches = self.categories_list.findItems(current, Qt.MatchExactly)
            if matches:
                target_row = self.categories_list.row(matches[0])
        self.categories_list.setCurrentRow(target_row)
        self.load_buttons()

    def refresh_all(self, preferred_category=None):
        self.refresh_profile_combo()
        self.refresh_categories(preferred_category)

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
        visible = [
            (index, button)
            for index, button in enumerate(self.deck["buttons"])
            if button["category"] == category and button.get("enabled", True)
        ]
        hidden_count = sum(
            1
            for button in self.deck["buttons"]
            if button["category"] == category and not button.get("enabled", True)
        )
        self.category_title.setText(category)
        count_text = f"{len(visible)} action{'s' if len(visible) != 1 else ''}"
        if hidden_count:
            count_text += f" · {hidden_count} hidden"
        self.category_meta.setText(f"{self.config['active_profile']} profile · {count_text}")

        if not visible:
            empty_box = QFrame()
            empty_box.setObjectName("dialogCard")
            empty_layout = QVBoxLayout(empty_box)
            empty_layout.setContentsMargins(28, 32, 28, 32)
            empty_layout.setAlignment(Qt.AlignCenter)
            empty_layout.setSpacing(6)
            icon = QLabel("＋")
            icon.setObjectName("emptyIcon")
            icon.setAlignment(Qt.AlignCenter)
            title = QLabel("Nothing here yet")
            title.setObjectName("emptyTitle")
            title.setAlignment(Qt.AlignCenter)
            hint = QLabel("Add an action to this category and it will appear here.")
            hint.setObjectName("mutedText")
            hint.setAlignment(Qt.AlignCenter)
            hint.setWordWrap(True)
            add = QPushButton("Add action")
            add.setObjectName("primaryButton")
            add.clicked.connect(self.add_button)
            empty_layout.addWidget(icon)
            empty_layout.addWidget(title)
            empty_layout.addWidget(hint)
            empty_layout.addSpacing(8)
            empty_layout.addWidget(add, 0, Qt.AlignCenter)
            self.buttons_layout.addWidget(empty_box, 0, 0, 1, 3)
            return

        for position, (index, button_data) in enumerate(visible):
            button = QPushButton(button_data["label"])
            button.setObjectName("deckButton")
            button.setToolTip(action_summary(button_data["command"]))
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda pos, btn=button, idx=index: self.open_button_menu(btn, pos, idx)
            )

            icon_path = resolve_icon(button_data.get("icon", ""))
            if icon_path:
                button.setIcon(QIcon(str(icon_path)))
                button.setIconSize(QSize(34, 34))

            button.clicked.connect(
                lambda checked=False, cmd=button_data["command"]: self.run_action(cmd)
            )
            row, col = divmod(position, 4)
            self.buttons_layout.addWidget(button, row, col)

    def run_action(self, command):
        if command.startswith("obs_"):
            result = obs_client.execute_obs_action(command, self.config["obs"])
        else:
            result = handlers.execute_command(command)

        self.statusBar().showMessage(result.message, 6000)
        if not result.success:
            QMessageBox.warning(self, "Action failed", result.message)

    def open_button_menu(self, button_widget, position, index):
        menu = QMenu(self)

        edit_action = QAction("Edit action", self)
        edit_action.triggered.connect(lambda: self.edit_button(index))
        menu.addAction(edit_action)

        delete_action = QAction("Delete action", self)
        delete_action.triggered.connect(lambda: self.delete_button(index))
        menu.addAction(delete_action)

        menu.exec(button_widget.mapToGlobal(position))

    def switch_profile(self, name):
        if not name or name not in self.config["profiles"]:
            return
        if name == self.config["active_profile"]:
            return
        self.config["active_profile"] = name
        if self.save_config_safely():
            self.refresh_categories()
            self.statusBar().showMessage(f"Switched to profile '{name}'.", 4000)

    def add_button(self):
        current = self.categories_list.currentItem()
        seed = {"category": current.text()} if current else None
        editor = ButtonEditorDialog(seed, self.deck["categories"], self)
        if editor.exec() != QDialog.Accepted:
            return

        button = editor.get_button_data()
        self.deck["buttons"].append(button)
        if button["category"] not in self.deck["categories"]:
            self.deck["categories"].append(button["category"])
        self.persist_and_refresh(button["category"])

    def edit_button(self, index):
        if index < 0 or index >= len(self.deck["buttons"]):
            return
        editor = ButtonEditorDialog(
            self.deck["buttons"][index], self.deck["categories"], self
        )
        if editor.exec() != QDialog.Accepted:
            return

        button = editor.get_button_data()
        self.deck["buttons"][index] = button
        if button["category"] not in self.deck["categories"]:
            self.deck["categories"].append(button["category"])
        self.persist_and_refresh(button["category"])

    def delete_button(self, index):
        if index < 0 or index >= len(self.deck["buttons"]):
            return
        button = self.deck["buttons"][index]
        answer = QMessageBox.question(
            self,
            "Delete button",
            f"Delete '{button['label']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            category = button["category"]
            del self.deck["buttons"][index]
            self.persist_and_refresh(category)

    def open_manager(self):
        dialog = ManageButtonsDialog(self.deck, self)
        if dialog.exec() == QDialog.Accepted:
            self.config["profiles"][self.config["active_profile"]] = dialog.deck
            self.persist_and_refresh()

    def open_profiles(self):
        dialog = ProfileManagerDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.config
            self.persist_and_refresh()
            self.statusBar().showMessage(
                f"Active profile · {self.config['active_profile']}", 4000
            )

    def open_obs_settings(self):
        dialog = OBSSettingsDialog(self.config["obs"], self)
        if dialog.exec() == QDialog.Accepted:
            self.config["obs"] = dialog.settings()
            if self.save_config_safely():
                self.statusBar().showMessage("OBS settings saved.", 4000)

    def save_config_safely(self):
        try:
            save_config(self.config, self.config_path)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save config", str(exc))
            return False
        return True

    def persist_and_refresh(self, preferred_category=None):
        if not self.save_config_safely():
            return
        self.refresh_all(preferred_category)
        self.statusBar().showMessage(f"Saved · {self.config_path}", 5000)

    def closeEvent(self, event):
        try:
            save_config(self.config, self.config_path)
        except OSError:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StreamFlow")
    app.setStyle("Fusion")
    window = StreamFlow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
