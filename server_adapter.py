from pathlib import Path
import re
import subprocess
import shutil


class ServerAdapter:
    def __init__(self, server_path):
        self.server_path = Path(server_path)
        self.process = None

    def detect_fabric_from_jar(self):
        pattern = re.compile(
            r"fabric-server-mc\.(.+?)-loader\.(.+?)-launcher\.(.+?)\.jar",
            re.IGNORECASE
        )

        for file in self.server_path.glob("*.jar"):
            match = pattern.match(file.name)

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
        fabric = self.detect_fabric_from_jar()

        if fabric:
            return fabric

        libraries = self.server_path / "libraries"

        if not libraries.exists():
            return self.unknown_loader()

        neoforge_path = libraries / "net" / "neoforged" / "neoforge"

        if neoforge_path.exists():
            versions = [
                x.name
                for x in neoforge_path.iterdir()
                if x.is_dir()
            ]

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
            versions = [
                x.name
                for x in forge_path.iterdir()
                if x.is_dir()
            ]

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
            for folder in versions_path.iterdir():
                if folder.is_dir():
                    if re.fullmatch(
                        r"\d+\.\d+(?:\.\d+)?",
                        folder.name
                    ):
                        return folder.name

        return "unknown"

    def count_mods(self):
        mods_path = self.server_path / "mods"

        if not mods_path.exists():
            return 0

        return len(
            list(mods_path.glob("*.jar"))
        )

    def read_server_properties(self):
        props_path = (
            self.server_path /
            "server.properties"
        )

        data = {}

        if not props_path.exists():
            return data

        with open(
            props_path,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                if "=" in line:
                    key, value = line.split(
                        "=",
                        1
                    )

                    data[key] = value

        return data

    def detect_java(self):
        java_path = shutil.which("java")

        if not java_path:
            return {
                "found": False,
                "path": None,
                "version": None
            }

        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True
            )

            output = (
                result.stderr
                or result.stdout
            )

            match = re.search(
                r'version "([^"]+)"',
                output
            )

            version = (
                match.group(1)
                if match
                else "unknown"
            )

            return {
                "found": True,
                "path": java_path,
                "version": version
            }

        except Exception:
            return {
                "found": False,
                "path": java_path,
                "version": None
            }

    def inspect(self):
        loader = self.detect_loader()
        props = self.read_server_properties()
        java = self.detect_java()

        return {
            "server_path": str(self.server_path),

            "minecraft_version":
                self.detect_minecraft_version(),

            "loader":
                loader["type"],

            "loader_version":
                loader["loader_version"],

            "launcher_version":
                loader["launcher_version"],

            "server_jar":
                loader["jar"],

            "mods":
                self.count_mods(),

            "world":
                props.get(
                    "level-name",
                    "world"
                ),

            "port":
                props.get(
                    "server-port",
                    "25565"
                ),

            "max_players":
                props.get(
                    "max-players",
                    "unknown"
                ),

            "java_found":
                java["found"],

            "java_path":
                java["path"],

            "java_version":
                java["version"]
        }

    def is_running(self):
        return (
            self.process is not None
            and self.process.poll() is None
        )

    def start(self, min_ram="4G", max_ram="8G"):
        if self.is_running():
            raise RuntimeError(
                "El servidor ya está iniciado."
            )

        loader = self.detect_loader()
        java = self.detect_java()

        if not java["found"]:
            raise RuntimeError(
                "Java no fue encontrado."
            )

        if not loader["jar"]:
            raise RuntimeError(
                "No se encontró el JAR del servidor."
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
            cwd=self.server_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        return self.process

    def send_command(self, command):
        if not self.is_running():
            raise RuntimeError(
                "El servidor no está iniciado."
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
        if self.is_running():
            self.process.kill()