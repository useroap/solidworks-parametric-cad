# 🤖 Arquitectura Prompt-to-CAD & Ingeniería Inversa de MecAgent Copilot

Esta guía detalla la arquitectura para crear y automatizar modelos 3D paramétricos en **SolidWorks 2025** a partir de prompts en lenguaje natural, incorporando las mejores prácticas de ingeniería descubiertas en la ingeniería inversa de **MecAgent Copilot**.

---

## 1. ¿Cómo funciona MecAgent Copilot por dentro? (Hallazgos de Reverse Engineering)

MecAgent Copilot (`mecagent-app`) implementa una arquitectura híbrida cliente-nube altamente optimizada:

```
+-------------------------------------------------------------+
|                MecAgent Companion (Electron/React)         |
|  - UI Flotante / Acoplada junto a SolidWorks (Three.js/OCCT) |
|  - Previsualizador 3D interactivo con WebAssembly           |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             Event Collector (collectionWorker.js)           |
|  - Escucha eventos COM de SolidWorks en tiempo real         |
|  - SelectionChanged (Caras, Aristas, Vértices seleccionados) |
|  - FeatureTreeChanged & DocumentActivated                   |
|  - Mantiene el contexto sincronizado                        |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|               Cloud Agent (proxy.mecagent.com)              |
|  - Orquesta el prompt, el contexto de selección y bosquejos |
|  - Intención: CAD Copilot, DrawingToCad, CadToDrawing       |
|  - Genera comandos C# / Roslyn por celdas interactivas      |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|         In-Process Roslyn Runner (MecAgent.Runner.exe)       |
|  - Compila C# en caliente con Roslyn Scripting              |
|  - Reescritura AST: intercepta Activator y enlaza swApp     |
|  - CellEffectAnalyzer: detecta efectos y bucles peligrosos  |
|  - Timeouts de seguridad (1s-2s) para evitar colgar CAD     |
|  - Captura ortogonal (_view_capture: front, top, iso.png)   |
+-------------------------------------------------------------+
```

---

## 2. Nuestra Arquitectura Nativa Prompt-to-CAD (Python + COM)

En lugar de depender de servidores en la nube cerrados o suscripciones de pago, replicamos este flujo completo de manera nativa, offline y gratuita en nuestro repositorio:

| Componente MecAgent | Nuestra Implementación Nativa | Ventajas |
| :--- | :--- | :--- |
| **Context Collector** | `scripts/sw_context_inspector.py` | Consulta en $O(1)$ documento activo, selección (caras/aristas) y árbol de operaciones sin sobrecarga. |
| **Execution Runner** | `scripts/sw_prompt_runner.py` + `run_in_interactive_session.ps1` | Ejecuta código de forma interactiva puenteando sandbox (`MK_E_UNAVAILABLE`), registra logs y analiza salida. |
| **Safety & Anti-Freeze** | Reglas `AGENTS.md` + `_v(x)` wrapper + `GetActiveObject` | Previene procesos zombies `SLDWORKS.exe` y fugas de memoria GDI. |
| **View Capture & Verificación** | Captura automática de vistas (`iso.png`, `front.png`, etc.) y propiedades de masa (masa en gramos, volumen, centro de masa). | Inspección visual instantánea y auditoría dimensional. |
| **Self-Healing Loop** | Diagnóstico estructurado JSON con errores de línea COM | Si SolidWorks rechaza una operación, el agente lee el traceback y repara el código automáticamente. |

---

## 3. Protocolo de 4 Pasos para Crear CAD con Prompts

Cuando el usuario pida: *"Crea una cubitera cónica de 200mm de alto con 2 asas y vaciado de 2.5mm"* o *"Redondea las aristas seleccionadas a 3mm"*:

### Paso 1: Inspeccionar el Contexto en Vivo
Ejecutar el inspector para saber qué está abierto y qué seleccionó el usuario:
```bash
python .agents/skills/solidworks-parametric-cad/scripts/sw_context_inspector.py
```
Salida JSON esperada:
```json
{
  "connected": true,
  "has_active_doc": true,
  "document": { "title": "Pieza1.SLDPRT", "type": "Part" },
  "selection": { "count": 2, "items": [{"type": "Edge", "name": "Edge1"}] },
  "feature_tree": { "features": [...] }
}
```

### Paso 2: Generar Código Paramétrico Autónomo
- Si es una pieza nueva, crear carpeta en `tools/cad/<nombre_pieza>/`:
  - `params.py`: Dimensiones maestras en milímetros.
  - `build_sw.py`: Script SolidWorks derivado de `sw_base_template.py`.
- Si es una operación interactiva sobre la pieza actual:
  - Generar el bloque Python COM usando `swApp.ActiveDoc`, aplicando la operación sobre las caras/aristas detectadas en el Paso 1.

### Paso 3: Ejecución Interactiva con Auto-Sanación
Ejecutar mediante `sw_prompt_runner.py`:
```bash
python .agents/skills/solidworks-parametric-cad/scripts/sw_prompt_runner.py tools/cad/<nombre>/build_sw.py tools/cad/<nombre>
```
Si el resultado tiene `"success": false`:
- Analizar el campo `"error"` del JSON retornado.
- Reparar la selección, plano de croquis o método COM.
- Re-ejecutar hasta obtener `"success": true`.

### Paso 4: Verificación Visual & Entrega
- Revisar las imágenes generadas (`iso.png`, `alzado.png`, `planta.png`).
- Verificar que el árbol de operaciones quedó limpio y el croquis 100% definido (líneas negras).
- Exportar `.STEP` y generar plano técnico si se requiere.
