# ABOUTME: Settings panel widget for conversion options.
# ABOUTME: Provides voice selection, speed control, and metadata fields.

"""SettingsPanel for conversion settings."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QSlider,
    QLineEdit,
    QGroupBox,
)

from gui.models.voice import Voice

logger = logging.getLogger(__name__)


class SettingsPanel(QWidget):
    """Widget for conversion settings.

    Provides controls for:
    - Voice selection
    - Random voice mode with quality filter
    - Speed/length_scale slider
    - Author and title metadata fields

    Signals:
        settingsChanged: Emitted when any setting changes
    """

    settingsChanged = Signal()

    def __init__(
        self,
        installed_voices: Optional[list[Voice]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._installed_voices = installed_voices or []
        self._setup_ui()
        self._setup_connections()
        self._populate_voices()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)

        # Voice selection group
        voice_group = QGroupBox("Voice")
        voice_inner = QVBoxLayout(voice_group)
        voice_inner.setSpacing(8)

        self._voice_selector = QComboBox()
        voice_inner.addWidget(self._voice_selector)

        random_row = QHBoxLayout()
        self._random_checkbox = QCheckBox("Random")
        random_row.addWidget(self._random_checkbox)

        self._random_filter_label = QLabel("Quality:")
        self._random_filter_label.setVisible(False)
        random_row.addWidget(self._random_filter_label)

        self._random_filter = QComboBox()
        self._random_filter.addItems(["Any", "High", "Medium", "Low"])
        self._random_filter.setVisible(False)
        random_row.addWidget(self._random_filter)

        random_row.addStretch()
        voice_inner.addLayout(random_row)

        layout.addWidget(voice_group)

        # Speed group
        speed_group = QGroupBox("Speed")
        speed_layout = QVBoxLayout(speed_group)

        slider_row = QHBoxLayout()
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setMinimum(1)   # 0.1x
        self._speed_slider.setMaximum(30)  # 3.0x
        self._speed_slider.setValue(10)    # 1.0x default (normal speed)
        self._speed_slider.setTickPosition(QSlider.TicksBelow)
        self._speed_slider.setTickInterval(5)

        self._speed_display = QLabel("1.0x")
        self._speed_display.setMinimumWidth(40)

        slider_row.addWidget(self._speed_slider)
        slider_row.addWidget(self._speed_display)
        speed_layout.addLayout(slider_row)

        layout.addWidget(speed_group)

        # Metadata group
        metadata_group = QGroupBox("Metadata (ID3 Tags)")
        metadata_layout = QFormLayout(metadata_group)

        self._author_field = QLineEdit()
        self._author_field.setPlaceholderText("e.g., Jane Austen")
        metadata_layout.addRow("Author:", self._author_field)

        self._title_field = QLineEdit()
        self._title_field.setPlaceholderText("e.g., Pride and Prejudice")
        metadata_layout.addRow("Book Title:", self._title_field)

        layout.addWidget(metadata_group)

        layout.addStretch()

    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        self._voice_selector.currentIndexChanged.connect(self._on_settings_changed)
        self._random_checkbox.toggled.connect(self._on_random_toggled)
        self._random_filter.currentIndexChanged.connect(self._on_settings_changed)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        self._author_field.textChanged.connect(self._on_settings_changed)
        self._title_field.textChanged.connect(self._on_settings_changed)

    def _populate_voices(self) -> None:
        """Populate voice selector with installed voices."""
        self._voice_selector.clear()

        for voice in self._installed_voices:
            # Display: "Ryan (en_US) - high"
            display = f"{voice.name} ({voice.language}) - {voice.quality}"
            self._voice_selector.addItem(display, voice.key)

    def _on_settings_changed(self) -> None:
        """Handle any setting change."""
        self.settingsChanged.emit()

    def _on_random_toggled(self, checked: bool) -> None:
        """Handle random checkbox toggle."""
        self._random_filter.setVisible(checked)
        self._random_filter_label.setVisible(checked)
        self._voice_selector.setEnabled(not checked)
        self._on_settings_changed()

    def _on_speed_changed(self, value: int) -> None:
        """Handle speed slider change."""
        speed = value / 10.0
        self._speed_display.setText(f"{speed:.1f}x")
        self._on_settings_changed()

    def get_selected_voice(self) -> Optional[str]:
        """Get the currently selected voice key.

        Returns None if random mode is selected.
        """
        if self._random_checkbox.isChecked():
            return None
        return self._voice_selector.currentData()

    def is_random_mode(self) -> bool:
        """Check if random voice mode is enabled."""
        return self._random_checkbox.isChecked()

    def set_random_mode(self, enabled: bool) -> None:
        """Set random voice mode."""
        self._random_checkbox.setChecked(enabled)

    def get_random_filter(self) -> Optional[str]:
        """Get the random quality filter.

        Returns None if 'Any' is selected.
        """
        if not self._random_checkbox.isChecked():
            return None

        text = self._random_filter.currentText().lower()
        if text == "any":
            return None
        return text

    def get_speed(self) -> float:
        """Get the user-facing speed multiplier (e.g., 1.5 = 50% faster)."""
        return self._speed_slider.value() / 10.0

    def set_speed(self, value: float) -> None:
        """Set the user-facing speed multiplier."""
        self._speed_slider.setValue(int(value * 10))

    def get_length_scale(self) -> float:
        """Get Piper's length_scale value (inverse of speed).

        Speed 1.0x = length_scale 1.0 (normal).
        Speed 1.5x = length_scale 0.667 (faster speech).
        Speed 0.5x = length_scale 2.0 (slower speech).
        """
        speed = self.get_speed()
        return round(1.0 / speed, 3)

    def set_length_scale(self, value: float) -> None:
        """Set speed from a Piper length_scale value (for config compat)."""
        speed = round(1.0 / value, 1) if value > 0 else 1.0
        self.set_speed(speed)

    def get_author(self) -> str:
        """Get the author field value (trimmed)."""
        return self._author_field.text().strip()

    def get_title(self) -> str:
        """Get the title field value (trimmed)."""
        return self._title_field.text().strip()

    def refresh_voices(self, voices: list[Voice]) -> None:
        """Refresh the voice list."""
        self._installed_voices = voices
        self._populate_voices()
