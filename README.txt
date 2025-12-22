# Быстрый запуск проекта

1. Открой терминал в папке messenger
2. Создай виртуальное окружение:
   python -m venv venv
3. Активируй его:
   PowerShell:
       .\venv\Scripts\Activate.ps1
       (если выдаёт ошибку: Set-ExecutionPolicy RemoteSigned)
   CMD:
       venv\Scripts\activate.bat
4. Установи зависимости:
   pip install --upgrade pip
   pip install fastapi uvicorn
5. Запусти сервер:
   python -m uvicorn main:app --reload
6. Открой браузер:
   http://127.0.0.1:8000/
