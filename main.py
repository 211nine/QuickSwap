
import json
import os
import threading
import time
import tkinter as tk
import customtkinter as ctk
from pynput import keyboard, mouse

app_name = "QuickSwap"
settings_dir = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), app_name)
settings_path = os.path.join(settings_dir, "settings.json")

default_settings = {
    "activation_key": "v",
    "spear_slot": "4",
    "return_slot": "1",
    "interval": 295,
    "always_on_top": False
}

bg = "#1c1c21"
field_bg = "#292930"
field_hover = "#33333b"
border = "#3b3b44"
divider = "#32323a"
text_color = "#e8e8ed"
muted = "#9595a1"
red = "#df8e99"
green = "#83d2ab"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class QuickSwap:
    def __init__(self):
        self.settings = self.load_settings()
        self.enabled = False
        self.activation_held = False
        self.running = True
        self.capturing = None
        self.pressed_keys = set()
        self.lock = threading.RLock()
        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()
        self.root = ctk.CTk()
        self.root.title(app_name)
        self.root.configure(fg_color=bg)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", self.settings["always_on_top"])
        self.drag_x = 0
        self.drag_y = 0
        self.toggle_progress = 1.0 if self.settings["always_on_top"] else 0.0
        self.toggle_target = self.toggle_progress
        self.toggle_hovered = False
        self.toggle_job = None

        self.build_ui()
        self.center_window()

        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()

        self.worker = threading.Thread(
            target=self.macro_loop,
            daemon=True
        )
        self.worker.start()

        self.root.after(75, self.refresh_ui)

    def load_settings(self):
        settings = default_settings.copy()

        try:
            with open(settings_path, "r", encoding="utf-8") as file:
                saved = json.load(file)

            if isinstance(saved, dict):
                for key in settings:
                    if key in saved:
                        settings[key] = saved[key]
        except (OSError, ValueError, TypeError):
            pass

        settings["activation_key"] = str(settings["activation_key"]).lower()
        settings["spear_slot"] = str(settings["spear_slot"])
        settings["return_slot"] = str(settings["return_slot"])

        if not settings["activation_key"] or settings["activation_key"] == "f1":
            settings["activation_key"] = "v"

        if settings["spear_slot"] not in tuple("123456789"):
            settings["spear_slot"] = "4"

        if settings["return_slot"] not in tuple("123456789"):
            settings["return_slot"] = "1"

        try:
            settings["interval"] = max(1, min(60000, int(settings["interval"])))
        except (TypeError, ValueError):
            settings["interval"] = 295

        settings["always_on_top"] = bool(settings["always_on_top"])
        return settings

    def save_settings(self):
        try:
            os.makedirs(settings_dir, exist_ok=True)

            with open(settings_path, "w", encoding="utf-8") as file:
                json.dump(self.settings, file, indent=4)
        except OSError:
            pass

    def center_window(self):
        self.root.update_idletasks()

        width = 390
        height = self.main.winfo_reqheight() + 24

        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def build_ui(self):
        self.main = ctk.CTkFrame(
            self.root,
            fg_color=bg,
            corner_radius=0
        )
        self.main.pack(fill="both", expand=True, padx=19, pady=12)

        self.title_bar = ctk.CTkFrame(
            self.main,
            fg_color="transparent",
            height=30
        )
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.title_bar,
            text=app_name,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#f4f4f6"
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")

        self.close_button = ctk.CTkButton(
            self.title_bar,
            text="×",
            width=27,
            height=27,
            corner_radius=5,
            fg_color="transparent",
            hover_color="#64343c",
            text_color="#b0b0ba",
            font=ctk.CTkFont(size=19),
            command=self.close
        )
        self.close_button.pack(side="right")

        self.minimize_button = ctk.CTkButton(
            self.title_bar,
            text="−",
            width=27,
            height=27,
            corner_radius=5,
            fg_color="transparent",
            hover_color=field_hover,
            text_color="#b0b0ba",
            font=ctk.CTkFont(size=18),
            command=self.minimize
        )
        self.minimize_button.pack(side="right", padx=(0, 4))

        for widget in (self.title_bar, self.title_label):
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.drag)

        self.status_label = ctk.CTkLabel(
            self.main,
            text="Disabled",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=red,
            height=48
        )
        self.status_label.pack(pady=(9, 8))

        self.divider()

        self.settings_frame = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )
        self.settings_frame.pack(fill="x", pady=(10, 8))

        self.activation_button = self.add_key_row(
            "Activation key",
            self.settings["activation_key"].upper(),
            "activation_key"
        )

        self.spear_button = self.add_key_row(
            "Spear slot",
            self.settings["spear_slot"],
            "spear_slot"
        )

        self.return_button = self.add_key_row(
            "Return slot",
            self.settings["return_slot"],
            "return_slot"
        )

        interval_row = self.make_row("Interval (ms)")

        self.interval_var = tk.StringVar(
            value=str(self.settings["interval"])
        )

        self.interval_entry = ctk.CTkEntry(
            interval_row,
            width=88,
            height=32,
            corner_radius=6,
            fg_color=field_bg,
            border_color=border,
            border_width=1,
            text_color="#f4f4f6",
            justify="center",
            textvariable=self.interval_var,
            font=ctk.CTkFont(size=13)
        )
        self.interval_entry.pack(side="right")

        self.interval_entry.bind("<FocusOut>", self.save_interval)
        self.interval_entry.bind("<Return>", self.save_interval)
        top_row = self.make_row("Always on top")

        self.toggle_holder = ctk.CTkFrame(
            top_row,
            fg_color="transparent",
            width=88,
            height=32
        )
        self.toggle_holder.pack(side="right")
        self.toggle_holder.pack_propagate(False)

        self.top_canvas = tk.Canvas(
            self.toggle_holder,
            width=44,
            height=26,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )
        self.top_canvas.place(relx=0.5, rely=0.5, anchor="center")

        self.top_canvas.bind("<Button-1>", self.toggle_topmost)
        self.top_canvas.bind("<Enter>", self.on_toggle_enter)
        self.top_canvas.bind("<Leave>", self.on_toggle_leave)
        self.draw_toggle()
        self.divider()

        self.help_label = ctk.CTkLabel(
            self.main,
            text="Press F1 to enable or disable",
            font=ctk.CTkFont(size=11),
            text_color=muted,
            height=27
        )
        self.help_label.pack(pady=(5, 0))

    def divider(self):
        ctk.CTkFrame(
            self.main,
            height=1,
            corner_radius=0,
            fg_color=divider
        ).pack(fill="x", pady=3)

    def make_row(self, label):
        row = ctk.CTkFrame(
            self.settings_frame,
            fg_color="transparent",
            height=46
        )
        row.pack(fill="x")
        row.pack_propagate(False)

        ctk.CTkLabel(
            row,
            text=label,
            text_color=text_color,
            font=ctk.CTkFont(size=13)
        ).pack(side="left")

        return row

    def add_key_row(self, label, value, setting):
        row = self.make_row(label)

        button = ctk.CTkButton(
            row,
            text=value,
            width=88,
            height=32,
            corner_radius=6,
            fg_color=field_bg,
            hover_color=field_hover,
            border_width=1,
            border_color=border,
            text_color="#f4f4f6",
            font=ctk.CTkFont(size=13),
            command=lambda: self.start_capture(setting)
        )
        button.pack(side="right")

        return button

    def blend_color(self, start, end, amount):
        start = start.lstrip("#")
        end = end.lstrip("#")

        values = []

        for i in (0, 2, 4):
            a = int(start[i:i + 2], 16)
            b = int(end[i:i + 2], 16)
            values.append(round(a + (b - a) * amount))

        return "#{:02x}{:02x}{:02x}".format(*values)

    def draw_toggle(self):
        canvas = self.top_canvas
        canvas.delete("all")
        p = self.toggle_progress
        off_color = "#464650"
        on_color = "#398e6e"

        track = self.blend_color(off_color, on_color, p)

        if self.toggle_hovered:
            track = self.blend_color(track, "#777783", 0.12)

        x1 = 2
        y1 = 3
        x2 = 42
        y2 = 23
        radius = 10

        canvas.create_oval(
            x1, y1, x1 + radius * 2, y2,
            fill=track,
            outline=track
        )
        canvas.create_oval(
            x2 - radius * 2, y1, x2, y2,
            fill=track,
            outline=track
        )
        canvas.create_rectangle(
            x1 + radius, y1,
            x2 - radius, y2,
            fill=track,
            outline=track
        )

        knob_x = 12 + 20 * p

        canvas.create_oval(
            knob_x - 8,
            5,
            knob_x + 8,
            21,
            fill="#f3f3f5",
            outline="#f3f3f5"
        )

    def on_toggle_enter(self, event=None):
        self.toggle_hovered = True
        self.draw_toggle()

    def on_toggle_leave(self, event=None):
        self.toggle_hovered = False
        self.draw_toggle()

    def toggle_topmost(self, event=None):
        value = not self.settings["always_on_top"]
        self.settings["always_on_top"] = value
        self.root.attributes("-topmost", value)
        self.save_settings()
        self.toggle_target = 1.0 if value else 0.0

        if self.toggle_job is None:
            self.animate_toggle()

    def animate_toggle(self):
        difference = self.toggle_target - self.toggle_progress

        if abs(difference) < 0.008:
            self.toggle_progress = self.toggle_target
            self.draw_toggle()
            self.toggle_job = None
            return

        self.toggle_progress += difference * 0.24
        self.draw_toggle()

        self.toggle_job = self.root.after(12, self.animate_toggle)

    def start_capture(self, setting):
        with self.lock:
            self.capturing = setting
            self.activation_held = False

        self.get_key_button(setting).configure(text="Press key")

    def get_key_button(self, setting):
        return {
            "activation_key": self.activation_button,
            "spear_slot": self.spear_button,
            "return_slot": self.return_button
        }[setting]

    def key_name(self, key):
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char.lower()

            if key.vk is not None:
                if 65 <= key.vk <= 90:
                    return chr(key.vk).lower()

                if 48 <= key.vk <= 57:
                    return chr(key.vk)

        if isinstance(key, keyboard.Key):
            return key.name.lower()

        return None

    def on_key_press(self, key):
        name = self.key_name(key)

        if name is None:
            return

        with self.lock:
            if name in self.pressed_keys:
                return

            self.pressed_keys.add(name)

            if self.capturing:
                setting = self.capturing

                if setting in ("spear_slot", "return_slot"):
                    if len(name) != 1 or name not in "123456789":
                        return

                elif name == "f1":
                    return

                self.settings[setting] = name
                self.capturing = None
                self.save_settings()
                return

            if name == "f1":
                self.enabled = not self.enabled

                if not self.enabled:
                    self.activation_held = False

                return

            if name == self.settings["activation_key"]:
                self.activation_held = True

    def on_key_release(self, key):
        name = self.key_name(key)

        if name is None:
            return

        with self.lock:
            self.pressed_keys.discard(name)

            if name == self.settings["activation_key"]:
                self.activation_held = False

    def macro_loop(self):
        while self.running:
            with self.lock:
                active = (
                    self.enabled
                    and self.activation_held
                    and self.capturing is None
                )

                spear = self.settings["spear_slot"]
                back = self.settings["return_slot"]
                interval = self.settings["interval"]

            if not active:
                time.sleep(0.01)
                continue

            try:
                self.keyboard_controller.press(spear)
                self.keyboard_controller.release(spear)
                time.sleep(0.015)
                self.mouse_controller.click(mouse.Button.left)
                time.sleep(0.015)
                self.keyboard_controller.press(back)
                self.keyboard_controller.release(back)
            except Exception:
                pass

            end = time.monotonic() + interval / 1000

            while self.running and time.monotonic() < end:
                time.sleep(0.01)

                with self.lock:
                    if not self.enabled or not self.activation_held:
                        break

    def save_interval(self, event=None):
        try:
            value = int(self.interval_var.get())
            value = max(1, min(60000, value))
        except ValueError:
            value = self.settings["interval"]

        with self.lock:
            self.settings["interval"] = value

        self.interval_var.set(str(value))
        self.save_settings()
        self.root.focus_set()

    def refresh_ui(self):
        if not self.running:
            return

        with self.lock:
            enabled = self.enabled
            capturing = self.capturing
            activation = self.settings["activation_key"]
            spear = self.settings["spear_slot"]
            back = self.settings["return_slot"]

        self.status_label.configure(
            text="Enabled" if enabled else "Disabled",
            text_color=green if enabled else red
        )

        if capturing is None:
            self.activation_button.configure(text=activation.upper())
            self.spear_button.configure(text=spear)
            self.return_button.configure(text=back)

        self.root.after(75, self.refresh_ui)

    def start_drag(self, event):
        self.drag_x = event.x_root - self.root.winfo_x()
        self.drag_y = event.y_root - self.root.winfo_y()

    def drag(self, event):
        x = event.x_root - self.drag_x
        y = event.y_root - self.drag_y

        self.root.geometry(f"+{x}+{y}")

    def minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(200, self.check_restore)

    def check_restore(self):
        if not self.running:
            return

        if self.root.state() == "normal":
            self.root.overrideredirect(True)
            return

        self.root.after(200, self.check_restore)

    def close(self):
        self.save_interval()

        self.running = False
        self.enabled = False
        self.activation_held = False

        if self.toggle_job is not None:
            self.root.after_cancel(self.toggle_job)

        try:
            self.listener.stop()
        except Exception:
            pass

        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    QuickSwap().run()