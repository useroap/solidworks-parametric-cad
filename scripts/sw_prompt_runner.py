"""
sw_prompt_runner.py - Ejecutor Paramétrico Prompt-to-CAD con Auto-Sanación y Capturas
====================================================================================
Inspirado en el ciclo Roslyn + ViewCapture de MecAgent Copilot.
Permite ejecutar scripts generados por IA en SolidWorks 2025, capturar vistas
ortogonales automáticamente y devolver un diagnóstico estructurado para auto-sanación.
"""

import sys
import os
import json
import subprocess
import glob
from pathlib import Path

def run_cad_script(script_path, work_dir=None, timeout=120):
    """
    Ejecuta un script CAD en la sesión interactiva de SolidWorks y recopila resultados.
    """
    script_full = os.path.abspath(script_path)
    if not os.path.exists(script_full):
        return {
            "success": False,
            "stage": "pre-execution",
            "error": f"Script not found: {script_full}"
        }
    
    if work_dir is None:
        work_dir = os.path.dirname(script_full)
    else:
        work_dir = os.path.abspath(work_dir)
        
    out_dir = os.path.join(work_dir, "out")
    os.makedirs(out_dir, exist_ok=True)
    
    # Ruta del lanzador interactivo
    skill_root = Path(__file__).resolve().parent.parent
    launcher_ps1 = skill_root / "scripts" / "run_in_interactive_session.ps1"
    
    if not launcher_ps1.exists():
        return {
            "success": False,
            "stage": "pre-execution",
            "error": f"Launcher not found: {launcher_ps1}"
        }
        
    script_name = os.path.relpath(script_full, work_dir).replace("\\", "/")
    
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(launcher_ps1),
        "-WorkDir", work_dir,
        "-ScriptName", script_name,
        "-TimeoutSeconds", str(timeout)
    ]
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 15
        )
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stage": "timeout",
            "error": f"Execution timed out after {timeout} seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "stage": "launcher",
            "error": str(e)
        }
        
    # Leer build_log.txt generado en out/
    log_file = os.path.join(out_dir, "build_log.txt")
    log_content = ""
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()
            
    # Detectar capturas generadas
    images = glob.glob(os.path.join(out_dir, "*.png"))
    
    # Analizar resultado
    success = (exit_code == 0) and ("EXIT=0" in log_content or "EXIT=0" in stdout)
    
    # Extraer errores si falló
    error_summary = None
    if not success:
        error_lines = []
        for line in log_content.splitlines():
            if any(k in line.lower() for k in ["traceback", "error", "exception", "failed", "exit="]):
                error_lines.append(line)
        error_summary = "\n".join(error_lines[-10:]) if error_lines else stdout[-500:]

    return {
        "success": success,
        "exit_code": exit_code,
        "stage": "execution" if success else "runtime_error",
        "log": log_content,
        "error": error_summary,
        "images": images,
        "output_dir": out_dir
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python sw_prompt_runner.py <ruta_script.py> [work_dir]")
        sys.exit(1)
        
    target_script = sys.argv[1]
    w_dir = sys.argv[2] if len(sys.argv) > 2 else None
    res = run_cad_script(target_script, w_dir)
    print(json.dumps(res, indent=2))
