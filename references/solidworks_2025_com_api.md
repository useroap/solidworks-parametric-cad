# SolidWorks 2025 COM API Reference (`pywin32` Late-Binding)

This reference documents the exact COM signatures, unit conventions, and `pywin32` late-binding rules required to automate **SolidWorks 2025** reliably from Python without crashes or dialog deadlocks.

---

## 1. Connection & Threading Rules

1. **Single-Threaded Apartment (STA):**
   Always call `pythoncom.CoInitialize()` on the main thread before invoking any SolidWorks COM method.
2. **Active Instance Only (`AGENTS.md` Mandatory Rule):**
   ```python
   import pythoncom
   import win32com.client

   pythoncom.CoInitialize()
   sw = win32com.client.GetActiveObject("SldWorks.Application")
   sw.Visible = True
   sw.SetUserPreferenceToggle(10, False)  # swInputDimValOnCreate = False (prevents popup deadlock)
   ```
   - **Never** use `win32com.client.Dispatch("SldWorks.Application")` in background scripts or loops.

---

## 2. Units & Coordinate System

- **Internal SI Units:** Every coordinate, radius, extrusion depth, and plane offset passed to the SolidWorks API MUST be in **meters** (`m(mm) = mm * 0.001`). Every angle MUST be in **radians**.
- **Standard Plane Coordinate Mapping:**
  When iterating `doc.FirstFeature` / `GetNextFeature` for `GetTypeName2 == "RefPlane"`, the first 3 planes in any default SolidWorks part template are:
  1. `planes[0]` — **Front / Alzado** (Sketch $(x_s, y_s) = (X, Y)$, normal $+Z$)
  2. `planes[1]` — **Top / Planta** (Sketch $(x_s, y_s) = (X, -Z)$, normal $+Y$)
  3. `planes[2]` — **Right / Vista lateral** (Sketch $(x_s, y_s) = (-Z, Y)$, normal $+X$)

---

## 3. `pywin32` Late-Binding Property vs. Method Trap (`_v(x)`)

In `pywin32` dynamic dispatch (`CDispatch`), zero-argument SolidWorks API members are sometimes resolved as `types.MethodType` and sometimes evaluated directly as properties. Always use the helper `_v(x)`:

```python
import types

def _v(x):
    """Safely evaluate a zero-arg COM member whether pywin32 bound it as property or method."""
    return x() if isinstance(x, types.MethodType) else x
```

Members that commonly require `_v(...)` or direct property access:
- `doc.FirstFeature`, `feat.GetNextFeature`, `feat.GetTypeName2`
- `doc.GetEquationMgr`, `doc.BlankRefGeom`, `doc.ViewZoomtofit2`
- `sw.GetDocuments`, `doc.GetPathName`, `doc.GetTitle`
- `body.GetBodyBox`, `body.Name`, `body.GetTessTriangles(True)`
- `doc.Extension.CreateMassProperty`, `mp.Volume`, `mp.Mass`

---

## 4. High-Speed, Deterministic Sketching (`SketchManager`)

Always bracket sketch creation with `AddToDB = True` and `DisplayWhenAdded = False` to bypass UI snapping, inference lines, and slow viewport redraws:

```python
sm = doc.SketchManager
doc.ClearSelection2(True)
plane_feat.Select2(False, 0)
sm.InsertSketch(True)
sm.AddToDB = True
sm.DisplayWhenAdded = False

# ... create geometry in meters ...

sm.AddToDB = False
sm.DisplayWhenAdded = True
sm.InsertSketch(True)  # closes sketch
sketch_feat = doc.FeatureByPositionReverse(0)
sketch_feat.Name = "My_Sketch"
```

### Key Sketch Primitives & Traps
| Method | Signature & Critical Notes |
| :--- | :--- |
| `CreateLine` | `sm.CreateLine(x1, y1, 0, x2, y2, 0)` |
| `CreateCenterLine` | `sm.CreateCenterLine(x1, y1, 0, x2, y2, 0)` — Required inside the sketch for `FeatureRevolve2`. |
| `Create3PointArc` | `sm.Create3PointArc(x_start, y_start, 0, x_end, y_end, 0, x_mid, y_mid, 0)`<br>**TRAP:** The 2nd point is the **END** point and the 3rd point is the **MIDPOINT**! |
| `CreateArc` | `sm.CreateArc(xc, yc, 0, x_start, y_start, 0, x_end, y_end, 0, direction)` (`direction = 1` CCW, `-1` CW). |
| `CreateCircleByRadius` | `sm.CreateCircleByRadius(xc, yc, 0, radius)` |
| `CreateSpline2` | Requires a `VARIANT` double array of $[x_0, y_0, z_0, x_1, y_1, z_1, \dots]$:<br>`arr = VARIANT(pythoncom.VT_ARRAY \| pythoncom.VT_R8, data)`<br>`sm.CreateSpline2(arr, False)` |

---

## 5. Solid B-Rep Operations (`FeatureManager`)

### 5.1 Reference Plane Offset (`InsertRefPlane`)
```python
doc.ClearSelection2(True)
right_plane.Select2(False, 0)
fm.InsertRefPlane(8, m(x_offset_mm), 0, 0, 0, 0)  # 8 = swRefPlaneReferenceConstraint_Distance
ref_plane = doc.FeatureByPositionReverse(0)
```

### 5.2 Solid Loft (`InsertProtrusionBlend2`)
Select all cross-section sketches in order with `Mark = 1` and `Append = True`:
```python
doc.ClearSelection2(True)
for sk in sketches:
    sk.Select2(True, 1)
loft = fm.InsertProtrusionBlend2(
    False, True, False, 1.0, 0, 0, 1.0, 1.0,
    True, True, False, 0.0, 0.0, 0,
    True,  # Merge (param 15/16)
    True, True, 0
)
```

### 5.3 Boss Extrusion (`FeatureExtrusion3`)
For a mid-plane extrusion (`swEndCondMidPlane = 6`) of total width `w_mm`:
```python
doc.ClearSelection2(True)
sketch.Select2(False, 0)
ext = fm.FeatureExtrusion3(
    True, False, False, 6, 0, m(w_mm), 0.0,
    False, False, False, False, 0, 0, False, False, False, False,
    True,  # Merge (param 18): True = merge with existing body, False = new solid body
    True, True, 0, 0, False
)
```

### 5.4 Boss Revolve (`FeatureRevolve2`)
Sketch must contain a centerline (`CreateCenterLine`). Parameter 18 controls `Merge`:
```python
doc.ClearSelection2(True)
sketch.Select2(False, 0)
rev = fm.FeatureRevolve2(
    True, True, False, False, False, False, 0, 0, 2 * math.pi, 0,
    False, False, 0, 0, 0, 0, 0,
    merge_bool,  # Parameter 18: True = merge, False = create separate solid body!
    True, True
)
```

### 5.5 Extruded Cut (`FeatureCut4`)
**Critical Best Practice:** Avoid `Flip = True` (`FlipSideToCut`) with `ThroughAllBoth` (`9, 9`), as SolidWorks 2025 can ignore `Flip = True` on spline contours. Instead, draw a **closed loop around the outer region to remove** and pass `Flip = False`:
```python
doc.ClearSelection2(True)
cut_sketch.Select2(False, 0)
cut = fm.FeatureCut4(
    False,  # Sd = False (two-directional cut)
    False,  # Flip = False (cut inside the closed loop)
    False,
    9, 9,   # d1 = 9 (swEndCondThroughAllBoth), d2 = 9
    0.01, 0.01,
    False, False, False, False, 0, 0,
    False, False, False, False, False,
    True, True, True, True, False, 0, 0, False, False
)
```

---

## 6. Multi-Body Naming & Exact Bounding Box Verification

1. **Inspecting & Naming Solid Bodies:**
   ```python
   bodies = doc.GetBodies2(0, True) or []  # 0 = swSolidBody, True = visible only
   for b in bodies:
       b.Name = "Descriptive_Body_Name"
   ```
2. **Why `GetBodyBox` Over-Estimates Spine/Loft Bounds:**
   `IBody2::GetBodyBox` returns the NURBS control-point bounding box, which can be $1.0\text{–}1.8\text{ mm}$ larger than the actual B-Rep surface on lofted faces.
   To measure exact physical bounds in millimeters, inspect the tessellation vertices via `GetTessTriangles(True)`:
   ```python
   def exact_body_bounds_mm(b):
       tris = _v(b.GetTessTriangles(True))
       if tris and len(tris) >= 9:
           xs, ys, zs = tris[0::3], tris[1::3], tris[2::3]
           return [min(xs)*1000, min(ys)*1000, min(zs)*1000,
                   max(xs)*1000, max(ys)*1000, max(zs)*1000]
       return [v * 1000.0 for v in _v(b.GetBodyBox)]
   ```

---

## 7. Sketch Constraints, Dimensions & Equations (Fully Defining Sketches)

### 7.1 Entity Creation vs Interactive Constraint Mode
When scripting sketches via COM, creating entities in interactive mode (`AddToDB = False`) enables auto-inferencing which can merge or distort vertices during coordinate calculation.
**Rule of Thumb:**
1. Draw all geometry first with `sm.AddToDB = True; sm.DisplayWhenAdded = False`.
2. Switch to `sm.AddToDB = False; sm.DisplayWhenAdded = True`.
3. Add geometric constraints and dimensions.

```python
# 1. Geometría en base de datos
sm.AddToDB = True
sm.DisplayWhenAdded = False
line1 = sm.CreateLine(0, 0, 0, m(10), 0, 0)
line2 = sm.CreateLine(m(10), 0, 0, m(10), m(5), 0)

# 2. Modo interactivo para cotas y relaciones
sm.AddToDB = False
sm.DisplayWhenAdded = True
```

### 7.2 Adding Geometric Constraints (`SketchAddConstraints`)
Entities must be selected via `Select4(False, NOTHING)` where `NOTHING = VARIANT(pythoncom.VT_DISPATCH, None)`:
```python
doc.ClearSelection2(True)
line1.Select4(False, NOTHING)
doc.SketchAddConstraints("sgHORIZONTAL2D")

# Restricción entre 2 entidades (ej. colineal, tangencia):
doc.ClearSelection2(True)
line1.Select4(False, NOTHING)
line2.Select4(True, NOTHING)  # Append = True
doc.SketchAddConstraints("sgCOLINEAR")  # o "sgTANGENT", "sgCONCENTRIC"
```

### 7.3 Adding Dimensions & Linking to Global Equations
`doc.AddDimension2(x, y, z)` returns an `IDisplayDimension`. Retrieve the underlying `IDimension` via `.GetDimension2(0)`:
```python
doc.ClearSelection2(True)
line1.Select4(False, NOTHING)
disp = doc.AddDimension2(m(5), m(2), 0)
if disp is not None:
    dim = disp.GetDimension2(0)
    # Vincular a variable global en EquationMgr:
    eq = doc.GetEquationMgr
    eq.Add2(-1, f'"{dim.Name}@{sketch_name}" = "L_mango"', True)
```

### 7.4 Fully Defining Sketches (`FullyDefineSketch`)
To apply auto-solve relations without popping UI dialogs:
```python
sm.FullyDefineSketch(
    True,   # InCurrentSketch
    True,   # ApplyRelations
    31,     # RelationFlags (horiz, vert, colinear, tangent, concentric)
    False,  # ApplyDimensions (False to keep user-driven dimensions only)
    0, NOTHING, 0, NOTHING, 0, 0
)
```

---

## 8. Saving `.SLDPRT`, `.STEP`, and Viewport `.BMP` / `.PNG`

```python
NOTHING = VARIANT(pythoncom.VT_DISPATCH, None)
err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
wrn = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)

doc.Extension.SaveAs(base_path + ".SLDPRT", 0, 1, NOTHING, err, wrn)
doc.Extension.SaveAs(base_path + ".STEP", 0, 1, NOTHING, err, wrn)

for vname, vid in (("iso", 7), ("planta", 5), ("alzado", 1), ("lateral", 4), ("inferior", 6)):
    doc.ShowNamedView2("*" + vname, vid)
    _v(doc.ViewZoomtofit2)
    doc.SaveBMP(f"{base_path}_{vname}.bmp", 1600, 1000)
```

---

## 9. Advanced Plastic & Bottle Operations (`FeatureManager`)

### 9.1 Helix & Spiral (`IModelDoc2.InsertHelix`) - Parametric & Editable in UI
To generate a native, 100% editable constant-pitch helix from a selected base circle sketch (replaces rigid 3D Splines):
```python
# 1. Seleccionar el croquis circular base (100% Fully Defined con Cota Ø y Coincidente con Origen)
doc.ClearSelection2(True)
circle_sketch_feat.Select2(False, 0)

# 2. IModelDoc2.InsertHelix (10 parámetros obligatorios):
# doc.InsertHelix(Reversed, Clockwised, Tapered, Outward, Helixdef, Height, Pitch, Revolution, TaperAngle, Startangle)
# - Reversed (bool): False = hacia arriba (+Y), True = hacia abajo (-Y)
# - Clockwised (bool): True = Sentido horario (rosca derecha convencional), False = antihorario
# - Tapered (bool): False (sin conicidad para roscas cilíndricas)
# - Outward (bool): False
# - Helixdef (int): 0 = swHelixDefinedByPitchAndRevolution
# - Height (double): Altura total en metros (m(pitch_mm * revs))
# - Pitch (double): Paso axial en metros (m(4.233) para 6 TPI)
# - Revolution (double): Número de vueltas (float, ej. 1.2)
# - TaperAngle (double): 0.0
# - Startangle (double): Ángulo de inicio en radianes (0.0 rad para cortar exactamente el plano Front/Alzado en Z=0)
doc.InsertHelix(
    False, True, False, False, 0,
    m(pitch_mm * revs), m(pitch_mm), float(revs), 0.0, 0.0
)
helix_feat = doc.FeatureByPositionReverse(0)
helix_feat.Name = "Rosca_Helice_Nativa"
```

### 9.2 Swept Boss & Cut (`InsertProtrusionSwept4` / `InsertCutSwept4`)
Select profile sketch with `Mark = 1` and helix path with `Mark = 4`:
```python
doc.ClearSelection2(True)
# Mark 1: Perfil (Croquis Estilo 'M')
profile_feat.Select2(True, 1)
# Mark 4: Trayectoria (Hélice)
helix_feat.Select2(True, 4)

# InsertProtrusionSwept4(Propagate, Alignment, TwistCtrl, KeepNormal, Thin, Thickness1, Thickness2, ThinType, StartCond, EndCond, Merge)
sweep = fm.InsertProtrusionSwept4(
    False, 0, 0, False, False, 0, 0, 0, 0, 0,
    True  # Merge = True (unir con la pared de la tapa)
)
```

### 9.3 Delete Face for Thread Runout (`InsertDeleteFace2`)
Eliminates abrupt 90° start/end cut faces of swept threads so closures do not bind:
```python
# swDeleteFaceOptions_e: 1 = swDeleteFace_Heal (eliminar y emparchar/prolongar caras vecinas)
doc.ClearSelection2(True)
face_obj.Select4(False, NOTHING)
fm.InsertDeleteFace2(1)
```

### 9.4 Circular Pattern (`FeatureCircularPattern4`)
For cap knurling, outer ribs, or multi-start threads:
```python
doc.ClearSelection2(True)
# Mark 1: Operación o caras a patronar
rib_feat.Select2(True, 1)
# Mark 4: Eje de rotación (Línea central o cara cilíndrica)
axis_feat.Select2(True, 4)

# FeatureCircularPattern4(TotalInstances, SpacingRad, EqualSpacing, ReverseDir, GeometryPattern, VisualProperties)
pattern = fm.FeatureCircularPattern4(
    instances, 2 * math.pi, True, False, False, True
)
```

### 9.5 Fillets & Chamfers (`FeatureFillet3`)
Apply constant-radius fillets on parting lines or transitions:
```python
# swFeatureFilletType_e: 0 = swFilletUniformRadius
doc.ClearSelection2(True)
edge_obj.Select4(True, NOTHING)
fm.FeatureFillet3(
    0, m(radius_mm), 0, 0, 0, 0, 0,
    VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [m(radius_mm)]),
    NOTHING, NOTHING, NOTHING, NOTHING, NOTHING, NOTHING
)
```

---

## 10. Automated 2D Engineering Drawings (ISO/ANSI Standard Template)

```python
# 1. Crear nuevo dibujo usando plantilla corporativa ISO/ANSI Standard
sheet_format_path = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\lang\spanish\sheetformat\a_landscape.slddrt"
draw_doc = sw.NewDocument(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Dibujo.drwdot", 12, 0.2794, 0.2159) # Carta horizontal

sheet = draw_doc.GetCurrentSheet
sheet.SetTemplateName(sheet_format_path)
sheet.ReloadTemplate(False)

# 2. Insertar vistas del modelo 3D activo
# swDrawingViewTypes_e: 1=Front, 2=Top, 3=Right, 7=Isometric
draw_doc.CreateDrawViewFromModelView3(model_path, "*Alzado", 0.08, 0.12, 0)
draw_doc.CreateDrawViewFromModelView3(model_path, "*Superior", 0.08, 0.05, 0)
draw_doc.CreateDrawViewFromModelView3(model_path, "*Vista lateral", 0.16, 0.12, 0)
iso_view = draw_doc.CreateDrawViewFromModelView3(model_path, "*Isométrica", 0.20, 0.06, 0)
if iso_view:
    iso_view.SetDisplayMode3(False, 3, False, True) # Sombreado con aristas
```
