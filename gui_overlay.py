import math
import queue
import sys
from ctypes import c_void_p

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget


class _PillWindow(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.setFixedSize(
            self.overlay._pill_width + (2 * self.overlay._pill_pad),
            self.overlay._pill_height + (2 * self.overlay._pill_pad),
        )
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        if hasattr(Qt, "WA_MacAlwaysShowToolWindow"):
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        self.setFocusPolicy(Qt.NoFocus)

    def enterEvent(self, event):
        self.overlay._on_pill_enter()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.overlay._on_pill_leave()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        x1 = float(self.overlay._pill_pad)
        y1 = float(self.overlay._pill_pad)
        w = float(self.overlay._pill_width)
        h = float(self.overlay._pill_height)
        radius = h / 2.0

        fill, border, bar_color, heights = self.overlay._render_params()

        rect = QRectF(x1, y1, w, h)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        painter.fillPath(path, QColor(fill))
        pen = QPen(QColor(border))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)

        inner_pad = 20.0
        usable_w = w - (2.0 * inner_pad)
        if usable_w <= 0.0 or not heights:
            return

        center_y = y1 + (h / 2.0)
        max_h = h * 0.36
        step = usable_w / (len(heights) + 1)
        bar_w = max(2.0, step * 0.36)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(bar_color))

        for index, height in enumerate(heights):
            px = x1 + inner_pad + ((index + 1) * step)
            bar_h = max(2.0, max_h * height)
            bar_rect = QRectF(
                px - (bar_w / 2.0),
                center_y - (bar_h / 2.0),
                bar_w,
                bar_h,
            )
            painter.drawRect(bar_rect)


class _TipWindow(QWidget):
    def __init__(self, overlay, left_text, key_text, right_text):
        super().__init__()
        self.overlay = overlay

        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        if hasattr(Qt, "WA_MacAlwaysShowToolWindow"):
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        self.setFocusPolicy(Qt.NoFocus)

        self.setStyleSheet(
            "QWidget {"
            "background-color: #000000;"
            "border: 2px solid #545454;"
            "border-radius: 26px;"
            "}"
            "QLabel {"
            "background: transparent;"
            "border: none;"
            "}"
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(22, 12, 22, 12)
        layout.setSpacing(0)

        base_font = QFont("Helvetica", 20)
        bold_font = QFont("Helvetica", 20)
        bold_font.setBold(True)

        left = QLabel(left_text)
        left.setFont(base_font)
        left.setStyleSheet("color: #f2f2f2;")
        layout.addWidget(left)

        key = QLabel(key_text)
        key.setFont(bold_font)
        key.setStyleSheet("color: #f38fd7;")
        layout.addWidget(key)

        right = QLabel(right_text)
        right.setFont(base_font)
        right.setStyleSheet("color: #f2f2f2;")
        layout.addWidget(right)

        self.setLayout(layout)

    def enterEvent(self, event):
        self.overlay._on_tip_enter()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.overlay._on_tip_leave()
        super().leaveEvent(event)


class FloatingOverlay:
    """Small always-on-top overlay with hover hint and animated audio waves."""

    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_TRANSCRIBING = "transcribing"
    _VALID_STATES = {STATE_IDLE, STATE_RECORDING, STATE_TRANSCRIBING}

    def __init__(self, get_level, mode="push_to_talk", hotkey_label="Right Command"):
        self.get_level = get_level
        self.mode = mode
        self.hotkey_label = hotkey_label

        self.state = self.STATE_IDLE
        self._state_updates = queue.SimpleQueue()
        self._phase = 0.0
        self._running = False
        self._hovering_pill = False
        self._hovering_tip = False

        self._pill_width = 96
        self._pill_height = 30
        self._pill_pad = 8

        self._app = QApplication.instance()
        self._owns_app = self._app is None
        if self._app is None:
            self._app = QApplication([])

        self._pill = _PillWindow(self)
        left_text, key_text, right_text = self._hint_parts()
        self._tip = _TipWindow(self, left_text, key_text, right_text)
        self._tip.hide()

        self._tick_timer = QTimer()
        self._tick_timer.timeout.connect(self._tick)

        self._shutdown_timer = QTimer()
        self._shutdown_timer.timeout.connect(self._watch_shutdown)

    def _hint_parts(self):
        if self.mode == "toggle":
            return ("Press ", self.hotkey_label, " to toggle dictating")
        return ("Click or hold ", self.hotkey_label, " to start dictating")

    def set_state_threadsafe(self, state):
        if state in self._VALID_STATES:
            self._state_updates.put(state)

    def run(self, shutdown_event):
        self._running = True
        self._shutdown_event = shutdown_event

        self._position_pill()
        self._pill.show()
        self._pill.raise_()
        self._apply_native_window_hints(self._pill)
        self._apply_native_window_hints(self._tip)
        self._tick_timer.start(50)
        self._shutdown_timer.start(100)

        if self._owns_app:
            self._app.exec()

    def close(self):
        if not self._running and not self._pill.isVisible() and not self._tip.isVisible():
            return

        self._running = False
        self._tick_timer.stop()
        self._shutdown_timer.stop()

        self._tip.hide()
        self._pill.hide()

        self._tip.close()
        self._pill.close()

        if self._owns_app:
            self._app.quit()

    def _watch_shutdown(self):
        if not self._running:
            return
        if self._shutdown_event.is_set():
            self.close()

    def _on_pill_enter(self):
        self._hovering_pill = True
        self._update_tip_visibility()

    def _on_pill_leave(self):
        self._hovering_pill = False
        QTimer.singleShot(60, self._update_tip_visibility)

    def _on_tip_enter(self):
        self._hovering_tip = True
        self._update_tip_visibility()

    def _on_tip_leave(self):
        self._hovering_tip = False
        QTimer.singleShot(60, self._update_tip_visibility)

    def _update_tip_visibility(self):
        if not self._running:
            return

        should_show = (self._hovering_pill or self._hovering_tip) and self.state == self.STATE_IDLE
        if should_show:
            self._position_tip()
            self._tip.show()
            self._tip.raise_()
            self._apply_native_window_hints(self._tip)
        else:
            self._tip.hide()

    def _screen_geometry(self):
        screen = self._pill.screen() or self._app.primaryScreen()
        return screen.geometry()

    def _position_pill(self):
        geometry = self._screen_geometry()
        x = int(geometry.x() + ((geometry.width() - self._pill.width()) / 2))
        y = int(geometry.y() + geometry.height() - self._pill.height() - 56)
        self._pill.move(x, y)

    def _position_tip(self):
        self._tip.adjustSize()

        geometry = self._screen_geometry()
        x = int(geometry.x() + ((geometry.width() - self._tip.width()) / 2))
        y = int(self._pill.y() - self._tip.height() - 10)
        self._tip.move(x, y)

    def _tick(self):
        if not self._running:
            return

        new_state = None
        while not self._state_updates.empty():
            new_state = self._state_updates.get()

        if new_state and new_state != self.state:
            self.state = new_state
            self._update_tip_visibility()

        self._pill.update()

    def _apply_native_window_hints(self, widget):
        if sys.platform != "darwin":
            return

        try:
            import objc
            from AppKit import (
                NSFloatingWindowLevel,
                NSWindowCollectionBehaviorCanJoinAllSpaces,
                NSWindowCollectionBehaviorFullScreenAuxiliary,
            )
        except Exception:
            return

        try:
            native_view = objc.objc_object(c_void_p=int(widget.winId()))
            native_window = native_view.window()
            if native_window is None:
                return
            native_window.setLevel_(NSFloatingWindowLevel)
            behavior = (
                NSWindowCollectionBehaviorCanJoinAllSpaces
                | NSWindowCollectionBehaviorFullScreenAuxiliary
            )
            native_window.setCollectionBehavior_(behavior)
        except Exception:
            # Fall back to Qt-only behavior if native hooks are unavailable.
            return

    def _render_params(self):
        if self.state == self.STATE_IDLE:
            fill = "#7f7f7f"
            border = "#c8c8c8"
            heights = [0.16] * 9
            bar_color = "#d9d9d9"
        elif self.state == self.STATE_TRANSCRIBING:
            fill = "#000000"
            border = "#555555"
            heights = self._transcribing_heights()
            bar_color = "#9f9f9f"
        else:
            fill = "#000000"
            border = "#555555"
            heights = self._recording_heights()
            bar_color = "#f0f0f0"

        return fill, border, bar_color, heights

    def _recording_heights(self):
        try:
            level = float(self.get_level())
        except Exception:
            level = 0.0

        level = min(1.0, max(0.0, level))
        self._phase += 0.45

        heights = []
        for i in range(9):
            wobble = 0.5 + (0.5 * math.sin(self._phase + (i * 0.65)))
            energy = 0.2 + (0.8 * level)
            heights.append(min(1.0, 0.14 + (wobble * energy)))
        return heights

    def _transcribing_heights(self):
        self._phase += 0.35
        heights = []
        for i in range(9):
            wobble = 0.5 + (0.5 * math.sin(self._phase + (i * 0.75)))
            heights.append(0.16 + (0.36 * wobble))
        return heights
