import re
import threading
import tkinter as tk

from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import filedialog

from server_adapter import ServerAdapter


class ServerManagerGUI:
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

    def __init__(self, profile_manager):
        self.profile_manager = profile_manager

        self.adapter = None
        self.profile = None
        self.info = None

        self.root = tk.Tk()
        self.root.title("Minecraft Server Manager")
        self.root.geometry("1250x800")
        self.root.minsize(1000, 650)

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.counters = {
            "info": 0,
            "warning": 0,
            "error": 0,
            "success": 0,
            "system": 0
        }

        self.console_widgets = {}

        self.active_block_type = None
        self.active_block_lines = []

        self.warning_blocks = []
        self.error_blocks = []

        self.warning_number = 0
        self.error_number = 0

        self.create_main_interface()
        self.load_initial_profile()

    # =========================================================
    # PESTAÑAS PRINCIPALES
    # =========================================================

    def create_main_interface(self):
        self.main_notebook = ttk.Notebook(
            self.root
        )

        self.main_notebook.pack(
            fill="both",
            expand=True
        )

        self.home_page = ttk.Frame(
            self.main_notebook
        )

        self.launcher_page = ttk.Frame(
            self.main_notebook
        )

        self.server_page = ttk.Frame(
            self.main_notebook
        )

        self.main_notebook.add(
            self.home_page,
            text="INICIO"
        )

        self.main_notebook.add(
            self.launcher_page,
            text="LAUNCHER"
        )

        self.main_notebook.add(
            self.server_page,
            text="SERVIDOR"
        )

        self.create_home_page()
        self.create_launcher_page()
        self.create_server_page()

    # =========================================================
    # INICIO
    # =========================================================

    def create_home_page(self):
        title = ttk.Label(
            self.home_page,
            text="Minecraft Server Manager",
            font=("Segoe UI", 22, "bold")
        )

        title.pack(
            pady=(40, 10)
        )

        ttk.Label(
            self.home_page,
            text=(
                "Administrá versiones, loaders, "
                "modpacks y servidores desde un solo lugar."
            )
        ).pack(
            pady=5
        )

        self.home_profile_label = ttk.Label(
            self.home_page,
            text="Perfil activo: Ninguno",
            font=("Segoe UI", 13, "bold")
        )

        self.home_profile_label.pack(
            pady=(40, 5)
        )

        self.home_info_label = ttk.Label(
            self.home_page,
            text=""
        )

        self.home_info_label.pack(
            pady=5
        )

        ttk.Button(
            self.home_page,
            text="Ir al Launcher",
            command=lambda:
                self.main_notebook.select(
                    self.launcher_page
                )
        ).pack(
            pady=20
        )

    # =========================================================
    # LAUNCHER
    # =========================================================

    def create_launcher_page(self):
        frame = ttk.Frame(
            self.launcher_page,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="Launcher",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w"
        )

        ttk.Label(
            frame,
            text=(
                "Seleccioná o importá una "
                "instancia de servidor."
            )
        ).pack(
            anchor="w",
            pady=(5, 25)
        )

        profile_frame = ttk.LabelFrame(
            frame,
            text="Perfil",
            padding=15
        )

        profile_frame.pack(
            fill="x",
            pady=10
        )

        self.profile_combo = ttk.Combobox(
            profile_frame,
            state="readonly",
            width=40
        )

        self.profile_combo.pack(
            side="left",
            padx=(0, 10)
        )

        self.profile_combo.bind(
            "<<ComboboxSelected>>",
            self.on_profile_selected
        )

        ttk.Button(
            profile_frame,
            text="Actualizar",
            command=self.refresh_profiles
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            profile_frame,
            text="Eliminar",
            command=self.delete_current_profile
        ).pack(
            side="left",
            padx=5
        )

        import_frame = ttk.LabelFrame(
            frame,
            text="Importar servidor existente",
            padding=15
        )

        import_frame.pack(
            fill="x",
            pady=10
        )

        ttk.Label(
            import_frame,
            text="Nombre:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.profile_name_entry = ttk.Entry(
            import_frame,
            width=40
        )

        self.profile_name_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        ttk.Label(
            import_frame,
            text="Carpeta:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.server_path_entry = ttk.Entry(
            import_frame,
            width=70
        )

        self.server_path_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        ttk.Button(
            import_frame,
            text="Examinar",
            command=self.browse_server_folder
        ).grid(
            row=1,
            column=2,
            padx=5
        )

        ttk.Label(
            import_frame,
            text="RAM mínima:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.min_ram_entry = ttk.Entry(
            import_frame,
            width=10
        )

        self.min_ram_entry.insert(
            0,
            "4G"
        )

        self.min_ram_entry.grid(
            row=2,
            column=1,
            sticky="w",
            padx=5,
            pady=5
        )

        ttk.Label(
            import_frame,
            text="RAM máxima:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.max_ram_entry = ttk.Entry(
            import_frame,
            width=10
        )

        self.max_ram_entry.insert(
            0,
            "8G"
        )

        self.max_ram_entry.grid(
            row=3,
            column=1,
            sticky="w",
            padx=5,
            pady=5
        )

        ttk.Button(
            import_frame,
            text="IMPORTAR SERVIDOR",
            command=self.import_existing_server
        ).grid(
            row=4,
            column=0,
            columnspan=3,
            pady=20
        )

        import_frame.columnconfigure(
            1,
            weight=1
        )

        info_frame = ttk.LabelFrame(
            frame,
            text="Instancia detectada",
            padding=15
        )

        info_frame.pack(
            fill="x",
            pady=10
        )

        self.launcher_info_label = ttk.Label(
            info_frame,
            text="Ningún perfil seleccionado."
        )

        self.launcher_info_label.pack(
            anchor="w"
        )

    def browse_server_folder(self):
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta del servidor"
        )

        if not folder:
            return

        self.server_path_entry.delete(
            0,
            "end"
        )

        self.server_path_entry.insert(
            0,
            folder
        )

    def refresh_profiles(self):
        names = (
            self.profile_manager
            .get_profile_names()
        )

        self.profile_combo[
            "values"
        ] = names

    def load_initial_profile(self):
        self.refresh_profiles()

        profile = (
            self.profile_manager
            .get_active_profile()
        )

        if not profile:
            return

        self.profile_combo.set(
            profile["name"]
        )

        self.load_profile(
            profile
        )

    def on_profile_selected(
        self,
        event=None
    ):
        name = (
            self.profile_combo
            .get()
            .strip()
        )

        if not name:
            return

        profile = (
            self.profile_manager
            .load_profile(name)
        )

        if not profile:
            return

        self.profile_manager.set_active_profile(
            name
        )

        self.load_profile(
            profile
        )

    def import_existing_server(self):
        name = (
            self.profile_name_entry
            .get()
            .strip()
        )

        server_path = (
            self.server_path_entry
            .get()
            .strip()
        )

        if not name:
            messagebox.showerror(
                "Error",
                "Poné un nombre al perfil."
            )
            return

        if not server_path:
            messagebox.showerror(
                "Error",
                "Seleccioná una carpeta."
            )
            return

        try:
            adapter = ServerAdapter(
                server_path
            )

            info = adapter.inspect()

            profile = (
                self.profile_manager
                .create_profile(
                    name=name,
                    server_path=server_path,
                    min_ram=(
                        self.min_ram_entry
                        .get()
                        .strip()
                        or "4G"
                    ),
                    max_ram=(
                        self.max_ram_entry
                        .get()
                        .strip()
                        or "8G"
                    )
                )
            )

            profile[
                "minecraft"
            ][
                "version"
            ] = info[
                "minecraft_version"
            ]

            profile[
                "loader"
            ][
                "type"
            ] = info[
                "loader"
            ]

            profile[
                "loader"
            ][
                "version"
            ] = info[
                "loader_version"
            ]

            self.profile_manager.save_profile(
                profile
            )

            self.profile_manager.set_active_profile(
                profile["name"]
            )

            self.refresh_profiles()

            self.profile_combo.set(
                profile["name"]
            )

            self.load_profile(
                profile
            )

            messagebox.showinfo(
                "Servidor importado",
                (
                    f"Perfil '{name}' creado.\n\n"
                    f"Minecraft: "
                    f"{info['minecraft_version']}\n"
                    f"Loader: "
                    f"{info['loader']} "
                    f"{info['loader_version']}"
                )
            )

        except Exception as error:
            messagebox.showerror(
                "No se pudo importar",
                str(error)
            )

    def load_profile(
        self,
        profile
    ):
        if (
            self.adapter
            and self.adapter.is_running()
        ):
            messagebox.showwarning(
                "Servidor activo",
                (
                    "No podés cambiar de perfil "
                    "mientras el servidor está corriendo."
                )
            )
            return

        self.profile = profile

        self.adapter = ServerAdapter(
            profile["server_path"]
        )

        try:
            self.info = self.adapter.inspect()

        except Exception as error:
            self.info = None

            messagebox.showerror(
                "Perfil inválido",
                str(error)
            )

            return

        self.update_profile_display()

    def update_profile_display(self):
        if not self.profile:
            return

        info = self.info

        text = (
            f"Perfil: {self.profile['name']}\n"
            f"Ruta: {self.profile['server_path']}\n"
            f"Minecraft: {info['minecraft_version']}\n"
            f"Loader: {info['loader']} "
            f"{info['loader_version']}\n"
            f"Mods: {info['mods']}\n"
            f"Mundo: {info['world']}\n"
            f"Puerto: {info['port']}"
        )

        self.launcher_info_label.config(
            text=text
        )

        self.home_profile_label.config(
            text=(
                f"Perfil activo: "
                f"{self.profile['name']}"
            )
        )

        self.home_info_label.config(
            text=(
                f"Minecraft "
                f"{info['minecraft_version']} | "
                f"{info['loader']} "
                f"{info['loader_version']} | "
                f"{info['mods']} mods"
            )
        )

        self.update_server_header()

    def delete_current_profile(self):
        name = (
            self.profile_combo
            .get()
            .strip()
        )

        if not name:
            return

        if (
            self.adapter
            and self.adapter.is_running()
        ):
            messagebox.showwarning(
                "Servidor activo",
                "Primero detené el servidor."
            )
            return

        confirm = messagebox.askyesno(
            "Eliminar perfil",
            (
                f"¿Eliminar el perfil '{name}'?\n\n"
                "NO se borrará la carpeta "
                "del servidor."
            )
        )

        if not confirm:
            return

        self.profile_manager.delete_profile(
            name
        )

        self.profile = None
        self.adapter = None
        self.info = None

        self.profile_combo.set("")

        self.refresh_profiles()

        self.launcher_info_label.config(
            text="Ningún perfil seleccionado."
        )

        self.home_profile_label.config(
            text="Perfil activo: Ninguno"
        )

        self.home_info_label.config(
            text=""
        )

        self.update_server_header()

    # =========================================================
    # SERVIDOR
    # =========================================================

    def create_server_page(self):
        self.server_container = ttk.Frame(
            self.server_page
        )

        self.server_container.pack(
            fill="both",
            expand=True
        )

        self.create_top_panel()
        self.create_counter_panel()
        self.create_console_tabs()
        self.create_command_panel()
        self.create_bottom_buttons()

    def create_top_panel(self):
        frame = ttk.Frame(
            self.server_container,
            padding=10
        )

        frame.pack(
            fill="x"
        )

        self.server_profile_label = ttk.Label(
            frame,
            text="Perfil: Ninguno"
        )

        self.server_profile_label.pack(
            side="left",
            padx=10
        )

        self.server_minecraft_label = ttk.Label(
            frame,
            text="Minecraft: -"
        )

        self.server_minecraft_label.pack(
            side="left",
            padx=10
        )

        self.server_loader_label = ttk.Label(
            frame,
            text="Loader: -"
        )

        self.server_loader_label.pack(
            side="left",
            padx=10
        )

        self.server_mods_label = ttk.Label(
            frame,
            text="Mods: -"
        )

        self.server_mods_label.pack(
            side="left",
            padx=10
        )

        self.server_java_label = ttk.Label(
            frame,
            text="Java: -"
        )

        self.server_java_label.pack(
            side="left",
            padx=10
        )

        self.server_port_label = ttk.Label(
            frame,
            text="Puerto: -"
        )

        self.server_port_label.pack(
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

    def update_server_header(self):
        if not self.info or not self.profile:
            self.server_profile_label.config(
                text="Perfil: Ninguno"
            )

            self.server_minecraft_label.config(
                text="Minecraft: -"
            )

            self.server_loader_label.config(
                text="Loader: -"
            )

            self.server_mods_label.config(
                text="Mods: -"
            )

            self.server_java_label.config(
                text="Java: -"
            )

            self.server_port_label.config(
                text="Puerto: -"
            )

            return

        self.server_profile_label.config(
            text=(
                f"Perfil: "
                f"{self.profile['name']}"
            )
        )

        self.server_minecraft_label.config(
            text=(
                f"Minecraft: "
                f"{self.info['minecraft_version']}"
            )
        )

        self.server_loader_label.config(
            text=(
                f"Loader: "
                f"{self.info['loader']} "
                f"{self.info['loader_version']}"
            )
        )

        self.server_mods_label.config(
            text=(
                f"Mods: "
                f"{self.info['mods']}"
            )
        )

        self.server_java_label.config(
            text=(
                f"Java: "
                f"{self.info['java_version']}"
            )
        )

        self.server_port_label.config(
            text=(
                f"Puerto: "
                f"{self.info['port']}"
            )
        )

    def create_counter_panel(self):
        frame = ttk.Frame(
            self.server_container,
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
            self.server_container,
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

            console = scrolledtext.ScrolledText(
                tab_frame,
                bg="#111111",
                fg="#dddddd",
                insertbackground="white",
                font=("Consolas", 10),
                state="disabled",
                wrap="none"
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
            self.server_container,
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
            self.server_container,
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

            title = (
                f"ERROR #{self.error_number}"
            )

            header_tag = (
                "header_error"
            )

        else:
            self.warning_number += 1
            self.warning_blocks.append(block)

            title = (
                f"WARNING #{self.warning_number}"
            )

            header_tag = (
                "header_warning"
            )

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

    def process_log_line(
        self,
        line
    ):
        explicit_level = (
            self.get_explicit_log_level(
                line
            )
        )

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

        if self.active_block_type:
            self.append_to_active_block(
                line
            )

            return

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
    # CONTROL SERVER
    # =========================================================

    def start_server(self):
        if self.adapter is None:
            messagebox.showwarning(
                "Sin servidor",
                (
                    "Primero seleccioná o importá "
                    "un perfil en LAUNCHER."
                )
            )

            self.main_notebook.select(
                self.launcher_page
            )

            return

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

            memory = (
                self.profile.get(
                    "memory",
                    {}
                )
                if self.profile
                else {}
            )

            process = self.adapter.start(
                min_ram=memory.get(
                    "min",
                    "4G"
                ),
                max_ram=memory.get(
                    "max",
                    "8G"
                )
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

        if self.adapter is not None:
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
        if (
            self.adapter is None
            or not self.adapter.is_running()
        ):
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
        if self.adapter is None:
            self.start_server()
            return

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
        if self.adapter is None:
            return

        process = self.adapter.process

        if process is None:
            self.root.after(
                500,
                self.start_server
            )
            return

        process.wait()

        if self.adapter is not None:
            self.adapter.process = None

        self.root.after(
            1000,
            self.start_server
        )

    def send_command(self):
        command = (
            self.command_entry
            .get()
            .strip()
        )

        if not command:
            return

        if (
            self.adapter is None
            or not self.adapter.is_running()
        ):
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
        if (
            self.adapter is None
            or not self.adapter.is_running()
        ):
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
        if (
            self.adapter is not None
            and self.adapter.is_running()
        ):
            self.root.after(
                250,
                self.wait_for_close
            )

            return

        self.root.destroy()

    def run(self):
        self.root.mainloop()
