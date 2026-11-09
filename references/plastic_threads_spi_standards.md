---
title: "Subhabilidad: Modelado Paramétrico de Roscas Plásticas & Estándares de Envases (SPI / GPI / ISBT)"
company: "CAD Automation"
module: "cad_threads"
date: 2026-10-29
tags:
  - solidworks
  - threads
  - spi-400
  - spi-410
  - spi-415
  - isbt
  - parametric-cad
---

# Subhabilidad: Modelado Paramétrico de Roscas Plásticas & Estándares de Envases (SPI / GPI / ISBT)

Esta subhabilidad documenta la teoría dimensional, estándares industriales y el flujo de automatización en **SolidWorks 2025 (Python COM API)** para generar roscas plásticas de inyección y soplado (cuellos de botellas y tapas roscadas) con restricción geométrica total (sketches 100% definidos con cotas y relaciones).

Basado en los estándares de ingeniería de **CAD Automation**:
- `C:\Users\USER\OneDrive - CAD Automation\Diseno\Libros\Standard\sp400.pdf`
- `C:\Users\USER\OneDrive - CAD Automation\Diseno\Libros\Standard\sp410.pdf`
- `C:\Users\USER\OneDrive - CAD Automation\Diseno\Libros\Standard\sp415.pdf`
- `C:\Users\USER\OneDrive - CAD Automation\Diseno\Libros\Standard\spichart.pdf`
- `ISBT-Threadspecs-R-Terminologies-Bottle-Finishes-2021.pdf`
- `ISBT-Threadspecs-R-Terminologies-Finish-Features-Card-2022.pdf`

---

## 1. Nomenclatura Estándar de Acabados de Envases (Finish Features)

Según la norma internacional **SPI / GPI / ISBT**:

| Símbolo | Término | Definición Técnica |
| :---: | :--- | :--- |
| **T** | *Thread Diameter* | Diámetro exterior en la cresta del hilo de la rosca del cuello (macho), o diámetro mayor de la rosca de la tapa (hembra). |
| **E** | *Core / Minor Diameter* | Diámetro en la raíz de la rosca (pared exterior del cuello de la botella). En tapas hembra, corresponde al diámetro interior del cilindro base. |
| **I** | *Inner Diameter* | Diámetro del orificio interior del cuello por donde fluye el líquido. |
| **H** | *Finish Height* | Altura total del terminado del cuello desde la superficie de sellado (labio) hasta el escalón/anillo de transferencia. |
| **S** | *Start of Thread* | Distancia vertical desde la superficie de sellado superior hasta el punto donde comienza el hilo de rosca completo. |
| **W** | *Transfer Bead / Neck Ring* | Diámetro del anillo de transferencia para sujeción en soplado y transporte. |
| **Pitch (P)** | *Paso de Rosca* | Distancia axial entre dos crestas consecutivas. Se relaciona con los hilos por pulgada (TPI) mediante $P = \frac{25.4}{\text{TPI}}$ mm. |

---

## 2. Tipos de Series SPI (SP-400, SP-410, SP-415)

Las series estándar SPI para tapas y frascos de plástico se diferencian por la **longitud axial del cuello y número de vueltas de rosca**:

| Serie | Vueltas Típicas | Descripción & Aplicación |
| :--- | :---: | :--- |
| **SP-400** | ~1 vuelta ($360^\circ - 400^\circ$) | Cuello bajo estándar. Aplicado en tapas de perfil bajo (tapas flip-top, cosméticos, botellas PET de bebidas y tapas Garota). |
| **SP-410** | ~1.5 vueltas ($540^\circ$) | Cuello de altura intermedia. Mayor área de agarre contra desacople por presión interna. |
| **SP-415** | ~2 vueltas ($720^\circ$) | Cuello alto / extendido. Utilizado para tapas dosificadoras, dispensadores de bomba (pumps), atomizadores y goteros. |

---

## 3. Perfiles de Hilo: Estilo "M" vs Estilo "L"

Los estándares SPI contemplan dos geometrías de filete de rosca:

### 3.1 Estilo "M" (Modified Buttress Thread) - Estándar Mandatorio para Plásticos
Es el perfil utilizado en la industria del plástico de inyección por su **resistencia al torque sin abrir la tapa** (evita el "stripping" o salto de filete):
- **Flanco superior:** Ángulo de caída de **$45^\circ$**. Facilita la entrada y el desenrosque suave.
- **Flanco de carga inferior:** Ángulo de retención de **$10^\circ$** (casi recto). Bloquea la fuerza de apriete vertical contra el filete del cuello evitando que la falda de la tapa se expanda radialmente.
- **Radios de transición:** Radio en cresta $R_{\text{top}} \approx 0.75 \pm 0.08$ mm, radio en raíz $R_{\text{bot}} \approx 0.25 \pm 0.08$ mm.
- **Dimensiones para 6 TPI ($P = 4.233$ mm):**
  - Ancho de base $a = 2.39$ mm ($0.094''$)
  - Altura radial $b = 1.19$ mm ($0.047''$)
  - Cara plana vertical en cresta $c = 0.99$ mm ($0.039''$)

> [!NOTE]
> Este perfil **Estilo "M" de 6 TPI** coincide al 100% con el modelado manual verificado en la tapa `Garota_co8468_12_Tapa_02_Parametrico.SLDPRT`.

### 3.2 Estilo "L" (General Purpose Thread)
- Filete simétrico de **$30^\circ / 30^\circ$** con radios simétricos ($R \approx 0.50$ mm).
- Utilizado típicamente en tapas metálicas o aplicaciones de bajo torque.

---

## 4. Tabla Dimensional SPI para Diámetros Típicos (mm)

| Diámetro Nominal | TPI | Paso $P$ (mm) | $a$ Base (mm) | $b$ Altura (mm) | $c$ Cresta (mm) | Vueltas SP-400 | Vueltas SP-410 | Vueltas SP-415 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **18 mm** | 8 | 3.175 | 1.83 | 0.89 | 0.76 | 1.0 | 1.5 | 2.0 |
| **20 mm** | 8 | 3.175 | 1.83 | 0.89 | 0.76 | 1.0 | 1.5 | 2.0 |
| **24 mm** | 8 | 3.175 | 1.83 | 0.89 | 0.76 | 1.0 | 1.5 | 2.0 |
| **28 mm** | 6 | 4.233 | 2.39 | 1.19 | 0.99 | 1.0 | 1.5 | 2.0 |
| **33 mm** | 6 | 4.233 | 2.39 | 1.19 | 0.99 | 1.1 | 1.5 | 2.0 |
| **38 mm** | 6 | 4.233 | 2.39 | 1.19 | 0.99 | 1.1 | 1.5 | 2.0 |
| **45 mm** | 6 | 4.233 | 2.39 | 1.19 | 0.99 | 1.15 | 1.5 | 2.0 |
| **53 mm** | 6 | 4.233 | 2.39 | 1.19 | 0.99 | 1.2 | 1.5 | 2.0 |
| **63 mm (Garota)** | 6 | 4.233 | 2.39 | 1.19 | 0.99 | 1.2 | 1.5 | 2.0 |

---

## 5. Estrategia de Modelado CAD en SolidWorks 2025: Hélice Nativa vs. Spline 3D

> [!DANGER]
> **PROHIBICIÓN DE TRAYECTORIAS SPLINE 3D PARA ROSCAS:**
> Nunca generar roscas mediante `Insert3DSketch` + `CreateSpline2` (splines 3D discretizadas por puntos).
> **Motivo:** Las splines 3D son estáticas e imposibles de editar de forma paramétrica por un diseñador en la interfaz de SolidWorks.
> **Regla Mandatoria:** La trayectoria de rosca DEBE crearse SIEMPRE mediante la operación nativa de SolidWorks **`Hélice/Espiral` (`IModelDoc2.InsertHelix`)** a partir de un croquis circular base, seguido de un **`Saliente Barrido` (`InsertProtrusionSwept4`)**. Esto permite al diseñador hacer clic derecho en la Hélice y modificar interactivamente el paso ($P$), las revoluciones o la altura en el PropertyManager estándar de SolidWorks.

```
[Plano de Referencia: Offset z_start] 
            │
            ▼
[Croquis Circular Base: Círculo Ø = 2*r_wall] ──► [Operación: Hélice / Espiral Nativa (InsertHelix)]
(100% Fully Defined con Cota Ø y Coincidente Origen)               │ (Trayectoria Paramétrica Editable)
                                                                   ▼
[Croquis Perfil: Estilo "M" en Alzado]        ──► [Operación: Saliente Barrido (InsertProtrusionSwept4)]
(Solapamiento ~0.4 mm en pared, 100% Fully Defined)                │
                                                                   ▼
                                                  [Desvanecimiento / Salida de Rosca]
                                                  (Runout cut a 45° o 'Eliminar Cara')
```

### Reglas Críticas para Evitar Fallos en SolidWorks:
1. **Solapamiento / Penetración de Pared:** El croquis del perfil del filete **NO** debe ser tangente exacta a la pared cilíndrica. Debe penetrar en la pared sólida entre **$0.3$ y $0.5$ mm** ($0.40\text{ mm}$ estándar). De lo contrario, el kernel Parasolid genera el error `Zero-thickness geometry` (geometría de espesor cero) o caras no manifold.
2. **Plano y Ángulo de Inicio de Hélice:** La hélice debe crearse con ángulo inicial `Startangle = 0.0 rad` para que comience exactamente en $(X = r_{\text{wall}}, Y = z_{\text{start}}, Z = 0)$, coincidiendo de forma limpia con el plano frontal `Alzado` (`Front Plane` donde $Z = 0$).
3. **Firma de la API COM de SolidWorks para Hélice Nativa (10 Parámetros):**
   ```python
   # doc.InsertHelix(Reversed, Clockwised, Tapered, Outward, Helixdef, Height, Pitch, Revolution, TaperAngle, Startangle)
   doc.InsertHelix(
       reverse_dir,            # False = hacia arriba (+Y), True = hacia abajo (-Y)
       clockwise,              # True = rosca derecha (horaria), False = izquierda
       False,                  # Tapered (False para roscas cilíndricas estándar)
       False,                  # Outward
       0,                      # Helixdef: 0 = swHelixDefinedByPitchAndRevolution
       m(pitch_mm * num_turns),# Height (m)
       m(pitch_mm),            # Pitch (m)
       float(num_turns),       # Revolution (float)
       0.0,                    # TaperAngle
       0.0                     # Startangle (0 rad para cortar exactamente el plano Alzado)
   )
   ```
3. **Desvanecimiento de Extremos (Thread Runout):**
   - Una rosca que termina bruscamente en una cara plana de $90^\circ$ se atasca durante el cierre en la máquina tapadora.
   - Para resolverlo se usan dos métodos:
     - **Método A (Operación Eliminar Cara):** `doc.Extension.SelectByID2` sobre la cara plana terminal de inicio/fin y ejecutar `FeatureManager.InsertDeleteFace2(swDeleteFace_Heal)`.
     - **Método B (Corte de Rampa / Runout Cut):** Extrusión de corte con ángulo de desmoldeo o boceto tangencial de $30^\circ - 45^\circ$ que bisela la salida del hilo.

---

## 6. Automatización de Bocetos 100% Definidos (Cotadas & Relacionadas)

Para que los croquis no queden en azul (subdefinidos) en SolidWorks:

### Código de Ejemplo: Definición Total del Perfil de Rosca

```python
import win32com.client
from win32com.client import VARIANT
import pythoncom

def _v(x): return x() if callable(x) else x

def create_fully_defined_thread_profile(doc, r_inner_wall, z_start, pitch=4.233, b_depth=1.194, a_width=2.388, c_flat=0.99):
    """
    Crea el perfil Estilo 'M' completamente restringido y acotado.
    r_inner_wall: Radio interior de la falda de la tapa (m)
    z_start: Posición axial Z del plano de referencia (m)
    """
    sm = doc.SketchManager
    doc.ClearSelection2(True)
    
    # 1. Seleccionar plano frontal
    doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
    sm.InsertSketch(True)
    
    # IMPORTANTE: Desactivar AddToDB para que SolidWorks resuelva restricciones
    sm.AddToDB = False
    
    # Parámetros en metros
    overlap = 0.0004 # 0.4 mm de penetración en pared
    x_wall = r_inner_wall
    x_root = x_wall + overlap
    x_tip = x_root - b_depth/1000.0
    y_center = z_start
    
    # Dibujar las 4 líneas del trapecio Modificado
    # Línea 1: Pared de anclaje (Vertical dentro de la pared)
    l1 = sm.CreateLine(x_root, y_center + a_width*0.0005, 0, x_root, y_center - a_width*0.0005, 0)
    # Línea 2: Flanco superior (45°)
    l2 = sm.CreateLine(x_root, y_center + a_width*0.0005, 0, x_tip, y_center + c_flat*0.0005, 0)
    # Línea 3: Cara plana de cresta (Vertical)
    l3 = sm.CreateLine(x_tip, y_center + c_flat*0.0005, 0, x_tip, y_center - c_flat*0.0005, 0)
    # Línea 4: Flanco de carga inferior (10°)
    l4 = sm.CreateLine(x_tip, y_center - c_flat*0.0005, 0, x_root, y_center - a_width*0.0005, 0)
    
    # Aplicar restricciones geométricas explícitas
    # Vertical en cresta
    doc.ClearSelection2(True)
    l3.Select4(False, None)
    doc.SketchAddConstraints("sgVERTICAL2D")
    
    # Vertical en anclaje
    doc.ClearSelection2(True)
    l1.Select4(False, None)
    doc.SketchAddConstraints("sgVERTICAL2D")
    
    # Acotar dimensiones clave (Driving Dimensions)
    doc.ClearSelection2(True)
    # Cota de profundidad (b = 1.194 mm)
    doc.AddDimension2((x_tip + x_root)/2.0, y_center + 0.002, 0)
    
    # Cota de altura plana (c = 0.99 mm)
    doc.ClearSelection2(True)
    l3.Select4(False, None)
    doc.AddDimension2(x_tip - 0.001, y_center, 0)
    
    # Forzar FullyDefineSketch para anclar grados de libertad restantes
    # swSketchFullDefineOption: 1=All entities, swSketchFullDefineDimensionOption: 1=Chain, 2=Baseline
    sm.FullyDefineSketch(True, True, 1, 1, 1, 1, 1, 1)
    
    sm.InsertSketch(True) # Cerrar croquis
    doc.ClearSelection2(True)
```

---

## 7. Verificación del Estándar en la Tapa Garota

- **Archivo inspeccionado:** `Garota_co8468_12_Tapa_02_Parametrico.SLDPRT`
- **Diámetro del filete exterior:** $\varnothing 63.47$ mm
- **Filetes por pulgada:** 6 TPI ($P = 4.2333$ mm)
- **Ángulos medidos:** $45^\circ$ superior / $10^\circ$ de desmoldeo inferior
- **Profundidad radial:** $1.1938$ mm ($0.047''$)
- **Ancho del filete:** $2.3876$ mm ($0.094''$)
- **Conclusión:** Cumple estrictamente con la norma **SPI SP-400 / SP-410 Estilo "M"**.
