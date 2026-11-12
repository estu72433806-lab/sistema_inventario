"""
Modelo para la gestión de clientes.
Permite registrar, consultar, modificar y desactivar clientes sin borrar el historial de ventas.
"""
from database.db import get_connection
import uuid
from datetime import datetime

class ClienteModel:
    @staticmethod
    def listar_clientes(busqueda="", solo_activos=True):
        """Lista clientes filtrados por número de documento o nombre."""
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT id, tipo_documento, numero_documento, nombre, telefono, email, direccion, activo
            FROM clientes
            WHERE 1=1
        """
        params = []
        if solo_activos:
            query += " AND activo = 1"

        if busqueda:
            query += " AND (numero_documento LIKE ? OR nombre LIKE ? OR telefono LIKE ?)"
            patron = f"%{busqueda.strip()}%"
            params.extend([patron, patron, patron])
        
        query += " ORDER BY nombre ASC;"
        cursor.execute(query, params)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]

    @staticmethod
    def obtener_por_id(cliente_id):
        """Retorna un cliente por su ID."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?;", (cliente_id,))
        fila = cursor.fetchone()
        conn.close()
        return dict(fila) if fila else None

    @staticmethod
    def obtener_por_documento(numero_documento):
        """Retorna un cliente por su documento."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE numero_documento = ? AND activo = 1;", (numero_documento.strip(),))
        fila = cursor.fetchone()
        conn.close()
        return dict(fila) if fila else None

    @staticmethod
    def crear_cliente(tipo_documento, numero_documento, nombre, telefono="", email="", direccion="", cliente_uuid=None):
        """Registra un nuevo cliente."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            c_uuid = cliente_uuid if cliente_uuid else str(uuid.uuid4())
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO clientes (uuid, tipo_documento, numero_documento, nombre, telefono, email, direccion, activo, fecha_modificacion, sincronizado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 0);
            """, (c_uuid, tipo_documento.strip(), numero_documento.strip(), nombre.strip(), telefono.strip(), email.strip(), direccion.strip(), ahora))
            conn.commit()
            nuevo_id = cursor.lastrowid
            return nuevo_id, None
        except Exception as e:
            return None, str(e)
        finally:
            conn.close()

    @staticmethod
    def actualizar_cliente(cliente_id, tipo_documento, numero_documento, nombre, telefono="", email="", direccion=""):
        """Actualiza la información de un cliente existente."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE clientes
                SET tipo_documento = ?, numero_documento = ?, nombre = ?, telefono = ?, email = ?, direccion = ?,
                    fecha_modificacion = ?, sincronizado = 0
                WHERE id = ?;
            """, (tipo_documento.strip(), numero_documento.strip(), nombre.strip(), telefono.strip(), email.strip(), direccion.strip(), ahora, cliente_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def desactivar_cliente(cliente_id):
        """Desactiva un cliente (borrado lógico para preservar el historial de ventas)."""
        if cliente_id == 1:
            return False, "No se puede desactivar el cliente genérico de público general."
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE clientes SET activo = 0, fecha_modificacion = ?, sincronizado = 0 WHERE id = ?;", (ahora, cliente_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
