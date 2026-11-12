"""
Modelo para la gestión de proveedores de componentes y tecnología.
Soporta operaciones completas de registro, consulta, modificación y desactivación (borrado lógico).
"""
from database.db import get_connection
import uuid
from datetime import datetime

class ProveedorModel:
    @staticmethod
    def listar_proveedores(busqueda="", solo_activos=True):
        """Lista proveedores filtrados por RUC/DNI o Razón Social."""
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT id, ruc_dni, razon_social, contacto, telefono, email, direccion, activo
            FROM proveedores
            WHERE 1=1
        """
        params = []
        if solo_activos:
            query += " AND activo = 1"

        if busqueda:
            query += " AND (ruc_dni LIKE ? OR razon_social LIKE ? OR contacto LIKE ?)"
            patron = f"%{busqueda.strip()}%"
            params.extend([patron, patron, patron])

        query += " ORDER BY razon_social ASC;"
        cursor.execute(query, params)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]

    @staticmethod
    def obtener_por_id(proveedor_id):
        """Retorna un proveedor por su ID."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proveedores WHERE id = ?;", (proveedor_id,))
        fila = cursor.fetchone()
        conn.close()
        return dict(fila) if fila else None

    @staticmethod
    def crear_proveedor(ruc_dni, razon_social, contacto="", telefono="", email="", direccion="", prov_uuid=None):
        """Registra un nuevo proveedor."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            p_uuid = prov_uuid if prov_uuid else str(uuid.uuid4())
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO proveedores (uuid, ruc_dni, razon_social, contacto, telefono, email, direccion, activo, fecha_modificacion, sincronizado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 0);
            """, (p_uuid, ruc_dni.strip(), razon_social.strip(), contacto.strip(), telefono.strip(), email.strip(), direccion.strip(), ahora))
            conn.commit()
            return cursor.lastrowid, None
        except Exception as e:
            return None, str(e)
        finally:
            conn.close()

    @staticmethod
    def actualizar_proveedor(proveedor_id, ruc_dni, razon_social, contacto="", telefono="", email="", direccion=""):
        """Actualiza los datos de un proveedor."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE proveedores
                SET ruc_dni = ?, razon_social = ?, contacto = ?, telefono = ?, email = ?, direccion = ?,
                    fecha_modificacion = ?, sincronizado = 0
                WHERE id = ?;
            """, (ruc_dni.strip(), razon_social.strip(), contacto.strip(), telefono.strip(), email.strip(), direccion.strip(), ahora, proveedor_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def desactivar_proveedor(proveedor_id):
        """Desactiva un proveedor sin eliminar su historial de compras y entradas."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE proveedores SET activo = 0, fecha_modificacion = ?, sincronizado = 0 WHERE id = ?;", (ahora, proveedor_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
