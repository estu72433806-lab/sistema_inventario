"""
Modelo para la gestión de ventas, detalle de venta y control de stock transaccional en SQLite.
Incluye validaciones estrictas de stock, descuentos (porcentaje o monto fijo) y prevención de inconsistencias.
"""
from datetime import datetime
from database.db import get_connection

class VentaModel:
    @staticmethod
    def generar_siguiente_numero_comprobante(tipo_comprobante="Boleta"):
        """Genera el correlativo siguiente para el comprobante (ej: B-000001 o F-000001)."""
        prefijo = "B" if tipo_comprobante == "Boleta" else ("F" if tipo_comprobante == "Factura" else "T")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT numero_comprobante FROM ventas WHERE tipo_comprobante = ? ORDER BY id DESC LIMIT 1;",
            (tipo_comprobante,)
        )
        fila = cursor.fetchone()
        conn.close()
        
        if fila and fila[0]:
            try:
                partes = fila[0].split("-")
                correlativo = int(partes[-1]) + 1
            except Exception:
                correlativo = 1
        else:
            correlativo = 1
            
        return f"{prefijo}-{str(correlativo).zfill(6)}"

    @staticmethod
    def registrar_venta(cliente_id: int, tipo_comprobante: str, metodo_pago: str, items: list,
                        tipo_descuento: str = "MONTO", valor_descuento: float = 0.0,
                        impuesto_porcentaje: float = 0.0, usuario_id: int = None):
        """
        Registra una venta completa en una transacción atómica de SQLite:
        - items: lista de dicts [{'producto_id', 'cantidad', 'precio_unitario'}]
        - tipo_descuento: 'MONTO' o 'PORCENTAJE'
        - Valida stock en tiempo real antes de procesar
        - Si falta stock en algún ítem, revierte la operación y retorna mensaje claro
        - Descuenta stock y registra la salida en movimientos_stock
        """
        if not items:
            return None, "El carrito de ventas no contiene ningún producto."

        # 1. Validar cantidades de cada ítem
        for it in items:
            cant = it.get("cantidad", 0)
            pu = it.get("precio_unitario", 0.0)
            if not isinstance(cant, int) or cant <= 0:
                return None, f"La cantidad para el producto ID {it.get('producto_id')} debe ser un número entero mayor a cero."
            if pu < 0:
                return None, f"El precio unitario no puede ser negativo."

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 2. Verificar existencia y stock disponible de cada producto en la base de datos
            for it in items:
                cursor.execute(
                    "SELECT id, nombre, stock, activo FROM productos WHERE id = ?;",
                    (it["producto_id"],)
                )
                prod = cursor.fetchone()
                if not prod or prod["activo"] != 1:
                    conn.rollback()
                    return None, f"El producto con ID {it['producto_id']} no se encuentra activo o no existe en el catálogo."

                stock_disponible = prod["stock"]
                cant_solicitada = it["cantidad"]
                if stock_disponible < cant_solicitada:
                    conn.rollback()
                    return None, (
                        f"Stock insuficiente para '{prod['nombre']}'.\n"
                        f"• Stock disponible en almacén: {stock_disponible} unidad(es)\n"
                        f"• Cantidad solicitada en la venta: {cant_solicitada} unidad(es)\n"
                        f"Por favor ajuste la cantidad antes de continuar."
                    )

            # 3. Calcular montos brutos
            subtotal_bruto = sum(round(it["cantidad"] * float(it["precio_unitario"]), 2) for it in items)
            subtotal_bruto = round(subtotal_bruto, 2)

            # 4. Validar y calcular descuento
            monto_descuento = 0.0
            tipo_descuento = tipo_descuento.upper()

            if valor_descuento < 0:
                conn.rollback()
                return None, "El valor del descuento no puede ser negativo."

            if tipo_descuento == "PORCENTAJE":
                if valor_descuento > 100.0:
                    conn.rollback()
                    return None, "El descuento por porcentaje no puede ser mayor al 100%."
                monto_descuento = round(subtotal_bruto * (valor_descuento / 100.0), 2)
            elif tipo_descuento == "MONTO":
                if valor_descuento > subtotal_bruto:
                    conn.rollback()
                    return None, f"El monto de descuento (S/ {valor_descuento:.2f}) no puede superar el subtotal bruto (S/ {subtotal_bruto:.2f})."
                monto_descuento = round(valor_descuento, 2)
            else:
                conn.rollback()
                return None, "Tipo de descuento no válido ('MONTO' o 'PORCENTAJE')."

            subtotal_neto = max(0.0, round(subtotal_bruto - monto_descuento, 2))

            # 5. Calcular impuesto y total final
            if impuesto_porcentaje < 0:
                conn.rollback()
                return None, "El porcentaje de impuesto no puede ser negativo."

            impuesto = round(subtotal_neto * (impuesto_porcentaje / 100.0), 2)
            total_final = round(subtotal_neto + impuesto, 2)
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            import uuid
            # 6. Generar correlativo de comprobante y UUID global
            numero_comprobante = VentaModel.generar_siguiente_numero_comprobante(tipo_comprobante)
            venta_uuid = str(uuid.uuid4())

            # 7. Insertar cabecera de la venta
            cursor.execute("""
                INSERT INTO ventas (
                    uuid, numero_comprobante, tipo_comprobante, fecha, cliente_id, usuario_id,
                    subtotal, descuento, impuesto, total, metodo_pago, estado,
                    fecha_modificacion, sincronizado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Completada', ?, 0);
            """, (
                venta_uuid, numero_comprobante, tipo_comprobante, fecha_actual, cliente_id, usuario_id,
                subtotal_bruto, monto_descuento, impuesto, total_final, metodo_pago,
                fecha_actual
            ))
            
            venta_id = cursor.lastrowid

            # 8. Insertar detalles, descontar stock de productos y registrar salida en movimientos_stock
            for it in items:
                it_subtotal = round(it["cantidad"] * float(it["precio_unitario"]), 2)
                det_uuid = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO detalle_ventas (uuid, venta_id, producto_id, cantidad, precio_unitario, subtotal, fecha_modificacion, sincronizado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0);
                """, (det_uuid, venta_id, it["producto_id"], it["cantidad"], it["precio_unitario"], it_subtotal, fecha_actual))

                # Descontar stock local y marcar producto para sincronización
                cursor.execute("""
                    UPDATE productos
                    SET stock = stock - ?, fecha_modificacion = ?, sincronizado = 0
                    WHERE id = ?;
                """, (it["cantidad"], fecha_actual, it["producto_id"]))

                # Auditoría Kardex en movimientos_stock
                mov_uuid = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO movimientos_stock (
                        uuid, producto_id, tipo_movimiento, cantidad, motivo, referencia, fecha, usuario_id, proveedor_id,
                        fecha_modificacion, sincronizado
                    ) VALUES (?, ?, 'SALIDA', ?, ?, ?, ?, ?, NULL, ?, 0);
                """, (
                    mov_uuid,
                    it["producto_id"],
                    it["cantidad"],
                    f"Venta con {tipo_comprobante} {numero_comprobante}",
                    numero_comprobante,
                    fecha_actual,
                    usuario_id,
                    fecha_actual
                ))

            # 9. Confirmar la transacción atómicamente
            conn.commit()
            return venta_id, None
        except Exception as e:
            # En caso de cualquier error imprevisto, revertir toda la transacción
            conn.rollback()
            return None, f"Error transaccional al procesar la venta: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def listar_ventas(fecha_inicio=None, fecha_fin=None, busqueda=""):
        """Retorna el listado de ventas con datos de cliente, vendedor y descuentos."""
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT v.id, v.numero_comprobante, v.tipo_comprobante, v.fecha,
                   c.nombre as cliente_nombre, c.numero_documento as cliente_doc,
                   u.username as vendedor_username, u.nombre_completo as vendedor_nombre,
                   v.subtotal, v.descuento, v.impuesto, v.total, v.metodo_pago, v.estado
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            query += " AND DATE(v.fecha) >= DATE(?)"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND DATE(v.fecha) <= DATE(?)"
            params.append(fecha_fin)
        if busqueda:
            query += " AND (v.numero_comprobante LIKE ? OR c.nombre LIKE ? OR c.numero_documento LIKE ?)"
            patron = f"%{busqueda.strip()}%"
            params.extend([patron, patron, patron])

        query += " ORDER BY v.id DESC;"
        cursor.execute(query, params)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]

    @staticmethod
    def obtener_venta_completa(venta_id: int):
        """Retorna la cabecera completa y la lista de ítems de una venta."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id, v.numero_comprobante, v.tipo_comprobante, v.fecha,
                   v.cliente_id, c.nombre as cliente_nombre, c.tipo_documento, c.numero_documento,
                   c.telefono, c.direccion,
                   u.username as vendedor_username, u.nombre_completo as vendedor_nombre,
                   v.subtotal, v.descuento, v.impuesto, v.total, v.metodo_pago, v.estado
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.id = ?;
        """, (venta_id,))
        cabecera = cursor.fetchone()
        if not cabecera:
            conn.close()
            return None

        cursor.execute("""
            SELECT dv.id, dv.producto_id, p.codigo, p.nombre, p.marca,
                   dv.cantidad, dv.precio_unitario, dv.subtotal
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = ?;
        """, (venta_id,))
        detalles = cursor.fetchall()
        conn.close()

        resultado = dict(cabecera)
        resultado["detalles"] = [dict(d) for d in detalles]
        return resultado

    @staticmethod
    def obtener_ventas_detalladas_rango(fecha_inicio=None, fecha_fin=None, busqueda=""):
        """
        Retorna una lista aplanada con el detalle completo de ventas y productos vendidos,
        cantidades, precios, descuentos y totales, para el rango de fechas especificado.
        """
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT v.id as venta_id, v.numero_comprobante, v.tipo_comprobante, v.fecha,
                   c.nombre as cliente_nombre, c.numero_documento as cliente_doc,
                   u.username as vendedor_username, u.nombre_completo as vendedor_nombre,
                   v.subtotal as venta_subtotal, v.descuento as venta_descuento,
                   v.impuesto as venta_impuesto, v.total as venta_total, v.metodo_pago,
                   dv.id as detalle_id, dv.producto_id, p.codigo as producto_codigo,
                   p.nombre as producto_nombre, p.marca as producto_marca,
                   dv.cantidad, dv.precio_unitario, dv.subtotal as detalle_subtotal
            FROM ventas v
            JOIN detalle_ventas dv ON v.id = dv.venta_id
            JOIN productos p ON dv.producto_id = p.id
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            query += " AND DATE(v.fecha) >= DATE(?)"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND DATE(v.fecha) <= DATE(?)"
            params.append(fecha_fin)
        if busqueda:
            query += " AND (v.numero_comprobante LIKE ? OR c.nombre LIKE ? OR c.numero_documento LIKE ? OR p.nombre LIKE ?)"
            patron = f"%{busqueda.strip()}%"
            params.extend([patron, patron, patron, patron])

        query += " ORDER BY v.id DESC, dv.id ASC;"
        cursor.execute(query, params)
        filas = cursor.fetchall()
        conn.close()
        return [dict(f) for f in filas]

    @staticmethod
    def obtener_metricas_dashboard():
        """
        Retorna las métricas en tiempo real para el panel principal desde SQLite:
        - Ventas del día (monto y conteo)
        - Cantidad de productos registrados activos
        - Cantidad de productos con stock igual o menor al stock mínimo
        """
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Ventas del día actual
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(total), 0.0)
            FROM ventas
            WHERE DATE(fecha) = DATE('now', 'localtime');
        """)
        fila_ventas = cursor.fetchone()
        ventas_hoy_count = fila_ventas[0] if fila_ventas else 0
        ventas_hoy_total = fila_ventas[1] if fila_ventas else 0.0

        # 2. Cantidad total de productos activos
        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1;")
        total_productos = cursor.fetchone()[0]

        # 3. Cantidad de productos con stock bajo
        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1 AND stock <= stock_minimo;")
        stock_bajo_count = cursor.fetchone()[0]

        conn.close()
        return {
            "ventas_hoy_total": float(ventas_hoy_total),
            "ventas_hoy_count": int(ventas_hoy_count),
            "total_productos": int(total_productos),
            "stock_bajo_count": int(stock_bajo_count)
        }
