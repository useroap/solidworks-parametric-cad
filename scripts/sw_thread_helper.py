"""
sw_thread_helper.py — Módulo de generación paramétrica de roscas plásticas SPI / GPI para SolidWorks 2025.
SolidWorks 2025 Python COM Automation Library

Permite insertar en cualquier documento activo de pieza (.SLDPRT) roscas estándar:
- Series: SP-400 (1.2 vueltas), SP-410 (1.5 vueltas), SP-415 (2.0 vueltas).
- Perfiles: Estilo "M" (Modified Buttress 45°/10°) y Estilo "L" (General Purpose 30°/30°).
- Tipo: Interna (hembra para tapas) o Externa (macho para cuellos de botellas).
- Solapamiento automático en pared (0.40 mm) para prevenir errores Parasolid de espesor cero.
- Trayectoria helicoidal 3D determinista (Insert3DSketch + CreateSpline2) + protección HideBody/ViewZoomTo2.
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
):
    """
    Genera una rosca paramétrica completa SPI en SolidWorks 2025 fusionada al sólido activo.
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

    planes = []
    feat = _v(doc.FirstFeature)
    while feat and len(planes) < 3:
        if _v(feat.GetTypeName2) == "RefPlane":
            planes.append(feat)
        feat = _v(feat.GetNextFeature)
    front_plane = planes[0]

    # 1. Ocultar temporalmente cuerpos sólidos para evitar snap de silueta durante CreateLine
    existing_bodies = doc.GetBodies2(0, True) or []
    for b in existing_bodies:
        try:
            b.HideBody = True
        except Exception:
            pass

    overlap = 0.40
    total_depth = b_depth + overlap
    dy_top = total_depth * 0.98
    dy_bot = total_depth * (0.18 if style.upper() == "M" else 0.58)
    y_crest_top = z_start_mm + c_flat / 2.0
    y_crest_bot = z_start_mm - c_flat / 2.0
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
    doc.ShowNamedView2("*Front", 1)
    doc.ViewZoomTo2(
        m(r_wall - 4.0), m(z_start_mm - 4.0), 0.0,
        m(r_wall + 4.0), m(z_start_mm + 4.0), 0.0,
    )
    sm.AddToDB = False
    sm.DisplayWhenAdded = True

    sm.CreateLine(m(pts[3][0]), m(pts[3][1]), 0, m(pts[0][0]), m(pts[0][1]), 0)
    sm.CreateLine(m(pts[0][0]), m(pts[0][1]), 0, m(pts[1][0]), m(pts[1][1]), 0)
    sm.CreateLine(m(pts[1][0]), m(pts[1][1]), 0, m(pts[2][0]), m(pts[2][1]), 0)
    sm.CreateLine(m(pts[2][0]), m(pts[2][1]), 0, m(pts[3][0]), m(pts[3][1]), 0)

    doc.ClearSelection2(True)
    sm.InsertSketch(True)
    sk_profile = doc.FeatureByPositionReverse(0)
    sk_profile.Name = f"Perfil_Rosca_{style}"

    for b in existing_bodies:
        try:
            b.HideBody = False
        except Exception:
            pass

    # 2. Trayectoria Helicoidal 3D exacta (Insert3DSketch + CreateSpline2)
    doc.ClearSelection2(True)
    sm.Insert3DSketch(True)
    sm.AddToDB = True
    sm.DisplayWhenAdded = False

    n_pts = 60
    max_theta = 2.0 * math.pi * num_turns
    dir_sign = 1.0 if clockwise else -1.0
    spline_coords = []
    for i in range(n_pts + 1):
        theta = max_theta * (i / float(n_pts))
        x_mm = r_wall * math.cos(dir_sign * theta)
        y_mm = z_start_mm + pitch_mm * (theta / (2.0 * math.pi))
        z_mm = r_wall * math.sin(dir_sign * theta)
        spline_coords.extend([m(x_mm), m(y_mm), m(z_mm)])

    var_pts = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, spline_coords)
    sm.CreateSpline2(var_pts, False)
    sm.AddToDB = False
    sm.DisplayWhenAdded = True
    doc.ClearSelection2(True)
    sm.Insert3DSketch(True)
    helix_feat = doc.FeatureByPositionReverse(0)
    helix_feat.Name = f"Helice_3D_{series}"

    # 3. Saliente Barrido (InsertProtrusionSwept4 con 20 parámetros de SolidWorks 2025)
    doc.ClearSelection2(True)
    sk_profile.Select2(True, 1)
    helix_feat.Select2(True, 4)

    sweep = fm.InsertProtrusionSwept4(
        False, False, 0, False, True, 0, 0, False, 0.0, 0.0, 0,
        0, True, True, True, 0.0, True, False, 0.0, 0
    )
    if sweep is not None:
        sweep.Name = f"Rosca_{series}_{style}"

    try:
        doc.ClearSelection2(True)
        helix_feat.Select2(False, 0)
        doc.BlankSketch()
    except Exception:
        pass

    doc.ForceRebuild3(False)
    print(f"Rosca {series} (D{nominal_dia} mm, {style}, {num_turns} vueltas) creada exitosamente.")
    return sweep
