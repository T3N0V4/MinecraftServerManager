from server_adapter import ServerAdapter
from gui import ServerGUI


SERVER_PATH = r"C:\Minecraft\HORIZONS_CHUNK_SERVER\Server"


def main():
    adapter = ServerAdapter(SERVER_PATH)
    app = ServerGUI(adapter)
    app.run()


if __name__ == "__main__":
    main()