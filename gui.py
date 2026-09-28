import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import threading


class ServerGUI:
    def __init__(self, adapter):
        self.adapter = adapter

        self.root = tk.Tk()
        self.root.title("Minecraft Server Manager")
        self.root.geometry("1200x760")
        self.root.minsize(950, 650)

        self.info = self.adapter.inspect()

        self.counters = {
            "info": 0,
            "warning": 0,
            "error": 0,
            "success": 0,
            "system": 0
        }

        self.console_widgets = {}
        self.current_error_block = []
        self.current_warning_block = []

        self.error_blocks = []
        self.warning_blocks = []

        self.error_number = 0
        self.warning_number = 0
        self.create_interface()

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
        frame.pack(fill="x")

        ttk.Label(
            frame,
            text=f"Minecraft: {self.info['minecraft_version']}"
        ).pack(side="left", padx=10)

        ttk.Label(
            frame,
            text=f"Loader: {self.info['loader']} {self.info['loader_version']}"
        ).pack(side="left", padx=10)

        ttk.Label(
            frame,
            text=f"Mods: {self.info['mods']}"
        ).pack(side="left", padx=10)

        ttk.Label(
            frame,
            text=f"Java: {self.info['java_version']}"
        ).pack(side="left", padx=10)

        self.status_label = ttk.Label(
            frame,
            text="● DETENIDO"
        )
        self.status_label.pack(side="right", padx=10)

    def create_counter_panel(self):
        frame = ttk.Frame(
            self.root,
            padding=(10, 0, 10, 10)
        )
        frame.pack(fill="x")

        self.info_counter = ttk.Label(
            frame,
            text="INFO: 0"
        )
        self.info_counter.pack(side="left", padx=8)

        self.warning_counter = ttk.Label(
            frame,
            text="WARN: 0"
        )
        self.warning_counter.pack(side="left", padx=8)

        self.error_counter = ttk.Label(
            frame,
            text="ERROR: 0"
        )
        self.error_counter.pack(side="left", padx=8)

        self.success_counter = ttk.Label(
            frame,
            text="SUCCESS: 0"
        )
        self.success_counter.pack(side="left", padx=8)

        self.system_counter = ttk.Label(
            frame,
            text="MANAGER: 0"
        )
        self.system_counter.pack(side="left", padx=8)

    def create_console_tabs(self):
        frame = ttk.Frame(
            self.root,
            padding=10
        )
        frame.pack(
            fill="both",
            expand=True
        )

        self.notebook = ttk.Notebook(frame)
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

            console = scrolledtext.ScrolledText(
                tab_frame,
                bg="#111111",
                fg="#dddddd",
                insertbackground="white",
                font=("Consolas", 10),
                state="disabled"
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

            self.console_widgets[key] = console

    def create_command_panel(self):
        frame = ttk.Frame(
            self.root,
            padding=10
        )
        frame.pack(fill="x")

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
            lambda event: self.send_command()
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
        frame.pack(fill="x")

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
            text="Limpiar consola",
            command=self.clear_console
        ).pack(
            side="right",
            padx=5
        )

    def write_console(self,text,tag="info",write_category=True):
        if tag in self.counters and write_category:
            self.counters[tag] += 1
            self.update_counters()

        self.insert_into_console(
            self.console_widgets["all"],
            text,
            tag
        )

        if (
            write_category
            and tag in self.console_widgets
        ):
            self.insert_into_console(
                self.console_widgets[tag],
                text,
                tag
            )
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

        console.see("end")

        console.configure(
            state="disabled"
        )

    def update_counters(self):
        self.info_counter.config(
            text=f"INFO: {self.counters['info']}"
        )

        self.warning_counter.config(
            text=f"WARN: {self.counters['warning']}"
        )

        self.error_counter.config(
            text=f"ERROR: {self.counters['error']}"
        )

        self.success_counter.config(
            text=f"SUCCESS: {self.counters['success']}"
        )

        self.system_counter.config(
            text=f"MANAGER: {self.counters['system']}"
        )

    def classify_line(self, line):
        lower = line.lower()

        if (
            "[error]" in lower
            or "exception" in lower
            or "fatal" in lower
            or "crash" in lower
            or "failed to load" in lower
        ):
            return "error"

        if (
            "[warn]" in lower
            or "warning" in lower
            or "could not" in lower
        ):
            return "warning"

        if (
            "done (" in lower
            or "server started" in lower
            or "started minecraft server" in lower
            or "joined the game" in lower
            or "successfully" in lower
        ):
            return "success"

        return "info"

    def start_server(self):
        if self.adapter.is_running():
            self.write_console(
                "[MANAGER] El servidor ya está iniciado.",
                "warning"
            )
            return

        try:
            self.write_console(
                "[MANAGER] Iniciando servidor...",
                "system"
            )

            process = self.adapter.start(
                min_ram="4G",
                max_ram="8G"
            )

            self.status_label.config(
                text="● INICIANDO"
            )

            thread = threading.Thread(
                target=self.read_output,
                args=(process,),
                daemon=True
            )

            thread.start()

        except Exception as error:
            self.write_console(
                f"[MANAGER ERROR] {error}",
                "error"
            )

    def read_output(self, process):
        for line in process.stdout:
            line = line.rstrip()

            if not line:
                continue

            self.root.after(
                0,
                self.process_log_line,
                line
            )

        self.root.after(
            0,
            self.flush_pending_blocks
        )

        self.root.after(
            0,
            self.server_stopped
        )
    def process_log_line(self, line):
        lower = line.lower()

        is_error_start = (
            "[error]" in lower
            or "exception" in lower
            or "fatal" in lower
            or "failed to load" in lower
        )

        is_warning_start = (
            "[warn]" in lower
            or "warning" in lower
        )

        is_stack_line = (
            line.startswith("\t")
            or line.startswith("    ")
            or line.startswith("at ")
            or line.startswith("Caused by:")
            or line.startswith("Suppressed:")
            or line.startswith("...")
        )

        # ERROR NUEVO
        if is_error_start:
            self.flush_warning_block()

            if self.current_error_block:
                self.flush_error_block()

            self.current_error_block.append(line)

            self.write_console(
                line,
                "error",
                write_category=False
            )

            return

        # CONTINUACIÓN DE ERROR
        if self.current_error_block and is_stack_line:
            self.current_error_block.append(line)

            self.insert_into_console(
                self.console_widgets["all"],
                line,
                "error"
            )

            return

        # WARNING NUEVO
        if is_warning_start:
            self.flush_error_block()

            if self.current_warning_block:
                self.flush_warning_block()

            self.current_warning_block.append(line)

            self.write_console(
                line,
                "warning",
                write_category=False
            )

            return

        # CONTINUACIÓN DE WARNING
        if self.current_warning_block and (
            line.startswith("\t")
            or line.startswith("    ")
            or line.startswith("- ")
        ):
            self.current_warning_block.append(line)

            self.insert_into_console(
                self.console_widgets["all"],
                line,
                "warning"
            )

            return

        # Si llegó una línea normal,
        # cerrar cualquier bloque pendiente
        self.flush_error_block()
        self.flush_warning_block()

        tag = self.classify_line(line)

        self.write_console(
            line,
            tag
        )

        if "Done (" in line:
            self.status_label.config(
                text="● ONLINE"
            )

    def server_stopped(self):
        self.status_label.config(
            text="● DETENIDO"
        )

        self.write_console(
            "[MANAGER] Servidor detenido.",
            "system"
        )

    def flush_warning_block(self):
        if not self.current_warning_block:
            return

        self.warning_number += 1

        block = "\n".join(
            self.current_warning_block
        )

        self.warning_blocks.append(block)

        console = self.console_widgets["warning"]

        console.configure(
            state="normal"
        )

        console.insert(
            "end",
            f"\nWARNING #{self.warning_number}\n",
            "warning"
        )

        console.insert(
            "end",
            "-" * 70 + "\n",
            "warning"
        )

        console.insert(
            "end",
            block + "\n",
            "warning"
        )

        console.insert(
            "end",
            "-" * 70 + "\n\n",
            "warning"
        )

        console.see("end")

        console.configure(
            state="disabled"
        )

        self.counters["warning"] += 1
        self.update_counters()

        self.current_warning_block = []
    
    def flush_error_block(self):
        if not self.current_error_block:
            return

        self.error_number += 1

        block = "\n".join(
            self.current_error_block
        )

        self.error_blocks.append(block)

        console = self.console_widgets["error"]

        console.configure(
            state="normal"
        )

        console.insert(
            "end",
            f"\nERROR #{self.error_number}\n",
            "error"
        )

        console.insert(
            "end",
            "-" * 70 + "\n",
            "error"
        )

        console.insert(
            "end",
            block + "\n",
            "error"
        )

        console.insert(
            "end",
            "-" * 70 + "\n\n",
            "error"
        )

        console.see("end")

        console.configure(
            state="disabled"
        )

        self.counters["error"] += 1
        self.update_counters()

        self.current_error_block = []
    def flush_pending_blocks(self):
        self.flush_error_block()
        self.flush_warning_block()
    def stop_server(self):
        if not self.adapter.is_running():
            self.write_console(
                "[MANAGER] El servidor no está iniciado.",
                "warning"
            )
            return

        self.write_console(
            "[MANAGER] Deteniendo servidor...",
            "system"
        )

        try:
            self.adapter.stop()

        except Exception as error:
            self.write_console(
                f"[MANAGER ERROR] {error}",
                "error"
            )

    def restart_server(self):
        if not self.adapter.is_running():
            self.start_server()
            return

        self.write_console(
            "[MANAGER] Reiniciando servidor...",
            "system"
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
                "error"
            )

    def wait_and_restart(self):
        if self.adapter.process:
            self.adapter.process.wait()

        self.root.after(
            1000,
            self.start_server
        )

    def send_command(self):
        command = self.command_entry.get().strip()

        if not command:
            return

        if not self.adapter.is_running():
            self.write_console(
                "[MANAGER] El servidor no está iniciado.",
                "warning"
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
                "error"
            )

    def copy_console(self):
        current_tab = self.notebook.index(
            self.notebook.select()
        )

        tab_keys = [
            "all",
            "info",
            "warning",
            "error",
            "success",
            "system"
        ]

        key = tab_keys[current_tab]

        console = self.console_widgets[key]

        text = console.get(
            "1.0",
            "end-1c"
        )

        if not text:
            self.write_console(
                "[MANAGER] La pestaña actual está vacía.",
                "warning"
            )
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)

        self.write_console(
            f"[MANAGER] Consola '{key}' copiada.",
            "system"
        )

    def clear_console(self):
        current_tab = self.notebook.index(
            self.notebook.select()
        )

        tab_keys = [
            "all",
            "info",
            "warning",
            "error",
            "success",
            "system"
        ]

        key = tab_keys[current_tab]

        console = self.console_widgets[key]

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

    def run(self):
        self.root.mainloop()