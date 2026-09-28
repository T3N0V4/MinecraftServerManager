from server_adapter import ServerAdapter
from gui import ServerGUI


SERVER_PATH = r"C:\Minecraft\HORIZONS_CHUNK_SERVER\Server"


adapter = ServerAdapter(
    SERVER_PATH
)

app = ServerGUI(
    adapter
)

app.run()