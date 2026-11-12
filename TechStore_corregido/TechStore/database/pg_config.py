"""
Módulo de Configuración Segura para PostgreSQL (Nube / Servidor Remoto).
Maneja credenciales mediante variables de entorno o archivo 'config_db.json' (ignorado por Git).
No expone contraseñas en código fuente.
"""
import os
import json
from urllib.parse import urlparse, parse_qs, unquote

CONFIG_FILENAME = "config_db.json"
EXAMPLE_FILENAME = "config_db.example.json"

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_path():
    return os.path.join(get_base_dir(), CONFIG_FILENAME)

def get_example_path():
    return os.path.join(get_base_dir(), EXAMPLE_FILENAME)

def crear_archivo_ejemplo_si_no_existe():
    """Crea un archivo plantilla config_db.example.json para guiar al usuario."""
    path = get_example_path()
    if not os.path.exists(path):
        ejemplo = {
            "pg_host": "ep-example.us-east-2.aws.neon.tech",
            "pg_port": 5432,
            "pg_database": "techstore_db",
            "pg_user": "postgres",
            "pg_password": "TU_PASSWORD_AQUI",
            "pg_sslmode": "require",
            "auto_sync": True,
            "timeout_segundos": 4
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(ejemplo, f, indent=4)
        except Exception:
            pass

def obtener_configuracion_pg() -> dict:
    """
    Obtiene los parámetros de conexión a PostgreSQL priorizando:
    1. Variables de entorno (PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD, PG_SSLMODE)
    2. Archivo local seguro 'config_db.json'
    3. Valores por defecto (desconectado)
    """
    crear_archivo_ejemplo_si_no_existe()

    config = {
        "pg_host": os.environ.get("PG_HOST", ""),
        "pg_port": int(os.environ.get("PG_PORT", 5432)),
        "pg_database": os.environ.get("PG_DATABASE", ""),
        "pg_user": os.environ.get("PG_USER", ""),
        "pg_password": os.environ.get("PG_PASSWORD", ""),
        "pg_sslmode": os.environ.get("PG_SSLMODE", "prefer"),
        "timeout_segundos": int(os.environ.get("PG_TIMEOUT", 4)),
        "auto_sync": os.environ.get("PG_AUTO_SYNC", "true").lower() in ("true", "1", "yes")
    }

    config_file = get_config_path()
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                for k, v in file_data.items():
                    # Solo sobreescribe si la variable de entorno no estaba fijada
                    if not config.get(k):
                        config[k] = v
        except Exception as e:
            print(f"Aviso: no se pudo leer {CONFIG_FILENAME}: {e}")

    return config

def guardar_configuracion_pg(nueva_config: dict) -> tuple[bool, str]:
    """Guarda la configuración en config_db.json de forma segura."""
    config_file = get_config_path()
    try:
        # Asegurarse de tipos correctos
        datos = {
            "pg_host": str(nueva_config.get("pg_host", "")).strip(),
            "pg_port": int(nueva_config.get("pg_port", 5432)),
            "pg_database": str(nueva_config.get("pg_database", "")).strip(),
            "pg_user": str(nueva_config.get("pg_user", "")).strip(),
            "pg_password": str(nueva_config.get("pg_password", "")),
            "pg_sslmode": str(nueva_config.get("pg_sslmode", "prefer")).strip(),
            "timeout_segundos": int(nueva_config.get("timeout_segundos", 4)),
            "auto_sync": bool(nueva_config.get("auto_sync", True))
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)
        return True, "Configuración guardada correctamente."
    except Exception as e:
        return False, f"Error al guardar configuración: {str(e)}"

def tiene_credenciales_pg() -> bool:
    """Verifica si al menos están especificados el host y la base de datos."""
    c = obtener_configuracion_pg()
    return bool(c.get("pg_host") and c.get("pg_database") and c.get("pg_user"))

def parse_connection_string(conn_string: str) -> tuple[dict, str]:
    """
    Parsea una URL de conexión de PostgreSQL (ej: postgresql://user:pass@host:5432/dbname?sslmode=require)
    comúnmente provista por servicios como Neon.tech, Supabase, Render, AWS, etc.
    Retorna (dict_datos, None) o (None, mensaje_error).
    """
    if not conn_string or not isinstance(conn_string, str):
        return None, "La cadena de conexión está vacía."

    s = conn_string.strip()
    # Limpiar posibles comandos de terminal como "psql " o comillas envolventes
    if s.lower().startswith("psql "):
        s = s[5:].strip()
    s = s.strip("'\"`")

    if not (s.startswith("postgres://") or s.startswith("postgresql://")):
        return None, "La URL debe comenzar con 'postgres://' o 'postgresql://'."

    try:
        parsed = urlparse(s)
        host = parsed.hostname or ""
        port = parsed.port or 5432
        user = unquote(parsed.username or "")
        password = unquote(parsed.password or "")

        # Eliminar barra inicial del path para obtener el nombre de la BD
        database = parsed.path.lstrip("/") if parsed.path else ""

        query_params = parse_qs(parsed.query)
        sslmode = query_params.get("sslmode", ["require"])[0]

        if not host:
            return None, "No se pudo identificar el Host / Servidor en la URL ingresada."
        if not database:
            return None, "No se pudo identificar el nombre de la Base de Datos en la URL."
        if not user:
            return None, "No se pudo identificar el Usuario en la URL."

        datos = {
            "pg_host": host,
            "pg_port": port,
            "pg_database": database,
            "pg_user": user,
            "pg_password": password,
            "pg_sslmode": sslmode,
            "timeout_segundos": 4,
            "auto_sync": True
        }
        return datos, None
    except Exception as e:
        return None, f"Error al procesar la cadena de conexión: {str(e)}"

