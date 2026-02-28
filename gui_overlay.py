import math
import queue
import tkinter as tk


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

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#dfdfdf")

        window_w = self._pill_width + (2 * self._pill_pad)
        window_h = self._pill_height + (2 * self._pill_pad)
        self.canvas = tk.Canvas(
            self.root,
            width=window_w,
            height=window_h,
            bg="#dfdfdf",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        self._tip = tk.Toplevel(self.root)
        self._tip.withdraw()
        self._tip.overrideredirect(True)
        self._tip.attributes("-topmost", True)
        self._tip.configure(bg="#000000")

        tip_frame = tk.Frame(self._tip, bg="#000000", padx=18, pady=12)
        tip_frame.pack()

        left_text, key_text, right_text = self._hint_parts()
        tk.Label(
            tip_frame,
            text=left_text,
            fg="#f2f2f2",
            bg="#000000",
            font=("Helvetica", 20, "normal"),
        ).pack(side="left")
        tk.Label(
            tip_frame,
            text=key_text,
            fg="#f38fd7",
            bg="#000000",
            font=("Helvetica", 20, "bold"),
        ).pack(side="left")
        tk.Label(
            tip_frame,
            text=right_text,
            fg="#f2f2f2",
            bg="#000000",
            font=("Helvetica", 20, "normal"),
        ).pack(side="left")

        for widget in (self.root, self.canvas):
            widget.bind("<Enter>", self._on_pill_enter)
            widget.bind("<Leave>", self._on_pill_leave)

        self._tip.bind("<Enter>", self._on_tip_enter)
        self._tip.bind("<Leave>", self._on_tip_leave)

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
        self.root.deiconify()
        self._render()
        self._tick()
        self._watch_shutdown()
        self.root.mainloop()

    def close(self):
        if not self._running:
            return

        self._running = False
        try:
            self._tip.withdraw()
            self._tip.destroy()
        except tk.TclError:
            pass

        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def _watch_shutdown(self):
        if not self._running:
            return
        if self._shutdown_event.is_set():
            self.close()
            return
        self.root.after(100, self._watch_shutdown)

    def _on_pill_enter(self, _event):
        self._hovering_pill = True
        self._update_tip_visibility()

    def _on_pill_leave(self, _event):
        self._hovering_pill = False
        self.root.after(60, self._update_tip_visibility)

    def _on_tip_enter(self, _event):
        self._hovering_tip = True
        self._update_tip_visibility()

    def _on_tip_leave(self, _event):
        self._hovering_tip = False
        self.root.after(60, self._update_tip_visibility)

    def _update_tip_visibility(self):
        if not self._running:
            return

        should_show = (self._hovering_pill or self._hovering_tip) and self.state == self.STATE_IDLE
        if should_show:
            self._position_tip()
            self._tip.deiconify()
        else:
            self._tip.withdraw()

    def _position_pill(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        window_w = int(self.canvas["width"])
        window_h = int(self.canvas["height"])

        x = int((screen_w - window_w) / 2)
        y = int(screen_h - window_h - 56)
        self.root.geometry(f"{window_w}x{window_h}+{x}+{y}")

    def _position_tip(self):
        self._tip.update_idletasks()

        screen_w = self.root.winfo_screenwidth()
        pill_y = self.root.winfo_y()

        tip_w = self._tip.winfo_reqwidth()
        tip_h = self._tip.winfo_reqheight()

        x = int((screen_w - tip_w) / 2)
        y = int(pill_y - tip_h - 10)
        self._tip.geometry(f"{tip_w}x{tip_h}+{x}+{y}")

    def _tick(self):
        if not self._running:
            return

        new_state = None
        while not self._state_updates.empty():
            new_state = self._state_updates.get()

        if new_state and new_state != self.state:
            self.state = new_state
            self._update_tip_visibility()

        self._render()
        self.root.after(50, self._tick)

    def _render(self):
        self.canvas.delete("all")

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

        x1 = self._pill_pad
        y1 = self._pill_pad
        x2 = x1 + self._pill_width
        y2 = y1 + self._pill_height
        radius = self._pill_height / 2

        self._draw_rounded_pill(x1, y1, x2, y2, radius, fill, border)
        self._draw_bars(x1, y1, x2, y2, heights, bar_color)

    def _draw_rounded_pill(self, x1, y1, x2, y2, radius, fill, border):
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=border, width=2)
        self.canvas.create_oval(x1, y1, x1 + (2 * radius), y2, fill=fill, outline=border, width=2)
        self.canvas.create_oval(x2 - (2 * radius), y1, x2, y2, fill=fill, outline=border, width=2)

    def _draw_bars(self, x1, y1, x2, y2, heights, color):
        inner_pad = 20
        usable_w = (x2 - x1) - (2 * inner_pad)
        center_y = y1 + ((y2 - y1) / 2)
        max_h = (y2 - y1) * 0.36

        if usable_w <= 0:
            return

        count = len(heights)
        if count == 0:
            return

        step = usable_w / (count + 1)
        bar_w = max(2, int(step * 0.36))

        for index, height in enumerate(heights):
            px = x1 + inner_pad + ((index + 1) * step)
            h = max(2.0, max_h * height)
            self.canvas.create_rectangle(
                px - (bar_w / 2),
                center_y - (h / 2),
                px + (bar_w / 2),
                center_y + (h / 2),
                fill=color,
                outline=color,
                width=0,
            )

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
