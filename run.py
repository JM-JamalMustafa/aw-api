# /run.py
from threading import Thread
from app import app, socketio  # Import the app and socketio initialized in __init__.py
# from trayicon import start_tray_icon  # Import the tray icon function

if __name__ == '__main__':
    # Start the Tray Icon in a separate thread
    # Thread(target=start_tray_icon, daemon=True).start()

    # Start Flask and WebSocket server
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
