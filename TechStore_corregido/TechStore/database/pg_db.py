"""
Módulo de Conexión a PostgreSQL (Nube / Servidor Remoto).
Maneja conexión con psycopg2, validación de conexión, tiempos límite (timeouts)
para evitar congelar la interfaz, y cierre seguro de recursos.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from database.pg_config import obtener_configuracion_pg, tiene_credenciales_pg

def get_pg_connection(timeout: int = None, config_override: dict = None):
    """
    Retorna una conexión activa a PostgreSQL.
    Si no es posible conectar o el servidor no responde dentro del timeout,
    retorna None y el mensaje de error correspondiente.
    """
    config = config_override if config_override else obtener_configuracion_pg()
    
    host = config.get("pg_host", "").strip()
    port = config.get("pg_port", 5432)
    database = config.get("pg_database", "").strip()
    user = config.get("pg_user", "").strip()
    password = config.get("pg_password", "")
    sslmode = config.get("pg_sslmode", "prefer")
    timeout_seg = timeout if timeout is not None else config.get("timeout_segundos", 4)

    if not host or not database or not user:
        return None, "Faltan datos de configuración de PostgreSQL (Host, Base de Datos o Usuario)."

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=user,
            password=password,
            sslmode=sslmode,
            connect_timeout=timeout_seg
        )
        return conn, None
    except psycopg2.OperationalError as e:
        msg = str(e).strip()
        if "timeout" in msg.lower():
            return None, f"Tiempo de espera agotado al conectar a PostgreSQL ({timeout_seg}s). Servidor inaccesible."
        return None, f"Error de conexión a PostgreSQL: {msg}"
    except Exception as e:
        return None, f"Error inesperado al conectar a PostgreSQL: {str(e)}"

def probar_conexion_pg(config_override: dict = None) -> tuple[bool, str]:
    """
    Prueba rápida de conectividad con PostgreSQL.
    Retorna (True, mensaje) o (False, mensaje de error).
    """
    conn, err = get_pg_connection(timeout=3, config_override=config_override)
    if not conn:
        return False, err

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver = cur.fetchone()
            version_str = ver[0] if ver else "PostgreSQL"
        conn.close()
        return True, f"Conexión exitosa a la nube: {version_str.split(',')[0]}"
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return False, f"Fallo en consulta de prueba: {str(e)}"
