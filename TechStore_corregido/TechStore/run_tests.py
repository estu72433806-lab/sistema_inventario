"""
Ejecuta todas las pruebas de tests/ y muestra un resumen final.
Uso:  python run_tests.py
Nota: las pruebas de interfaz (Tkinter) y de nube (psycopg2) requieren esas
librerías instaladas; si faltan, aparecerán como fallidas.
"""
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    archivos = sorted(glob.glob(os.path.join(ROOT, "tests", "test_*.py")))
    fallidas = []
    for ruta in archivos:
        nombre = os.path.basename(ruta)
        print(f"\n===== {nombre}")
        resultado = subprocess.run([sys.executable, ruta], cwd=ROOT)
        if resultado.returncode != 0:
            fallidas.append(nombre)

    print("\n" + "=" * 50)
    if fallidas:
        print(f"Con errores ({len(fallidas)}/{len(archivos)}): " + ", ".join(fallidas))
        return 1
    print(f"Todas las pruebas pasaron ({len(archivos)}/{len(archivos)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
