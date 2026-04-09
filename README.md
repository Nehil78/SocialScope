# 🔬 SocialScope Forensic Toolkit

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Mac-lightgrey?style=for-the-badge)


**A professional Instagram DM Forensic Analysis Tool**  
*Automatically extract, analyse, and report digital evidence from Instagram data*

</div>

---

## 📌 Overview

**SocialScope Forensic Toolkit** is a Python-based digital forensic tool designed for law enforcement and security researchers to analyse Instagram Direct Messages. It processes raw Instagram data (SQLite database or official JSON export) and generates a court-admissible PDF forensic report — all with a single click.

> ⚠️ **Disclaimer:** This tool is intended for **legal forensic investigations only**. Unauthorized use of this tool on data you do not own or have explicit permission to analyse is illegal. The developers are not responsible for misuse.

---

## 🖥️ GUI Preview

```
╔══════════════════════════════════════════════════════╗
║    SocialScope Forensic Toolkit  v1.0                ║
║    Instagram DM Analysis — 6-Phase Engine            ║
╚══════════════════════════════════════════════════════╝
```

- Modern dark-themed interface (CustomTkinter)
- Real-time analysis log with phase-by-phase progress
- One-click full analysis
- Clickable output file links after completion

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📥 **Dual Source Support** | Parses both `direct.db` (SQLite) and Instagram JSON export |
| 📊 **Master Timeline** | Chronological CSV of all messages with proper timestamps |
| 🚨 **Keyword & Sentiment Alert** | Flags suspicious/aggressive messages using configurable keywords |
| 🔐 **SHA-256 Integrity** | Cryptographic hash verification of evidence files |
| 🖼️ **EXIF Extraction** | GPS coordinates, camera model, and datetime from images |
| 🕸️ **Network Graph** | Interactive HTML visualization of communication network |
| 📄 **PDF Forensic Report** | Professional 8-section court-admissible report |
| 🎨 **Modern GUI** | Dark-themed CustomTkinter interface with real-time logs |

---

## 📁 Project Structure

```
SocialScope-Forensic-Toolkit/
│
├── SocialScope_GUI_FINAL.py    # Main GUI application (entry point)
│
├── config/
│   └── config.yaml             # Keywords, phrases, settings
│
├── core/
│   ├── __init__.py
│   ├── parser.py               # Phase 1 — Instagram data parsing
│   ├── timeline.py             # Phase 2 — Master timeline builder
│   ├── keyword_alert.py        # Phase 3 — Keyword & sentiment analysis
│   ├── media_extractor.py      # Phase 4 — SHA-256 hash + EXIF metadata
│   ├── network_graph.py        # Phase 5 — Network link analysis
│   └── report_generator.py    # Phase 6 — PDF forensic report
│
├── output/                     # Auto-created during analysis
│   ├── timeline_YYYYMMDD.csv
│   ├── alerts_YYYYMMDD.csv
│   ├── file_hashes.csv
│   ├── network_graph.html
│   └── FORENSIC_REPORT_*.pdf
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1 — Clone the repository
```bash
git clone https://github.com/yourusername/SocialScope-Forensic-Toolkit.git
cd SocialScope-Forensic-Toolkit
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Run the application
```bash
python SocialScope_GUI_FINAL.py
```

---

## 📦 Requirements

```
customtkinter>=5.2.0
pyyaml>=6.0
reportlab>=4.0
networkx>=3.0
plotly>=5.0
pandas>=2.0
Pillow>=10.0
rich>=13.0
```

Install all at once:
```bash
pip install customtkinter pyyaml reportlab networkx plotly pandas pillow rich
```

---

## 🚀 How to Use

### Step 1 — Prepare your data
You need one of the following:

**Option A — Instagram JSON Export (Recommended)**
1. Open Instagram → Settings → Your Activity
2. Download Your Information → Messages → JSON format
3. Extract the ZIP file

**Option B — Direct Database**
- Locate `direct.db` from the device
- Place it in a folder

### Step 2 — Launch the tool
```bash
python SocialScope_GUI_FINAL.py
```

### Step 3 — Fill case details
- Enter **Case ID** (e.g., `CASE-2024-001`)
- Enter **Investigator Name**
- Click **Browse** → select your data folder

### Step 4 — Run analysis
- Click **⚡ Run Full Analysis**
- Watch real-time progress in the log panel
- All output files appear as clickable buttons when done

---

## 🔍 6-Phase Analysis Engine

```
Phase 1 ──► Instagram Parsing
              ↓
Phase 2 ──► Master Timeline + CSV
              ↓
Phase 3 ──► Keyword & Sentiment Alert
              ↓
Phase 4 ──► SHA-256 Hash + EXIF
              ↓
Phase 5 ──► Network Link Analysis
              ↓
Phase 6 ──► PDF Forensic Report
```

### Phase 1 — Instagram Parsing (`parser.py`)
- Auto-detects JSON export or SQLite `direct.db`
- Handles microsecond timestamps (Instagram format)
- Identifies sender vs recipient using `is_sent_by_viewer` flag
- Extracts: sender, message text, timestamp, thread ID, message type

### Phase 2 — Master Timeline (`timeline.py`)
- Builds chronological DataFrame using Pandas
- Sorts all messages oldest to newest
- Exports to CSV (Excel-compatible)

### Phase 3 — Keyword & Sentiment Alert (`keyword_alert.py`)
- Scans all messages against configurable keyword watchlist
- Two-level classification: **Suspicious** and **Aggressive**
- Exports flagged messages to `alerts.csv`
- Fully customizable via `config/config.yaml`

### Phase 4 — SHA-256 Hash + EXIF (`media_extractor.py`)
- Computes SHA-256 hash of `direct.db` for integrity verification
- Scans and hashes all media files
- Extracts EXIF metadata: GPS coordinates, camera model, datetime
- Exports to `file_hashes.csv` and `exif_metadata.csv`

### Phase 5 — Network Link Analysis (`network_graph.py`)
- Builds communication graph using NetworkX
- Spring layout algorithm for natural clustering
- Node size proportional to message count
- Exports interactive HTML visualization using Plotly

### Phase 6 — PDF Forensic Report (`report_generator.py`)
- Professional A4 PDF with 8 sections
- Running header/footer on every page
- Color-coded suspicious message highlighting
- Investigator certification and signature block
- Court-admissible format

---

## 📄 PDF Report Sections

| Section | Content |
|---------|---------|
| **Cover Page** | Case ID, investigator, classification banner, statistics |
| **1. Investigation Details** | Full case metadata, tool version, hash |
| **2. Executive Summary** | Narrative summary, date range, participant count |
| **3. Participant Details** | Username, message count, role table |
| **4. Red Flag Messages** | Suspicious/aggressive messages highlighted in red |
| **5. Complete Timeline** | All messages in chronological table |
| **6. Deleted/Recovered** | Recovered data (if available) |
| **7. Integrity Verification** | SHA-256 hash, chain of custody |
| **8. Investigator Certification** | Signature block, date, legal declaration |

---

## ⚙️ Configuration

Edit `config/config.yaml` to customize keywords:

```yaml
general:
  version: "3.0"
  timezone: "Asia/Kolkata"

red_flags:
  keywords:
    - kill
    - murder
    - bomb
    - drug
    - payment
    - bitcoin
    - lsd
    - ak47
    - maar
    - khatam
  phrases:
    - "khatam kar denge"
    - "milte hain"
    - "delivery krni"
```

> Add your own keywords without touching any Python code.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           GUI Layer                     │
│   SocialScope_GUI_FINAL.py              │
│   CustomTkinter + Threading             │
└──────────────┬──────────────────────────┘
               │ orchestrates
┌──────────────▼──────────────────────────┐
│           Core Layer                    │
│   parser → timeline → keyword_alert     │
│   → media_extractor → network_graph     │
│   → report_generator                    │
└──────────────┬──────────────────────────┘
               │ reads / writes
┌──────────────▼──────────────────────────┐
│           Data Layer                    │
│   _run_state{}  (shared pipeline state) │
│   direct.db / message_*.json (input)    │
│   CSV, HTML, PDF (output)               │
└─────────────────────────────────────────┘
```

**Design Patterns Used:**
- **Pipeline Pattern** — data flows through phases via `_run_state`
- **Observer Pattern** — log callback from backend to GUI
- **Strategy Pattern** — dual parser (JSON vs SQLite)
- **Single Responsibility** — each module has one job

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| `Python 3.8+` | Core language |
| `CustomTkinter` | Modern dark-themed GUI |
| `SQLite3` | Instagram database parsing |
| `Pandas` | Data processing and CSV export |
| `ReportLab` | Professional PDF generation |
| `NetworkX` | Graph theory and link analysis |
| `Plotly` | Interactive HTML visualization |
| `Hashlib` | SHA-256 cryptographic hashing |
| `Pillow` | Image processing and EXIF extraction |
| `PyYAML` | Configuration file parsing |
| `Rich` | Terminal output formatting |
| `Threading` | Non-blocking GUI analysis |

---

## 📊 Data Flow Diagram

```
Instagram Data (direct.db / JSON)
           │
           ▼
    ┌─────────────┐
    │  Phase 1    │──► messages[] ──► _run_state
    │  Parser     │
    └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  Phase 2    │──► timeline.csv
    │  Timeline   │
    └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  Phase 3    │──► alerts.csv ──► _run_state[suspicious]
    │  Keywords   │
    └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  Phase 4    │──► file_hashes.csv, exif.csv
    │  Hash+EXIF  │──► _run_state[db_hash]
    └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  Phase 5    │──► network_graph.html
    │  Network    │
    └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  Phase 6    │──► FORENSIC_REPORT.pdf
    │  PDF Report │    (uses all _run_state data)
    └─────────────┘
```

---

## 🔒 Forensic Principles

This tool follows key digital forensic principles:

- **Evidence Integrity** — SQLite opened in read-only mode (`?mode=ro`)
- **Chain of Custody** — Investigator name, date, and case ID logged
- **Hash Verification** — SHA-256 hash of all evidence files
- **Non-destructive** — Original data never modified
- **Auditability** — Full analysis log preserved
- **Reproducibility** — Network graph uses fixed `seed=42`

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `core/ not found` | Place `SocialScope_GUI_FINAL.py` in project root folder |
| `No messages parsed` | Check if `direct.db` has a `messages` table |
| `PDF generation failed` | Run `pip install reportlab` |
| `Import error: networkx` | Run `pip install networkx plotly` |
| `Timestamps wrong` | Instagram uses microseconds — handled automatically |
| `Sender shows ID not name` | Username not stored in `direct.db` — use JSON export |

---

## 🙏 Acknowledgements

- [ReportLab](https://www.reportlab.com/) — PDF generation
- [NetworkX](https://networkx.org/) — Graph analysis
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern GUI
- [Plotly](https://plotly.com/) — Interactive visualization

---

<div align="center">

**⭐ Star this repo if you found it useful!**

*Built with ❤️ for digital forensics education*

</div>
