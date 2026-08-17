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
QMainWindow, QDialog, QWidget { background-color: #202124; color: #f1f3f4; }
QPushButton { background-color: #3c4043; border: 1px solid #5f6368; border-radius: 8px; padding: 8px 12px; color: #f1f3f4; }
QPushButton:hover { background-color: #4b4f52; }
QPushButton#deckButton { background-color: #303134; font-size: 15px; font-weight: 600; min-width: 120px; min-height: 78px; }
QPushButton#primaryButton { background-color: #1a73e8; border-color: #1a73e8; }
QListWidget, QLineEdit, QComboBox, QSpinBox { background-color: #303134; border: 1px solid #5f6368; border-radius: 6px; padding: 6px; color: #f1f3f4; }
QListWidget::item { padding: 8px; }
QListWidget::item:selected { background-color: #1a73e8; }
QScrollArea { border: none; }
QStatusBar { color: #bdc1c6; }
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


class ButtonEditorDialog(QDialog):
    def __init__(self, button_data=None, categories=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Button" if button_data else "Add Button")
        self.resize(540, 300)
        self.button_data = button_data or {}
        categories = categories or []

        form = QFormLayout(self)

        self.label_input = QLineEdit(self.button_data.get("label", ""))
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
        self.value_input = QLineEdit()
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
        needs_value = action in VALUE_ACTIONS
        self.value_input.setEnabled(needs_value)
        self.value_input.setPlaceholderText(ACTION_PLACEHOLDERS.get(action, ""))
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
        self.resize(760, 520)
        self.deck = copy.deepcopy(deck)

        layout = QVBoxLayout(self)
        intro = QLabel("Add, edit, remove, hide, or reorder buttons in this profile.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _: self.edit_selected())
        layout.addWidget(self.list_widget)

        actions = QHBoxLayout()
        for label, callback in (
            ("Add", self.add_button),
            ("Edit", self.edit_selected),
            ("Delete", self.delete_selected),
        ):
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
        for index, button in enumerate(self.deck["buttons"]):
            status = "" if button.get("enabled", True) else " [hidden]"
            item = QListWidgetItem(
                f"{button['category']}  •  {button['label']}{status}\n{button['command']}"
            )
            item.setData(Qt.UserRole, index)
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
        self.resize(620, 440)
        self.config = copy.deepcopy(config)

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Profiles keep separate button layouts for streaming, work, gaming, or anything else."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        actions = QHBoxLayout()
        for label, callback in (
            ("New", self.add_profile),
            ("Duplicate", self.duplicate_profile),
            ("Rename", self.rename_selected),
            ("Delete", self.delete_selected),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)

        io_actions = QHBoxLayout()
        import_button = QPushButton("Import Profile…")
        import_button.clicked.connect(self.import_profile_file)
        io_actions.addWidget(import_button)
        export_button = QPushButton("Export Profile…")
        export_button.clicked.connect(self.export_selected)
        io_actions.addWidget(export_button)
        io_actions.addStretch(1)
        layout.addLayout(io_actions)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_with_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.reload(self.config["active_profile"])

    def reload(self, selected_name=None):
        self.list_widget.clear()
        for name in self.config["profiles"]:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
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
            created = create_profile(self.config, name.strip())
            self.reload(created)

    def duplicate_profile(self):
        source = self.selected_name()
        if not source:
            return
        created = create_profile(self.config, f"{source} Copy", source_name=source)
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
        self.setWindowTitle("OBS WebSocket Settings")
        self.resize(520, 260)

        form = QFormLayout(self)

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
            "OBS Studio 28+ includes obs-websocket. Find its server settings and password under OBS's Tools menu."
        )
        note.setWordWrap(True)
        form.addRow(note)

        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_obs_connection)
        form.addRow(test_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

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
        self.resize(1060, 700)
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

        profile_label = QLabel("Profile")
        profile_label.setStyleSheet("color: #bdc1c6;")
        header.addWidget(profile_label)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(150)
        self.profile_combo.currentTextChanged.connect(self.switch_profile)
        header.addWidget(self.profile_combo)

        profiles_button = QPushButton("Profiles")
        profiles_button.clicked.connect(self.open_profiles)
        header.addWidget(profiles_button)

        obs_button = QPushButton("OBS")
        obs_button.clicked.connect(self.open_obs_settings)
        header.addWidget(obs_button)

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

        self.refresh_all()
        self.statusBar().showMessage(f"Config: {self.config_path}")

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
            button.customContextMenuRequested.connect(
                lambda pos, btn=button, idx=index: self.open_button_menu(btn, pos, idx)
            )

            icon_path = resolve_icon(button_data.get("icon", ""))
            if icon_path:
                button.setIcon(QIcon(str(icon_path)))
                button.setIconSize(QSize(36, 36))

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

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_button(index))
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
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
                f"Active profile: {self.config['active_profile']}", 4000
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
