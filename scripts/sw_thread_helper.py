"""
sw_thread_helper.py — Módulo de generación paramétrica de roscas plásticas SPI / GPI para SolidWorks 2025.
Parametric CAD Automation Engine

Permite insertar en cualquier documento activo de pieza (.SLDPRT) roscas estándar:
- Series: SP-400 (1.2 vueltas), SP-410 (1.5 vueltas), SP-415 (2.0 vueltas).
- Perfiles: Estilo "M" (Modified Buttress 45°/10°) y Estilo "L" (General Purpose 30°/30°).
- Tipo: Interna (hembra para tapas) o Externa (macho para cuellos de botellas).
- Solapamiento automático en pared (0.40 mm) para prevenir errores Parasolid de espesor cero.
- MODELADO NATIVO PARAMÉTRICO Y EDITABLE: Usa Hélice/Espiral (IModelDoc2.InsertHelix) + Barrer (InsertProtrusionSwept4).
  Permite al diseñador editar interactivamente el paso, altura y revoluciones en la interfaz nativa de SolidWorks.
"""
import math
import types
import pythoncom
import win32com.client
from win32com.client import VARIANT

NOTHING = VARIANT(pythoncom.VT_DISPATCH, None)
MM = 0.001


def m(val_mm: float) -> float:
    return float(val_mm) * MM


def _v(x):
    return x() if isinstance(x, types.MethodType) else x


# Base de datos SPI estándar (Dimensiones en mm)
SPI_THREAD_TABLE = {
    # dia: (TPI, pitch, a_width, b_depth, c_flat, r_top, r_bot)
    18: (8, 3.1750, 1.8300, 0.8900, 0.76, 0.50, 0.20),
    20: (8, 3.1750, 1.8300, 0.8900, 0.76, 0.50, 0.20),
    22: (8, 3.1750, 1.8300, 0.8900, 0.76, 0.50, 0.20),
    24: (8, 3.1750, 1.8300, 0.8900, 0.76, 0.50, 0.20),
    28: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    33: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    38: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    43: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    45: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    48: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    53: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    58: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    63: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
    70: (6, 4.2333, 2.3876, 1.1938, 0.99, 0.75, 0.25),
}

DEFAULT_TURNS = {
    "SP-400": 1.2,
    "SP-410": 1.5,
    "SP-415": 2.0,
}


def add_spi_thread(
    doc,
    series: str = "SP-400",
    nominal_dia: int = 63,
    style: str = "M",
    internal: bool = True,
    wall_radius_mm: float = None,
    z_start_mm: float = 3.5,
    turns: float = None,
    clockwise: bool = True,
    reverse_direction: bool = False,
):
    """
    Genera una rosca paramétrica completa SPI en SolidWorks 2025 fusionada al sólido activo,
    utilizando la operación nativa Hélice/Espiral (InsertHelix) y Barrer (InsertProtrusionSwept4).
    
    Ventaja técnica fundamental:
      La rosca resultante es 100% editable mediante el diálogo nativo de SolidWorks
      (clic derecho -> Editar operación en la Hélice para modificar paso, altura o revoluciones),
      eliminando las trayectorias de Spline 3D rígidas y difíciles de modificar.
    """
    fm = doc.FeatureManager
    sm = doc.SketchManager

    params = SPI_THREAD_TABLE.get(nominal_dia)
    if not params:
        closest_dia = min(SPI_THREAD_TABLE.keys(), key=lambda d: abs(d - nominal_dia))
        params = SPI_THREAD_TABLE[closest_dia]

    tpi, pitch_mm, a_width, b_depth, c_flat, r_top, r_bot = params
    num_turns = turns if turns is not None else DEFAULT_TURNS.get(series.upper(), 1.2)
    r_wall = wall_radius_mm if wall_radius_mm is not None else (nominal_dia / 2.0)

    # Identificar planos principales
    planes = []
    feat = _v(doc.FirstFeature)
    while feat and len(planes) < 3:
        if _v(feat.GetTypeName2) == "RefPlane":
            planes.append(feat)
        feat = _v(feat.GetNextFeature)
    front_plane, top_plane, right_plane = planes[0], planes[1], planes[2]

    # 1. Crear Plano de inicio de la Hélice a z_start_mm (o usar Top si z_start == 0)
    ref_plane = top_plane
    if abs(z_start_mm) > 1e-4:
        doc.ClearSelection2(True)
        top_plane.Select2(False, 0)
        # swRefPlaneReferenceConstraint_Distance = 8
        fm.InsertRefPlane(8, m(z_start_mm), 0, 0, 0, 0)
        ref_plane = doc.FeatureByPositionReverse(0)
        ref_plane.Name = f"Plano_Inicio_Rosca_{series}"

    # 2. Croquis de Círculo Base para la Hélice
    doc.ClearSelection2(True)
    ref_plane.Select2(False, 0)
    sm.InsertSketch(True)
    sm.AddToDB = True
    sm.DisplayWhenAdded = False
    circ = sm.CreateCircleByRadius(0, 0, 0, m(r_wall))
    sm.AddToDB = False
    sm.DisplayWhenAdded = True
    
    # Auto-constrain / Fully define del circulo base
    try:
        sm.FullyDefineSketch(True, True, 31, True, 1, NOTHING, 1, NOTHING, 0, 0)
    except Exception:
        pass
        
    doc.ClearSelection2(True)
    sm.InsertSketch(True)
    sk_circ = doc.FeatureByPositionReverse(0)
    sk_circ.Name = f"Croquis_Circulo_Rosca_{series}"

    # 3. Operación Nativa Hélice/Espiral (IModelDoc2.InsertHelix)
    # Startangle = 0.0 rad sitúa el punto inicial exactamente sobre el plano Alzado (Front / Z=0)
    doc.ClearSelection2(True)
    sk_circ.Select2(False, 0)
    doc.InsertHelix(
        reverse_direction,          # Reversed (False = +Y, True = -Y)
        clockwise,                  # Clockwised (True = rosca derecha)
        False,                      # Tapered
        False,                      # Outward
        0,                          # Helixdef: 0 = swHelixDefinedByPitchAndRevolution
        m(pitch_mm * num_turns),    # Height
        m(pitch_mm),                # Pitch
        float(num_turns),           # Revolution
        0.0,                        # TaperAngle
        0.0                         # Startangle (0 rad -> cruza Alzado en X=r_wall, Y=z_start, Z=0)
    )
    helix_feat = doc.FeatureByPositionReverse(0)
    helix_feat.Name = f"Helice_SPI_{series}"

    # 4. Croquis de Perfil de Rosca en el Plano Frontal (Alzado)
    overlap = 0.40
    total_depth = b_depth + overlap
    dy_top = total_depth * 0.98
    dy_bot = total_depth * (0.18 if style.upper() == "M" else 0.58)

    y_center = z_start_mm
    y_crest_top = y_center + c_flat / 2.0
    y_crest_bot = y_center - c_flat / 2.0
    y_root_top = y_crest_top + dy_top
    y_root_bot = y_crest_bot - dy_bot

    if internal:
        x_anchor = r_wall + overlap
        x_crest = r_wall - b_depth
    else:
        x_anchor = r_wall - overlap
        x_crest = r_wall + b_depth

    pts = [
        (x_anchor, y_root_top),
        (x_crest, y_crest_top),
        (x_crest, y_crest_bot),
        (x_anchor, y_root_bot),
    ]

    doc.ClearSelection2(True)
    front_plane.Select2(False, 0)
    sm.InsertSketch(True)
    sm.AddToDB = True
    sm.DisplayWhenAdded = False

    sm.CreateLine(m(pts[3][0]), m(pts[3][1]), 0, m(pts[0][0]), m(pts[0][1]), 0)
    sm.CreateLine(m(pts[0][0]), m(pts[0][1]), 0, m(pts[1][0]), m(pts[1][1]), 0)
    sm.CreateLine(m(pts[1][0]), m(pts[1][1]), 0, m(pts[2][0]), m(pts[2][1]), 0)
    sm.CreateLine(m(pts[2][0]), m(pts[2][1]), 0, m(pts[3][0]), m(pts[3][1]), 0)

    sm.AddToDB = False
    sm.DisplayWhenAdded = True

    try:
        sm.FullyDefineSketch(True, True, 31, True, 1, NOTHING, 1, NOTHING, 0, 0)
    except Exception:
        pass

    doc.ClearSelection2(True)
    sm.InsertSketch(True)
    sk_profile = doc.FeatureByPositionReverse(0)
    sk_profile.Name = f"Perfil_Rosca_{style}_{series}"

    # 5. Saliente Barrido Nativo (InsertProtrusionSwept4)
    doc.ClearSelection2(True)
    sk_profile.Select2(True, 1)   # Mark 1: Profile
    helix_feat.Select2(True, 4)   # Mark 4: Path

    sweep = fm.InsertProtrusionSwept4(
        False, False, 0, False, False, 0, 0, False, 0.0, 0.0, 0,
        0, True, True, True, 0.0, True, False, 0.0, 0
    )
    if sweep is not None:
        sweep.Name = f"Rosca_Barrer_{series}_{style}"

    # Ocultar la hélice visualmente para mantener el viewport limpio
    try:
        doc.ClearSelection2(True)
        helix_feat.Select2(False, 0)
        doc.BlankSketch()
    except Exception:
        pass

    doc.ForceRebuild3(False)
    print(f"[OK] Rosca Nativa {series} (D{nominal_dia} mm, Estilo {style}, {num_turns} vueltas) creada exitosamente con Hélice/Espiral editable.")
    return sweep
