"""
sw_context_inspector.py - Inspector de Contexto en Tiempo Real para SolidWorks 2025
===================================================================================
Inspirado en el recolector de eventos y contexto de MecAgent Copilot.
Permite a cualquier agente de IA o prompt conocer exactamente:
  1. Modelo activo (Pieza, Ensamblaje, Plano) y configuración.
  2. Elementos seleccionados actualmente por el usuario (Caras, Aristas, Vértices, Croquis, Planos).
  3. Árbol de operaciones (Feature Tree) y su estado (suprimido/activo).
  4. Propiedades de masa y material del modelo.

Complejidad: O(1) en consulta de estado sin bucles infinitos ni llamadas a gc.collect().
Usa GetActiveObject() para evitar procesos zombies.
"""

import sys
import json
import os
import types

try:
    import win32com.client
    import pythoncom
except ImportError:
    print(json.dumps({"success": False, "error": "pywin32 not installed"}))
    sys.exit(1)

def _v(x):
    """Resuelve propiedades COM que puedan comportarse como métodos invocables."""
    return x() if isinstance(x, types.MethodType) else x

def get_doc_type_name(doc_type_int):
    types_map = {1: "Part", 2: "Assembly", 3: "Drawing"}
    return types_map.get(doc_type_int, f"Unknown ({doc_type_int})")

def get_selection_type_name(sel_type_int):
    types_map = {
        1: "Edge",
        2: "Face",
        3: "Vertex",
        4: "DatumPlane",
        5: "CoordinateSystem",
        6: "Sketch",
        9: "SketchSegment",
        10: "SketchPoint",
        13: "Dimension",
        15: "Component",
        20: "Feature",
        22: "Body",
        37: "ReferenceGeometry",
    }
    return types_map.get(sel_type_int, f"Type_{sel_type_int}")

def inspect_context():
    try:
        swApp = win32com.client.GetActiveObject("SldWorks.Application")
    except Exception as e:
        return {
            "success": False,
            "connected": False,
            "error": f"Could not connect to active SolidWorks session: {e}",
            "hint": "Ensure SolidWorks 2025 is running in the interactive session."
        }

    try:
        active_doc = _v(swApp.ActiveDoc)
        if not active_doc:
            return {
                "success": True,
                "connected": True,
                "has_active_doc": False,
                "message": "SolidWorks is running, but no document is open."
            }

        title = _v(active_doc.GetTitle) or ""
        path = _v(active_doc.GetPathName) or ""
        doc_type = _v(active_doc.GetType)
        doc_type_name = get_doc_type_name(doc_type)

        # Configuración activa
        active_config = ""
        try:
            config = _v(active_doc.GetActiveConfiguration)
            if config:
                active_config = _v(config.Name) or ""
        except:
            pass

        # Selección actual del usuario (SelectionManager)
        selections = []
        try:
            sel_mgr = _v(active_doc.SelectionManager)
            if sel_mgr:
                sel_count = sel_mgr.GetSelectedObjectCount2(-1)
                for i in range(1, min(sel_count + 1, 51)):  # max 50 items
                    sel_type = sel_mgr.GetSelectedObjectType3(i, -1)
                    sel_type_str = get_selection_type_name(sel_type)
                    sel_obj = sel_mgr.GetSelectedObject6(i, -1)
                    
                    obj_name = ""
                    if hasattr(sel_obj, "GetNameForSelection"):
                        try:
                            obj_name = sel_obj.GetNameForSelection()
                        except:
                            pass
                    
                    selections.append({
                        "index": i,
                        "type_id": sel_type,
                        "type": sel_type_str,
                        "name": obj_name
                    })
        except Exception as e:
            selections = [{"error": str(e)}]

        # Árbol de operaciones (Feature Tree)
        features = []
        try:
            feat = _v(active_doc.FirstFeature)
            feat_idx = 0
            while feat and feat_idx < 100:
                feat_name = _v(feat.Name)
                type_name = _v(feat.GetTypeName2)
                # Omitir características internas ruidosas
                if type_name not in ["HistoryFolder", "FavoriteFolder", "RefPlane", "OriginProfileFeature"]:
                    features.append({
                        "name": feat_name,
                        "type": type_name,
                    })
                feat = _v(feat.GetNextFeature)
                feat_idx += 1
        except Exception as e:
            features = [{"error": str(e)}]

        # Propiedades de masa (si es Part o Assembly)
        mass_info = {}
        if doc_type in [1, 2]:
            try:
                ext = _v(active_doc.Extension)
                mp = ext.CreateMassProperty()
                if mp:
                    mass_info = {
                        "mass_kg": round(float(_v(mp.Mass)), 6),
                        "mass_g": round(float(_v(mp.Mass)) * 1000.0, 3),
                        "volume_cm3": round(float(_v(mp.Volume)) * 1e6, 3),
                        "surface_area_cm2": round(float(_v(mp.SurfaceArea)) * 1e4, 3),
                        "center_of_mass_mm": [
                            round(c * 1000.0, 3) for c in _v(mp.CenterOfMass)
                        ] if _v(mp.CenterOfMass) else []
                    }
            except:
                pass

        return {
            "success": True,
            "connected": True,
            "has_active_doc": True,
            "document": {
                "title": title,
                "path": path,
                "type": doc_type_name,
                "configuration": active_config
            },
            "selection": {
                "count": len(selections),
                "items": selections
            },
            "feature_tree": {
                "count": len(features),
                "features": features
            },
            "mass_properties": mass_info
        }

    except Exception as e:
        return {
            "success": False,
            "connected": True,
            "error": f"Error inspecting active document: {e}"
        }

if __name__ == "__main__":
    context = inspect_context()
    
    # Asegurar directorio out
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "context.json")
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
        
    print(json.dumps(context, indent=2, ensure_ascii=False))
