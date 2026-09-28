from pathlib import Path
import re
import shutil
import socket
import subprocess


class ServerAdapter:
    def __init__(self, server_path):
        self.server_path = Path(server_path)
        self.process = None

    def validate_server_path(self):
        if not self.server_path.exists():
            raise RuntimeError(
                f"No existe la carpeta del servidor:\n{self.server_path}"
            )

        if not self.server_path.is_dir():
            raise RuntimeError(
                f"La ruta no es una carpeta:\n{self.server_path}"
            )

    def detect_fabric_from_jar(self):
        pattern = re.compile(
            r"fabric-server-mc\.(.+?)-loader\.(.+?)-launcher\.(.+?)\.jar",
            re.IGNORECASE
        )

        for file in self.server_path.glob("*.jar"):
            match = pattern.fullmatch(file.name)

            if match:
                return {
                    "type": "fabric",
                    "minecraft_version": match.group(1),
                    "loader_version": match.group(2),
                    "launcher_version": match.group(3),
                    "jar": file.name
                }

        return None

    def unknown_loader(self):
        return {
            "type": "unknown",
            "minecraft_version": None,
            "loader_version": None,
            "launcher_version": None,
            "jar": None
        }

    def detect_loader(self):
        self.validate_server_path()

        fabric = self.detect_fabric_from_jar()

        if fabric:
            return fabric

        libraries = self.server_path / "libraries"

        if not libraries.exists():
            return self.unknown_loader()

        neoforge_path = libraries / "net" / "neoforged" / "neoforge"

        if neoforge_path.exists():
            versions = sorted(
                [
                    folder.name
                    for folder in neoforge_path.iterdir()
                    if folder.is_dir()
                ]
            )

            if versions:
                return {
                    "type": "neoforge",
                    "minecraft_version": None,
                    "loader_version": versions[-1],
                    "launcher_version": None,
                    "jar": None
                }

        forge_path = libraries / "net" / "minecraftforge" / "forge"

        if forge_path.exists():
            versions = sorted(
                [
                    folder.name
                    for folder in forge_path.iterdir()
                    if folder.is_dir()
                ]
            )

            if versions:
                version = versions[-1]

                match = re.match(
                    r"(\d+\.\d+(?:\.\d+)?)",
                    version
                )

                minecraft_version = (
                    match.group(1)
                    if match
                    else None
                )

                return {
                    "type": "forge",
                    "minecraft_version": minecraft_version,
                    "loader_version": version,
                    "launcher_version": None,
                    "jar": None
                }

        return self.unknown_loader()

    def detect_minecraft_version(self):
        loader = self.detect_loader()

        if loader["minecraft_version"]:
            return loader["minecraft_version"]

        versions_path = self.server_path / "versions"

        if versions_path.exists():
            versions = []

            for folder in versions_path.iterdir():
                if not folder.is_dir():
                    continue

                if re.fullmatch(
                    r"\d+\.\d+(?:\.\d+)?",
                    folder.name
                ):
                    versions.append(folder.name)

            if versions:
                return sorted(versions)[-1]

        return "unknown"

    def count_mods(self):
        mods_path = self.server_path / "mods"

        if not mods_path.exists():
            return 0

        return len(
            list(mods_path.glob("*.jar"))
        )

    def read_server_properties(self):
        properties_path = (
            self.server_path
            / "server.properties"
        )

        properties = {}

        if not properties_path.exists():
            return properties

        with open(
            properties_path,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                if "=" not in line:
                    continue

                key, value = line.split(
                    "=",
                    1
                )

                properties[key.strip()] = value.strip()

        return properties

    def get_server_port(self):
        properties = self.read_server_properties()

        try:
            return int(
                properties.get(
                    "server-port",
                    "25565"
                )
            )
        except ValueError:
            return 25565

    def is_port_in_use(self, port=None):
        if port is None:
            port = self.get_server_port()

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(0.4)

        try:
            result = sock.connect_ex(
                ("127.0.0.1", port)
            )

            return result == 0

        finally:
            sock.close()

    def detect_java(self):
        java_path = shutil.which("java")

        if not java_path:
            return {
                "found": False,
                "path": None,
                "version": None,
                "major": None
            }

        try:
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = (
                result.stderr
                or result.stdout
            )

            match = re.search(
                r'version "([^"]+)"',
                output
            )

            if not match:
                return {
                    "found": True,
                    "path": java_path,
                    "version": "unknown",
                    "major": None
                }

            version = match.group(1)

            major = self.get_java_major(
                version
            )

            return {
                "found": True,
                "path": java_path,
                "version": version,
                "major": major
            }

        except Exception:
            return {
                "found": False,
                "path": java_path,
                "version": None,
                "major": None
            }

    def get_java_major(self, version):
        try:
            parts = version.split(".")

            if parts[0] == "1":
                return int(parts[1])

            return int(parts[0])

        except (ValueError, IndexError):
            return None

    def required_java_version(self):
        minecraft = self.detect_minecraft_version()

        if minecraft == "unknown":
            return None

        try:
            parts = [
                int(x)
                for x in minecraft.split(".")
            ]

        except ValueError:
            return None

        while len(parts) < 3:
            parts.append(0)

        version = tuple(parts[:3])

        if version >= (1, 20, 5):
            return 21

        if version >= (1, 18, 0):
            return 17

        if version >= (1, 17, 0):
            return 16

        return 8

    def inspect(self):
        self.validate_server_path()

        loader = self.detect_loader()
        properties = self.read_server_properties()
        java = self.detect_java()

        return {
            "server_path": str(self.server_path),
            "minecraft_version": self.detect_minecraft_version(),
            "loader": loader["type"],
            "loader_version": loader["loader_version"],
            "launcher_version": loader["launcher_version"],
            "server_jar": loader["jar"],
            "mods": self.count_mods(),
            "world": properties.get(
                "level-name",
                "world"
            ),
            "port": self.get_server_port(),
            "max_players": properties.get(
                "max-players",
                "unknown"
            ),
            "java_found": java["found"],
            "java_path": java["path"],
            "java_version": java["version"],
            "java_major": java["major"],
            "java_required": self.required_java_version()
        }

    def is_running(self):
        return (
            self.process is not None
            and self.process.poll() is None
        )

    def start(self, min_ram="4G", max_ram="8G"):
        self.validate_server_path()

        if self.is_running():
            raise RuntimeError(
                "El servidor ya está iniciado por este manager."
            )

        port = self.get_server_port()

        if self.is_port_in_use(port):
            raise RuntimeError(
                f"El puerto {port} ya está ocupado.\n"
                "Es posible que ya exista otro servidor "
                "de Minecraft ejecutándose."
            )

        loader = self.detect_loader()
        java = self.detect_java()

        if not java["found"]:
            raise RuntimeError(
                "Java no fue encontrado."
            )

        required = self.required_java_version()

        if (
            required is not None
            and java["major"] is not None
            and java["major"] < required
        ):
            raise RuntimeError(
                f"Minecraft necesita Java {required} "
                f"o superior, pero encontré Java "
                f"{java['major']}."
            )

        if loader["type"] != "fabric":
            raise RuntimeError(
                f"Se detectó {loader['type']}, "
                "pero todavía no implementamos "
                "su método de inicio."
            )

        if not loader["jar"]:
            raise RuntimeError(
                "No se encontró el JAR de Fabric."
            )

        command = [
            java["path"],
            f"-Xms{min_ram}",
            f"-Xmx{max_ram}",
            "-jar",
            loader["jar"],
            "nogui"
        ]

        self.process = subprocess.Popen(
            command,
            cwd=str(self.server_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        return self.process

    def send_command(self, command):
        if not self.is_running():
            raise RuntimeError(
                "El servidor no está iniciado."
            )

        if self.process.stdin is None:
            raise RuntimeError(
                "No está disponible la entrada "
                "de comandos del servidor."
            )

        self.process.stdin.write(
            command + "\n"
        )

        self.process.stdin.flush()

    def stop(self):
        if not self.is_running():
            return

        self.send_command("stop")

    def kill(self):
        if not self.is_running():
            return

        self.process.kill()
