import json
import re
from pathlib import Path


class ProfileManager:
    def __init__(self, base_path=None):
        if base_path is None:
            base_path = Path(__file__).parent

        self.base_path = Path(base_path)

        self.profiles_path = (
            self.base_path / "profiles"
        )

        self.config_path = (
            self.base_path / "manager_config.json"
        )

        self.profiles_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self._ensure_config()

    def _ensure_config(self):
        if self.config_path.exists():
            return

        self._save_config(
            {
                "active_profile": None
            }
        )

    def _load_config(self):
        try:
            with open(
                self.config_path,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except Exception:
            return {
                "active_profile": None
            }

    def _save_config(self, config):
        with open(
            self.config_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                config,
                file,
                indent=4,
                ensure_ascii=False
            )

    def _safe_name(self, name):
        name = name.strip()

        safe = re.sub(
            r"[^a-zA-Z0-9_\- ]",
            "",
            name
        )

        safe = safe.replace(
            " ",
            "_"
        )

        return safe.lower()

    def _profile_file(self, name):
        safe = self._safe_name(name)

        return (
            self.profiles_path
            / f"{safe}.json"
        )

    def create_profile(
        self,
        name,
        server_path,
        min_ram="4G",
        max_ram="8G"
    ):
        if not name.strip():
            raise ValueError(
                "El perfil necesita un nombre."
            )

        server_path = Path(
            server_path
        ).resolve()

        profile = {
            "name": name.strip(),
            "server_path": str(server_path),
            "memory": {
                "min": min_ram,
                "max": max_ram
            },
            "minecraft": {
                "version": None
            },
            "loader": {
                "type": None,
                "version": None
            }
        }

        self.save_profile(profile)

        return profile

    def save_profile(self, profile):
        name = profile.get("name")

        if not name:
            raise ValueError(
                "El perfil no tiene nombre."
            )

        path = self._profile_file(name)

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                profile,
                file,
                indent=4,
                ensure_ascii=False
            )

        return path

    def load_profile(self, name):
        path = self._profile_file(name)

        if not path.exists():
            return None

        try:
            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except Exception:
            return None

    def list_profiles(self):
        profiles = []

        for path in sorted(
            self.profiles_path.glob("*.json")
        ):
            try:
                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as file:
                    profile = json.load(file)

                profiles.append(profile)

            except Exception:
                continue

        return profiles

    def get_profile_names(self):
        return [
            profile["name"]
            for profile
            in self.list_profiles()
            if "name" in profile
        ]

    def set_active_profile(self, name):
        if self.load_profile(name) is None:
            raise ValueError(
                f"No existe el perfil '{name}'."
            )

        config = self._load_config()
        config["active_profile"] = name
        self._save_config(config)

    def get_active_profile_name(self):
        config = self._load_config()

        return config.get(
            "active_profile"
        )

    def get_active_profile(self):
        name = self.get_active_profile_name()

        if not name:
            return None

        return self.load_profile(name)

    def delete_profile(self, name):
        path = self._profile_file(name)

        if path.exists():
            path.unlink()

        config = self._load_config()

        if config.get("active_profile") == name:
            config["active_profile"] = None
            self._save_config(config)
