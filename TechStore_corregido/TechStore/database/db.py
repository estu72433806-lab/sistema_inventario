"""
Módulo de conexión y gestión de base de datos SQLite local.
La base vive en data/inventario_tienda.db. Si existe la copia antigua en la raíz
del proyecto, se mueve automáticamente a data/ la primera vez.
"""
import sqlite3
import os
import shutil

DB_FILENAME = "inventario_tienda.db"
DATA_DIRNAME = "data"

def get_base_dir():
    """Carpeta raíz del proyecto (un nivel por encima de database/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_path():
    """Retorna la ruta absoluta de la base SQLite, creando data/ si hace falta."""
    base_dir = get_base_dir()
    data_dir = os.path.join(base_dir, DATA_DIRNAME)
    os.makedirs(data_dir, exist_ok=True)
    ruta = os.path.join(data_dir, DB_FILENAME)
    legado = os.path.join(base_dir, DB_FILENAME)
    if not os.path.exists(ruta) and os.path.exists(legado):
        shutil.move(legado, ruta)
    return ruta

def get_connection():
    """Crea y retorna una conexión a la base SQLite con claves foráneas activas."""
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn
