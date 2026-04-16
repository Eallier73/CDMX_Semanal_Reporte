#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
from pathlib import Path
from datetime import date, datetime

# Cargar variables de entorno desde .env.local
def manual_load_dotenv(path):
    try:
        if not path.exists():
            return False
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    os.environ[key] = value
        return True
    except Exception:
        return False

env_file = Path(__file__).resolve().parent.parent / ".env.local"
try:
    from dotenv import load_dotenv
    if env_file.exists():
        load_dotenv(str(env_file))
except ImportError:
    manual_load_dotenv(env_file)

# Importar lógica del orquestador original
# Agregamos el path de Scripts para asegurar las importaciones
sys.path.append(str(Path(__file__).resolve().parent))

from orquestador_general import (
    PIPELINES, 
    PIPELINES_BY_CODE,
    DEFAULT_GLOBAL_ISO_WEEK,
    DEFAULT_GLOBAL_SINCE,
    DEFAULT_GLOBAL_BEFORE,
    iso_week_to_range,
    parse_date_range,
    ensure_pipeline_before,
    ensure_pipeline_after,
    build_pipeline,
    render_command,
    weekly_output_dir_for_command,
    _extract_flag_value,
    build_report_tag
)

class OrquestadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Orquestador Pipelines CDMX")
        self.root.geometry("800x700")
        
        self.running_process = None
        self.stop_requested = False
        self.venv_python = self.detect_venv()

        self.setup_ui()

    def detect_venv(self):
        """Busca un ejecutable de python en .venv o venv en la raíz del proyecto."""
        root = Path(__file__).resolve().parent.parent
        for folder in [".venv", "venv"]:
            # Windows usa Scripts/python.exe, Linux usa bin/python
            python_bin = root / folder / "bin" / "python3"
            if not python_bin.exists():
                python_bin = root / folder / "bin" / "python"
            if not python_bin.exists():
                python_bin = root / folder / "Scripts" / "python.exe"
            
            if python_bin.exists():
                return str(python_bin)
        return sys.executable # Default al actual si no se encuentra venv

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- SECCIÓN ENTORNO VIRTUAL ---
        venv_frame = ttk.LabelFrame(main_frame, text="Entorno de Ejecución", padding="10")
        venv_frame.pack(fill=tk.X, pady=5)

        self.use_venv_var = tk.BooleanVar(value=(self.venv_python != sys.executable))
        venv_cb = ttk.Checkbutton(venv_frame, text="Usar Entorno Virtual (.venv/venv)", variable=self.use_venv_var)
        venv_cb.grid(row=0, column=0, sticky=tk.W)

        self.venv_status_var = tk.StringVar(value=f"Ruta: {self.venv_python}")
        venv_label = ttk.Label(venv_frame, textvariable=self.venv_status_var, foreground="gray", font=("Helvetica", 8))
        venv_label.grid(row=1, column=0, sticky=tk.W, padx=20)

        # --- SECCIÓN FECHAS ---
        date_frame = ttk.LabelFrame(main_frame, text="Configuración Temporal", padding="10")
        date_frame.pack(fill=tk.X, pady=5)

        ttk.Label(date_frame, text="Semana ISO (YYYY-Www):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.iso_week_var = tk.StringVar(value=DEFAULT_GLOBAL_ISO_WEEK)
        self.iso_week_entry = ttk.Entry(date_frame, textvariable=self.iso_week_var, width=15)
        self.iso_week_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        btn_calc_week = ttk.Button(date_frame, text="Usar Semana", command=self.update_dates_from_week)
        btn_calc_week.grid(row=0, column=2, padx=5)

        ttk.Label(date_frame, text="Desde (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.since_var = tk.StringVar(value=DEFAULT_GLOBAL_SINCE)
        self.since_entry = ttk.Entry(date_frame, textvariable=self.since_var, width=15)
        self.since_entry.grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Label(date_frame, text="Hasta (YYYY-MM-DD):").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.before_var = tk.StringVar(value=DEFAULT_GLOBAL_BEFORE)
        self.before_entry = ttk.Entry(date_frame, textvariable=self.before_var, width=15)
        self.before_entry.grid(row=1, column=3, sticky=tk.W, padx=5)

        # --- SECCIÓN PIPELINES ---
        pipeline_frame = ttk.LabelFrame(main_frame, text="Selección de Pipelines (Secciones de Trabajo)", padding="10")
        pipeline_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.pipeline_vars = {}
        # Crear un canvas con scrollbar para la lista de pipelines si creciera mucho
        canvas = tk.Canvas(pipeline_frame)
        scrollbar = ttk.Scrollbar(pipeline_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for pipe in PIPELINES:
            var = tk.BooleanVar(value=False)
            self.pipeline_vars[pipe.code] = var
            cb = ttk.Checkbutton(scrollable_frame, text=f"{pipe.code}) {pipe.label}", variable=var)
            cb.pack(anchor=tk.W, pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- SECCIÓN OPCIONES ---
        options_frame = ttk.Frame(main_frame, padding="5")
        options_frame.pack(fill=tk.X)

        self.mode_var = tk.StringVar(value="all_networks")
        ttk.Radiobutton(options_frame, text="Modo Genérico (Defaults)", variable=self.mode_var, value="all_networks").pack(side=tk.LEFT, padx=10)
        # Nota: El modo específico en la GUI requeriría muchos más diálogos, 
        # por ahora implementamos el flujo principal que es el más solicitado.
        # ttk.Radiobutton(options_frame, text="Modo Específico", variable=self.mode_var, value="per_network").pack(side=tk.LEFT, padx=10)

        self.continue_error_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Continuar en error", variable=self.continue_error_var).pack(side=tk.LEFT, padx=10)

        # --- BOTONES DE CONTROL ---
        control_frame = ttk.Frame(main_frame, padding="10")
        control_frame.pack(fill=tk.X)

        self.play_button = ttk.Button(control_frame, text="▶ PLAY / EJECUTAR", command=self.start_execution)
        self.play_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.stop_button = ttk.Button(control_frame, text="⏹ DETENER", command=self.stop_execution, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # --- ÁREA DE LOG ---
        log_frame = ttk.LabelFrame(main_frame, text="Consola de Salida", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED, bg="black", fg="lightgreen", font=("Courier", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def update_dates_from_week(self):
        week = self.iso_week_var.get().strip()
        try:
            since, before = iso_week_to_range(week)
            self.since_var.set(since)
            self.before_var.set(before)
        except Exception as e:
            messagebox.showerror("Error", f"Semana ISO inválida: {e}")

    def log(self, message):
        def _append():
            self.log_area.config(state=tk.NORMAL)
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def clear_log(self):
        def _clear():
            self.log_area.config(state=tk.NORMAL)
            self.log_area.delete(1.0, tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(0, _clear)

    def get_selected_pipelines(self):
        selected = []
        for code, var in self.pipeline_vars.items():
            if var.get():
                selected.append(PIPELINES_BY_CODE[code])
        # Ordenar por el orden original en PIPELINES
        selected.sort(key=lambda x: [p.code for p in PIPELINES].index(x.code))
        return selected

    def validate_dependencies(self, selected):
        selected_codes = {s.code for s in selected}
        
        # Lógica copiada de orquestador_general.py
        if "5" in selected_codes and "4" not in selected_codes:
            self.log("⚠️ Agregando Facebook Posts (4) como dependencia de Comentarios (5)")
            facebook_posts_spec = PIPELINES_BY_CODE["4"]
            insert_at = next((index for index, item in enumerate(selected) if item.code == "5"), 0)
            selected.insert(insert_at, facebook_posts_spec)

        selected = ensure_pipeline_before(selected, "4", "5")

        required_by_consolidador = {"7": "Claude", "8": "Influencia", "9": "Guiados"}
        for dep_code in required_by_consolidador:
            selected_codes = {s.code for s in selected}
            if dep_code in selected_codes and "6" not in selected_codes:
                self.log(f"⚠️ Agregando Consolidador (6) como dependencia de {dep_code}")
                selected.insert(0, PIPELINES_BY_CODE["6"])
        
        # Asegurar orden
        for dep_code in required_by_consolidador:
            selected = ensure_pipeline_before(selected, "6", dep_code)
            
        selected = ensure_pipeline_after(selected, "10", ["1", "2", "4"])
        
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_selected = []
        for s in selected:
            if s.code not in seen:
                unique_selected.append(s)
                seen.add(s.code)
        
        return unique_selected

    def start_execution(self):
        selected = self.get_selected_pipelines()
        if not selected:
            messagebox.showwarning("Atención", "Selecciona al menos un pipeline para ejecutar.")
            return

        since = self.since_var.get().strip()
        before = self.before_var.get().strip()

        try:
            since, before = parse_date_range(since, before)
        except ValueError as e:
            messagebox.showerror("Error de Fechas", str(e))
            return

        self.clear_log()
        self.log(f"🚀 Iniciando ejecución: {since} al {before}")
        
        selected = self.validate_dependencies(selected)
        self.log(f"Pipelines a ejecutar: {', '.join(s.label for s in selected)}")
        
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.root.update_idletasks()
        self.stop_requested = False
        
        # Ejecutar en hilo separado para no bloquear la GUI
        thread = threading.Thread(target=self.run_pipelines, args=(selected, since, before))
        thread.daemon = True
        thread.start()

    def stop_execution(self):
        if self.running_process:
            self.stop_requested = True
            self.running_process.terminate()
            self.log("\n🛑 Solicitud de detención enviada...")

    def run_pipelines(self, selected, since, before):
        use_defaults = (self.mode_var.get() == "all_networks")
        facebook_posts_csv = ""
        
        for spec in selected:
            if self.stop_requested:
                break
                
            self.log(f"\n--- Ejecutando: {spec.label} ---")
            
            try:
                # Construir comando
                # Nota: build_pipeline espera use_defaults. En GUI por ahora forzamos True
                # para evitar prompts bloqueantes en el hilo secundario.
                
                # Extraer credenciales cargadas para pasarlas explícitamente
                api_key = os.getenv("YOUTUBE_API_KEY", "")
                apify_token = os.getenv("APIFY_TOKEN", "")
                claude_api_key = os.getenv("CLAUDE_API_KEY", "")
                
                cmd, env_vars = build_pipeline(
                    spec, since, before, 
                    use_defaults=use_defaults, 
                    facebook_posts_csv=facebook_posts_csv,
                    api_key=api_key,
                    apify_token=apify_token,
                    claude_api_key=claude_api_key
                )
                
                # Sustituir el ejecutable por el del venv si está activado
                if self.use_venv_var.get() and self.venv_python:
                    if cmd and cmd[0] == sys.executable:
                        cmd[0] = self.venv_python

                self.log(f"Comando: {render_command(cmd)}")
                
                # Preparar entorno
                current_env = os.environ.copy()
                # Asegurar que las variables de .env.local se pasen si existen en el entorno actual
                for key in ["YOUTUBE_API_KEY", "APIFY_TOKEN", "CLAUDE_API_KEY", "YT_PROXY_HTTP", "YT_PROXY_HTTPS"]:
                    if key in os.environ and key not in env_vars:
                        current_env[key] = os.environ[key]
                current_env.update(env_vars)
                
                # Log de depuración (solo presencia, no valores)
                keys_to_check = ["YOUTUBE_API_KEY", "APIFY_TOKEN", "CLAUDE_API_KEY"]
                keys_present = [k for k in keys_to_check if k in current_env and current_env[k]]
                
                if keys_present:
                    self.log(f"ℹ️ Variables de entorno detectadas: {', '.join(keys_present)}")
                
                keys_missing = [k for k in keys_to_check if k not in keys_present]
                if keys_missing:
                    self.log(f"⚠️ Faltan variables críticas: {', '.join(keys_missing)}")
                    self.log("   (Asegúrate de que .env.local existe en la raíz del proyecto)")

                # Ejecutar proceso
                self.running_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=current_env,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Capturar salida en tiempo real
                for line in self.running_process.stdout:
                    self.log(line.strip())
                
                self.running_process.wait()
                return_code = self.running_process.returncode
                
                if return_code == 0:
                    self.log(f"✅ {spec.label} finalizado con éxito.")
                    
                    # Si era el extractor de posts, capturar el CSV para el siguiente
                    if spec.code == "4":
                        # Usar la lógica oficial para encontrar el CSV
                        output_dir_arg = _extract_flag_value(cmd, "--output-dir") or str(Path(__file__).resolve().parent.parent / "Facebook")
                        report_tag = build_report_tag(since, "Facebook")
                        facebook_posts_csv = str(Path(output_dir_arg) / report_tag / f"{report_tag}_posts.csv")
                        
                        if os.path.exists(facebook_posts_csv):
                            self.log(f"ℹ️ Detectado CSV de posts: {facebook_posts_csv}")
                        else:
                            self.log(f"⚠️ CSV esperado no encontrado: {facebook_posts_csv}")
                            facebook_posts_csv = ""
                else:
                    if self.stop_requested:
                        self.log(f"⏹ Proceso detenido por el usuario.")
                        break
                    else:
                        self.log(f"❌ Error en {spec.label} (Código {return_code})")
                        if not self.continue_error_var.get():
                            self.log("Abortando ejecución.")
                            break
                            
            except Exception as e:
                self.log(f"💥 Error inesperado ejecutando {spec.label}: {e}")
                if not self.continue_error_var.get():
                    break

        self.log("\n🏁 Proceso terminado.")
        self.root.after(0, self.finish_ui)

    def finish_ui(self):
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.running_process = None
        if not self.stop_requested:
            messagebox.showinfo("Finalizado", "La ejecución de los pipelines ha concluido.")

if __name__ == "__main__":
    root = tk.Tk()
    app = OrquestadorGUI(root)
    root.mainloop()
