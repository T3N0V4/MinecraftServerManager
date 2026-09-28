import re
import threading
import tkinter as tk

from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox


class ServerGUI:
    LOG_LEVEL_PATTERN = re.compile(
        r"\[[^\]]+/(INFO|WARN|WARNING|ERROR|FATAL)\]:",
        re.IGNORECASE
    )

    LOG4J_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2} "
        r"\d{2}:\d{2}:\d{2}[,\d]* "
        r".*?\b(INFO|WARN|WARNING|ERROR|FATAL)\b",
        re.IGNORECASE
    )

    def __init__(self, adapter):
        self.adapter = adapter

        self.root = tk.Tk()

        self.root.title(
            "Minecraft Server Manager"
        )

        self.root.geometry(
            "1200x760"
        )

        self.root.minsize(
            950,
            650
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.info = self.adapter.inspect()

        self.counters = {
            "info": 0,
            "warning": 0,
            "error": 0,
            "success": 0,
            "system": 0
        }

        self.console_widgets = {}

        # Bloque activo:
        # None
        # "warning"
        # "error"
        self.active_block_type = None
        self.active_block_lines = []

        self.warning_blocks = []
        self.error_blocks = []

        self.warning_number = 0
        self.error_number = 0

        self.create_interface()

    # =========================================================
    # INTERFAZ
    # =========================================================

    def create_interface(self):
        self.create_top_panel()
        self.create_counter_panel()
        self.create_console_tabs()
        self.create_command_panel()
        self.create_bottom_buttons()

    def create_top_panel(self):
        frame = ttk.Frame(
            self.root,
            padding=10
        )

        frame.pack(
            fill="x"
        )

        minecraft = self.info[
            "minecraft_version"
        ]

        loader = self.info[
            "loader"
        ]

        loader_version = self.info[
            "loader_version"
        ]

        mods = self.info[
            "mods"
        ]

        java = self.info[
            "java_version"
        ]

        ttk.Label(
            frame,
            text=f"Minecraft: {minecraft}"
        ).pack(
            side="left",
            padx=10
        )

        ttk.Label(
            frame,
            text=(
                f"Loader: "
                f"{loader} "
                f"{loader_version}"
            )
        ).pack(
            side="left",
            padx=10
        )

        ttk.Label(
            frame,
            text=f"Mods: {mods}"
        ).pack(
            side="left",
            padx=10
        )

        ttk.Label(
            frame,
            text=f"Java: {java}"
        ).pack(
            side="left",
            padx=10
        )

        ttk.Label(
            frame,
            text=f"Puerto: {self.info['port']}"
        ).pack(
            side="left",
            padx=10
        )

        self.status_label = ttk.Label(
            frame,
            text="● DETENIDO"
        )

        self.status_label.pack(
            side="right",
            padx=10
        )

    def create_counter_panel(self):
        frame = ttk.Frame(
            self.root,
            padding=(10, 0, 10, 10)
        )

        frame.pack(
            fill="x"
        )

        self.info_counter = ttk.Label(
            frame,
            text="INFO: 0"
        )

        self.info_counter.pack(
            side="left",
            padx=8
        )

        self.warning_counter = ttk.Label(
            frame,
            text="WARNINGS: 0"
        )

        self.warning_counter.pack(
            side="left",
            padx=8
        )

        self.error_counter = ttk.Label(
            frame,
            text="ERRORES: 0"
        )

        self.error_counter.pack(
            side="left",
            padx=8
        )

        self.success_counter = ttk.Label(
            frame,
            text="SUCCESS: 0"
        )

        self.success_counter.pack(
            side="left",
            padx=8
        )

        self.system_counter = ttk.Label(
            frame,
            text="MANAGER: 0"
        )

        self.system_counter.pack(
            side="left",
            padx=8
        )

    def create_console_tabs(self):
        frame = ttk.Frame(
            self.root,
            padding=10
        )

        frame.pack(
            fill="both",
            expand=True
        )

        self.notebook = ttk.Notebook(
            frame
        )

        self.notebook.pack(
            fill="both",
            expand=True
        )

        tabs = [
            ("Todos", "all"),
            ("Info", "info"),
            ("Warnings", "warning"),
            ("Errores", "error"),
            ("Success", "success"),
            ("Manager", "system")
        ]

        for title, key in tabs:
            tab_frame = ttk.Frame(
                self.notebook
            )

            self.notebook.add(
                tab_frame,
                text=title
            )

            console = (
                scrolledtext.ScrolledText(
                    tab_frame,
                    bg="#111111",
                    fg="#dddddd",
                    insertbackground="white",
                    font=("Consolas", 10),
                    state="disabled",
                    wrap="none"
                )
            )

            console.pack(
                fill="both",
                expand=True
            )

            console.tag_config(
                "info",
                foreground="#dddddd"
            )

            console.tag_config(
                "warning",
                foreground="#ffcc66"
            )

            console.tag_config(
                "error",
                foreground="#ff6666"
            )

            console.tag_config(
                "success",
                foreground="#77dd77"
            )

            console.tag_config(
                "system",
                foreground="#66b3ff"
            )

            console.tag_config(
                "header_warning",
                foreground="#ffcc66",
                font=("Consolas", 10, "bold")
            )

            console.tag_config(
                "header_error",
                foreground="#ff6666",
                font=("Consolas", 10, "bold")
            )

            self.console_widgets[
                key
            ] = console

    def create_command_panel(self):
        frame = ttk.Frame(
            self.root,
            padding=10
        )

        frame.pack(
            fill="x"
        )

        self.command_entry = ttk.Entry(
            frame
        )

        self.command_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        self.command_entry.bind(
            "<Return>",
            lambda event:
            self.send_command()
        )

        ttk.Button(
            frame,
            text="Enviar comando",
            command=self.send_command
        ).pack(
            side="right",
            padx=(10, 0)
        )

    def create_bottom_buttons(self):
        frame = ttk.Frame(
            self.root,
            padding=10
        )

        frame.pack(
            fill="x"
        )

        ttk.Button(
            frame,
            text="Iniciar",
            command=self.start_server
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame,
            text="Detener",
            command=self.stop_server
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame,
            text="Reiniciar",
            command=self.restart_server
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame,
            text="Copiar consola",
            command=self.copy_console
        ).pack(
            side="right",
            padx=5
        )

        ttk.Button(
            frame,
            text="Limpiar pestaña",
            command=self.clear_console
        ).pack(
            side="right",
            padx=5
        )

    # =========================================================
    # CONSOLA
    # =========================================================

    def insert_into_console(
        self,
        console,
        text,
        tag
    ):
        console.configure(
            state="normal"
        )

        console.insert(
            "end",
            text + "\n",
            tag
        )

        console.see(
            "end"
        )

        console.configure(
            state="disabled"
        )

    def write_console(
        self,
        text,
        tag="info",
        count=True
    ):
        self.insert_into_console(
            self.console_widgets["all"],
            text,
            tag
        )

        if tag in self.console_widgets:
            self.insert_into_console(
                self.console_widgets[tag],
                text,
                tag
            )

        if count and tag in self.counters:
            self.counters[tag] += 1
            self.update_counters()

    def update_counters(self):
        self.info_counter.config(
            text=(
                f"INFO: "
                f"{self.counters['info']}"
            )
        )

        self.warning_counter.config(
            text=(
                f"WARNINGS: "
                f"{self.counters['warning']}"
            )
        )

        self.error_counter.config(
            text=(
                f"ERRORES: "
                f"{self.counters['error']}"
            )
        )

        self.success_counter.config(
            text=(
                f"SUCCESS: "
                f"{self.counters['success']}"
            )
        )

        self.system_counter.config(
            text=(
                f"MANAGER: "
                f"{self.counters['system']}"
            )
        )

    # =========================================================
    # DETECCIÓN DE NIVEL
    # =========================================================

    def get_explicit_log_level(
        self,
        line
    ):
        match = self.LOG_LEVEL_PATTERN.search(
            line
        )

        if match:
            level = match.group(1).upper()

            if level in (
                "WARN",
                "WARNING"
            ):
                return "warning"

            if level in (
                "ERROR",
                "FATAL"
            ):
                return "error"

            if level == "INFO":
                return "info"

        match = self.LOG4J_PATTERN.search(
            line
        )

        if match:
            level = match.group(1).upper()

            if level in (
                "WARN",
                "WARNING"
            ):
                return "warning"

            if level in (
                "ERROR",
                "FATAL"
            ):
                return "error"

            if level == "INFO":
                return "info"

        return None

    def classify_info_line(
        self,
        line
    ):
        lower = line.lower()

        success_words = (
            "done (",
            "server started",
            "voice chat server started",
            "joined the game",
            "successfully loaded",
            "successfully initialized",
            "initialized successfully"
        )

        if any(
            word in lower
            for word in success_words
        ):
            return "success"

        return "info"

    # =========================================================
    # BLOQUES WARN / ERROR
    # =========================================================

    def start_block(
        self,
        block_type,
        line
    ):
        self.flush_active_block()

        self.active_block_type = (
            block_type
        )

        self.active_block_lines = [
            line
        ]

        self.insert_into_console(
            self.console_widgets["all"],
            line,
            block_type
        )

    def append_to_active_block(
        self,
        line
    ):
        if not self.active_block_type:
            return False

        self.active_block_lines.append(
            line
        )

        self.insert_into_console(
            self.console_widgets["all"],
            line,
            self.active_block_type
        )

        return True

    def flush_active_block(self):
        if not self.active_block_type:
            return

        if not self.active_block_lines:
            self.active_block_type = None
            return

        block_type = (
            self.active_block_type
        )

        block = "\n".join(
            self.active_block_lines
        )

        if block_type == "error":
            self.error_number += 1
            self.error_blocks.append(block)

            number = self.error_number
            title = f"ERROR #{number}"
            header_tag = "header_error"

        else:
            self.warning_number += 1
            self.warning_blocks.append(block)

            number = self.warning_number
            title = f"WARNING #{number}"
            header_tag = "header_warning"

        console = self.console_widgets[
            block_type
        ]

        console.configure(
            state="normal"
        )

        console.insert(
            "end",
            "\n"
        )

        console.insert(
            "end",
            title + "\n",
            header_tag
        )

        console.insert(
            "end",
            "-" * 80 + "\n",
            block_type
        )

        console.insert(
            "end",
            block + "\n",
            block_type
        )

        console.insert(
            "end",
            "-" * 80 + "\n\n",
            block_type
        )

        console.see(
            "end"
        )

        console.configure(
            state="disabled"
        )

        self.counters[
            block_type
        ] += 1

        self.update_counters()

        self.active_block_type = None
        self.active_block_lines = []

    # =========================================================
    # PROCESAMIENTO DEL LOG
    # =========================================================

    def process_log_line(
        self,
        line
    ):
        explicit_level = (
            self.get_explicit_log_level(
                line
            )
        )

        # Una nueva línea con nivel explícito
        # termina el bloque anterior.
        if explicit_level is not None:
            self.flush_active_block()

            if explicit_level == "error":
                self.start_block(
                    "error",
                    line
                )
                return

            if explicit_level == "warning":
                self.start_block(
                    "warning",
                    line
                )
                return

            # INFO
            tag = self.classify_info_line(
                line
            )

            self.write_console(
                line,
                tag
            )

            if "Done (" in line:
                self.status_label.config(
                    text="● ONLINE"
                )

            return

        # No tiene nuevo nivel explícito.
        # Si había WARN/ERROR activo,
        # pertenece al bloque.
        if self.active_block_type:
            self.append_to_active_block(
                line
            )

            return

        # Algunas líneas aparecen fuera del
        # formato normal de Minecraft/Log4j.
        lower = line.lower()

        if (
            "fatal" in lower
            or lower.startswith(
                "java.lang."
            )
            or lower.startswith(
                "java.io."
            )
            or lower.startswith(
                "org.spongepowered."
            )
        ):
            self.start_block(
                "error",
                line
            )

            return

        self.write_console(
            line,
            "info"
        )

    # =========================================================
    # SERVER
    # =========================================================

    def start_server(self):
        if self.adapter.is_running():
            self.write_console(
                "[MANAGER] "
                "El servidor ya está iniciado.",
                "system"
            )

            return

        try:
            self.write_console(
                "[MANAGER] "
                "Iniciando servidor...",
                "system"
            )

            self.status_label.config(
                text="● INICIANDO"
            )

            process = self.adapter.start(
                min_ram="4G",
                max_ram="8G"
            )

            thread = threading.Thread(
                target=self.read_output,
                args=(process,),
                daemon=True
            )

            thread.start()

        except Exception as error:
            self.status_label.config(
                text="● DETENIDO"
            )

            self.write_console(
                f"[MANAGER ERROR] {error}",
                "system"
            )

            messagebox.showerror(
                "No se pudo iniciar",
                str(error)
            )

    def read_output(
        self,
        process
    ):
        if process.stdout is None:
            return

        for line in process.stdout:
            line = line.rstrip(
                "\r\n"
            )

            if not line.strip():
                continue

            self.root.after(
                0,
                self.process_log_line,
                line
            )

        return_code = process.wait()

        self.adapter.process = None

        self.root.after(
            0,
            self.server_stopped,
            return_code
        )

    def server_stopped(
        self,
        return_code
    ):
        self.flush_active_block()

        self.status_label.config(
            text="● DETENIDO"
        )

        if return_code == 0:
            self.write_console(
                "[MANAGER] "
                "Servidor detenido correctamente.",
                "system"
            )

        else:
            self.write_console(
                "[MANAGER] "
                f"El servidor terminó con código "
                f"{return_code}.",
                "system"
            )

    def stop_server(self):
        if not self.adapter.is_running():
            self.write_console(
                "[MANAGER] "
                "El servidor no está iniciado.",
                "system"
            )

            return

        self.status_label.config(
            text="● DETENIENDO"
        )

        self.write_console(
            "[MANAGER] "
            "Deteniendo servidor...",
            "system"
        )

        try:
            self.adapter.stop()

        except Exception as error:
            self.write_console(
                f"[MANAGER ERROR] {error}",
                "system"
            )

    def restart_server(self):
        if not self.adapter.is_running():
            self.start_server()
            return

        self.write_console(
            "[MANAGER] "
            "Reiniciando servidor...",
            "system"
        )

        self.status_label.config(
            text="● REINICIANDO"
        )

        try:
            self.adapter.stop()

            thread = threading.Thread(
                target=self.wait_and_restart,
                daemon=True
            )

            thread.start()

        except Exception as error:
            self.write_console(
                f"[MANAGER ERROR] {error}",
                "system"
            )

    def wait_and_restart(self):
        process = self.adapter.process

        if process is None:
            self.root.after(
                500,
                self.start_server
            )
            return

        process.wait()

        self.adapter.process = None

        self.root.after(
            1000,
            self.start_server
        )

    # =========================================================
    # COMANDOS
    # =========================================================

    def send_command(self):
        command = (
            self.command_entry
            .get()
            .strip()
        )

        if not command:
            return

        if not self.adapter.is_running():
            self.write_console(
                "[MANAGER] "
                "El servidor no está iniciado.",
                "system"
            )

            return

        try:
            self.adapter.send_command(
                command
            )

            self.write_console(
                f"> {command}",
                "system"
            )

            self.command_entry.delete(
                0,
                "end"
            )

        except Exception as error:
            self.write_console(
                f"[MANAGER ERROR] {error}",
                "system"
            )

    # =========================================================
    # COPIAR / LIMPIAR
    # =========================================================

    def get_current_console(self):
        current_index = (
            self.notebook.index(
                self.notebook.select()
            )
        )

        keys = [
            "all",
            "info",
            "warning",
            "error",
            "success",
            "system"
        ]

        key = keys[
            current_index
        ]

        return (
            key,
            self.console_widgets[key]
        )

    def copy_console(self):
        key, console = (
            self.get_current_console()
        )

        text = console.get(
            "1.0",
            "end-1c"
        )

        if not text.strip():
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(
            text
        )

        self.root.update()

        self.write_console(
            "[MANAGER] "
            f"Pestaña '{key}' copiada "
            f"al portapapeles.",
            "system"
        )

    def clear_console(self):
        _, console = (
            self.get_current_console()
        )

        console.configure(
            state="normal"
        )

        console.delete(
            "1.0",
            "end"
        )

        console.configure(
            state="disabled"
        )

    # =========================================================
    # CERRAR
    # =========================================================

    def on_close(self):
        if not self.adapter.is_running():
            self.root.destroy()
            return

        answer = messagebox.askyesno(
            "Servidor en ejecución",
            (
                "El servidor sigue ejecutándose.\n\n"
                "¿Querés detenerlo antes "
                "de cerrar el manager?"
            )
        )

        if not answer:
            return

        self.write_console(
            "[MANAGER] "
            "Cerrando servidor...",
            "system"
        )

        try:
            self.adapter.stop()

        except Exception:
            self.adapter.kill()

        self.wait_for_close()

    def wait_for_close(self):
        if self.adapter.is_running():
            self.root.after(
                250,
                self.wait_for_close
            )
            return

        self.root.destroy()

    # =========================================================
    # RUN
    # =========================================================

    def run(self):
        self.root.mainloop()