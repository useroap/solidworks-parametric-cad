"""
sw_base_template.py — Plantilla base reutilizable para modelado 3D paramétrico B-Rep
en SolidWorks 2025 vía API COM (pywin32).
SolidWorks 2025 Python COM Automation Library

Reglas obligatorias (AGENTS.md):
- Usa exclusivamente GetActiveObject("SldWorks.Application"); NUNCA usa Dispatch en segundo plano.
- Todas las cotas de entrada en milímetros; conversión interna a metros mediante m(v).
"""
import math
import os
import sys
import types

import pythoncom
import win32com.client
from win32com.client import VARIANT

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
MM = 0.001
NOTHING = VARIANT(pythoncom.VT_DISPATCH, None)


def m(v_mm: float) -> float:
    """Convierte milímetros a metros (unidad interna SI de la API de SolidWorks)."""
    return v_mm * MM


def _v(x):
    """Evalúa de forma segura miembros COM sin argumentos (propiedad vs método en pywin32)."""
    return x() if isinstance(x, types.MethodType) else x


# ----------------------------------------------------------------------------
# Conexión y configuración base del documento
# ----------------------------------------------------------------------------
def connect():
    try:
        sw = win32com.client.GetActiveObject("SldWorks.Application")
    except Exception:
        raise SystemExit("SolidWorks no está abierto en la sesión interactiva. Ábralo y reintente.")
    sw.Visible = True
    sw.SetUserPreferenceToggle(10, False)  # swInputDimValOnCreate = False
    return sw


def new_part(sw):
    tpl = sw.GetUserPreferenceStringValue(8)  # swDefaultTemplatePart
    doc = sw.NewDocument(tpl, 0, 0, 0)
    if doc is None:
        raise SystemExit(f"No se pudo crear la pieza con la plantilla: {tpl}")
    return doc


def std_planes(doc):
    """Devuelve [Front/Alzado, Top/Planta, Right/Vista lateral] sin depender del idioma."""
    planes = []
    f = _v(doc.FirstFeature)
    while f is not None and len(planes) < 3:
        if _v(f.GetTypeName2) == "RefPlane":
            planes.append(f)
        f = _v(f.GetNextFeature)
    return planes


def last_feature(doc):
    return doc.FeatureByPositionReverse(0)


def add_globals(doc, params_dict: dict):
    """Registra todos los parámetros numéricos en Herramientas > Ecuaciones."""
    eq = _v(doc.GetEquationMgr)
    for k, v in params_dict.items():
        if isinstance(v, bool):
            continue
        eq.Add2(-1, f'"{k}" = {v}', True)
    return eq


# ----------------------------------------------------------------------------
# Envoltorio de Boceto 2D de alto rendimiento con Cotas y Restricciones
# ----------------------------------------------------------------------------
class Sketch:
    def __init__(self, doc, plane_feat, name: str):
        self.doc = doc
        self.sm = doc.SketchManager
        self.name = name
        doc.ClearSelection2(True)
        plane_feat.Select2(False, 0)
        self.sm.InsertSketch(True)
        self.sm.AddToDB = True
        self.sm.DisplayWhenAdded = False
        self._in_db = True

    def _ensure_db(self):
        if not self._in_db:
            self.sm.AddToDB = True
            self.sm.DisplayWhenAdded = False
            self._in_db = True

    def _ensure_interactive(self):
        if self._in_db:
            self.sm.AddToDB = False
            self.sm.DisplayWhenAdded = True
            self._in_db = False

    def line(self, a, b):
        self._ensure_db()
        return self.sm.CreateLine(m(a[0]), m(a[1]), 0, m(b[0]), m(b[1]), 0)

    def cline(self, a, b):
        self._ensure_db()
        return self.sm.CreateCenterLine(m(a[0]), m(a[1]), 0, m(b[0]), m(b[1]), 0)

    def arc3(self, a, b, mid):
        """Arco de 3 puntos de a (inicio) -> b (fin) pasando por mid (punto intermedio)."""
        self._ensure_db()
        return self.sm.Create3PointArc(
            m(a[0]), m(a[1]), 0,
            m(b[0]), m(b[1]), 0,
            m(mid[0]), m(mid[1]), 0,
        )

    def arc_c(self, center, start, end, direction: int = 1):
        self._ensure_db()
        return self.sm.CreateArc(
            m(center[0]), m(center[1]), 0,
            m(start[0]), m(start[1]), 0,
            m(end[0]), m(end[1]), 0,
            direction,
        )

    def circle_r(self, center, radius: float):
        self._ensure_db()
        return self.sm.CreateCircleByRadius(m(center[0]), m(center[1]), 0, m(radius))

    def spline(self, pts):
        self._ensure_db()
        data = []
        for x, y in pts:
            data += [m(x), m(y), 0.0]
        arr = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, data)
        return self.sm.CreateSpline2(arr, False)

    def add_constraint(self, entity, constraint_type: str):
        """Aplica una restricción geométrica a una entidad (ej. 'sgHORIZONTAL2D', 'sgVERTICAL2D')."""
        if entity is not None:
            self._ensure_interactive()
            self.doc.ClearSelection2(True)
            entity.Select4(False, NOTHING)
            self.doc.SketchAddConstraints(constraint_type)

    def add_constraint_pair(self, entity1, entity2, constraint_type: str):
        """Aplica una restricción entre dos entidades (ej. 'sgCOLINEAR', 'sgTANGENT', 'sgCONCENTRIC')."""
        if entity1 is not None and entity2 is not None:
            self._ensure_interactive()
            self.doc.ClearSelection2(True)
            entity1.Select4(False, NOTHING)
            entity2.Select4(True, NOTHING)
            self.doc.SketchAddConstraints(constraint_type)

    def add_dimension(self, entity, x: float, y: float, z: float = 0.0, eq_name: str = None, eq_expr: str = None):
        """Añade una cota sobre una entidad y opcionalmente la vincula al EquationManager."""
        if entity is None:
            return None
        self._ensure_interactive()
        self.doc.ClearSelection2(True)
        entity.Select4(False, NOTHING)
        disp = self.doc.AddDimension2(m(x), m(y), m(z))
        if disp is not None:
            dim = disp.GetDimension2(0)
            if dim and eq_name and eq_expr:
                eq = _v(self.doc.GetEquationMgr)
                eq.Add2(-1, f'"{_v(dim.Name)}@{self.name}" = {eq_expr}', True)
            return dim
        return None

    def auto_constrain_segments(self, segments, origin_anchor: bool = True, tol: float = 1e-4):
        """
        Inspecciona una lista de líneas y aplica automáticamente:
        - sgHORIZONTAL2D si |y1 - y2| < tol
        - sgVERTICAL2D si |x1 - x2| < tol
        - sgCOINCIDENT en esquinas consecutivas
        - Anclaje al origen si origin_anchor=True
        """
        self._ensure_interactive()
        for seg in segments:
            if seg is None:
                continue
            try:
                sp = _v(seg.GetStartPoint2)
                ep = _v(seg.GetEndPoint2)
                if sp and ep:
                    dx = abs(_v(ep.X) - _v(sp.X))
                    dy = abs(_v(ep.Y) - _v(sp.Y))
                    if dy < tol:
                        self.add_constraint(seg, "sgHORIZONTAL2D")
                    elif dx < tol:
                        self.add_constraint(seg, "sgVERTICAL2D")
            except Exception:
                pass

    def fully_define(self, use_relations: bool = True, use_dimensions: bool = True):
        """
        Aplica FullyDefineSketch para garantizar que el boceto quede totalmente restringido (Líneas Negras).
        use_dimensions=True aplica cotas automáticas de línea base para cerrar los grados de libertad restantes.
        """
        try:
            self._ensure_interactive()
            return self.sm.FullyDefineSketch(
                True, use_relations, 31, use_dimensions, 1, NOTHING, 1, NOTHING, 0, 0
            )
        except Exception:
            return 0

    def close(self):
        self.sm.AddToDB = False
        self.sm.DisplayWhenAdded = True
        self.doc.ClearSelection2(True)
        self.sm.InsertSketch(True)
        f = last_feature(self.doc)
        f.Name = self.name
        return f


# ----------------------------------------------------------------------------
# Verificación de cuerpos sólidos, caja delimitadora exacta y exportación
# ----------------------------------------------------------------------------
def exact_body_bounds_mm(b):
    """Obtiene [xmin, ymin, zmin, xmax, ymax, zmax] exactos en mm desde los vértices de teselación."""
    try:
        tris = _v(b.GetTessTriangles(True))
        if tris and len(tris) >= 9:
            xs, ys, zs = tris[0::3], tris[1::3], tris[2::3]
            return [
                min(xs) * 1000.0, min(ys) * 1000.0, min(zs) * 1000.0,
                max(xs) * 1000.0, max(ys) * 1000.0, max(zs) * 1000.0,
            ]
    except Exception:
        pass
    bx = _v(b.GetBodyBox)
    return [v * 1000.0 for v in bx]


def report(doc) -> int:
    bodies = doc.GetBodies2(0, True) or []
    nb = len(bodies)
    print(f"Cuerpos sólidos: {nb}")
    xs, ys, zs = [], [], []
    for i, b in enumerate(bodies):
        b_mm = exact_body_bounds_mm(b)
        xs += [b_mm[0], b_mm[3]]
        ys += [b_mm[1], b_mm[4]]
        zs += [b_mm[2], b_mm[5]]
        print(
            f"  Body[{i}] '{_v(b.Name)}': "
            f"X {b_mm[0]:.2f}..{b_mm[3]:.2f}  "
            f"Y {b_mm[1]:.2f}..{b_mm[4]:.2f}  "
            f"Z {b_mm[2]:.2f}..{b_mm[5]:.2f}"
        )
    if xs:
        print(
            f"Caja global (mm): X {min(xs):.2f}..{max(xs):.2f}  "
            f"Y {min(ys):.2f}..{max(ys):.2f}  "
            f"Z {min(zs):.2f}..{max(zs):.2f}"
        )
    mp = _v(doc.Extension.CreateMassProperty)
    if mp is not None:
        print("Volumen total: %.1f mm3" % (_v(mp.Volume) * 1e9))
    return nb


def export_part_and_views(doc, base_path: str):
    """Guarda .SLDPRT, .STEP y las 5 vistas estándar en .BMP."""
    os.makedirs(os.path.dirname(base_path), exist_ok=True)
    err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    wrn = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    doc.Extension.SaveAs(base_path + ".SLDPRT", 0, 1, NOTHING, err, wrn)
    doc.Extension.SaveAs(base_path + ".STEP", 0, 1, NOTHING, err, wrn)
    for vname, vid in (("iso", 7), ("planta", 5), ("alzado", 1), ("lateral", 4), ("inferior", 6)):
        doc.ShowNamedView2("*" + vname, vid)
        _v(doc.ViewZoomtofit2)
        doc.SaveBMP(f"{base_path}_{vname}.bmp", 1600, 1000)
    doc.ShowNamedView2("*Isometric", 7)
    _v(doc.ViewZoomtofit2)
    print("Guardado:", base_path + ".SLDPRT / .STEP")
