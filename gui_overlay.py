import math
import queue
import sys
from ctypes import c_void_p

from PySide6.QtCore import QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QIcon, QPainter, QPainterPath, QPen
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
        pen.setWidthF(1.6)
        painter.setPen(pen)
        painter.drawPath(path)

        inner_pad = max(5.0, w * 0.12)
        usable_w = w - (2.0 * inner_pad)
        if usable_w <= 0.0 or not heights:
            return

        center_y = y1 + (h / 2.0)
        max_h = h * 0.68
        step = usable_w / (len(heights) + 1)
        bar_w = max(1.2, step * 0.34)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(bar_color))

        for index, height in enumerate(heights):
            px = x1 + inner_pad + ((index + 1) * step)
            bar_h = max(1.2, max_h * height)
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
        self._radius = 26.0

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

        layout = QHBoxLayout()
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(0)

        base_font = QFont("Helvetica", 20)
        bold_font = QFont("Helvetica", 20)
        bold_font.setBold(True)

        left = QLabel(left_text)
        left.setFont(base_font)
        left.setStyleSheet("color: #f2f2f2; background: transparent;")
        layout.addWidget(left)

        key = QLabel(key_text)
        key.setFont(bold_font)
        key.setStyleSheet("color: #f38fd7; background: transparent;")
        layout.addWidget(key)

        right = QLabel(right_text)
        right.setFont(base_font)
        right.setStyleSheet("color: #f2f2f2; background: transparent;")
        layout.addWidget(right)

        self.setLayout(layout)

    def enterEvent(self, event):
        self.overlay._on_tip_enter()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.overlay._on_tip_leave()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self._radius, self._radius)

        painter.fillPath(path, QColor(0, 0, 0, 235))
        pen = QPen(QColor("#5a5a5a"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)


class FloatingOverlay:
    """Small always-on-top overlay with hover hint and animated audio waves."""

    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_TRANSCRIBING = "transcribing"
    _VALID_STATES = {STATE_IDLE, STATE_RECORDING, STATE_TRANSCRIBING}

    def __init__(self, get_level, mode="push_to_talk", hotkey_label="Right Command", app_icon_path=None):
        self.get_level = get_level
        self.mode = mode
        self.hotkey_label = hotkey_label
        self.app_icon_path = app_icon_path

        self.state = self.STATE_IDLE
        self._state_updates = queue.SimpleQueue()
        self._phase = 0.0
        self._running = False
        self._hovering_pill = False
        self._hovering_tip = False

        self._pill_width = 52
        self._pill_height = 14
        self._pill_pad = 3
        self._screen_margin_x = 20
        self._screen_margin_bottom = 18
        self._last_anchor = None
        self._pill_opacity_idle = 0.60
        self._pill_opacity_active = 0.70
        self._smoothed_level = 0.0

        self._app = QApplication.instance()
        self._owns_app = self._app is None
        if self._app is None:
            self._app = QApplication([])

        self._pill = _PillWindow(self)
        left_text, key_text, right_text = self._hint_parts()
        self._tip = _TipWindow(self, left_text, key_text, right_text)
        self._tip.hide()
        self._apply_icon()

        self._tick_timer = QTimer()
        self._tick_timer.timeout.connect(self._tick)

        self._shutdown_timer = QTimer()
        self._shutdown_timer.timeout.connect(self._watch_shutdown)

    def _apply_icon(self):
        if not self.app_icon_path:
            return

        icon = QIcon(self.app_icon_path)
        if icon.isNull():
            return

        self._app.setWindowIcon(icon)
        self._pill.setWindowIcon(icon)
        self._tip.setWindowIcon(icon)

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
        self._apply_pill_opacity()
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

    def _target_screen(self):
        screen = QGuiApplication.screenAt(QCursor.pos())
        if screen is not None:
            return screen

        active_window = self._app.activeWindow()
        if active_window and active_window.screen():
            return active_window.screen()

        return self._pill.screen() or self._app.primaryScreen()

    def _screen_geometry(self):
        screen = self._target_screen()
        if screen is None:
            return QRect(0, 0, 1440, 900)
        return screen.availableGeometry()

    def _position_pill(self):
        screen_geometry = self._screen_geometry()
        geometry = screen_geometry

        x = int(geometry.x() + ((geometry.width() - self._pill.width()) / 2))
        x = max(screen_geometry.x() + self._screen_margin_x, x)
        x = min(screen_geometry.right() - self._pill.width() - self._screen_margin_x, x)

        y = int(geometry.bottom() - self._pill.height() - self._screen_margin_bottom)
        y = max(screen_geometry.y() + self._screen_margin_x, y)
        self._pill.move(x, y)
        self._last_anchor = (
            geometry.x(),
            geometry.y(),
            geometry.width(),
            geometry.height(),
        )

    def _position_tip(self):
        self._tip.adjustSize()

        geometry = self._screen_geometry()
        x = int(self._pill.x() + ((self._pill.width() - self._tip.width()) / 2))
        x = max(geometry.x() + self._screen_margin_x, x)
        x = min(geometry.right() - self._tip.width() - self._screen_margin_x, x)

        y = int(self._pill.y() - self._tip.height() - 10)
        y = max(geometry.y() + self._screen_margin_x, y)
        self._tip.move(x, y)

    def _tick(self):
        if not self._running:
            return

        geometry = self._screen_geometry()
        anchor = (
            geometry.x(),
            geometry.y(),
            geometry.width(),
            geometry.height(),
        )
        if anchor != self._last_anchor:
            self._position_pill()
            if self._tip.isVisible():
                self._position_tip()

        new_state = None
        while not self._state_updates.empty():
            new_state = self._state_updates.get()

        if new_state and new_state != self.state:
            self.state = new_state
            self._apply_pill_opacity()
            self._update_tip_visibility()

        self._pill.update()

    def _apply_pill_opacity(self):
        if self.state == self.STATE_IDLE:
            self._pill.setWindowOpacity(self._pill_opacity_idle)
        else:
            self._pill.setWindowOpacity(self._pill_opacity_active)

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
            fill = "#787878"
            border = "#c3c3c3"
            heights = [0.14] * 5
            bar_color = "#d7d7d7"
        elif self.state == self.STATE_TRANSCRIBING:
            fill = "#111111"
            border = "#4f4f4f"
            heights = self._transcribing_heights()
            bar_color = "#a7b2c8"
        else:
            fill = "#0b120d"
            border = "#4f6f5a"
            heights = self._recording_heights()
            bar_color = "#76ffad"

        return fill, border, bar_color, heights

    def _recording_heights(self):
        try:
            raw_level = float(self.get_level())
        except Exception:
            raw_level = 0.0

        raw_level = min(1.0, max(0.0, raw_level))
        boosted = min(1.0, math.sqrt(raw_level) * 1.18)
        self._smoothed_level = (0.72 * self._smoothed_level) + (0.28 * boosted)
        level = self._smoothed_level
        self._phase += 0.6
        envelope = [0.38, 0.64, 1.0, 0.64, 0.38]

        heights = []
        for i in range(5):
            pulse = 0.5 + (0.5 * math.sin((self._phase * 1.12) + (i * 0.95)))
            energy = 0.18 + (0.82 * level)
            h = 0.08 + (envelope[i] * energy * (0.35 + (0.65 * pulse)))
            heights.append(min(1.0, h))
        return heights

    def _transcribing_heights(self):
        self._phase += 0.4
        heights = []
        for i in range(5):
            wobble = 0.5 + (0.5 * math.sin(self._phase + (i * 0.75)))
            heights.append(0.22 + (0.42 * wobble))
        return heights
