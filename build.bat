    @echo off
setlocal

python -m pip install -r requirements.txt
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --icon assets\app_icon.ico ^
  --add-data "assets\app_icon.ico;assets" ^
  --add-data "assets\pdf_tool.png;assets" ^
  --exclude-module torch ^
  --exclude-module torchvision ^
  --exclude-module pandas ^
  --exclude-module scipy ^
  --exclude-module pyarrow ^
  --exclude-module onnxruntime ^
  --name pdf-toolbox ^
  app.py

echo.
echo Build complete. Output: dist\pdf-toolbox.exe
pause
