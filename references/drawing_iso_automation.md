---
title: "Subhabilidad: Automatización de Planos 2D con Formato ISO/ANSI Standard"
company: "CAD Automation"
module: "cad_drawings_iso_format"
date: 2026-10-29
tags:
  - solidworks
  - drawing-automation
  - iso_format
  - sheet-format
  - standard
---

# Subhabilidad: Automatización de Planos 2D con Formato ISO/ANSI Standard

Esta subhabilidad documenta la generación desatendida y automática de planos técnicos 2D (`.SLDDRW`, `.PDF`) en **SolidWorks 2025** utilizando el formato corporativo oficial de calidad **ISO/ANSI Standard (Carta Horizontal)** de **CAD Automation**.

---

## 1. Ubicación y Especificaciones del Formato ISO/ANSI Standard

- **Ubicación Oficial del Rótulo:**
  `C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\lang\spanish\sheetformat\a_landscape.slddrt`
- **Plantilla Base de Dibujo:**
  `C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Dibujo.drwdot`
- **Tamaño de Hoja:** Carta Horizontal (ANSI A Landscape):
  - Ancho: $279.4\text{ mm}$ ($0.2794\text{ m}$)
  - Alto: $215.9\text{ mm}$ ($0.2159\text{ m}$)
  - Código SolidWorks: `12` (`swDwgPapersUserDefined`)

---

## 2. Flujo de Generación de un Plano

```
[Modelo 3D Activo (.SLDPRT)]
            │
            ▼
1. Crear Documento de Dibujo (NewDocument + drwdot)
            │
            ▼
2. Asignar y Recargar Formato de Hoja (a_landscape.slddrt)
            │
            ▼
3. Cálculo de Escala Automática según Dimensiones de la Pieza
            │
            ▼
4. Inserción de Vistas del Modelo:
   ├── Vista Frontal (*Alzado) en (X=80 mm, Y=120 mm)
   ├── Vista Superior (*Superior / Planta) en (X=80 mm, Y=50 mm)
   ├── Vista Lateral (*Vista lateral) en (X=160 mm, Y=120 mm)
   └── Vista Isométrica (*Isométrica) en (X=210 mm, Y=60 mm) en Modo Sombreado
            │
            ▼
5. Anotaciones Automáticas (Líneas de centro, marcas de centro y cotas de modelo)
```

---

## 3. Código Maestro de Automatización en Python (`pywin32`)

```python
import os
import win32com.client
from win32com.client import VARIANT
import pythoncom

NOTHING = VARIANT(pythoncom.VT_DISPATCH, None)

def generate_iso_format_drawing(model_doc, out_dwg_path: str = None):
    """
    Crea un plano 2D normalizado ISO/ANSI Standard a partir del modelo activo de pieza.
    """
    sw = win32com.client.GetActiveObject("SldWorks.Application")
    model_path = model_doc.GetPathName
    if not model_path:
        raise ValueError("El modelo debe estar guardado en disco antes de generar su plano.")

    # 1. Crear documento de dibujo
    template_path = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Dibujo.drwdot"
    format_path = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\lang\spanish\sheetformat\a_landscape.slddrt"
    
    # 2. Calcular escala óptima según dimensiones de la pieza (BBox)
    bodies = model_doc.GetBodies2(0, True)
    scale_num, scale_den = 1, 1
    if bodies:
        bb = bodies[0].GetBodyBox
        dx = (bb[3] - bb[0]) * 1000.0 # mm
        dy = (bb[4] - bb[1]) * 1000.0 # mm
        dz = (bb[5] - bb[2]) * 1000.0 # mm
        max_dim = max(dx, dy, dz)
        
        # Selección rigurosa de escala para papel Carta (279.4 x 215.9 mm)
        if max_dim <= 40:
            scale_num, scale_den = 2, 1   # 2:1
        elif max_dim <= 90:
            scale_num, scale_den = 1, 1   # 1:1
        elif max_dim <= 180:
            scale_num, scale_den = 1, 2   # 1:2
        elif max_dim <= 280:
            scale_num, scale_den = 1, 4   # 1:4
        else:
            scale_num, scale_den = 1, 5   # 1:5 (Piezas grandes como cortavientos > 350 mm)

    # 3. NewDocument e instanciación con SetupSheet5 para carga física del cajetín
    # NOTA CRÍTICA: sheet.ReloadTemplate(False) NO carga el rótulo si la plantilla inicial era vacía.
    # Se DEBE usar SetupSheet5 indicando el formato .slddrt explícitamente.
    draw_doc = sw.NewDocument(template_path, 12, 0.2794, 0.2159)
    if not draw_doc:
        raise RuntimeError("No se pudo instanciar la plantilla de dibujo.")

    sheet = draw_doc.GetCurrentSheet
    sheet_name = sheet.GetName() if hasattr(sheet, "GetName") else "Hoja1"
    
    # SetupSheet5(Name, PaperSize, TemplateIn, Scale1, Scale2, FirstAngle, TemplateName, Width, Height, PropertyViewName, RemoveModifiedNotes)
    # TemplateIn=0 (swTemplateCustom), FirstAngle=False (Third Angle / ISO americano estándar), RemoveModifiedNotes=True
    draw_doc.SetupSheet5(sheet_name, 12, 0, scale_num, scale_den, False, format_path, 0.2794, 0.2159, "", True)

    # 4. Proyectar Vistas Ortogonales centradas
    # CreateDrawViewFromModelView3(ModelPath, ViewName, X, Y, Z) en metros
    v_front = draw_doc.CreateDrawViewFromModelView3(model_path, "*Alzado", 0.090, 0.130, 0.0)
    v_top = draw_doc.CreateDrawViewFromModelView3(model_path, "*Superior", 0.090, 0.055, 0.0)
    v_right = draw_doc.CreateDrawViewFromModelView3(model_path, "*Vista lateral", 0.185, 0.130, 0.0)
    v_iso = draw_doc.CreateDrawViewFromModelView3(model_path, "*Isométrica", 0.215, 0.065, 0.0)

    # 5. Forzar escala de hoja en cada vista proyectada para evitar vistas microscópicas
    for v in [v_front, v_top, v_right, v_iso]:
        if v:
            v.UseSheetScale = 1  # Forzar herencia de escala 1:scale_den de la hoja

    # 6. Configurar la vista isométrica sombreada con aristas
    if v_iso:
        # SetDisplayMode3(UseParent=False, DisplayMode=3 (swShadedWithEdges), Facetted=False, Edges=True)
        v_iso.SetDisplayMode3(False, 3, False, True)

    # 7. Insertar Marcas de Centro Automáticas en agujeros y círculos
    draw_doc.Extension.InsertCenterMark2(1, 0, False, False, False, 0, 0, False, False, 0)
    draw_doc.ForceRebuild3(False)

    # 8. Guardar archivo si se especificó ruta
    if out_dwg_path:
        err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        wrn = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        draw_doc.Extension.SaveAs(out_dwg_path, 0, 1, NOTHING, err, wrn)
        print(f"Plano ISO/ANSI Standard guardado en: {out_dwg_path}")

    return draw_doc
```

---

## 4. Rótulo de Calidad y Metadatos de Ingeniería

El formato `a_landscape.slddrt` lee propiedades personalizadas del archivo 3D. Para que el cajetín se rellene solo sin edición manual:

```python
cust_prop = model_doc.Extension.CustomPropertyManager("")
cust_prop.Add3("CLIENTE", 30, "CLIENTE INDUSTRIAL", 1)
cust_prop.Add3("DESCRIPCION", 30, "COMPONENTE MODULAR Ø63 mm", 1)
cust_prop.Add3("MATERIAL", 30, "POLIPROPILENO (PP)", 1)
cust_prop.Add3("DIBUJO", 30, "INGENIERÍA DE DISEÑO", 1)
cust_prop.Add3("CODIGO_FORMATO", 30, "ISO/ANSI Standard", 1)
```
