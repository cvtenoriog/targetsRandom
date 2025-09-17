import subprocess

GAZE_EXE_PATH = r"C:\Users\ctenorio\Documents\dev\tobii\tobiiCpp\build\gaze.exe"
SCREEN_W, SCREEN_H = 1920, 1080

process = subprocess.Popen(GAZE_EXE_PATH, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

print("Extrayendo coordenadas de mirada en píxeles...\n")

try:
    for line in iter(process.stdout.readline, ''):
        if "Gaze point:" in line:
            try:
                parts = line.strip().split("Gaze point:")[1]
                x_norm, y_norm = [float(v.strip()) for v in parts.split(",")]
                x_pix = int(x_norm * SCREEN_W)
                y_pix = int(y_norm * SCREEN_H)
                print(f"Gaze en píxeles: ({x_pix}, {y_pix})")
            except Exception as e:
                print("Error parseando:", line, e)
except KeyboardInterrupt:
    print("Interrumpido por usuario.")
finally:
    process.kill()
