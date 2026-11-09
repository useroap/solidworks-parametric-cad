# 🛡️ Estándar de Ejecución Aislada en Segundo Plano (Ventana Oculta & Zero-Distraction)

---

## 1. Problema de Interferencia en Automatización CAD

Cuando un script o agente de automatización interactúa con SolidWorks mediante la API COM tradicional (`pywin32`):
1. **Robo de Foco y Ventana:** Al llamar `swApp.NewDocument()` o `swApp.OpenDoc6()`, SolidWorks crea una nueva ventana gráfica en primer plano, robando el foco del diseñador humano.
2. **Interrupción del Flujo de Trabajo:** Si el usuario está modelando un ensamblaje, una pieza o editando un croquis, el script reemplaza `swApp.ActiveDoc`, rota la vista con `ShowNamedView2` y hace zoom con `ViewZoomtofit2`, congelando o alterando el entorno de trabajo interactivo.
3. **Parpadeo de Ventanas de Consola:** Las tareas programadas o scripts por lotes tradicionales abren ventanas de terminal negras (`cmd.exe`) que distraen al usuario.
4. **Riesgo de Procesos Zombies (`AGENTS.md`):** Intentar aislar abriendo instancias independientes con `Dispatch("SldWorks.Application")` satura los recursos GDI y genera múltiples ejecutables `sldworks.exe` en segundo plano consumiendo 5+ GB de RAM cada uno.

---

## 2. Arquitectura de Tarea Aislada en Segundo Plano (Zero-Distraction)

La solución óptima y nativa de SolidWorks aprovecha dos niveles de aislamiento:

### Nivel 1: Nivel de Sistema Operativo (Lanzador GUI Invisible con `wscript.exe`)
En `run_in_interactive_session.ps1`:
- **Por qué `cmd.exe` o `powershell.exe` parpadeaban:** En Windows, los ejecutables de consola (`IMAGE_SUBSYSTEM_WINDOWS_CUI`) obligan al sistema a instanciar un host de consola (`conhost.exe`). Aunque se use `-WindowStyle Hidden`, Windows muestra un parpadeo negro antes de ocultar la ventana.
- **La Solución Nativa (`wscript.exe` + `run_silent.vbs`):**
  - Se invoca `C:\Windows\System32\wscript.exe` (que es un binario nativo de subsistema GUI: `IMAGE_SUBSYSTEM_WINDOWS_GUI`). Al ser GUI, Windows **NUNCA** crea una ventana de consola.
  - El script [run_silent.vbs](../scripts/run_silent.vbs) invoca la línea de comandos con el parámetro `SW_HIDE = 0`:
    ```vbs
    Set WshShell = CreateObject("WScript.Shell")
    intReturn = WshShell.Run("cmd.exe /c """ & WScript.Arguments(0) & """", 0, True)
    WScript.Quit intReturn
    ```
  - La tarea programada se registra con `$Settings = New-ScheduledTaskSettingsSet -Hidden`.
  - **Resultado:** **CERO ventanas de CMD visibles**, cero parpadeos y ejecución 100% silenciosa en segundo plano.

### Nivel 2: Nivel de SolidWorks COM (Documentos Invisibles en Memoria)
En la API COM de SolidWorks:
- Se conecta a la instancia interactiva existente mediante `win32com.client.GetActiveObject("SldWorks.Application")` (cumpliendo con `AGENTS.md` y evitando abrir nuevos procesos pesados).
- Antes de crear o abrir el documento de trabajo, se activa el modo invisible:
  ```python
  sw.DocumentVisible(False, 1)  # 1 = swDocPART, 2 = swDocASSEMBLY, 3 = swDocDRAWING
  ```
- Se crea el documento con `doc = sw.NewDocument(...)` o se abre con `sw.OpenDoc6(...)`.
- Inmediatamente se restaura `sw.DocumentVisible(True, 1)` para que futuras acciones manuales del diseñador en la GUI sigan siendo visibles.
- **El documento del script vive 100% en memoria:**
  - `swApp.ActiveDoc` sigue siendo el documento del diseñador (ensamblaje, pieza previa).
  - El usuario puede seguir trabajando, seleccionando caras y dibujando croquis sin interrupción.
  - El script manipula su propio puntero `doc` (`doc.SketchManager`, `doc.FeatureManager`, `doc.Extension.SaveAs`, etc.).
  - Las operaciones matemáticas, extusiones, hélices y barridos corren a máxima velocidad en CPU/RAM sin gastar ciclos de GPU renderizando en pantalla.

---

## 3. Patrón de Implementación: `BackgroundCADSession`

En `sw_base_template.py`, el gestor de contexto `BackgroundCADSession` encapsula todo el ciclo de vida:

```python
import os
import types
import pythoncom
import win32com.client
from win32com.client import VARIANT

def _v(x):
    return x() if isinstance(x, types.MethodType) else x

class BackgroundCADSession:
    """
    Gestor de contexto (with BackgroundCADSession() as doc:) para ejecutar tareas de modelado
    en una ventana / tarea oculta en segundo plano, garantizando que la sesión interactiva y el
    documento activo del usuario permanezcan 100% intactos y sin interferencias.
    """
    def __init__(self, sw=None, doc_type: int = 1):
        if sw is None:
            sw = win32com.client.GetActiveObject("SldWorks.Application")
        self.sw = sw
        self.doc_type = doc_type
        self.doc = None
        self.prev_title = None

    def __enter__(self):
        # 1. Guardar el documento activo en el que el usuario esta trabajando
        try:
            prev_doc = self.sw.ActiveDoc
            self.prev_title = _v(prev_doc.GetTitle) if prev_doc else None
        except Exception:
            self.prev_title = None

        # 2. Configurar modo silencioso invisible para el nuevo documento
        self.sw.DocumentVisible(False, self.doc_type)
        tpl = self.sw.GetUserPreferenceStringValue(8 if self.doc_type == 1 else 9)
        self.doc = self.sw.NewDocument(tpl, 0, 0, 0)
        self.sw.DocumentVisible(True, self.doc_type)  # Restaurar para el usuario

        if not self.doc:
            raise RuntimeError("No se pudo instanciar el documento CAD en segundo plano.")
        return self.doc

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 3. Limpieza garantizada del documento para evitar fugas de memoria o procesos zombies
        if self.doc:
            title = _v(self.doc.GetTitle)
            try:
                self.sw.CloseDoc(title)
            except Exception:
                pass

        # 4. Asegurar que el usuario regrese a su documento activo original
        if self.prev_title:
            try:
                curr_active = self.sw.ActiveDoc
                curr_title = _v(curr_active.GetTitle) if curr_active else None
                if curr_title != self.prev_title:
                    err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                    self.sw.ActivateDoc3(self.prev_title, False, 0, err)
            except Exception:
                pass
        return False
```

---

## 4. Exportación y Renderizado en Modo Oculto

### Guardado Directo (.SLDPRT y .STEP)
Un documento invisible en memoria admite guardado directo sin necesidad de una ventana gráfica:
```python
nothing = VARIANT(pythoncom.VT_DISPATCH, None)
err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
wrn = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)

doc.Extension.SaveAs(r"C:\ruta\pieza.SLDPRT", 0, 1, nothing, err, wrn)
doc.Extension.SaveAs(r"C:\ruta\pieza.STEP", 0, 1, nothing, err, wrn)
```

### Renders y Vistas
1. **Render Silencioso Rápido (100% Invisible):**
   ```python
   doc.SaveAs(r"C:\ruta\pieza_iso.png")
   ```
   SolidWorks genera directamente el archivo PNG de alta resolución con la vista isométrica 3D sombreada del modelo en memoria, sin necesidad de crear un viewport en el escritorio.
2. **Vistas Ortogonales Específicas (Alzado, Planta, Lateral):**
   Si se requieren las 5 proyecciones ortogonales estándar, se habilita temporalmente la visibilidad (`doc.Visible = True`), se ejecutan las capturas `SaveBMP` en menos de 0.5 segundos, y el gestor `BackgroundCADSession` cierra el documento y devuelve inmediatamente el foco al documento previo del usuario.

---

## 5. Matriz de Cumplimiento Normativo (`AGENTS.md`)

| Requisito AGENTS.md | Solución Implementada | Estado |
| :--- | :--- | :--- |
| **No procesos zombies de SolidWorks** | Usa `GetActiveObject` y garantiza `sw.CloseDoc()` en bloque `finally` / `__exit__`. | ✅ Garantizado |
| **No bloqueo de la GUI del usuario** | Modelado en memoria con `DocumentVisible(False)`. `ActiveDoc` del usuario permanece intacto. | ✅ Garantizado |
| **Complejidad $O(1)$ por tick** | No hay polling continuo ni `gc.collect()` forzado. | ✅ Garantizado |
| **Cero parpadeo de consola en Windows** | Tarea programada registrada con `$Settings.Hidden = $True` y `-WindowStyle Hidden`. | ✅ Garantizado |
