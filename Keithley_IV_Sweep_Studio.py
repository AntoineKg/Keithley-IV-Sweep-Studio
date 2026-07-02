from __future__ import annotations

import csv
import math
import queue
import threading
import time
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from keithley2600 import Keithley2600


OFFICIAL_MANUAL_URLS = {
    "A": "https://download.tek.com/manual/2600AS-901-01--E-Aug2011--Ref.pdf",
    "B": "https://www.tek.com/en/keithley-source-measure-units/smu-2600b-series-sourcemeter-manual-8",
}

DEVICE_SPECS = {
    "2602A": {
        "description": "Dual-channel 40 V Series 2600A System SourceMeter",
        "max_voltage": 40.4,
        "boundary_voltage": 6.06,
        "low_voltage_current": 3.0,
        "high_voltage_current": 1.0,
        "voltage_ranges": "100 mV, 1 V, 6 V, 40 V",
        "current_ranges": "100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 3 A",
        "resolution": "100 fA current / 100 nV voltage",
        "power": "40 W DC per channel; 200 W pulse",
    },
    "2612A": {
        "description": "Dual-channel 200 V Series 2600A System SourceMeter",
        "max_voltage": 202.0,
        "boundary_voltage": 20.2,
        "low_voltage_current": 1.5,
        "high_voltage_current": 0.1,
        "voltage_ranges": "200 mV, 2 V, 20 V, 200 V",
        "current_ranges": "100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 1.5 A",
        "resolution": "100 fA current / 100 nV voltage",
        "power": "30 W DC per channel; 200 W pulse",
    },
    "2636A": {
        "description": "Dual-channel 200 V ultra-low-current Series 2600A System SourceMeter",
        "max_voltage": 202.0,
        "boundary_voltage": 20.2,
        "low_voltage_current": 1.5,
        "high_voltage_current": 0.1,
        "voltage_ranges": "200 mV, 2 V, 20 V, 200 V",
        "current_ranges": "100 pA measure-only; 1 nA, 10 nA, 100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 1.5 A",
        "resolution": "0.1 fA current / 100 nV voltage",
        "power": "30 W DC per channel; 200 W pulse",
    },
    "2602B": {
        "description": "Dual-channel 40 V general-purpose System SourceMeter",
        "max_voltage": 40.4,
        "boundary_voltage": 6.06,
        "low_voltage_current": 3.0,
        "high_voltage_current": 1.0,
        "voltage_ranges": "100 mV, 1 V, 6 V, 40 V",
        "current_ranges": "100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 3 A",
        "resolution": "100 fA current / 100 nV voltage",
        "power": "40 W DC per channel; 200 W pulse",
    },
    "2604B": {
        "description": "Dual-channel 40 V System SourceMeter",
        "max_voltage": 40.4,
        "boundary_voltage": 6.06,
        "low_voltage_current": 3.0,
        "high_voltage_current": 1.0,
        "voltage_ranges": "100 mV, 1 V, 6 V, 40 V",
        "current_ranges": "100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 3 A",
        "resolution": "100 fA current / 100 nV voltage",
        "power": "40 W DC per channel; 200 W pulse",
    },
    "2612B": {
        "description": "Dual-channel 200 V general-purpose System SourceMeter",
        "max_voltage": 202.0,
        "boundary_voltage": 20.2,
        "low_voltage_current": 1.5,
        "high_voltage_current": 0.1,
        "voltage_ranges": "200 mV, 2 V, 20 V, 200 V",
        "current_ranges": "100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 1.5 A",
        "resolution": "100 fA current / 100 nV voltage",
        "power": "30 W DC per channel; 200 W pulse",
    },
    "2614B": {
        "description": "Dual-channel 200 V System SourceMeter",
        "max_voltage": 202.0,
        "boundary_voltage": 20.2,
        "low_voltage_current": 1.5,
        "high_voltage_current": 0.1,
        "voltage_ranges": "200 mV, 2 V, 20 V, 200 V",
        "current_ranges": "100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 1.5 A",
        "resolution": "100 fA current / 100 nV voltage",
        "power": "30 W DC per channel; 200 W pulse",
    },
    "2634B": {
        "description": "Dual-channel 200 V low-current System SourceMeter",
        "max_voltage": 202.0,
        "boundary_voltage": 20.2,
        "low_voltage_current": 1.5,
        "high_voltage_current": 0.1,
        "voltage_ranges": "200 mV, 2 V, 20 V, 200 V",
        "current_ranges": "1 nA, 10 nA, 100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 1.5 A",
        "resolution": "1 fA current / 100 nV voltage",
        "power": "30 W DC per channel; 200 W pulse",
    },
    "2636B": {
        "description": "Dual-channel 200 V ultra-low-current System SourceMeter",
        "max_voltage": 202.0,
        "boundary_voltage": 20.2,
        "low_voltage_current": 1.5,
        "high_voltage_current": 0.1,
        "voltage_ranges": "200 mV, 2 V, 20 V, 200 V",
        "current_ranges": "100 pA measure-only; 1 nA, 10 nA, 100 nA, 1 µA, 10 µA, 100 µA, 1 mA, 10 mA, 100 mA, 1 A, 1.5 A",
        "resolution": "0.1 fA current / 100 nV voltage",
        "power": "30 W DC per channel; 200 W pulse",
    },
}


@dataclass(frozen=True)
class SweepConfig:
    start_voltage: float
    stop_voltage: float
    step_voltage: float
    integration_ms: float
    current_limit: float
    settling_delay: float
    fixed_vb: float
    nplc: float


@dataclass(frozen=True)
class Measurement:
    point: int
    elapsed_s: float
    set_voltage_a: float
    voltage_a: float
    current_a: float
    voltage_b: float
    current_b: float


def build_sweep_points(start: float, stop: float, step: float) -> list[float]:
    """Build a sweep that always includes stop and never overshoots it."""
    if math.isclose(start, stop, rel_tol=0.0, abs_tol=1e-12):
        return [start]

    direction = 1.0 if stop > start else -1.0
    span = abs(stop - start)
    whole_steps = int(math.floor(span / step + 1e-12))
    points = [start + direction * step * index for index in range(whole_steps + 1)]

    if math.isclose(points[-1], stop, rel_tol=1e-10, abs_tol=1e-12):
        points[-1] = stop
    else:
        points.append(stop)
    return points


class IVGui:
    COLORS = {
        "background": "#F6F0D8",
        "surface": "#FFFCF2",
        "navy": "#607F98",
        "navy_light": "#7896AC",
        "accent": "#AFCADF",
        "accent_hover": "#9DBED6",
        "danger": "#D7A099",
        "danger_hover": "#C98D85",
        "text": "#33424C",
        "muted": "#727B7E",
        "border": "#DDD5BD",
        "success": "#5F829B",
        "warning": "#9A774C",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Keithley 2600  |  I–V Sweep Studio")
        self.root.geometry("1180x730")
        self.root.minsize(980, 620)
        self.root.configure(bg=self.COLORS["background"])

        self.k = None
        self.data: list[Measurement] = []
        self.event_queue: queue.Queue = queue.Queue()
        self.abort_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.running = False
        self.connecting = False
        self.closing = False
        self.selected_model: str | None = None

        self._configure_styles()
        self._build_interface()
        self._update_controls()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-s>", self._save_shortcut)
        self.root.after(75, self._drain_event_queue)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", font=("Helvetica", 10))
        style.configure("App.TFrame", background=self.COLORS["background"])
        style.configure("Card.TFrame", background=self.COLORS["surface"])
        style.configure(
            "Card.TLabelframe",
            background=self.COLORS["surface"],
            bordercolor=self.COLORS["border"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=self.COLORS["surface"],
            foreground=self.COLORS["text"],
            font=("Helvetica", 11, "bold"),
        )
        style.configure(
            "Section.TLabel",
            background=self.COLORS["surface"],
            foreground=self.COLORS["text"],
            font=("Helvetica", 11, "bold"),
        )
        style.configure(
            "Field.TLabel",
            background=self.COLORS["surface"],
            foreground=self.COLORS["text"],
        )
        style.configure(
            "Muted.TLabel",
            background=self.COLORS["surface"],
            foreground=self.COLORS["muted"],
            font=("Helvetica", 9),
        )
        style.configure(
            "Primary.TButton",
            background=self.COLORS["accent"],
            foreground="#294354",
            borderwidth=0,
            relief="flat",
            padding=(14, 9),
            font=("Helvetica", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[
                ("pressed", "#8FB2CD"),
                ("active", self.COLORS["accent_hover"]),
                ("disabled", "#D7E0E4"),
            ],
            foreground=[("disabled", "#98A3A8")],
        )
        style.configure(
            "Secondary.TButton",
            background="#E4EDF3",
            foreground=self.COLORS["navy"],
            borderwidth=0,
            relief="flat",
            padding=(12, 8),
            font=("Helvetica", 10, "bold"),
        )
        style.map(
            "Secondary.TButton",
            background=[("pressed", "#C9DBE7"), ("active", "#D6E5EE"), ("disabled", "#EEEFEA")],
            foreground=[("disabled", "#A4A9A7")],
        )
        style.configure(
            "Danger.TButton",
            background=self.COLORS["danger"],
            foreground="#5A3734",
            borderwidth=0,
            relief="flat",
            padding=(14, 9),
            font=("Helvetica", 10, "bold"),
        )
        style.map(
            "Danger.TButton",
            background=[
                ("pressed", "#BF817A"),
                ("active", self.COLORS["danger_hover"]),
                ("disabled", "#E4D0CB"),
            ],
            foreground=[("disabled", "#A38E89")],
        )
        style.configure(
            "TEntry",
            fieldbackground="#FFFDF7",
            foreground=self.COLORS["text"],
            bordercolor=self.COLORS["border"],
            lightcolor=self.COLORS["border"],
            darkcolor=self.COLORS["border"],
            padding=7,
        )
        style.map("TEntry", bordercolor=[("focus", self.COLORS["accent"])])
        style.configure(
            "Treeview",
            background="#FFFDF7",
            fieldbackground="#FFFDF7",
            foreground=self.COLORS["text"],
            borderwidth=0,
            rowheight=29,
        )
        style.map("Treeview", background=[("selected", "#DCEAF3")], foreground=[("selected", self.COLORS["text"])])
        style.configure(
            "Treeview.Heading",
            background="#DFEBF2",
            foreground=self.COLORS["navy"],
            borderwidth=0,
            relief="flat",
            padding=(8, 8),
            font=("Helvetica", 9, "bold"),
        )
        style.map("Treeview.Heading", background=[("active", "#D2E3ED"), ("pressed", "#C5DAE7")])
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#E8E4D6",
            background=self.COLORS["accent"],
            borderwidth=0,
            thickness=7,
        )

    def _build_interface(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self.root, bg=self.COLORS["navy"], height=92)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        title_group = tk.Frame(header, bg=self.COLORS["navy"])
        title_group.grid(row=0, column=0, sticky="w", padx=24, pady=17)
        tk.Label(
            title_group,
            text="I–V Sweep Studio",
            bg=self.COLORS["navy"],
            fg="white",
            font=("Helvetica", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_group,
            text="Keithley 2600 dual-channel source-measure control",
            bg=self.COLORS["navy"],
            fg="#E8F0F5",
            font=("Helvetica", 10),
        ).pack(anchor="w", pady=(3, 0))

        self.device_menu_button = tk.Menubutton(
            header,
            text="Compatible devices  ▾",
            bg="#7896AC",
            activebackground="#89A6BA",
            fg="white",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=13,
            pady=7,
            font=("Helvetica", 9, "bold"),
        )
        device_menu = tk.Menu(
            self.device_menu_button,
            tearoff=False,
            bg=self.COLORS["surface"],
            fg=self.COLORS["text"],
            activebackground=self.COLORS["accent"],
            activeforeground=self.COLORS["text"],
            font=("Helvetica", 10),
        )
        device_menu.add_command(label="Series 2600A", state="disabled")
        for model in ("2602A", "2612A", "2636A"):
            device_menu.add_command(label=f"  Keithley {model}", command=lambda selected=model: self._select_device(selected))
        device_menu.add_separator()
        device_menu.add_command(label="Series 2600B", state="disabled")
        for model in ("2602B", "2604B", "2612B", "2614B", "2634B", "2636B"):
            device_menu.add_command(label=f"  Keithley {model}", command=lambda selected=model: self._select_device(selected))
        self.device_menu_button.configure(menu=device_menu)
        self.device_menu_button.grid(row=0, column=1, padx=(0, 10))

        self.connection_badge = tk.Label(
            header,
            text="●  DISCONNECTED",
            bg=self.COLORS["navy_light"],
            fg="#F1F5F7",
            padx=13,
            pady=7,
            font=("Helvetica", 9, "bold"),
        )
        self.connection_badge.grid(row=0, column=2, padx=(0, 24))

        main = ttk.Frame(self.root, style="App.TFrame", padding=(18, 16, 18, 14))
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_columnconfigure(0, minsize=330)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self._build_control_panel(main)
        self._build_results_panel(main)

        footer = tk.Frame(self.root, bg="#EEE7D0", height=34)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_propagate(False)

        self.status_label = tk.Label(
            footer,
            text="●  Ready to connect",
            bg="#EEE7D0",
            fg=self.COLORS["muted"],
            anchor="w",
            font=("Helvetica", 9),
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=18, pady=7)
        tk.Label(
            footer,
            text="Ctrl+S  Save data",
            bg="#EEE7D0",
            fg=self.COLORS["muted"],
            font=("Helvetica", 9),
        ).grid(row=0, column=1, padx=18)

    def _select_device(self, model: str) -> None:
        self.selected_model = model
        self.device_menu_button.configure(text=f"Keithley {model}  ▾")
        self._set_status(f"{model} selected · model-specific sweep limits enabled", "success")
        self._show_device_ranges(model)

    def _show_device_ranges(self, model: str) -> None:
        spec = DEVICE_SPECS[model]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Keithley {model} · Compatible ranges")
        dialog.geometry("940x650")
        dialog.minsize(760, 520)
        dialog.configure(bg=self.COLORS["background"])
        dialog.transient(self.root)

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        heading = tk.Frame(dialog, bg=self.COLORS["navy"], padx=24, pady=18)
        heading.grid(row=0, column=0, sticky="ew")
        tk.Label(
            heading,
            text=f"Keithley {model}",
            bg=self.COLORS["navy"],
            fg="white",
            font=("Helvetica", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            heading,
            text=spec["description"],
            bg=self.COLORS["navy"],
            fg="#E8F0F5",
            font=("Helvetica", 10),
        ).pack(anchor="w", pady=(4, 0))

        content = ttk.Frame(dialog, style="Card.TFrame", padding=18)
        content.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        ttk.Label(
            content,
            text="Allowed application inputs and instrument ranges",
            style="Section.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        table_frame = ttk.Frame(content, style="Card.TFrame")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        table = ttk.Treeview(
            table_frame,
            columns=("parameter", "range", "details"),
            show="headings",
            selectmode="none",
        )
        table.heading("parameter", text="Parameter")
        table.heading("range", text="Allowed value / range")
        table.heading("details", text="Details")
        table.column("parameter", width=180, minwidth=150, anchor="w", stretch=False)
        table.column("range", width=300, minwidth=240, anchor="w")
        table.column("details", width=390, minwidth=300, anchor="w")

        max_voltage = spec["max_voltage"]
        boundary = spec["boundary_voltage"]
        low_current = spec["low_voltage_current"]
        high_current = spec["high_voltage_current"]
        rows = [
            ("Application support", "Compatible", "This GUI uses SMUA and SMUB in DC voltage-source mode."),
            ("SMU channels", "2", "Both channels are controlled and measured by the application."),
            ("Start voltage", f"−{max_voltage:g} to +{max_voltage:g} V", "Applied to channel A."),
            ("Stop voltage", f"−{max_voltage:g} to +{max_voltage:g} V", "Applied to channel A; ascending and descending sweeps are supported."),
            ("Fixed channel B", f"−{max_voltage:g} to +{max_voltage:g} V", "Constant bias voltage for channel B."),
            ("Voltage step", "> 0 V", "The stop value is always included; maximum 6,000 sweep points."),
            (
                "Current compliance",
                f"0.0001–{low_current:g} A at |V| ≤ {boundary:g} V",
                f"Above {boundary:g} V, the DC limit is {high_current:g} A. One limit is applied to both channels.",
            ),
            ("Integration time", "0.2–2000 ms", "Application range: 0.01–100 NPLC at a 50 Hz line frequency."),
            ("Settling delay", "0 s or greater", "Additional wait after each voltage step before measuring."),
            ("Voltage ranges", spec["voltage_ranges"], "Nominal source and measurement ranges."),
            ("DC current ranges", spec["current_ranges"], "Instrument ranges; the GUI uses current autoranging."),
            ("Pulse capability", "Up to 10 A", "Not exposed by this application; the current sweep is DC only."),
            ("Measurement resolution", spec["resolution"], "Best available instrument resolution."),
            ("Maximum output power", spec["power"], "Operating boundaries and thermal derating still apply."),
        ]
        for index, row in enumerate(rows):
            table.insert("", "end", values=row, tags=("even" if index % 2 == 0 else "odd",))
        table.tag_configure("even", background="#FFF8E8")
        table.tag_configure("odd", background="#FFFDF7")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        dialog.after_idle(lambda: table.yview_moveto(0.0))

        ttk.Label(
            content,
            text=(
                "Selecting this model enables model-specific voltage and DC compliance checks. "
                "The values summarize application limits and do not replace the instrument manual, "
                "operating-boundary graphs, or laboratory safety procedures."
            ),
            style="Muted.TLabel",
            wraplength=830,
            justify="left",
        ).grid(row=2, column=0, sticky="ew", pady=(12, 8))

        actions = ttk.Frame(content, style="Card.TFrame")
        actions.grid(row=3, column=0, sticky="e")
        ttk.Button(
            actions,
            text="Official manual",
            style="Secondary.TButton",
            command=lambda: webbrowser.open(OFFICIAL_MANUAL_URLS[model[-1]]),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Close", style="Primary.TButton", command=dialog.destroy).pack(side="left")

    def _build_control_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=18)
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        panel.grid_columnconfigure(0, weight=1)

        ttk.Label(panel, text="Connection", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(panel, text="VISA TCP/IP instrument address", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(3, 9)
        )

        connection_row = ttk.Frame(panel, style="Card.TFrame")
        connection_row.grid(row=2, column=0, sticky="ew")
        connection_row.grid_columnconfigure(0, weight=1)
        self.ip_var = tk.StringVar(value="192.168.1.100")
        self.ip_entry = ttk.Entry(connection_row, textvariable=self.ip_var)
        self.ip_entry.grid(row=0, column=0, sticky="ew", padx=(0, 7))
        self.connect_btn = ttk.Button(connection_row, text="Connect", style="Secondary.TButton", command=self.connect)
        self.connect_btn.grid(row=0, column=1)

        ttk.Separator(panel).grid(row=3, column=0, sticky="ew", pady=17)

        ttk.Label(panel, text="Sweep parameters", style="Section.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Label(panel, text="Values are checked before outputs are enabled", style="Muted.TLabel").grid(
            row=5, column=0, sticky="w", pady=(3, 8)
        )

        fields = ttk.Frame(panel, style="Card.TFrame")
        fields.grid(row=6, column=0, sticky="ew")
        fields.grid_columnconfigure(1, weight=1)

        field_specs = [
            ("start_voltage", "Start voltage", "V", "-15.0"),
            ("stop_voltage", "Stop voltage", "V", "20.0"),
            ("step_voltage", "Voltage step", "V", "1.0"),
            ("integration_ms", "Integration time", "ms", "20"),
            ("current_limit", "Current compliance", "A", "1.0"),
            ("settling_delay", "Settling delay", "s", "0.5"),
            ("fixed_vb", "Fixed channel B", "V", "1.0"),
        ]

        self.entry_vars: dict[str, tk.StringVar] = {}
        self.entries: dict[str, ttk.Entry] = {}
        for row, (key, label, unit, default) in enumerate(field_specs):
            ttk.Label(fields, text=label, style="Field.TLabel").grid(row=row, column=0, sticky="w", pady=5)
            value = tk.StringVar(value=default)
            entry = ttk.Entry(fields, textvariable=value, width=12, justify="right")
            entry.grid(row=row, column=1, sticky="ew", padx=(12, 7), pady=5)
            ttk.Label(fields, text=unit, width=3, style="Muted.TLabel").grid(row=row, column=2, sticky="w", pady=5)
            self.entry_vars[key] = value
            self.entries[key] = entry

        ttk.Label(panel, text="Integration time assumes a 50 Hz line frequency.", style="Muted.TLabel").grid(
            row=7, column=0, sticky="w", pady=(8, 0)
        )

        ttk.Separator(panel).grid(row=8, column=0, sticky="ew", pady=17)

        sweep_actions = ttk.Frame(panel, style="Card.TFrame")
        sweep_actions.grid(row=9, column=0, sticky="ew")
        sweep_actions.grid_columnconfigure(0, weight=1)
        sweep_actions.grid_columnconfigure(1, weight=1)
        self.run_btn = ttk.Button(sweep_actions, text="▶  Run sweep", style="Primary.TButton", command=self.run_sweep)
        self.run_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.abort_btn = ttk.Button(sweep_actions, text="■  Abort", style="Danger.TButton", command=self.safe_abort)
        self.abort_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_results_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=18)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        toolbar = ttk.Frame(panel, style="Card.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)

        heading = ttk.Frame(toolbar, style="Card.TFrame")
        heading.grid(row=0, column=0, sticky="w")
        ttk.Label(heading, text="Measurement results", style="Section.TLabel").pack(anchor="w")
        ttk.Label(heading, text="Live readings from both SMU channels", style="Muted.TLabel").pack(anchor="w", pady=(3, 0))

        actions = ttk.Frame(toolbar, style="Card.TFrame")
        actions.grid(row=0, column=1, sticky="e")
        self.clear_btn = ttk.Button(actions, text="Clear", style="Secondary.TButton", command=self.clear_data)
        self.clear_btn.pack(side="left", padx=(0, 6))
        self.plot_btn = ttk.Button(actions, text="Plot", style="Secondary.TButton", command=self.plot_iv)
        self.plot_btn.pack(side="left", padx=(0, 6))
        self.save_btn = ttk.Button(actions, text="Save CSV", style="Primary.TButton", command=self.save_csv)
        self.save_btn.pack(side="left")

        progress_row = ttk.Frame(panel, style="Card.TFrame")
        progress_row.grid(row=1, column=0, sticky="ew", pady=(18, 6))
        progress_row.grid_columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(progress_row, mode="determinate", maximum=1)
        self.progress.grid(row=0, column=0, sticky="ew")
        self.progress_text = ttk.Label(progress_row, text="0 / 0", style="Muted.TLabel")
        self.progress_text.grid(row=0, column=1, padx=(12, 0))

        ttk.Separator(panel).grid(row=2, column=0, sticky="ew", pady=(0, 10))

        table_frame = ttk.Frame(panel, style="Card.TFrame")
        table_frame.grid(row=3, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("point", "elapsed", "set_a", "voltage_a", "current_a", "voltage_b", "current_b")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        headings = {
            "point": "Point",
            "elapsed": "Time (s)",
            "set_a": "Set A (V)",
            "voltage_a": "Measured A (V)",
            "current_a": "Current A (A)",
            "voltage_b": "Voltage B (V)",
            "current_b": "Current B (A)",
        }
        widths = {"point": 60, "elapsed": 90, "set_a": 95, "voltage_a": 115, "current_a": 120, "voltage_b": 105, "current_b": 120}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], minwidth=60, anchor="e", stretch=True)

        self.tree.tag_configure("even", background="#FFF8E8")
        self.tree.tag_configure("odd", background="#FFFDF7")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def _set_status(self, text: str, tone: str = "neutral") -> None:
        colors = {
            "neutral": self.COLORS["muted"],
            "success": self.COLORS["success"],
            "warning": self.COLORS["warning"],
            "error": self.COLORS["danger"],
            "busy": self.COLORS["accent"],
        }
        self.status_label.configure(text=f"●  {text}", fg=colors.get(tone, self.COLORS["muted"]))

    def _set_connection_badge(self, state: str, detail: str = "") -> None:
        states = {
            "disconnected": ("●  DISCONNECTED", self.COLORS["navy_light"], "#F1F5F7"),
            "connecting": ("●  CONNECTING", "#8C754E", "#FFF0C8"),
            "connected": ("●  CONNECTED", "#6D91AA", "#EDF6FA"),
        }
        text, background, foreground = states[state]
        if detail:
            text = f"{text}  ·  {detail}"
        self.connection_badge.configure(text=text, bg=background, fg=foreground)

    def _update_controls(self) -> None:
        idle = not self.running and not self.connecting and not self.closing
        connected = self.k is not None
        has_data = bool(self.data)

        self.connect_btn.configure(state="normal" if idle else "disabled", text="Reconnect" if connected else "Connect")
        self.ip_entry.configure(state="normal" if idle else "disabled")
        self.run_btn.configure(state="normal" if idle and connected else "disabled")
        self.abort_btn.configure(state="normal" if self.running and not self.abort_event.is_set() else "disabled")
        self.save_btn.configure(state="normal" if idle and has_data else "disabled")
        self.plot_btn.configure(state="normal" if idle and has_data else "disabled")
        self.clear_btn.configure(state="normal" if idle and has_data else "disabled")
        for entry in self.entries.values():
            entry.configure(state="normal" if idle else "disabled")

    def connect(self) -> None:
        address = self.ip_var.get().strip()
        if not address:
            messagebox.showwarning("Missing address", "Enter the instrument IP address first.", parent=self.root)
            self.ip_entry.focus_set()
            return

        self.connecting = True
        self._set_connection_badge("connecting", address)
        self._set_status(f"Connecting to {address}…", "busy")
        self._update_controls()

        self.worker = threading.Thread(target=self._connect_worker, args=(address,), daemon=True)
        self.worker.start()

    def _connect_worker(self, address: str) -> None:
        try:
            instrument = Keithley2600(f"TCPIP0::{address}::INSTR")
            instrument.reset()
            instrument.errorqueue.clear()
            self.event_queue.put(("connected", instrument, address))
        except Exception as error:
            self.event_queue.put(("connection_error", str(error), address))

    def _read_config(self) -> tuple[SweepConfig, list[float]]:
        labels = {
            "start_voltage": "Start voltage",
            "stop_voltage": "Stop voltage",
            "step_voltage": "Voltage step",
            "integration_ms": "Integration time",
            "current_limit": "Current compliance",
            "settling_delay": "Settling delay",
            "fixed_vb": "Fixed channel B voltage",
        }
        values: dict[str, float] = {}
        for key, variable in self.entry_vars.items():
            try:
                value = float(variable.get())
            except ValueError as error:
                raise ValueError(f"{labels[key]} must be a number.") from error
            if not math.isfinite(value):
                raise ValueError(f"{labels[key]} must be finite.")
            values[key] = value

        if abs(values["start_voltage"]) > 202 or abs(values["stop_voltage"]) > 202:
            raise ValueError("Start and stop voltages must be between −202 V and +202 V.")
        if abs(values["fixed_vb"]) > 202:
            raise ValueError("Fixed channel B voltage must be between −202 V and +202 V.")
        if values["step_voltage"] <= 0:
            raise ValueError("Voltage step must be greater than zero.")
        if not 0.0001 <= values["current_limit"] <= 10:
            raise ValueError("Current compliance must be between 0.0001 A and 10 A.")
        if values["settling_delay"] < 0:
            raise ValueError("Settling delay cannot be negative.")

        if self.selected_model:
            spec = DEVICE_SPECS[self.selected_model]
            peak_voltage = max(
                abs(values["start_voltage"]),
                abs(values["stop_voltage"]),
                abs(values["fixed_vb"]),
            )
            if peak_voltage > spec["max_voltage"]:
                raise ValueError(
                    f"Keithley {self.selected_model} supports up to ±{spec['max_voltage']:g} V. "
                    "Reduce the channel A sweep or channel B bias."
                )

            if peak_voltage <= spec["boundary_voltage"]:
                maximum_dc_current = spec["low_voltage_current"]
            else:
                maximum_dc_current = spec["high_voltage_current"]
            if values["current_limit"] > maximum_dc_current:
                raise ValueError(
                    f"At a requested magnitude of {peak_voltage:g} V, Keithley {self.selected_model} "
                    f"allows at most {maximum_dc_current:g} A DC compliance."
                )

        nplc = values["integration_ms"] / 20.0
        if not 0.01 <= nplc <= 100:
            raise ValueError("Integration time must be between 0.2 ms and 2000 ms at 50 Hz.")

        points = build_sweep_points(values["start_voltage"], values["stop_voltage"], values["step_voltage"])
        if len(points) > 6000:
            raise ValueError(f"This sweep contains {len(points):,} points. Increase the voltage step.")

        config = SweepConfig(
            start_voltage=values["start_voltage"],
            stop_voltage=values["stop_voltage"],
            step_voltage=values["step_voltage"],
            integration_ms=values["integration_ms"],
            current_limit=values["current_limit"],
            settling_delay=values["settling_delay"],
            fixed_vb=values["fixed_vb"],
            nplc=nplc,
        )
        return config, points

    def run_sweep(self) -> None:
        if self.k is None:
            messagebox.showwarning("Not connected", "Connect to the instrument before starting a sweep.", parent=self.root)
            return

        try:
            config, points = self._read_config()
        except ValueError as error:
            messagebox.showerror("Check sweep parameters", str(error), parent=self.root)
            return

        self.clear_data(update_status=False)
        self.abort_event.clear()
        self.running = True
        self.progress.configure(maximum=len(points), value=0)
        self.progress_text.configure(text=f"0 / {len(points):,}")
        self._set_status(f"Sweep running · {len(points):,} points", "busy")
        self._update_controls()

        self.worker = threading.Thread(target=self._sweep_worker, args=(config, points), daemon=True)
        self.worker.start()

    def _sweep_worker(self, config: SweepConfig, points: list[float]) -> None:
        instrument = self.k
        smua = instrument.smua
        smub = instrument.smub
        started = time.monotonic()
        error_message = None
        cleanup_errors: list[str] = []

        try:
            instrument.errorqueue.clear()

            for smu in (smua, smub):
                smu.source.output = smu.OUTPUT_OFF
                smu.source.func = smu.OUTPUT_DCVOLTS
                smu.source.levelv = 0
                smu.source.limiti = config.current_limit
                smu.measure.nplc = config.nplc
                smu.measure.autorangev = smu.AUTORANGE_ON
                smu.measure.autorangei = smu.AUTORANGE_ON
                smu.source.delay = 0.1
                smu.measure.delay = 0.05

            smua.source.levelv = points[0]
            smub.source.levelv = config.fixed_vb
            smua.source.output = smua.OUTPUT_ON
            smub.source.output = smub.OUTPUT_ON

            for index, set_voltage in enumerate(points, start=1):
                if self.abort_event.is_set():
                    break

                smua.source.levelv = set_voltage
                if self.abort_event.wait(config.settling_delay):
                    break

                voltage_a = smua.measure.v()
                current_a = smua.measure.i()
                voltage_b = smub.measure.v()
                current_b = smub.measure.i()

                measurement = Measurement(
                    point=index,
                    elapsed_s=time.monotonic() - started,
                    set_voltage_a=set_voltage,
                    voltage_a=voltage_a,
                    current_a=current_a,
                    voltage_b=voltage_b,
                    current_b=current_b,
                )
                self.event_queue.put(("measurement", measurement, len(points)))
        except Exception as error:
            error_message = str(error)
        finally:
            for name, smu in (("SMUA", smua), ("SMUB", smub)):
                try:
                    smu.source.output = smu.OUTPUT_OFF
                except Exception as cleanup_error:
                    cleanup_errors.append(f"{name}: {cleanup_error}")

            if cleanup_errors:
                cleanup_text = "Could not confirm output-off for " + "; ".join(cleanup_errors)
                error_message = f"{error_message}\n\n{cleanup_text}" if error_message else cleanup_text

            self.event_queue.put(("sweep_finished", self.abort_event.is_set(), error_message))

    def safe_abort(self) -> None:
        if not self.running:
            return
        self.abort_event.set()
        self._set_status("Abort requested · waiting for safe output shutdown…", "warning")
        self._update_controls()

    def _drain_event_queue(self) -> None:
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass

        try:
            if self.root.winfo_exists():
                self.root.after(75, self._drain_event_queue)
        except tk.TclError:
            # The callback may have processed the event that destroyed the window.
            pass

    def _handle_event(self, event: tuple) -> None:
        event_name = event[0]

        if event_name == "connected":
            _, instrument, address = event
            self.k = instrument
            self.connecting = False
            self._set_connection_badge("connected", address)
            self._set_status(f"Connected to {address}", "success")
            self._update_controls()

        elif event_name == "connection_error":
            _, error, address = event
            self.k = None
            self.connecting = False
            self._set_connection_badge("disconnected")
            self._set_status(f"Connection to {address} failed", "error")
            self._update_controls()
            messagebox.showerror("Connection failed", error, parent=self.root)

        elif event_name == "measurement":
            _, measurement, total = event
            self.data.append(measurement)
            values = (
                measurement.point,
                f"{measurement.elapsed_s:.3f}",
                f"{measurement.set_voltage_a:.6g}",
                f"{measurement.voltage_a:.6g}",
                f"{measurement.current_a:.6e}",
                f"{measurement.voltage_b:.6g}",
                f"{measurement.current_b:.6e}",
            )
            tag = "even" if measurement.point % 2 == 0 else "odd"
            self.tree.insert("", "end", values=values, tags=(tag,))
            self.tree.yview_moveto(1.0)
            self.progress.configure(value=measurement.point)
            self.progress_text.configure(text=f"{measurement.point:,} / {total:,}")
            self._set_status(
                f"Point {measurement.point:,}/{total:,} · A {measurement.voltage_a:.3f} V, {measurement.current_a:.2e} A",
                "busy",
            )

        elif event_name == "sweep_finished":
            _, aborted, error = event
            self.running = False
            self._update_controls()

            if self.closing:
                self.root.destroy()
                return

            if error:
                self._set_status("Sweep stopped with an error · outputs were switched off", "error")
                messagebox.showerror("Sweep error", error, parent=self.root)
            elif aborted:
                self._set_status(f"Sweep aborted safely · {len(self.data):,} points retained", "warning")
            else:
                self._set_status(f"Sweep complete · {len(self.data):,} points acquired", "success")

        elif event_name == "shutdown_finished":
            self.root.destroy()

    def clear_data(self, update_status: bool = True) -> None:
        if self.running:
            return
        self.data.clear()
        self.tree.delete(*self.tree.get_children())
        self.progress.configure(value=0, maximum=1)
        self.progress_text.configure(text="0 / 0")
        self._update_controls()
        if update_status:
            self._set_status("Results cleared", "neutral")

    def save_csv(self) -> None:
        if not self.data:
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save sweep data",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            initialfile="iv_sweep.csv",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as output:
                writer = csv.writer(output)
                writer.writerow(
                    [
                        "Point",
                        "Elapsed Time (s)",
                        "Set Voltage A (V)",
                        "Measured Voltage A (V)",
                        "Current A (A)",
                        "Voltage B (V)",
                        "Current B (A)",
                    ]
                )
                for item in self.data:
                    writer.writerow(
                        [
                            item.point,
                            item.elapsed_s,
                            item.set_voltage_a,
                            item.voltage_a,
                            item.current_a,
                            item.voltage_b,
                            item.current_b,
                        ]
                    )
        except OSError as error:
            messagebox.showerror("Could not save data", str(error), parent=self.root)
            return

        self._set_status(f"Saved {len(self.data):,} points to {Path(file_path).name}", "success")

    def _save_shortcut(self, _event=None) -> None:
        if self.data and not self.running:
            self.save_csv()

    def plot_iv(self) -> None:
        if not self.data:
            return

        sweep_voltage = [item.set_voltage_a for item in self.data]
        current_a = [item.current_a for item in self.data]
        current_b = [item.current_b for item in self.data]
        nonzero_currents = [abs(value) for value in current_a + current_b if value != 0]
        linear_threshold = max(min(nonzero_currents, default=1e-12), 1e-15)

        figure, axis = plt.subplots(figsize=(8.5, 5.2))
        axis.plot(sweep_voltage, current_a, "o-", markersize=3, linewidth=1.2, label="SMUA current")
        axis.plot(sweep_voltage, current_b, "s-", markersize=3, linewidth=1.2, label="SMUB current")
        axis.set_yscale("symlog", linthresh=linear_threshold)
        axis.set_xlabel("SMUA set voltage (V)")
        axis.set_ylabel("Current (A)")
        axis.set_title("I–V sweep")
        axis.grid(True, which="both", alpha=0.25)
        axis.legend()
        figure.tight_layout()
        plt.show(block=False)

    def on_close(self) -> None:
        if self.closing:
            return

        if self.running:
            should_close = messagebox.askyesno(
                "Sweep in progress",
                "Abort the sweep, switch both outputs off, and close the application?",
                icon="warning",
                parent=self.root,
            )
            if not should_close:
                return
            self.closing = True
            self.abort_event.set()
            self._set_status("Closing safely · waiting for output shutdown…", "warning")
            self._update_controls()
            return

        if self.k is None:
            self.root.destroy()
            return

        self.closing = True
        self._set_status("Closing safely · switching outputs off…", "warning")
        self._update_controls()
        threading.Thread(target=self._shutdown_worker, daemon=True).start()

    def _shutdown_worker(self) -> None:
        try:
            for smu in (self.k.smua, self.k.smub):
                try:
                    smu.source.output = smu.OUTPUT_OFF
                except Exception:
                    pass
        finally:
            self.event_queue.put(("shutdown_finished",))


if __name__ == "__main__":
    root = tk.Tk()
    app = IVGui(root)
    root.mainloop()
