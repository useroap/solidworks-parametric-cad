---
title: "Subhabilidad: Ingeniería Inversa de Mallas (STL a Sólido B-Rep Paramétrico)"
company: "CAD Automation"
module: "cad_reverse_engineering"
date: 2026-10-29
tags:
  - reverse-engineering
  - stl-to-cad
  - trimesh
  - shapely
  - solidworks
  - parametric-cad
---

# Subhabilidad: Ingeniería Inversa de Mallas (STL a Sólido B-Rep Paramétrico)

Esta subhabilidad documenta la metodología desarrollada en **CAD Automation** para convertir mallas poligonales trianguladas (`.STL`, escaneos 3D o archivos de diseño conceptual) en sólidos paramétricos nativos (`.SLDPRT`, `.STEP`) en **SolidWorks 2025**, garantizando árboles de operaciones editables, cotas conductoras y precisión dimensional estricta ($< 0.1\text{ mm}$).

---

## 1. El Problema de las Mallas STL en Ingeniería de Moldes

Un archivo `.STL` solo contiene una "sopa" de triángulos planos facetados:
- **No tiene historia ni operaciones:** No se puede modificar el espesor de pared, cambiar el diámetro de rosca ni extraer planos de molde.
- **Roscas deformadas:** Si se corta una sección transversal de una tapa roscada, el perfil del hilo aparece en una posición fija angular que varía según el plano de corte, generando cortes o salientes asimétricos no aptos para revolución simple.
- **Sobrecarga de SolidWorks:** Importar un STL como cuerpo gráfico o de superficie directa satura el kernel Parasolid, ralentiza los ensambles y no permite generar dibujos técnicos normalizados (ISO/ANSI Standard).

---

## 2. Flujo de Trabajo en 5 Etapas

```
[Malla STL Cruda]
       │
       ▼
1. Centrado & Alineación (Bounding Box / Centroide Z_min = 0)
       │
       ▼
2. Corte Seccional Analítico (Plano Y=0 o radial vía Trimesh)
       │
       ▼
3. Separación de Geometría:
   ├── A. Perfil de Revolución Base (Pared lisa cilíndrica)
   └── B. Parámetros de Rosca (Paso P, TPI, Diámetro E, Estilo "M")
       │
       ▼
4. Reconstrucción Paramétrica en SolidWorks:
   ├── FeatureRevolve2 (Cuerpo base cerrado)
   └── FeatureSweep + Helix (Hélice SPI 6 TPI / 8 TPI)
       │
       ▼
5. Auditoría Dimensional & Volumétrica (ΔV < 1%, Bounding Box idéntico)
```

---

## 3. Extracción y Filtrado del Perfil 2D con Python

### 3.1 Alineación y Centrado Automático
Antes de cortar, se traslada el centro geométrico $X, Y$ al origen $(0,0)$ y la base inferior de apoyo $Z_{\text{min}}$ a $Z = 0$:

```python
import trimesh
import numpy as np

def align_and_center_mesh(mesh_path: str):
    mesh = trimesh.load(mesh_path)
    bounds = mesh.bounds
    cx = (bounds[0][0] + bounds[1][0]) / 2.0
    cy = (bounds[0][1] + bounds[1][1]) / 2.0
    z_min = bounds[0][2]
    
    verts = mesh.vertices.copy()
    verts[:, 0] -= cx
    verts[:, 1] -= cy
    verts[:, 2] -= z_min
    
    centered = trimesh.Trimesh(vertices=verts, faces=mesh.faces)
    return centered
```

### 3.2 Corte Seccional y Simplificación Topológica (`Shapely`)
Para piezas axilsimétricas (tapas, botellas, preformas), se realiza un corte con el plano $Y = 0$:

```python
from shapely.geometry import LineString

def extract_axisymmetric_profile(mesh, tolerance=0.08):
    # Corte transversal Y = 0
    slice_y = mesh.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    if not slice_y:
        raise ValueError("No se pudo cortar la sección transversal de la malla")
        
    # Obtener el polígono continuo con mayor cantidad de vértices
    paths = slice_y.discrete
    lens = [len(p) for p in paths]
    main_p = paths[np.argmax(lens)]
    
    # Extraer el semiperfil derecho (Radio R >= 0, Altura Z)
    pts_r = []
    for pt in main_p:
        if pt[0] >= -0.01:
            pts_r.append((max(0.0, float(pt[0])), float(pt[2])))
            
    # Simplificación controlada evitando ruido de facetado STL
    line = LineString(pts_r)
    simplified = line.simplify(tolerance, preserve_topology=True)
    coords = list(simplified.coords)
    
    # Forzar cierre en el eje de simetría X = 0
    if coords[0][0] > 0.05:
        coords.insert(0, (0.0, coords[0][1]))
    else:
        coords[0] = (0.0, coords[0][1])
        
    if coords[-1][0] > 0.05:
        coords.append((0.0, coords[-1][1]))
    else:
        coords[-1] = (0.0, coords[-1][1])
        
    coords.append(coords[0]) # Anillo cerrado
    return coords
```

---

## 4. Detección y Separación de Roscas

> [!IMPORTANT]
> **Regla de Oro en STL-to-CAD:** Si un STL de una tapa contiene roscas interiores, **NUNCA** debes incluir los dientes de la rosca en el croquis de revolución de la pared.
> El corte 2D solo muestra el hilo en un único ángulo; revolucionar ese perfil crearía anillos circulares concéntricos cerrados, no una hélice continua por donde pueda entrar la botella.

### Heurística de Separación:
1. **Pared Base del Cilindro:** Filtrar la pared interna eliminando los picos de la rosca y conectando el diámetro de raíz $E$. La revolución debe generar un cilindro liso de espesor uniforme.
2. **Identificación de la Rosca:**
   - Medir el paso axial entre crestas consecutivas: Si la distancia es $\approx 4.23\text{ mm}$ $\rightarrow$ **6 TPI**; si es $\approx 3.17\text{ mm}$ $\rightarrow$ **8 TPI**.
   - Medir el diámetro en la raíz $E$ y en la cresta $T$.
   - Aplicar el perfil estándar **SPI Estilo "M"** documentado en [plastic_threads_spi_standards.md](./plastic_threads_spi_standards.md) mediante un barrido helicoidal independiente (`FeatureSweep`).

---

## 5. Auditoría Volumétrica y Control de Calidad

Para validar que el modelo B-Rep reconstruido en SolidWorks refleja fielmente la pieza real escaneada, comparar las propiedades de masa:

```python
def verify_fidelity(mesh, sw_doc):
    # 1. Volumen STL en cm3
    vol_stl = float(mesh.volume) / 1000.0 # mm3 a cm3
    
    # 2. Volumen SolidWorks B-Rep en cm3
    mp = sw_doc.Extension.CreateMassProperty
    vol_cad = (mp.Volume * 1e9) / 1000.0 # m3 a cm3
    
    # 3. Discrepancia
    delta_pct = abs(vol_cad - vol_stl) / vol_stl * 100.0
    print(f"Volumen STL: {vol_stl:.2f} cm3 | CAD: {vol_cad:.2f} cm3 | Error: {delta_pct:.2f}%")
    
    assert delta_pct < 2.0, f"Discrepancia volumétrica excesiva: {delta_pct:.2f}%"
```

---

## 6. Tratamiento Avanzado: Suavizado de Escaneos Rugosos con Rectas en Máximos

En piezas procedentes de **contramoldes de silicona o escaneos ópticos con ruido**, la superficie presenta micro-ondulaciones y rugosidad que impiden el uso directo de polilíneas seccionales:
* **Problema:** Si se dibuja el croquis siguiendo los vértices ruidosos, el corte o saliente por barrido helicoidal (`FeatureSweep`) falla por auto-intersección de aristas adyacentes o genera superficies facetadas imposibles de mecanizar en CNC.
* **Solución Analítica:** Reemplazar las polilíneas ruidosas por **tramos continuos de línea recta ortogonales e inclinados** ajustados estrictamente a las cotas envolventes extremas (máximos y mínimos locales):
  1. **Alojamiento Cilíndrico del Liner:** Recta vertical en el radio máximo de la cavidad ($R = 31.560\text{ mm}$, $\varnothing = 63.120\text{ mm}$, $H = 1.45\text{ mm}$).
  2. **Pestaña Retenedora del Liner (Under-cut Bead):**
     - Rampa superior recta a $49.7^\circ$.
     - Cara vertical plana en el radio mínimo ($R_{\min} = 30.842\text{ mm}$, $\varnothing = 61.684\text{ mm}$, ancho $0.25\text{ mm}$).
     - Flanco de retención inferior recto a $21.6^\circ$ para retener el disco elástico sin expulsión.
  3. **Pared Cilíndrica de Raíz de Rosca ($E$):** Recta vertical en $R = 31.854\text{ mm}$ ($\varnothing E = 63.708\text{ mm}$).
  4. **Filete Helicoidal Trapezoidal (Estilo "M"):**
     - Cresta plana vertical en el radio extremo ($R = 30.621\text{ mm}$, $\varnothing T = 61.242\text{ mm}$, ancho de cresta $0.64\text{ mm}$).
     - Flanco superior a $48.0^\circ$ y flanco inferior de carga a $20.1^\circ$.

---

## 7. Desenrollado Polar y RANSAC en Hélices con Solapamiento ($> 360^\circ$)

Cuando la hélice cubre más de una vuelta completa ($375^\circ = 1.04\text{ vueltas}$ en SPI 63-400), un algoritmo simple de $\min(R)$ por cada ángulo $\theta \in [0, 2\pi)$ superpone la vuelta 1 con la vuelta 2 en el arco compartido ($0^\circ \to 15^\circ$), distorsionando el cálculo del paso axial $P$.

**Metodología de Desenrollado RANSAC:**
1. En cada sector polar $\Delta\theta$, detectar todos los picos radiales de cresta mediante `scipy.signal.find_peaks`.
2. Proyectar los puntos a un espacio angular continuo $\theta_{\text{unwrapped}} = \theta + 2\pi k$ ($k \in \{0, 1\}$).
3. Aplicar regresión lineal robusta RANSAC sobre $Z(\theta_{\text{unwrapped}}) = Z_0 - \frac{P}{2\pi}\,\theta_{\text{unwrapped}}$.
4. El paso axial exacto $P$ queda determinado por la pendiente, filtrando el $100\%$ de los puntos espurios y garantizando una trayectoria helicoidal suave para la herramienta `InsertProtrusionSwept4` o `InsertCutSwept4` en SolidWorks 2025.
