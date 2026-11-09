---
name: solidworks-parametric-cad
description: >-
  Generate parametric 3D B-Rep models (.SLDPRT, .STEP), reverse engineer meshes (.STL to CAD),
  automate plastic threads (SPI-400/410/415), and generate ISO drawings (.SLDDRW ISO-7200)
  in SolidWorks 2025 via the Python COM API (pywin32) and ezdxf.
---

# SolidWorks 2025 Parametric 3D CAD, Reverse Engineering & ISO Drawings Skill

This skill provides a complete, battle-tested engineering workflow for generating **100% parametric B-Rep 3D solids (zero meshes)** in **SolidWorks 2025** via `pywin32` COM automation, including **STL-to-CAD reverse engineering**, **standard plastic bottle/closure threads (SPI / ISBT)**, **fully constrained sketches**, and **automated technical drawings (ISO/ANSI format)**.

---

## 1. Prerequisites & Environment Checklist

Before writing or running any SolidWorks script, verify the following requirements:

1. **SolidWorks 2025 Active Session:**
   - SolidWorks (`SLDWORKS.exe`) must be open in the user's interactive Windows session.
   - **Strict Rule (`AGENTS.md`):** **NEVER** call `win32com.client.Dispatch("SldWorks.Application")` in background scripts or loops (it spawns invisible zombie `SLDWORKS.exe` processes that exhaust GDI and CPU). **ALWAYS** connect to the active instance via `win32com.client.GetActiveObject("SldWorks.Application")`.
2. **Python Packages:**
   - `pywin32` (`pythoncom`, `win32com.client`, `VARIANT`)
   - `ezdxf` (for 2D `.dxf` curve generation)
   - `trimesh` & `shapely` (for STL slicing, polygon simplification, and reverse engineering)
   - `Pillow` (`PIL.Image`, for converting SolidWorks `.bmp` captures to `.png` and photogrammetric calibration)
3. **Interactive Session Bridge (Windows Sandbox / `exebox`):**
   - Agent commands executed via `run_command` run inside a sandboxed desktop (`exebox-...`) whose COM Running Object Table (ROT) is isolated from the interactive `Default` desktop where SolidWorks runs.
   - Calling `GetActiveObject` directly inside `run_command` fails with `MK_E_UNAVAILABLE (-2147221021)`.
   - **Always execute SolidWorks scripts via an interactive Scheduled Task** using [run_in_interactive_session.ps1](./scripts/run_in_interactive_session.ps1) (see [Sandbox Desktop Bridge Reference](./references/sandbox_desktop_bridge.md)).

---

## 2. Standard Architecture for CAD Projects

Organize each part under `tools/cad/<part_name>/`:

| File | Responsibility |
| :--- | :--- |
| `params.py` | Master dictionary `P` of all engineering dimensions (in **mm**), resin shrinkage, and analytical profiles. |
| `build_sw.py` | Connects to SolidWorks 2025, builds the parametric B-Rep feature tree, verifies mass/volume, and exports `.SLDPRT`, `.STEP`, and orthogonal views. Start from [sw_base_template.py](./scripts/sw_base_template.py). |
| `export_dxf.py` | Standalone `ezdxf` script that exports 2D construction curves organized by layers (`PLANTA`, `LATERAL`, `REVOLUCION`, `SECCIONES`, `EJES`). |
| `run_build.bat` | Batch launcher invoked by the interactive Windows Scheduled Task. |

---

## 3. Step-by-Step Engineering Workflow

### Step 1: Input Analysis & Geometry Extraction
- **Case A: Engineering Drawings or Photos:** Follow [Photogrammetry & Loft Geometry Guide](./references/photogrammetry_and_loft_geometry.md). Overlay pixel grids, calculate scale factor ($\text{px}/\text{mm}$), and extract stations $X, Y, Z$.
- **Case B: Raw Polygon Mesh (`.STL` / Scan):** Follow [Subhabilidad: Ingeniería Inversa STL a B-Rep](./references/reverse_engineering_stl_to_brep.md). Align the mesh to the Z-axis via SVD/PCA, slice axially with `trimesh.section`, and separate the smooth base revolution wall from the helical thread path. If the scan is noisy (e.g. silicone internal cast), apply **Straight-Line Peak/Extrema Fitting** to replace rough polylines with clean tangent segments on the functional extrema (liner seat, retention bead, thread crest/root) to ensure smooth, manufacturable toolpaths.
- **Case C: Neutral CAD Formats (`.STEP` / `.IGES`):** In SolidWorks 2025, do **not** use `OpenDoc6` on neutral files (it fails with `Errors=2097152`). Always import using `doc = sw.LoadFile4(step_path, "", NOTHING, err)` where `NOTHING = VARIANT(pythoncom.VT_DISPATCH, None)`. Inspect bodies via `doc.GetBodies2(0, True)`.

### Step 2: 2D DXF Curve Verification (`export_dxf.py`)
1. Implement `params.py` and `export_dxf.py`.
2. Run `python export_dxf.py` directly to validate all analytical curves and preview 2D contours before touching SolidWorks.

### Step 3: Parametric 3D B-Rep Modeling (`build_sw.py`)
1. Copy or adapt [sw_base_template.py](./scripts/sw_base_template.py).
2. Follow the mandatory SolidWorks 2025 COM API rules in [SolidWorks 2025 COM API Reference](./references/solidworks_2025_com_api.md):
   - **Fully Constrained Sketches (Black Lines):** Draw entities in database mode (`AddToDB = True`), switch to interactive mode (`AddToDB = False`), call `auto_constrain_segments()`, apply explicit relations (`sgHORIZONTAL2D`, `sgVERTICAL2D`, `sgCOINCIDENT`, `sgCOLINEAR`), add driving dimensions linked to `EquationMgr`, and close with `fully_define(use_relations=True, use_dimensions=True)`.
   - **Plastic Bottle & Cap Threads (SPI / GPI / ISBT):** Import [sw_thread_helper.py](./scripts/sw_thread_helper.py) and consult [Subhabilidad: Roscas Plásticas SPI](./references/plastic_threads_spi_standards.md). Always model the Modified Buttress Style "M" ($45^\circ / 10^\circ$) thread with helix sweep, $0.4\text{ mm}$ wall overlap, and end runout relief.
   - **DFM Guidelines for Plastics:** Consult [Subhabilidad: DFM Plástico](./references/dfm_plastic_injection_and_blow_molding.md) for sealing lips (olive/bore seal, crab's claw), tamper-evident bridge bands, draft angles ($1^\circ$), and resin shrinkages/weights (PP, HDPE, PET).
   - Convert all millimeters to **meters** (`m(v) = v * 0.001`) and degrees to **radians**.
   - Discover standard planes (`[Front, Top, Right]`) by iterating `doc.FirstFeature` / `GetNextFeature` where `_v(f.GetTypeName2) == "RefPlane"`.
   - Wrap zero-arg COM members with `_v(x)` (`x() if isinstance(x, types.MethodType) else x`).

### Step 4: Verification, Mass Audit & Orthogonal Captures
1. Run `build_sw.py` through [run_in_interactive_session.ps1](./scripts/run_in_interactive_session.ps1):
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/skills/solidworks-parametric-cad/scripts/run_in_interactive_session.ps1" -WorkDir "tools\cad\<part_name>"
   ```
2. Verify in `out/build_log.txt`:
   - `EXIT=0`.
   - Body count, name, and exact tessellated bounding box (`exact_body_bounds_mm`).
   - Volumetric discrepancy vs. STL ($< 1\%$) and accurate part weight in grams.
3. Inspect `planta.png`, `alzado.png`, `lateral.png`, `inferior.png`, and `iso.png`.

### Step 4b: Mandatory Ground-Truth Geometric Audit (Anti-Hallucination Protocol)
> [!CAUTION]
> **NUNCA dar por exitosa una modificación por mensajes de consola ("SUCCESS") o diferencias de píxeles visuales.**
> Consulte el protocolo estricto en [Protocolo de Auditoría Geométrica Real](./references/cad_modification_audit_protocol.md).
>
> Ejecute siempre en solo lectura [sw_model_auditor.py](./scripts/sw_model_auditor.py) sobre el archivo final guardado en disco:
> ```powershell
> python .agents/skills/solidworks-parametric-cad/scripts/sw_model_auditor.py "ruta\al\modelo.SLDPRT" --baseline "ruta\al\modelo_base.SLDPRT" --params "D1@Croquis1,D2@Croquis2"
> ```
> El modelo solo es aceptable si cumple las 5 invariantes físicas:
> 1. **Cotas reales modificadas:** El valor numérico de cada cota leída de la base de datos cambió al valor requerido.
> 2. **Cero supresiones involuntarias:** `suppressed_features == 0`. Prohibido suprimir vaciados o redondeos para forzar que el árbol cierre.
> 3. **Cero fugas de superficie:** `surface_bodies_count == 0` (sólido cerrado B-Rep).
> 4. **Volumen coherente con DFM:** Ratio de volumen dentro de la variación esperada ($\Delta \text{Vol} \ll 50\%$). Si el volumen se triplica, se quebró el vaciado de pared.
> 5. **Envolvente modificada:** La caja envolvente (`bbox_mm`) refleja físicamente la nueva silueta.

### Step 5: Automated 2D Engineering Drawings (ISO/ANSI Format)
- Follow [Subhabilidad: Automatización de Planos ISO/ANSI](./references/drawing_iso_automation.md).
- Instantiates `a_landscape.slddrt` from `C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\lang\spanish\sheetformat\a_landscape.slddrt`, projects the 3 standard views + shaded isometric view, calculates auto-scale, and populates the corporate title block with part metadata.

### Step 6: Interactive Prompt-to-CAD Workflow (MecAgent Architecture)
- Consult [Arquitectura Prompt-to-CAD](./references/prompt_to_cad_architecture.md).
- When asked to create or modify geometry from a prompt:
  1. **Live Context Inspection:** Run `python .agents/skills/solidworks-parametric-cad/scripts/sw_context_inspector.py` to identify the active document, selected faces/edges (`SelectionManager`), and current feature tree in $O(1)$.
  2. **Parametric Code Generation:** Generate clean Python COM code following Section 3 rules (units in meters, `_v(x)` wrapper, fully constrained sketches).
  3. **Protected Interactive Execution:** Run via `python .agents/skills/solidworks-parametric-cad/scripts/sw_prompt_runner.py <script_path> <work_dir>`.
  4. **Self-Healing Diagnostics:** If `"success": false`, parse the structured JSON error/traceback, repair the sketch constraints or feature parameters, and rerun.
  5. **Visual Audit:** Verify generated orthogonal views (`iso.png`, `front.png`) and confirm mass properties match engineering specifications.

---

## 4. Reference Documentation & Sub-Skills

- **[Protocolo de Auditoría Geométrica Real & Lecciones Aprendidas](./references/cad_modification_audit_protocol.md)** — Metodología obligatoria de validación ground-truth (las 5 invariantes físicas) y lecciones aprendidas en modificaciones paramétricas de piezas complejas (prevención de falsos positivos y de supresiones arbitrarias).
- **[Arquitectura Prompt-to-CAD & MecAgent Reverse Engineering](./references/prompt_to_cad_architecture.md)** — Metodología de modelado con IA mediante prompts en lenguaje natural, captura de contexto en vivo y bucle de auto-sanación.
- **[Subhabilidad: Roscas Plásticas & Estándares SPI / GPI / ISBT](./references/plastic_threads_spi_standards.md)** — Estándares SP-400, SP-410, SP-415, perfiles Estilo "M" ($45^\circ / 10^\circ$), tablas dimensionales, y automatización con hélice, barrido y desvanecimiento de rosca (runout).
- **[Subhabilidad: Ingeniería Inversa STL a B-Rep](./references/reverse_engineering_stl_to_brep.md)** — Metodología de corte axial, separación de pared base y rosca, simplificación poligonal y auditoría de volumen.
- **[Subhabilidad: Automatización de Planos 2D ISO/ANSI](./references/drawing_iso_automation.md)** — Generación automática de planos normalizados con rótulo normalizado de ingeniería.
- **[Subhabilidad: DFM Plástico para Inyección y Soplado](./references/dfm_plastic_injection_and_blow_molding.md)** — Reglas de sellos (bore seal, crab's claw), bandas inviolables frangibles, densidades y contracciones.
- **[SolidWorks 2025 COM API Reference](./references/solidworks_2025_com_api.md)** — Signatures completas de `SketchManager`, `FeatureManager`, hélices, barridos, eliminación de caras, matrices y planos.
- **[Sandbox Desktop Bridge Reference](./references/sandbox_desktop_bridge.md)** — Ejecución de scripts interactivos en SolidWorks evitando el error `MK_E_UNAVAILABLE`.
- **[Photogrammetry & Loft Geometry Guide](./references/photogrammetry_and_loft_geometry.md)** — Reconstrucción de curvas Hermite $C^1$ y superficies complejas desde fotos.

---

## 5. Scripts & Reusable Helpers

- **[Auditor Universal de Modelos (`sw_model_auditor.py`)](./scripts/sw_model_auditor.py)** — Herramienta de solo lectura que audita cotas reales, operaciones suprimidas, conteo de cuerpos, volumen/área y caja envolvente, comparando contra pieza base en CLI o JSON.
- **[Live Context Inspector (`sw_context_inspector.py`)](./scripts/sw_context_inspector.py)** — Inspecciona en $O(1)$ documento activo, selección (caras/aristas/planos) y árbol de operaciones para inyectar contexto a los prompts.
- **[Prompt-to-CAD Runner (`sw_prompt_runner.py`)](./scripts/sw_prompt_runner.py)** — Ejecutor interactivo de scripts CAD con puente de escritorio, capturas automáticas de vistas y diagnóstico estructurado JSON.
- **[Helper de Roscas Paramétricas (`sw_thread_helper.py`)](./scripts/sw_thread_helper.py)** — Generador de roscas SPI SP-400/410/415 de 1 línea en SolidWorks.
- **[Base Script Template (`sw_base_template.py`)](./scripts/sw_base_template.py)** — Plantilla con croquis 100% acotados y relacionados (`auto_constrain_segments()`, `fully_define()`).
- **[Interactive Runner (`run_in_interactive_session.ps1`)](./scripts/run_in_interactive_session.ps1)** — Lanzador PowerShell para sesión interactiva de Windows con aislamiento de tareas efímeras y limpieza automática de bitmaps y diarios COM.
- **[Ejemplo Multicuerpo: Enclosure Paramétrico Bicomponente](./examples/multi_body_enclosure_example.md)** — Ejemplo de pieza inyectada multicuerpo con chasis rígido y junta de estanqueidad perimetral.
