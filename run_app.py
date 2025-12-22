import webview
import threading
import subprocess
import sys
import time

# Функция для запуска FastAPI/uvicorn сервера
def start_server():
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload"])

# Запускаем сервер в отдельном потоке
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Даём серверу пару секунд на старт
time.sleep(2)

# Открываем веб-приложение в отдельном окне
webview.create_window("Messenger", "http://127.0.0.1:8000")
webview.start()