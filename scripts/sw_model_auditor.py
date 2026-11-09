# -*- coding: utf-8 -*-
"""
sw_model_auditor.py - Herramienta Universal de Auditoria Geometrica Real (Solo Lectura)
Valida las 5 Invariantes Fisicas en SolidWorks 2025 para prevenir reportes falsos positivos.

Uso CLI:
  python sw_model_auditor.py "<ruta_sldprt>" [--baseline "<ruta_base_sldprt>"] [--params "D1@Croquis1,D2@Croquis2"] [--json]
"""
import os, sys, argparse, json, types
import pythoncom
import win32com.client
from win32com.client import VARIANT

def _v(x):
    return x() if isinstance(x, types.MethodType) else x

def audit_part(sw, part_path, target_params=None):
    if not os.path.exists(part_path):
        return {"error": f"Archivo no existe: {part_path}"}

    part_name = os.path.basename(part_path)
    # Cerrar si ya estaba abierto en modo interactivo para garantizar solo lectura limpia
    try:
        sw.CloseDoc(part_name)
    except Exception:
        pass

    err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    wrn = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    # 1 = swDocPART, 1 | 2 = swOpenDocOptions_Silent | swOpenDocOptions_ReadOnly
    doc = sw.OpenDoc6(part_path, 1, 1 | 2, "", err, wrn)
    if not doc:
        return {"error": f"No se pudo abrir en SolidWorks: {part_path} (Err={int(err.value)})"}

    res = {
        "file_name": part_name,
        "file_path": part_path,
        "file_size_bytes": os.path.getsize(part_path),
        "parameters": {},
        "total_features": 0,
        "suppressed_features": [],
        "solid_bodies": [],
        "surface_bodies_count": 0,
        "error_features": [],
        "verdict": "UNKNOWN"
    }

    # 1. Auditoria de Parametros
    if target_params:
        for p_name in target_params:
            p_obj = doc.Parameter(p_name.strip())
            if p_obj:
                res["parameters"][p_name.strip()] = {
                    "value_mm": round(_v(p_obj.SystemValue) * 1000.0, 4),
                    "exists": True
                }
            else:
                res["parameters"][p_name.strip()] = {"value_mm": None, "exists": False}

    # 2. Auditoria del Arbol de Operaciones
    feat = _v(doc.FirstFeature)
    while feat:
        res["total_features"] += 1
        fname = _v(feat.Name)
        ftype = _v(feat.GetTypeName2)
        if _v(feat.IsSuppressed):
            res["suppressed_features"].append(fname)
        err_code = 0
        try:
            err_code = feat.GetErrorCode()
        except Exception:
            pass
        if err_code != 0:
            res["error_features"].append({"name": fname, "type": ftype, "error_code": err_code})
        feat = _v(feat.GetNextFeature)

    # 3. Auditoria de Cuerpos Solidos
    bods = doc.GetBodies2(0, False) or []
    for b in bods:
        bb = _v(b.GetBodyBox)
        mp = b.GetMassProperties(1000.0)
        vol_mm3 = round(mp[3] * 1e9, 2) if mp else 0.0
        area_mm2 = round(mp[4] * 1e6, 2) if mp else 0.0
        bbox_dict = None
        if bb:
            bbox_dict = {
                "x_min": round(bb[0] * 1000.0, 2),
                "x_max": round(bb[3] * 1000.0, 2),
                "y_min": round(bb[1] * 1000.0, 2),
                "y_max": round(bb[4] * 1000.0, 2),
                "z_min": round(bb[2] * 1000.0, 2),
                "z_max": round(bb[5] * 1000.0, 2),
                "dx": round((bb[3] - bb[0]) * 1000.0, 2),
                "dy": round((bb[4] - bb[1]) * 1000.0, 2),
                "dz": round((bb[5] - bb[2]) * 1000.0, 2)
            }
        res["solid_bodies"].append({
            "name": _v(b.Name),
            "visible": bool(_v(b.Visible)),
            "volume_mm3": vol_mm3,
            "surface_area_mm2": area_mm2,
            "bbox_mm": bbox_dict
        })

    # 4. Auditoria de Cuerpos de Superficie
    surfs = doc.GetBodies2(1, False) or []
    res["surface_bodies_count"] = len(surfs)

    # 5. Calculo de Veredicto de Salud B-Rep
    visible_solids = [b for b in res["solid_bodies"] if b["visible"]]
    if res["surface_bodies_count"] > 0 and len(visible_solids) == 0:
        res["verdict"] = "BROKEN_SURFACE_LEAK"
    elif len(visible_solids) == 0:
        res["verdict"] = "NO_VISIBLE_SOLID"
    elif len(res["suppressed_features"]) > 0:
        res["verdict"] = "UNEXPECTED_SUPPRESSIONS"
    else:
        res["verdict"] = "HEALTHY"

    sw.CloseDoc(part_name)
    return res

def compare_with_baseline(audit_test, audit_base):
    comp = {
        "volume_ratio": None,
        "delta_volume_pct": None,
        "delta_bbox_mm": {},
        "param_differences": {}
    }
    # Tomar solidos visibles principales
    sol_test = next((b for b in audit_test.get("solid_bodies", []) if b["visible"]), None)
    sol_base = next((b for b in audit_base.get("solid_bodies", []) if b["visible"]), None)

    if sol_test and sol_base and sol_base["volume_mm3"] > 0:
        v_test = sol_test["volume_mm3"]
        v_base = sol_base["volume_mm3"]
        ratio = v_test / v_base
        comp["volume_ratio"] = round(ratio, 3)
        comp["delta_volume_pct"] = round((ratio - 1.0) * 100.0, 2)

        bb_t = sol_test.get("bbox_mm") or {}
        bb_b = sol_base.get("bbox_mm") or {}
        for axis in ["dx", "dy", "dz"]:
            comp["delta_bbox_mm"][axis] = round(bb_t.get(axis, 0.0) - bb_b.get(axis, 0.0), 2)

    # Comparar parametros comunes
    p_t = audit_test.get("parameters", {})
    p_b = audit_base.get("parameters", {})
    for k, v in p_t.items():
        if k in p_b and v.get("value_mm") is not None and p_b[k].get("value_mm") is not None:
            diff = round(v["value_mm"] - p_b[k]["value_mm"], 4)
            comp["param_differences"][k] = {
                "base_mm": p_b[k]["value_mm"],
                "test_mm": v["value_mm"],
                "delta_mm": diff
            }

    return comp

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Auditor Real de Modelos SolidWorks 2025")
    parser.add_argument("part_path", help="Ruta del archivo .SLDPRT a auditar")
    parser.add_argument("--baseline", help="Ruta de la pieza base (.SLDPRT) para calcular variacion", default=None)
    parser.add_argument("--params", help="Lista de parametros separada por comas", default=None)
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON estructurado")
    args = parser.parse_args()

    pythoncom.CoInitialize()
    try:
        sw = win32com.client.GetActiveObject("SldWorks.Application")
    except Exception as e:
        err_msg = {"error": f"No se pudo conectar a SolidWorks activo: {e}"}
        if args.json:
            print(json.dumps(err_msg, indent=2))
        else:
            print(f"ERROR: {err_msg['error']}")
        sys.exit(1)

    target_params = [p.strip() for p in args.params.split(",")] if args.params else None
    audit = audit_part(sw, os.path.abspath(args.part_path), target_params)

    comparison = None
    if args.baseline:
        base_audit = audit_part(sw, os.path.abspath(args.baseline), target_params)
        comparison = compare_with_baseline(audit, base_audit)
        audit["comparison_vs_baseline"] = comparison

    if args.json:
        print(json.dumps(audit, indent=2, ensure_ascii=False))
        return

    # Salida Tabular Humana
    print("\n" + "=" * 75)
    print(f"[AUDITORIA GEOMETRICA REAL] {audit.get('file_name')}")
    print("=" * 75)
    print(f"Veredicto:          {audit.get('verdict')}")
    print(f"Tamano archivo:     {audit.get('file_size_bytes', 0):,} bytes")
    print(f"Operaciones arbol:  {audit.get('total_features')} (Suprimidas: {len(audit.get('suppressed_features', []))})")
    if audit.get("suppressed_features"):
        print(f"  -> Suprimidas:    {', '.join(audit['suppressed_features'][:10])}")
    print(f"Cuerpos superficie: {audit.get('surface_bodies_count')} (Esperado: 0 para solido cerrado)")

    print(f"\nCuerpos Solidos ({len(audit.get('solid_bodies', []))}):")
    for i, b in enumerate(audit.get("solid_bodies", [])):
        bb = b.get("bbox_mm") or {}
        bbox_str = f"X[{bb.get('x_min')},{bb.get('x_max')}] Y[{bb.get('y_min')},{bb.get('y_max')}] Z[{bb.get('z_min')},{bb.get('z_max')}]"
        print(f"  [{i}] '{b['name']}' | Visible={b['visible']} | Vol={b['volume_mm3']:,.0f} mm3 | Area={b['surface_area_mm2']:,.0f} mm2")
        print(f"      Envolvente: {bbox_str} (dX={bb.get('dx')}, dY={bb.get('dy')}, dZ={bb.get('dz')} mm)")

    if audit.get("parameters"):
        print(f"\nParametros Clave:")
        for k, v in audit["parameters"].items():
            val_str = f"{v['value_mm']:.3f} mm" if v["value_mm"] is not None else "NO EXISTE"
            print(f"  {k:<22} = {val_str}")

    if comparison:
        print(f"\nComparativa vs Base ({os.path.basename(args.baseline)}):")
        if comparison.get("volume_ratio") is not None:
            pct_str = f"{comparison.get('delta_volume_pct'):+0.1f}%" if comparison.get("delta_volume_pct") is not None else "N/A"
            print(f"  Ratio de Volumen:   {comparison.get('volume_ratio')}x ({pct_str})")
        else:
            print("  Ratio de Volumen:   NO COMPARABLE (Sin solido visible valido en test o base)")
        if comparison.get("delta_bbox_mm"):
            print(f"  Delta Envolvente:   dX={comparison['delta_bbox_mm'].get('dx'):+0.1f} mm, dY={comparison['delta_bbox_mm'].get('dy'):+0.1f} mm, dZ={comparison['delta_bbox_mm'].get('dz'):+0.1f} mm")
        if comparison.get("param_differences"):
            print("  Cambios de Cota:")
            for pk, pv in comparison["param_differences"].items():
                print(f"    {pk:<20}: {pv['base_mm']:.2f} mm -> {pv['test_mm']:.2f} mm (Delta={pv['delta_mm']:+0.2f} mm)")

    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
