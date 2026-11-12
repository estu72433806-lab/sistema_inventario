"""
Modelo para auditoría y registro de movimientos de stock (Kardex de Inventario).
Maneja entradas de mercadería de proveedores y ajustes por pérdida o daño en transacciones atómicas.
"""
import uuid
from datetime import datetime
from database.db import get_connection

class MovimientoStockModel:
    @staticmethod
    def registrar_movimiento(producto_id: int, tipo_movimiento: str, cantidad: int, motivo: str, usuario_id: int = None, referencia: str = "", proveedor_id: int = None):
        """Método general para registrar un movimiento en el Kardex y actualizar stock."""
        if tipo_movimiento.upper() == "ENTRADA":
            return MovimientoStockModel.registrar_entrada_mercaderia(
                producto_id=producto_id,
                cantidad=cantidad,
                proveedor_id=proveedor_id,
                referencia=referencia,
                motivo=motivo,
                usuario_id=usuario_id
            )
        else:
            return MovimientoStockModel.registrar_ajuste_stock(
                producto_id=producto_id,
                cantidad=cantidad,
                motivo=motivo,
                tipo_movimiento=tipo_movimiento.upper(),
                usuario_id=usuario_id,
                referencia=referencia
            )

    @staticmethod
    def registrar_entrada_mercaderia(producto_id: int, cantidad: int, proveedor_id: int = None, referencia: str = "", motivo: str = "Compra / Ingreso de mercadería", usuario_id: int = None):
        """
        Registra una entrada de mercadería:
        - Incrementa el stock del producto
        - Asocia el proveedor y documento de referencia (Guía/Factura)
        - Inserta el movimiento en el historial
        """
        if cantidad <= 0:
            return None, "La cantidad de ingreso debe ser mayor a cero."

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Verificar producto activo
            cursor.execute("SELECT id, nombre, stock FROM productos WHERE id = ? AND activo = 1;", (producto_id,))
            prod = cursor.fetchone()
            if not prod:
                conn.rollback()
                return None, "El producto especificado no existe o está inactivo."

            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mov_uuid = str(uuid.uuid4())

            # 2. Incrementar stock
            cursor.execute("""
                UPDATE productos
                SET stock = stock + ?, fecha_modificacion = ?, sincronizado = 0
                WHERE id = ?;
            """, (cantidad, fecha_actual, producto_id))

            # 3. Registrar movimiento
            cursor.execute("""
                INSERT INTO movimientos_stock (uuid, producto_id, tipo_movimiento, cantidad, motivo, referencia, fecha, usuario_id, proveedor_id, fecha_modificacion, sincronizado)
                VALUES (?, ?, 'ENTRADA', ?, ?, ?, ?, ?, ?, ?, 0);
            """, (mov_uuid, producto_id, cantidad, motivo.strip(), referencia.strip(), fecha_actual, usuario_id, proveedor_id, fecha_actual))

            mov_id = cursor.lastrowid
            conn.commit()
            return mov_id, None
        except Exception as e:
            conn.rollback()
            return None, f"Error al registrar la entrada de stock: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def registrar_ajuste_stock(producto_id: int, cantidad: int, motivo: str, tipo_movimiento: str = "SALIDA", usuario_id: int = None, referencia: str = ""):
        """
        Registra un ajuste por pérdida, daño físico, avería o corrección de inventario:
        - Si es 'SALIDA' (ej: daño o pérdida): descuenta del stock validando existencia
        - Si es 'ENTRADA' (ej: recuperación o sobrante): incrementa el stock
        """
        if cantidad <= 0:
            return None, "La cantidad a ajustar debe ser mayor a cero."

        tipo_movimiento = tipo_movimiento.upper()
        if tipo_movimiento not in ("SALIDA", "ENTRADA", "AJUSTE"):
            return None, "Tipo de movimiento no válido."

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, nombre, stock FROM productos WHERE id = ? AND activo = 1;", (producto_id,))
            prod = cursor.fetchone()
            if not prod:
                conn.rollback()
                return None, "El producto especificado no existe o está inactivo."

            stock_actual = prod["stock"]
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mov_uuid = str(uuid.uuid4())

            if tipo_movimiento == "SALIDA":
                if stock_actual < cantidad:
                    conn.rollback()
                    return None, f"No se puede descontar {cantidad} unidades. El stock actual es solo de {stock_actual} unidades."
                cursor.execute("""
                    UPDATE productos
                    SET stock = stock - ?, fecha_modificacion = ?, sincronizado = 0
                    WHERE id = ?;
                """, (cantidad, fecha_actual, producto_id))
            else:
                cursor.execute("""
                    UPDATE productos
                    SET stock = stock + ?, fecha_modificacion = ?, sincronizado = 0
                    WHERE id = ?;
                """, (cantidad, fecha_actual, producto_id))

            cursor.execute("""
                INSERT INTO movimientos_stock (uuid, producto_id, tipo_movimiento, cantidad, motivo, referencia, fecha, usuario_id, proveedor_id, fecha_modificacion, sincronizado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 0);
            """, (mov_uuid, producto_id, tipo_movimiento, cantidad, motivo.strip(), referencia.strip(), fecha_actual, usuario_id, fecha_actual))

            mov_id = cursor.lastrowid
            conn.commit()
            return mov_id, None
        except Exception as e:
            conn.rollback()
            return None, f"Error al procesar el ajuste de stock: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def listar_movimientos(producto_id: int = None, tipo_movimiento: str = None, busqueda: str = "", limite: int = 100):
        """
        Retorna el historial completo de movimientos con datos del producto, proveedor y usuario responsable.
        """
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT m.id, m.fecha, m.tipo_movimiento, m.cantidad, m.motivo, m.referencia,
                   p.id as producto_id, p.codigo as producto_codigo, p.nombre as producto_nombre,
                   prov.razon_social as proveedor_nombre,
                   u.username as usuario_nombre
            FROM movimientos_stock m
            JOIN productos p ON m.producto_id = p.id
            LEFT JOIN proveedores prov ON m.proveedor_id = prov.id
            LEFT JOIN usuarios u ON m.usuario_id = u.id
            WHERE 1=1
        """
        params = []
        if producto_id:
            query += " AND m.producto_id = ?"
            params.append(producto_id)

        if tipo_movimiento:
            query += " AND m.tipo_movimiento = ?"
            params.append(tipo_movimiento.upper())

        if busqueda:
            query += " AND (p.nombre LIKE ? OR p.codigo LIKE ? OR m.motivo LIKE ? OR m.referencia LIKE ?)"
            patron = f"%{busqueda.strip()}%"
            params.extend([patron, patron, patron, patron])

        query += " ORDER BY m.id DESC LIMIT ?;"
        params.append(limite)

        cursor.execute(query, params)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]
