# ⚙️ SolidWorks 2025 Parametric 3D CAD & ISO Automation Skill

[![SolidWorks](https://img.shields.io/badge/SolidWorks-2025-blue.svg)](https://www.solidworks.com/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![COM API](https://img.shields.io/badge/API-pywin32%20COM-informational.svg)](https://github.com/mhammond/pywin32)
[![Quality](https://img.shields.io/badge/ISO-9001%3A2015%20(8.3.6)-success.svg)](https://www.iso.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade, battle-tested engineering skill and automation framework for generating **100% parametric B-Rep 3D CAD models (zero polygon meshes)**, automating **STL-to-CAD reverse engineering**, modeling **standard plastic bottle/closure threads (SPI / ISBT)**, executing **ground-truth anti-hallucination audits**, and generating **official ISO manufacturing drawings (ISO/ANSI format)** in **SolidWorks 2025** via Python COM (`pywin32`).

---

## 🚀 Key Capabilities

1. **100% Parametric B-Rep Solids & Fully Defined Sketches:**
   - Full Feature Tree generation (`SketchManager`, `FeatureManager`, `Extrusion`, `Revolve`, `Fillet`, `Chamfer`, `Loft`, `Shell`).
   - Mandatory **100% Fully Constrained Sketches (Black Lines / Zero Blue Lines)**: mathematical constraint hierarchy, origin anchoring, baseline driving dimensions, and status auditing (`is_fully_defined()`).
2. **Editable Native Plastic Threads (Helix & Sweep — Zero Rigid Splines):**
   - Parametric Modified Buttress Style "M" ($45^\circ / 10^\circ$) threads.
   - Built-in library: SP-400, SP-410, SP-415 with runout relief and proper lead-in taper via [`scripts/sw_thread_helper.py`](./scripts/sw_thread_helper.py).
   - Modeled exclusively with native **`InsertHelix` (10 parameters)** + **`InsertProtrusionSwept4`** for total GUI editability by human designers.
3. **Zero-Distraction Isolated Background CAD Tasks:**
   - Models run invisibly in memory using `DocumentVisible(False)` / `BackgroundCADSession` without stealing focus or altering the user's active document window.
   - Native Windows GUI launcher ([`scripts/run_silent.vbs`](./scripts/run_silent.vbs) + `wscript.exe`) guarantees **100% hidden execution with ZERO CMD console popups**.
4. **Ground-Truth Geometric Audit Tool ([`scripts/sw_model_auditor.py`](./scripts/sw_model_auditor.py)):**
   - Read-only CAD inspection tool verifying the **6 physical invariants**:
     - Exact database dimension validation (avoids visual false positives).
     - Detection of unapproved feature suppressions (`suppressed_features == 0`).
     - Zero surface leaks (`surface_bodies == 0`, strictly closed solids).
     - DFM wall thickness & volume ratio verification (flags solidifications).
     - Bounding box shift verification.
     - **Invariant 6: Zero under-defined sketches** (`under_defined_sketches == []`).
5. **Automated 2D ISO Drawings (ISO/ANSI Format):**
   - Automated layout on ANSI Letter Landscape ($279.4 \times 215.9\text{ mm}$).
   - Physical title block and border insertion via `SetupSheet5` with `a_landscape.slddrt`.
   - Dynamic auto-scaling ($1:1, 1:2, 1:4, 1:5$), centered orthogonal views, and shaded isometric view.
6. **Interactive Windows Sandbox Desktop Bridge:**
   - [`scripts/run_in_interactive_session.ps1`](./scripts/run_in_interactive_session.ps1) resolves the Windows `MK_E_UNAVAILABLE` sandbox COM isolation by bridging tasks into the interactive user desktop.
   - Ephemeral scheduled tasks with folder-hashed names, automatic `.bmp` to `.png` conversion, and rotating COM journals (`swxJRNL.swj`).
7. **MecAgent Architecture (Prompt-to-CAD):**
   - Live context inspector ([`scripts/sw_context_inspector.py`](./scripts/sw_context_inspector.py)) reading active models, selections, and features in $O(1)$.
   - Protected runner ([`scripts/sw_prompt_runner.py`](./scripts/sw_prompt_runner.py)) with structured self-healing JSON diagnostics.

---

## 📁 Repository Structure

```
solidworks-parametric-cad/
│
├── SKILL.md                               # Main agent skill definition & instructions
├── README.md                              # Repository overview & usage documentation
├── requirements.txt                       # Python dependencies (pywin32, ezdxf, etc.)
├── .gitignore                             # Ignored temporaries, logs, and journals
│
├── scripts/                               # Core Python & PowerShell automation scripts
│   ├── sw_model_auditor.py                # Universal ground-truth geometric model auditor
│   ├── sw_context_inspector.py            # Real-time SolidWorks selection & tree inspector
│   ├── sw_prompt_runner.py                # Prompt-to-CAD interactive execution & capture runner
│   ├── sw_thread_helper.py                # SPI-400/410/415 parametric plastic thread generator
│   ├── sw_base_template.py                # Production template with fully constrained sketches
│   └── run_in_interactive_session.ps1    # Ephemeral interactive session desktop bridge
│
├── references/                            # Engineering guides, protocols & API references
│   ├── cad_modification_audit_protocol.md # 5 physical invariants audit protocol & post-mortem
│   ├── drawing_iso_automation.md        # ISO-7200 drawing automation & SetupSheet5 implementation
│   ├── plastic_threads_spi_standards.md   # SPI / GPI / ISBT plastic closure standards
│   ├── reverse_engineering_stl_to_brep.md # STL slicing, extrema fitting & B-Rep reconstruction
│   ├── dfm_plastic_injection_and_blow_molding.md # DFM guidelines for plastics
│   ├── solidworks_2025_com_api.md         # Full pywin32 COM API signature reference
│   ├── sandbox_desktop_bridge.md          # Technical analysis of Windows COM sandbox bridge
│   ├── prompt_to_cad_architecture.md      # AI agent prompt-to-CAD closed-loop design
│   └── photogrammetry_and_loft_geometry.md# Hermite C1 lofts and photogrammetric calibration
│
└── examples/
    └── multi_body_enclosure_example.md        # Industrial dual-body enclosure with rigid housing and sealing gasket
```

---

## ⚡ Prerequisites

1. **Operating System:** Windows 10 / 11 (64-bit).
2. **CAD Software:** SolidWorks 2025 SP0 or later (active interactive session).
3. **Python:** Python 3.10 - 3.12 (64-bit).
4. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🛠️ Usage

### 1. Ground-Truth Geometric Audit
Inspect any `.SLDPRT` file in read-only mode to verify dimensions and ensure zero broken surfaces or suppressed features:
```bash
python scripts/sw_model_auditor.py "path/to/model.SLDPRT" --baseline "path/to/base.SLDPRT" --params "D1@Croquis1,D2@Croquis2"
```

### 2. Live Context Inspection
Inspect the active document, selected faces/edges, and feature tree in real time ($O(1)$ complexity):
```bash
python scripts/sw_context_inspector.py
```

### 3. Running Interactive CAD Scripts via Desktop Bridge
Execute parametric generation scripts inside the user's interactive session from any shell or sandboxed environment:
```powershell
powershell -ExecutionPolicy Bypass -File "scripts/run_in_interactive_session.ps1" -WorkDir "path/to/project_folder" -ScriptName "build_sw.py"
```

---

## ⚡ Performance Rules (High CPU & Zombie Prevention)

- **Strict Rule:** NEVER call `win32com.client.Dispatch("SldWorks.Application")` in background loops (it spawns invisible zombie `SLDWORKS.exe` processes). ALWAYS connect via `win32com.client.GetActiveObject("SldWorks.Application")`.
- **Zero Busy Waiting:** Background loops must use events or native timeouts. Do not invoke `gc.collect()` inside high-frequency polling.
- **Complexity:** All context queries and inspection routines run in $O(1)$ or $O(N)$ with respect to the immediate feature tree.

---

## 📜 Quality Standards & Norms

- **ISO 9001:2015:** Clause 8.3.6 (Design and Development Changes Control).
- **ISO 7200 / ASME Y14:** Technical product documentation - Title blocks and drawing layout.
- **Packaging Standards:** SPI (Society of the Plastics Industry) / ISBT / GPI Closure Standards.

---

*SolidWorks 2025 Parametric CAD Automation Toolkit*
