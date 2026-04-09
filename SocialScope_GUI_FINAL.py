"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SocialScope Forensic Toolkit  —  GUI v1.0                          ║
║          6-Phase Engine (Deleted Recovery removed)                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

HOW TO RUN:
    1. Place this file in the ROOT of your project (same folder as /core/)
    2. pip install customtkinter rich reportlab networkx plotly pandas pillow pyyaml
    3. python SocialScope_GUI_FINAL.py

PROJECT STRUCTURE:
    your_project/
    ├── SocialScope_GUI_FINAL.py   ← THIS FILE
    ├── config/
    │   └── config.yaml
    └── core/
        ├── __init__.py
        ├── parser.py
        ├── timeline.py
        ├── keyword_alert.py
        ├── media_extractor.py
        ├── network_graph.py
        └── report_generator.py
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import sys
import subprocess
import platform
import csv
import yaml
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
#  COLOURS & FONTS
# ──────────────────────────────────────────────────────────────────────────────
BG_MAIN        = "#0D0F14"
BG_PANEL       = "#141720"
BG_CARD        = "#1C1F2E"
BG_INPUT       = "#12141C"
BG_HOVER       = "#252840"

ACCENT_BLUE    = "#3D72F5"
ACCENT_CYAN    = "#00D4FF"
ACCENT_GREEN   = "#00E676"
ACCENT_AMBER   = "#FFB300"
ACCENT_RED     = "#FF4757"

TEXT_PRIMARY   = "#E8EAF6"
TEXT_SECONDARY = "#7B82A0"
TEXT_DIM       = "#4A5068"

FONT_MONO  = ("Courier New", 11)
FONT_LABEL = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
FONT_PHASE = ("Segoe UI", 11, "bold")

# ──────────────────────────────────────────────────────────────────────────────
#  PHASE METADATA  (6 phases — deleted recovery removed)
# ──────────────────────────────────────────────────────────────────────────────
PHASES = [
    {"id": 1, "icon": "📥", "name": "Instagram Parsing",
     "desc": "Parse direct.db / JSON export"},
    {"id": 2, "icon": "📊", "name": "Master Timeline + CSV",
     "desc": "Build chronological event timeline"},
    {"id": 3, "icon": "🚨", "name": "Keyword & Sentiment Alert",
     "desc": "Flag suspicious language & sentiment"},
    {"id": 4, "icon": "🔐", "name": "SHA-256 Hash + EXIF",
     "desc": "Hash media files & extract metadata"},
    {"id": 5, "icon": "🕸️",  "name": "Network Link Analysis",
     "desc": "Generate interactive contact graph"},
    {"id": 6, "icon": "📄", "name": "PDF Forensic Report",
     "desc": "Compile professional PDF report"},
]

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIG LOADER
# ──────────────────────────────────────────────────────────────────────────────
def load_config():
    script_dir = Path(__file__).parent
    candidates = [
        script_dir / "config" / "config.yaml",
        script_dir / "config.yaml",
        Path("config") / "config.yaml",
        Path("config.yaml"),
    ]
    for p in candidates:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    return {
        "general": {"default_output_dir": "./output"},
        "red_flags": {
            "keywords": ["kill", "murder", "bomb", "payment", "bitcoin",
                         "drug", "deal", "maar", "khatam", "lsd", "ak47"],
            "phrases":  ["khatam kar denge", "milte hain", "delivery krni"],
        },
    }

# ──────────────────────────────────────────────────────────────────────────────
#  BACKEND BRIDGE
# ──────────────────────────────────────────────────────────────────────────────
def _ensure_core_importable():
    root = str(Path(__file__).parent)
    if root not in sys.path:
        sys.path.insert(0, root)

_ensure_core_importable()

# ── Shared state between phases ───────────────────────────────────────────────
_run_state: dict = {}


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 1 — Instagram Parsing
# ──────────────────────────────────────────────────────────────────────────────
def run_phase_1(case_id, investigator, data_folder, output_folder, log):
    global _run_state
    _run_state.clear()

    try:
        from core.parser import InstagramParser
    except ImportError as e:
        log(f"  ✗ Import error: {e}")
        return {"success": False, "files": []}

    config = load_config()
    log(f"  → Config loaded ({len(config.get('red_flags', {}).get('keywords', []))} keywords)")

    # Check for JSON export first
    json_files = list(Path(data_folder).rglob("message_*.json"))
    if json_files:
        log(f"  → Instagram JSON export detected ({len(json_files)} file(s))")
    else:
        db_path = Path(data_folder) / "direct.db"
        if not db_path.exists():
            found = list(Path(data_folder).rglob("direct.db"))
            if found:
                db_path = found[0]
                log(f"  → direct.db found at: {db_path.relative_to(data_folder)}")
            else:
                log("  ✗ No data found! Need direct.db OR message_1.json")
                return {"success": False, "files": []}
        log(f"  → direct.db found ({db_path.stat().st_size:,} bytes)")

    log("  → Parsing messages…")
    parser = InstagramParser(config, data_folder)
    messages = parser.parse_direct_messages()

    if not messages:
        log("  ✗ No messages parsed")
        return {"success": False, "files": []}

    active  = sum(1 for m in messages if m.get("status") == "ACTIVE")
    log(f"  → {len(messages):,} total  |  {active:,} active")

    _run_state["messages"]    = messages
    _run_state["config"]      = config
    _run_state["data_folder"] = data_folder

    # Unique senders
    senders = set(m.get("sender", "") for m in messages)
    log(f"  → Participants: {', '.join(list(senders)[:5])}")
    log(f"  ✓ Phase 1 complete — {len(messages):,} messages parsed")
    return {"success": True, "files": []}


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 2 — Master Timeline + CSV
# ──────────────────────────────────────────────────────────────────────────────
def run_phase_2(case_id, investigator, data_folder, output_folder, log):
    messages = _run_state.get("messages", [])
    if not messages:
        log("  ✗ No messages from Phase 1")
        return {"success": False, "files": []}

    try:
        from core.timeline import MasterTimeline
    except ImportError as e:
        log(f"  ✗ Import error: {e}")
        return {"success": False, "files": []}

    log(f"  → Building timeline for {len(messages):,} messages…")
    timeline = MasterTimeline(messages)
    df = timeline.build_timeline()

    if df is None or df.empty:
        log("  ✗ Timeline empty")
        return {"success": False, "files": []}

    log(f"  → {len(df):,} events sorted chronologically")
    csv_path = Path(output_folder) / f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    log(f"  → Saved: {csv_path.name}")

    _run_state["timeline_csv"] = str(csv_path)
    log("  ✓ Phase 2 complete — timeline.csv generated")
    return {"success": True, "files": [str(csv_path)]}


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 3 — Keyword & Sentiment Alert
# ──────────────────────────────────────────────────────────────────────────────
def run_phase_3(case_id, investigator, data_folder, output_folder, log):
    messages = _run_state.get("messages", [])
    config   = _run_state.get("config", load_config())

    if not messages:
        log("  ✗ No messages available")
        return {"success": False, "files": []}

    try:
        from core.keyword_alert import KeywordAlert
    except ImportError as e:
        log(f"  ✗ Import error: {e}")
        return {"success": False, "files": []}

    kw_count = len(config.get("red_flags", {}).get("keywords", []))
    ph_count = len(config.get("red_flags", {}).get("phrases", []))
    log(f"  → Watchlist: {kw_count} keywords + {ph_count} phrases")
    log(f"  → Analysing {len(messages):,} messages…")

    alert_system = KeywordAlert(config)
    suspicious_messages = []

    for msg in messages:
        analysis = alert_system.analyze_message(msg.get("text", ""))
        msg["sentiment"]     = analysis["status"]
        msg["red_flags"]     = analysis["flags"]
        msg["is_suspicious"] = analysis["is_suspicious"]
        if msg["is_suspicious"]:
            suspicious_messages.append(msg)

    _run_state["suspicious"] = suspicious_messages

    aggressive    = sum(1 for m in suspicious_messages if m["sentiment"] == "Aggressive")
    susp_only     = len(suspicious_messages) - aggressive
    log(f"  → {len(suspicious_messages):,} flagged  |  🔴 Aggressive: {aggressive}  |  🟡 Suspicious: {susp_only}")

    csv_path = Path(output_folder) / f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Sender", "Message", "Sentiment", "Flags"])
        for msg in suspicious_messages:
            writer.writerow([
                msg.get("readable_time", "N/A"),
                msg.get("sender", "Unknown"),
                msg.get("text", "")[:200],
                msg.get("sentiment", "N/A"),
                ", ".join(msg.get("red_flags", [])),
            ])
    log(f"  → Saved: {csv_path.name}")
    _run_state["alerts_csv"] = str(csv_path)
    log("  ✓ Phase 3 complete — alerts.csv generated")
    return {"success": True, "files": [str(csv_path)]}


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 4 — SHA-256 Hash + EXIF
# ──────────────────────────────────────────────────────────────────────────────
def run_phase_4(case_id, investigator, data_folder, output_folder, log):
    messages = _run_state.get("messages", [])

    try:
        from core.media_extractor import MediaExtractor
    except ImportError as e:
        log(f"  ✗ Import error: {e}")
        return {"success": False, "files": []}

    extractor = MediaExtractor(data_folder)

    # Hash direct.db if present
    db_path = Path(data_folder) / "direct.db"
    if not db_path.exists():
        found = list(Path(data_folder).rglob("direct.db"))
        db_path = found[0] if found else None

    db_hash = "N/A"
    if db_path and db_path.exists():
        log(f"  → Hashing direct.db ({db_path.stat().st_size:,} bytes)…")
        db_hash = extractor.calculate_sha256(db_path)
        log(f"  → SHA-256: {db_hash[:32]}…")
    else:
        log("  → direct.db not found — skipping DB hash")

    _run_state["db_hash"] = db_hash

    # Scan media files
    log("  → Scanning for image/video files…")
    media_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.mp4", "*.gif", "*.webp", "*.mov"]:
        media_files.extend(Path(data_folder).rglob(ext))

    hash_records = []
    exif_records = []

    if media_files:
        log(f"  → {len(media_files)} media files found — hashing…")
        for mf in media_files[:100]:
            try:
                fhash = extractor.calculate_sha256(mf)
                hash_records.append({
                    "file": mf.name,
                    "path": str(mf),
                    "sha256": fhash,
                    "size_bytes": mf.stat().st_size,
                })
                if mf.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    exif = extractor.extract_exif(mf)
                    if exif:
                        exif_records.append({
                            "file": mf.name,
                            "exif_keys": ", ".join(list(exif.keys())[:10]),
                            "gps": str(exif.get("GPS", "N/A"))[:120],
                            "datetime_orig": str(exif.get("DateTimeOriginal", "N/A")),
                            "camera": str(exif.get("Make", "")) + " " + str(exif.get("Model", "")),
                        })
            except Exception:
                pass
    else:
        log("  → No media files found in folder")

    # Save hashes CSV
    hashes_csv = Path(output_folder) / "file_hashes.csv"
    with open(hashes_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "path", "sha256", "size_bytes"])
        writer.writeheader()
        if db_path and db_path.exists():
            writer.writerow({"file": "direct.db", "path": str(db_path),
                             "sha256": db_hash, "size_bytes": db_path.stat().st_size})
        writer.writerows(hash_records)
    log(f"  → Saved: {hashes_csv.name}  ({len(hash_records)+1} entries)")

    output_files = [str(hashes_csv)]

    if exif_records:
        exif_csv = Path(output_folder) / "exif_metadata.csv"
        with open(exif_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["file", "exif_keys", "gps", "datetime_orig", "camera"])
            writer.writeheader()
            writer.writerows(exif_records)
        log(f"  → Saved: {exif_csv.name}  ({len(exif_records)} images with EXIF)")
        output_files.append(str(exif_csv))

    log("  ✓ Phase 4 complete — integrity verified")
    return {"success": True, "files": output_files}


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 5 — Network Link Analysis
# ──────────────────────────────────────────────────────────────────────────────
def run_phase_5(case_id, investigator, data_folder, output_folder, log):
    messages = _run_state.get("messages", [])
    if not messages:
        log("  ✗ No messages available")
        return {"success": False, "files": []}

    try:
        from core.network_graph import NetworkGraph
        import networkx as nx
        import plotly.graph_objects as go
    except ImportError as e:
        log(f"  ✗ Import error: {e}")
        return {"success": False, "files": []}

    log("  → Mapping communication graph…")
    graph = NetworkGraph(messages)
    graph.build_graph()

    node_count = len(graph.G.nodes())
    edge_count = len(graph.G.edges())
    log(f"  → {node_count} contacts (nodes)  |  {edge_count} connections (edges)")

    from collections import Counter
    sender_count = Counter(m.get("sender") for m in messages)
    log("  → Top contacts:")
    for name, count in sender_count.most_common(5):
        log(f"      {name}  →  {count:,} messages")

    # Build and save interactive graph
    pos = nx.spring_layout(graph.G, seed=42)
    edge_x, edge_y = [], []
    for edge in graph.G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = [pos[n][0] for n in graph.G.nodes()]
    node_y = [pos[n][1] for n in graph.G.nodes()]
    node_labels = list(graph.G.nodes())
    node_sizes  = [max(10, min(60, sender_count.get(n, 1) * 3)) for n in node_labels]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1.5, color="#3D72F5"), hoverinfo="none"
    ))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(size=node_sizes, color="#00D4FF",
                    line=dict(width=2, color="#FF2D78")),
        text=node_labels,
        textposition="top center",
        hovertext=[f"{n}: {sender_count.get(n, 0)} msgs" for n in node_labels],
        hoverinfo="text",
    ))
    fig.update_layout(
        title=f"SocialScope — Network Analysis  |  Case: {case_id}",
        paper_bgcolor="#0D0F14", plot_bgcolor="#0D0F14",
        font=dict(color="#E8EAF6"), showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    graph_path = Path(output_folder) / "network_graph.html"
    fig.write_html(str(graph_path))
    log(f"  → Saved: {graph_path.name}")
    log("  ✓ Phase 5 complete — interactive network graph saved")
    return {"success": True, "files": [str(graph_path)]}


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 6 — PDF Forensic Report
# ──────────────────────────────────────────────────────────────────────────────
def run_phase_6(case_id, investigator, data_folder, output_folder, log):
    messages   = _run_state.get("messages",   [])
    suspicious = _run_state.get("suspicious", [])
    db_hash    = _run_state.get("db_hash",    "N/A")

    try:
        from core.report_generator import ForensicReport
    except ImportError as e:
        log(f"  ✗ Import error: {e}")
        return {"success": False, "files": []}

    log(f"  → Compiling report data…")
    log(f"      Messages   : {len(messages):,}")
    log(f"      Red flags  : {len(suspicious):,}")
    log(f"      DB Hash    : {str(db_hash)[:24]}…")
    log("  → Generating PDF…")

    report = ForensicReport(case_id, investigator)
    report.output_dir = Path(output_folder)
    report.output_dir.mkdir(parents=True, exist_ok=True)

    # Pass empty list for deleted (removed from project)
    pdf_path = report.generate_report(messages, [], suspicious, db_hash)

    if pdf_path and Path(pdf_path).exists():
        size_kb = Path(pdf_path).stat().st_size // 1024
        log(f"  → PDF size: {size_kb:,} KB")
        log(f"  → Saved: {Path(pdf_path).name}")
        log("  ✓ Phase 6 complete — Forensic Report PDF generated")
        return {"success": True, "files": [str(pdf_path)]}
    else:
        log("  ✗ PDF generation failed")
        return {"success": False, "files": []}


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE RUNNERS LIST
# ──────────────────────────────────────────────────────────────────────────────
PHASE_RUNNERS = [
    run_phase_1, run_phase_2, run_phase_3,
    run_phase_4, run_phase_5, run_phase_6,
]


# ──────────────────────────────────────────────────────────────────────────────
#  OS HELPER
# ──────────────────────────────────────────────────────────────────────────────
def open_in_os(path: str):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open:\n{e}")


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE CARD WIDGET
# ──────────────────────────────────────────────────────────────────────────────
class PhaseCard(ctk.CTkFrame):
    STATUS_IDLE    = "idle"
    STATUS_RUNNING = "running"
    STATUS_DONE    = "done"
    STATUS_ERROR   = "error"

    STATUS_COLORS = {
        STATUS_IDLE:    TEXT_DIM,
        STATUS_RUNNING: ACCENT_AMBER,
        STATUS_DONE:    ACCENT_GREEN,
        STATUS_ERROR:   ACCENT_RED,
    }
    STATUS_ICONS = {
        STATUS_IDLE:    "○",
        STATUS_RUNNING: "◉",
        STATUS_DONE:    "✓",
        STATUS_ERROR:   "✗",
    }

    def __init__(self, parent, phase_data, **kwargs):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=10,
                         border_width=1, border_color="#252840", **kwargs)
        self.phase = phase_data
        self._build()

    def _build(self):
        self.grid_columnconfigure(2, weight=1)

        self.status_label = ctk.CTkLabel(
            self, text=self.STATUS_ICONS[self.STATUS_IDLE],
            font=("Segoe UI", 16),
            text_color=self.STATUS_COLORS[self.STATUS_IDLE],
            width=28
        )
        self.status_label.grid(row=0, column=0, rowspan=2, padx=(14, 6), pady=10)

        badge = ctk.CTkLabel(
            self, text=f"P{self.phase['id']}",
            font=("Courier New", 9, "bold"),
            text_color=ACCENT_BLUE, fg_color="#1A2040",
            corner_radius=4, width=26, height=18
        )
        badge.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(10, 0))

        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.grid(row=0, column=2, sticky="w", pady=(10, 0), padx=(0, 10))
        ctk.CTkLabel(name_frame, text=self.phase["icon"],
                     font=("Segoe UI", 13), text_color=TEXT_PRIMARY
                     ).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(name_frame, text=self.phase["name"],
                     font=FONT_PHASE, text_color=TEXT_PRIMARY
                     ).pack(side="left")

        ctk.CTkLabel(
            self, text=self.phase["desc"],
            font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w"
        ).grid(row=1, column=1, columnspan=2, sticky="w", padx=(0, 10), pady=(0, 10))

        self.progress = ctk.CTkProgressBar(
            self, height=3, corner_radius=2,
            progress_color=ACCENT_BLUE, fg_color=BG_INPUT
        )
        self.progress.set(0)

    def set_status(self, status: str):
        color = self.STATUS_COLORS[status]
        icon  = self.STATUS_ICONS[status]
        self.status_label.configure(text=icon, text_color=color)

        if status == self.STATUS_RUNNING:
            self.configure(border_color=ACCENT_BLUE)
            self.progress.grid(row=2, column=0, columnspan=3,
                               sticky="ew", padx=10, pady=(0, 8))
            self.progress.configure(mode="indeterminate",
                                    progress_color=ACCENT_AMBER)
            self.progress.start()
        elif status == self.STATUS_DONE:
            self.configure(border_color=ACCENT_GREEN)
            self.progress.stop()
            self.progress.configure(mode="determinate",
                                    progress_color=ACCENT_GREEN)
            self.progress.set(1)
        elif status == self.STATUS_ERROR:
            self.configure(border_color=ACCENT_RED)
            self.progress.stop()
            self.progress.configure(mode="determinate",
                                    progress_color=ACCENT_RED)
            self.progress.set(1)
        else:
            self.configure(border_color="#252840")
            try:
                self.progress.grid_forget()
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ──────────────────────────────────────────────────────────────────────────────
class SocialScopeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("SocialScope — Instagram DM Forensic Toolkit v3.0")
        self.geometry("1300x820")
        self.minsize(1100, 700)
        self.configure(fg_color=BG_MAIN)

        self.data_folder   = tk.StringVar(value="")
        self.case_id       = tk.StringVar(value="")
        self.investigator  = tk.StringVar(value="")
        self.output_folder = ""
        self.all_output_files: list[str] = []
        self.is_running    = False

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=66)
        header.pack(fill="x")
        header.pack_propagate(False)

        left_h = ctk.CTkFrame(header, fg_color="transparent")
        left_h.pack(side="left", padx=22, pady=10)
        ctk.CTkLabel(left_h, text="🔬", font=("Segoe UI", 26)).pack(side="left", padx=(0, 10))
        col = ctk.CTkFrame(left_h, fg_color="transparent")
        col.pack(side="left")
        ctk.CTkLabel(col, text="SocialScope",
                     font=("Segoe UI Semibold", 19, "bold"),
                     text_color=ACCENT_CYAN).pack(anchor="w")
        ctk.CTkLabel(col, text="Instagram DM Forensic Toolkit  •  v3.0  |  6-Phase Engine",
                     font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w")

        right_h = ctk.CTkFrame(header, fg_color="transparent")
        right_h.pack(side="right", padx=22)
        self.time_lbl = ctk.CTkLabel(right_h, text="",
                                      font=("Courier New", 11), text_color=TEXT_DIM)
        self.time_lbl.pack(anchor="e")
        self.core_lbl = ctk.CTkLabel(right_h, text="",
                                      font=FONT_SMALL, text_color=TEXT_DIM)
        self.core_lbl.pack(anchor="e")
        self._tick_clock()
        self._check_core()

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0, minsize=370)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left  = ctk.CTkFrame(body, fg_color=BG_PANEL, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        right = ctk.CTkFrame(body, fg_color=BG_MAIN, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_left(left)
        self._build_right(right)

        # Status bar
        bar = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_dot = ctk.CTkLabel(bar, text="●", font=("Segoe UI", 9),
                                        text_color=TEXT_DIM)
        self.status_dot.pack(side="left", padx=(14, 4))
        self.status_msg = ctk.CTkLabel(bar,
                                        text="Ready — fill case details and select the data folder",
                                        font=FONT_SMALL, text_color=TEXT_SECONDARY)
        self.status_msg.pack(side="left")

    def _build_left(self, parent):
        parent.grid_rowconfigure(5, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self._section_lbl(parent, "CASE DETAILS", 0)
        details = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                                border_width=1, border_color="#252840")
        details.grid(row=1, column=0, padx=18, sticky="ew", pady=(0, 4))
        details.grid_columnconfigure(0, weight=1)
        self._entry(details, "Case ID", "e.g.  CASE-2024-001", self.case_id, 0)
        self._entry(details, "Investigator Name", "Full name", self.investigator, 2)

        self._section_lbl(parent, "DATA SOURCE  (folder with direct.db or message_1.json)", 2)
        folder_card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                                   border_width=1, border_color="#252840")
        folder_card.grid(row=3, column=0, padx=18, sticky="ew", pady=(0, 4))
        folder_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(folder_card, text="Instagram Data Folder",
                     font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        row_f = ctk.CTkFrame(folder_card, fg_color="transparent")
        row_f.grid(row=1, column=0, padx=12, pady=(0, 14), sticky="ew")
        row_f.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(row_f, textvariable=self.data_folder,
                     placeholder_text="Click Browse…",
                     fg_color=BG_INPUT, border_color="#2A2D40",
                     text_color=TEXT_PRIMARY, font=FONT_SMALL, height=34
                     ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(row_f, text="Browse", width=76, height=34, font=FONT_SMALL,
                      fg_color="#252840", hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
                      command=self._browse_folder).grid(row=0, column=1)

        self._section_lbl(parent, "ANALYSIS PHASES", 4)
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", corner_radius=0,
                                         scrollbar_button_color=BG_CARD,
                                         scrollbar_button_hover_color=BG_HOVER)
        scroll.grid(row=5, column=0, sticky="nsew", padx=18, pady=(0, 10))
        scroll.grid_columnconfigure(0, weight=1)

        self.phase_cards: list[PhaseCard] = []
        for i, ph in enumerate(PHASES):
            card = PhaseCard(scroll, ph)
            card.grid(row=i, column=0, sticky="ew", pady=(0, 6))
            self.phase_cards.append(card)

        self.run_btn = ctk.CTkButton(
            parent, text="⚡  Run Full Analysis",
            height=50, font=("Segoe UI Semibold", 14, "bold"),
            fg_color=ACCENT_BLUE, hover_color="#2D5AD4",
            text_color="white", corner_radius=10,
            command=self._start_analysis
        )
        self.run_btn.grid(row=6, column=0, padx=18, pady=(0, 18), sticky="ew")

    def _build_right(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 8))
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="ANALYSIS LOG",
                     font=("Courier New", 10, "bold"),
                     text_color=ACCENT_BLUE).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(hdr, text="Clear", width=60, height=24, font=FONT_SMALL,
                      fg_color="transparent", border_width=1, border_color="#252840",
                      text_color=TEXT_SECONDARY, hover_color=BG_HOVER,
                      command=self._clear_log).grid(row=0, column=2, sticky="e")

        log_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                                  border_width=1, border_color="#1E2135")
        log_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 14))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(log_frame, fg_color="transparent",
                                       text_color=TEXT_PRIMARY, font=FONT_MONO,
                                       wrap="word", state="disabled",
                                       scrollbar_button_color=BG_PANEL,
                                       scrollbar_button_hover_color=BG_HOVER)
        self.log_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Output files panel
        self.output_panel = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                                          border_width=1, border_color="#252840")
        self.output_panel.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))
        self.output_panel.grid_columnconfigure(0, weight=1)
        self.output_panel.grid_remove()

        phdr = ctk.CTkFrame(self.output_panel, fg_color="transparent")
        phdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))
        phdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(phdr, text="📁  Generated Output Files",
                     font=("Segoe UI Semibold", 12, "bold"),
                     text_color=ACCENT_GREEN).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(phdr, text="Open Output Folder  →",
                      width=150, height=28, font=FONT_SMALL,
                      fg_color=ACCENT_GREEN, hover_color="#00B25A",
                      text_color="#000",
                      command=self._open_output_folder
                      ).grid(row=0, column=2, sticky="e")

        self.files_frame = ctk.CTkFrame(self.output_panel, fg_color="transparent")
        self.files_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        self._write_log(self._banner())

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _section_lbl(self, parent, text, row):
        ctk.CTkLabel(parent, text=text,
                     font=("Courier New", 10, "bold"), text_color=ACCENT_BLUE
                     ).grid(row=row, column=0, padx=18, pady=(18, 6), sticky="w")

    def _entry(self, parent, label, placeholder, var, row):
        ctk.CTkLabel(parent, text=label, font=FONT_SMALL,
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=row, column=0, padx=14, pady=(12, 4), sticky="w")
        ctk.CTkEntry(parent, textvariable=var, placeholder_text=placeholder,
                     fg_color=BG_INPUT, border_color="#2A2D40",
                     text_color=TEXT_PRIMARY, font=FONT_LABEL, height=36
                     ).grid(row=row+1, column=0, padx=12, pady=(0, 8), sticky="ew")

    def _banner(self):
        return (
            "╔══════════════════════════════════════════════════════╗\n"
            "║    SocialScope Forensic Toolkit  v1.0                ║\n"
            "║    Instagram DM Analysis — 6-Phase Engine            ║\n"
            "╚══════════════════════════════════════════════════════╝\n\n"
            "  Phases  :  P1 Parse → P2 Timeline → P3 Alerts\n"
            "             P4 Hash/EXIF → P5 Network → P6 PDF\n\n"
            "  To start :  Fill case details → Browse folder → Run\n\n"
            "──────────────────────────────────────────────────────\n"
        )

    def _check_core(self):
        try:
            from core import parser as _p  # noqa
            self.core_lbl.configure(text="core/ ✓ imported", text_color=ACCENT_GREEN)
        except ImportError:
            self.core_lbl.configure(text="⚠ core/ not found", text_color=ACCENT_AMBER)

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Instagram Data Folder")
        if folder:
            self.data_folder.set(folder)
            json_found = list(Path(folder).rglob("message_*.json"))
            db_found   = list(Path(folder).rglob("direct.db"))
            if json_found:
                self._set_status(f"✓ JSON export found ({len(json_found)} file(s))", ACCENT_GREEN)
            elif db_found:
                self._set_status(f"✓ direct.db found — ready", ACCENT_GREEN)
            else:
                self._set_status("⚠  No data found — need direct.db or message_1.json", ACCENT_AMBER)

    def _start_analysis(self):
        if not self.case_id.get().strip():
            messagebox.showwarning("Missing", "Please enter a Case ID.")
            return
        if not self.investigator.get().strip():
            messagebox.showwarning("Missing", "Please enter Investigator Name.")
            return
        if not self.data_folder.get().strip() or not os.path.isdir(self.data_folder.get()):
            messagebox.showwarning("Missing", "Please select a valid data folder.")
            return
        if self.is_running:
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_folder = os.path.join(
            self.data_folder.get(),
            f"SocialScope_Output_{self.case_id.get().strip()}_{ts}"
        )
        os.makedirs(self.output_folder, exist_ok=True)

        self.all_output_files.clear()
        self.is_running = True
        self.run_btn.configure(state="disabled",
                               text="⏳  Analysis Running…",
                               fg_color="#1A2D6B")
        self.output_panel.grid_remove()
        for card in self.phase_cards:
            card.set_status(PhaseCard.STATUS_IDLE)

        self._clear_log()
        self._write_log(self._banner())
        threading.Thread(target=self._analysis_thread, daemon=True).start()

    def _analysis_thread(self):
        cid  = self.case_id.get().strip()
        inv  = self.investigator.get().strip()
        dfol = self.data_folder.get().strip()
        ofol = self.output_folder

        self._log("┌─ CASE INITIATED ─────────────────────────────────────────")
        self._log(f"│  Case ID      : {cid}")
        self._log(f"│  Investigator : {inv}")
        self._log(f"│  Data Folder  : {dfol}")
        self._log(f"│  Output Dir   : {Path(ofol).name}")
        self._log(f"│  Started      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log("└──────────────────────────────────────────────────────────\n")
        self._set_status("Analysis running…", ACCENT_AMBER)

        success_count = 0
        all_files: list[str] = []

        for i, (phase, runner) in enumerate(zip(PHASES, PHASE_RUNNERS)):
            self._set_card(i, PhaseCard.STATUS_RUNNING)
            self._log(f"━━ Phase {phase['id']} / {len(PHASES)}  {phase['icon']}  {phase['name']}")
            try:
                result = runner(cid, inv, dfol, ofol, self._log)
                if result.get("success"):
                    self._set_card(i, PhaseCard.STATUS_DONE)
                    new_files = [f for f in result.get("files", [])
                                 if f and Path(f).exists()]
                    all_files.extend(new_files)
                    success_count += 1
                else:
                    self._set_card(i, PhaseCard.STATUS_ERROR)
                    self._log(f"  ✗ Phase {phase['id']} failed\n")
            except Exception as exc:
                self._set_card(i, PhaseCard.STATUS_ERROR)
                import traceback
                self._log(f"  ✗ EXCEPTION: {exc}")
                self._log(f"  {traceback.format_exc().splitlines()[-1]}\n")

        self.all_output_files = all_files
        self._finish(success_count, len(PHASES))

    def _finish(self, success_count, total):
        all_ok = success_count == total
        self._log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if all_ok:
            self._log(f"  ✅  ALL {total} PHASES COMPLETED SUCCESSFULLY")
        else:
            self._log(f"  ⚠️   {success_count}/{total} phases completed")
        self._log(f"  📁  Output: {self.output_folder}")
        self._log(f"  🕒  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        color = ACCENT_GREEN if all_ok else ACCENT_AMBER
        text  = ("✓ Analysis complete — all phases passed" if all_ok else
                 f"Done with {total - success_count} error(s)")
        self._set_status(text, color)
        self.after(0, self._show_output_panel)
        self.is_running = False
        self.after(0, lambda: self.run_btn.configure(
            state="normal", text="⚡  Run Full Analysis", fg_color=ACCENT_BLUE))

    def _show_output_panel(self):
        for w in self.files_frame.winfo_children():
            w.destroy()

        ICONS = {".pdf": "📄", ".csv": "📊", ".json": "📋",
                 ".html": "🌐", ".png": "🖼️", ".txt": "📝"}
        for i, fp in enumerate(self.all_output_files or []):
            ext  = Path(fp).suffix.lower()
            icon = ICONS.get(ext, "📎")
            ctk.CTkButton(
                self.files_frame,
                text=f"{icon}  {Path(fp).name}",
                font=FONT_SMALL, height=30,
                fg_color=BG_INPUT, hover_color=BG_HOVER,
                text_color=TEXT_PRIMARY,
                border_width=1, border_color="#2A2D40",
                anchor="w",
                command=lambda p=fp: open_in_os(p)
            ).grid(row=i//2, column=i%2, padx=(0, 6), pady=3, sticky="ew")

        self.files_frame.grid_columnconfigure(0, weight=1)
        self.files_frame.grid_columnconfigure(1, weight=1)
        self.output_panel.grid()

    def _open_output_folder(self):
        if self.output_folder and os.path.isdir(self.output_folder):
            open_in_os(self.output_folder)

    def _log(self, msg: str):
        self.after(0, lambda m=msg: self._write_log(m + "\n"))

    def _write_log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _set_card(self, index: int, status: str):
        self.after(0, lambda i=index, s=status: self.phase_cards[i].set_status(s))

    def _set_status(self, msg: str, color: str = TEXT_SECONDARY):
        self.after(0, lambda: self.status_msg.configure(text=msg, text_color=color))
        self.after(0, lambda: self.status_dot.configure(text_color=color))

    def _center_window(self):
        self.update_idletasks()
        w, h   = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _tick_clock(self):
        self.time_lbl.configure(text=datetime.now().strftime("%d %b %Y   %H:%M:%S"))
        self.after(1000, self._tick_clock)


# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    missing = []
    for pkg, pip_name in [
        ("customtkinter", "customtkinter"),
        ("yaml",          "pyyaml"),
        ("reportlab",     "reportlab"),
        ("networkx",      "networkx"),
        ("plotly",        "plotly"),
        ("pandas",        "pandas"),
        ("PIL",           "pillow"),
        ("rich",          "rich"),
    ]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"\n[ERROR] Missing packages: {', '.join(missing)}")
        print(f"Run: pip install {' '.join(missing)}\n")
        sys.exit(1)

    app = SocialScopeApp()
    app.mainloop()