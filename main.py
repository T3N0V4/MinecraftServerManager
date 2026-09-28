from gui import ServerManagerGUI
from profile_manager import ProfileManager


def main():
    profile_manager = ProfileManager()

    app = ServerManagerGUI(
        profile_manager
    )

    app.run()


if __name__ == "__main__":
    main()
