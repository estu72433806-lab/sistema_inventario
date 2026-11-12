"""
Vista del Módulo de Ventas (Punto de Venta / POS) y emisión de comprobantes PDF con ReportLab.
Incluye:
- Selección de cliente con visualización de datos en tiempo real.
- Tabla con columnas explícitas: Producto, Cantidad, Precio Unitario, Subtotal y Total.
- Cambio de cantidades interactivas y eliminación de ítems.
- Sistema de descuentos configurable: Monto Fijo (S/) o Porcentaje (%), con validación de límites.
- Verificación estricta de stock disponible en SQLite antes de confirmar.
- Transacción atómica: si falta stock o falla algún ítem, revierte la operación (Rollback).
- Descuento automático de inventario y auditoría de salida en movimientos_stock.
- Protección estricta anti-doble clic.
- Ventana modal de resumen de la venta confirmada y generación del PDF.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from models.cliente import ClienteModel
from models.producto import ProductoModel
from models.venta import VentaModel
from services.pdf_service import PDFService
from ui.theme import Color

class VentasView(ttk.Frame):
    def __init__(self, parent, usuario_sesion=None, callback_producto_actualizado=None):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion or {"id": 1, "username": "admin", "rol": "administrador"}
        self.callback_producto_actualizado = callback_producto_actualizado
        self.carrito = [] # Lista de ítems en venta actual
        self.clientes_cache = []
        self.productos_cache = []
        self.procesando_venta = False # Bandera anti-doble clic

        self._construir_ui()
        self.actualizar_datos()

    def _construir_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # 1. Cabecera: cliente, comprobante y método de pago (etiqueta encima del campo)
        frame_cabecera = ttk.LabelFrame(self, text="  Datos de la venta  ", padding=(14, 8, 14, 10))
        frame_cabecera.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        frame_cabecera.columnconfigure(0, weight=3)
        frame_cabecera.columnconfigure(1, weight=1)
        frame_cabecera.columnconfigure(2, weight=1)

        ttk.Label(frame_cabecera, text="Cliente *", style="Campo.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 2))
        ttk.Label(frame_cabecera, text="Tipo de comprobante *", style="Campo.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 2))
        ttk.Label(frame_cabecera, text="Método de pago *", style="Campo.TLabel").grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 2))

        self.combo_cliente = ttk.Combobox(frame_cabecera, state="readonly")
        self.combo_cliente.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        self.combo_cliente.bind("<<ComboboxSelected>>", self._on_cliente_seleccionado)

        self.combo_comprobante = ttk.Combobox(frame_cabecera, values=["Boleta", "Factura"], state="readonly", width=12)
        self.combo_comprobante.current(0)
        self.combo_comprobante.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(0, 2))

        self.combo_pago = ttk.Combobox(frame_cabecera, values=["Efectivo", "Tarjeta de Débito/Crédito", "Transferencia", "Billetera Digital (Yape/Plin)"], state="readonly", width=22)
        self.combo_pago.current(0)
        self.combo_pago.grid(row=1, column=2, sticky="ew", padx=(12, 0), pady=(0, 2))

        self.lbl_cliente_info = ttk.Label(frame_cabecera, text="Documento: - | Dirección: - | Teléfono: -", style="Nota.TLabel")
        self.lbl_cliente_info.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # 2. Selector de productos para agregar al carrito
        frame_seleccion = ttk.LabelFrame(self, text="  Agregar productos  ", padding=(14, 8, 14, 10))
        frame_seleccion.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        frame_seleccion.columnconfigure(0, weight=4)
        frame_seleccion.columnconfigure(1, weight=0)
        frame_seleccion.columnconfigure(2, weight=0)
        frame_seleccion.columnconfigure(3, weight=0)

        ttk.Label(frame_seleccion, text="Producto", style="Campo.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 2))
        ttk.Label(frame_seleccion, text="Cantidad", style="Campo.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 2))
        ttk.Label(frame_seleccion, text="", style="Campo.TLabel").grid(row=0, column=2, padx=(12, 0))

        self.combo_producto = ttk.Combobox(frame_seleccion, state="readonly")
        self.combo_producto.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        self.combo_producto.bind("<<ComboboxSelected>>", self._on_producto_seleccionado)

        self.spin_cantidad = ttk.Spinbox(frame_seleccion, from_=1, to=999, width=7)
        self.spin_cantidad.set(1)
        self.spin_cantidad.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(0, 2))

        btn_agregar = ttk.Button(frame_seleccion, text="Agregar al carrito", style="Accent.TButton", command=self.agregar_al_carrito)
        btn_agregar.grid(row=1, column=2, sticky="ew", padx=(12, 0), pady=(0, 2))

        self.lbl_info_prod = ttk.Label(frame_seleccion, text="Stock: - | Precio: S/ 0.00", font=("Segoe UI", 9, "bold"), foreground=Color.ACENTO_OSCURO)
        self.lbl_info_prod.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # 3. Detalle de la Venta (Tabla con Producto, Cantidad, Precio Unitario, Subtotal y Total)
        frame_carrito = ttk.LabelFrame(self, text=" Detalle de Productos en la Venta ", padding=10)
        frame_carrito.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        frame_carrito.rowconfigure(0, weight=1)
        frame_carrito.columnconfigure(0, weight=1)

        cols = ("num", "codigo", "producto", "cantidad", "precio", "subtotal", "total")
        self.tree_carrito = ttk.Treeview(frame_carrito, columns=cols, show="headings", selectmode="browse")

        self.tree_carrito.heading("num", text="#")
        self.tree_carrito.heading("codigo", text="Código SKU")
        self.tree_carrito.heading("producto", text="Producto / Componente")
        self.tree_carrito.heading("cantidad", text="Cantidad")
        self.tree_carrito.heading("precio", text="Precio Unitario")
        self.tree_carrito.heading("subtotal", text="Subtotal")
        self.tree_carrito.heading("total", text="Total")

        self.tree_carrito.column("num", width=35, anchor="center")
        self.tree_carrito.column("codigo", width=95, anchor="center")
        self.tree_carrito.column("producto", width=330, anchor="w")
        self.tree_carrito.column("cantidad", width=75, anchor="center")
        self.tree_carrito.column("precio", width=105, anchor="e")
        self.tree_carrito.column("subtotal", width=110, anchor="e")
        self.tree_carrito.column("total", width=110, anchor="e")

        scroll_c = ttk.Scrollbar(frame_carrito, orient="vertical", command=self.tree_carrito.yview)
        self.tree_carrito.configure(yscrollcommand=scroll_c.set)

        self.tree_carrito.grid(row=0, column=0, sticky="nsew")
        scroll_c.grid(row=0, column=1, sticky="ns")

        # Acciones sobre la tabla del carrito
        frame_acciones_c = ttk.Frame(frame_carrito)
        frame_acciones_c.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        btn_modificar_cant = ttk.Button(frame_acciones_c, text="✏ Modificar Cantidad", command=self.modificar_cantidad_item)
        btn_modificar_cant.pack(side="left", padx=5)

        btn_quitar = ttk.Button(frame_acciones_c, text="❌ Quitar Producto", command=self.quitar_item)
        btn_quitar.pack(side="left", padx=5)

        btn_vaciar = ttk.Button(frame_acciones_c, text="🗑 Vaciar Carrito", command=self.vaciar_carrito)
        btn_vaciar.pack(side="left", padx=5)

        # 4. Sección de Descuento, Impuestos y Liquidación
        frame_total = ttk.LabelFrame(self, text=" Descuentos, Impuestos y Total Final ", padding=12)
        frame_total.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        frame_total.columnconfigure(0, weight=1)
        frame_total.columnconfigure(1, weight=1)
        frame_total.columnconfigure(2, weight=1)

        # 4.1 Sub-panel Descuento
        frame_desc = ttk.LabelFrame(frame_total, text=" Aplicar Descuento a la Venta ", padding=8)
        frame_desc.grid(row=0, column=0, sticky="nsew", padx=5)

        self.var_tipo_descuento = tk.StringVar(value="NINGUNO")

        rb_no_desc = ttk.Radiobutton(frame_desc, text="Sin descuento", variable=self.var_tipo_descuento, value="NINGUNO", command=self._on_cambio_tipo_descuento)
        rb_no_desc.grid(row=0, column=0, sticky="w", pady=2)

        rb_monto = ttk.Radiobutton(frame_desc, text="Monto Fijo (S/)", variable=self.var_tipo_descuento, value="MONTO", command=self._on_cambio_tipo_descuento)
        rb_monto.grid(row=0, column=1, sticky="w", pady=2, padx=5)

        rb_pct = ttk.Radiobutton(frame_desc, text="Porcentaje (%)", variable=self.var_tipo_descuento, value="PORCENTAJE", command=self._on_cambio_tipo_descuento)
        rb_pct.grid(row=0, column=2, sticky="w", pady=2)

        self.lbl_desc_input = ttk.Label(frame_desc, text="Sin descuento:")
        self.lbl_desc_input.grid(row=1, column=0, sticky="w", pady=(6, 2))

        self.entry_descuento = ttk.Entry(frame_desc, width=12)
        self.entry_descuento.insert(0, "0")
        self.entry_descuento.config(state="disabled")
        self.entry_descuento.grid(row=1, column=1, sticky="w", pady=(6, 2), padx=5)
        self.entry_descuento.bind("<KeyRelease>", lambda e: self.recalcular_totales())

        self.lbl_alerta_desc = ttk.Label(frame_desc, text="", foreground=Color.PELIGRO_OSCURO, font=("Segoe UI", 8))
        self.lbl_alerta_desc.grid(row=2, column=0, columnspan=3, sticky="w")

        # 4.2 Sub-panel Impuesto (IGV)
        frame_igv = ttk.LabelFrame(frame_total, text=" Configuración de Impuesto ", padding=8)
        frame_igv.grid(row=0, column=1, sticky="nsew", padx=5)

        self.var_aplicar_igv = tk.BooleanVar(value=True)
        chk_igv = ttk.Checkbutton(
            frame_igv,
            text="Aplicar IGV (18%)",
            variable=self.var_aplicar_igv,
            command=self.recalcular_totales
        )
        chk_igv.pack(anchor="w", pady=5)

        ttk.Label(frame_igv, text="Desmarcar para ventas exoneradas o netas.", font=("Segoe UI", 8), foreground=Color.GRIS_OSCURO).pack(anchor="w")

        # 4.3 Sub-panel Totales Finales y Botón de Cobro
        frame_liquidacion = ttk.Frame(frame_total)
        frame_liquidacion.grid(row=0, column=2, sticky="nsew", padx=5)

        self.lbl_subtotal_bruto = ttk.Label(frame_liquidacion, text="Subtotal Bruto: S/ 0.00", font=("Segoe UI", 9))
        self.lbl_subtotal_bruto.pack(anchor="e")

        self.lbl_descuento_aplicado = ttk.Label(frame_liquidacion, text="Descuento: -S/ 0.00", font=("Segoe UI", 9), foreground=Color.PELIGRO_OSCURO)
        self.lbl_descuento_aplicado.pack(anchor="e")

        self.lbl_igv = ttk.Label(frame_liquidacion, text="IGV (18%): S/ 0.00", font=("Segoe UI", 9))
        self.lbl_igv.pack(anchor="e")

        self.lbl_total_final = ttk.Label(frame_liquidacion, text="TOTAL: S/ 0.00", font=("Segoe UI", 13, "bold"), foreground=Color.TEAL)
        self.lbl_total_final.pack(anchor="e", pady=(3, 6))

        # Botón de Cobro con protección anti-doble clic
        self.btn_cobrar = ttk.Button(
            frame_liquidacion,
            text="💳 CONFIRMAR VENTA Y EMITIR PDF",
            command=self.procesar_venta
        )
        self.btn_cobrar.pack(fill="x", ipady=6)

    def _on_cambio_tipo_descuento(self):
        tipo = self.var_tipo_descuento.get()
        if tipo == "NINGUNO":
            self.entry_descuento.delete(0, tk.END)
            self.entry_descuento.insert(0, "0")
            self.entry_descuento.config(state="disabled")
            self.lbl_desc_input.config(text="Sin descuento:")
            self.lbl_alerta_desc.config(text="")
        elif tipo == "MONTO":
            self.entry_descuento.config(state="normal")
            self.entry_descuento.delete(0, tk.END)
            self.entry_descuento.insert(0, "0")
            self.lbl_desc_input.config(text="Monto en Soles (S/):")
            self.lbl_alerta_desc.config(text="Límite: de S/ 0 hasta el subtotal bruto")
        else: # PORCENTAJE
            self.entry_descuento.config(state="normal")
            self.entry_descuento.delete(0, tk.END)
            self.entry_descuento.insert(0, "0")
            self.lbl_desc_input.config(text="Porcentaje (%):")
            self.lbl_alerta_desc.config(text="Límite: de 0% a 100%")
        self.recalcular_totales()

    def actualizar_datos(self):
        # 1. Clientes
        self.clientes_cache = ClienteModel.listar_clientes()
        opciones_c = [f"{c['numero_documento']} - {c['nombre']}" for c in self.clientes_cache]
        self.combo_cliente["values"] = opciones_c
        if opciones_c:
            self.combo_cliente.current(0)
            self._on_cliente_seleccionado()

        # 2. Productos
        self.productos_cache = ProductoModel.listar_productos()
        opciones_p = [f"[{p['codigo']}] {p['nombre']} - Stock: {p['stock']}" for p in self.productos_cache]
        self.combo_producto["values"] = opciones_p
        if opciones_p:
            self.combo_producto.current(0)
            self._on_producto_seleccionado()

    def _on_cliente_seleccionado(self, event=None):
        idx = self.combo_cliente.current()
        if 0 <= idx < len(self.clientes_cache):
            c = self.clientes_cache[idx]
            self.lbl_cliente_info.config(
                text=f"{c['tipo_documento']}: {c['numero_documento']} | Dirección: {c['direccion'] or '-'} | Teléfono: {c['telefono'] or '-'}"
            )

    def _on_producto_seleccionado(self, event=None):
        idx = self.combo_producto.current()
        if 0 <= idx < len(self.productos_cache):
            p = self.productos_cache[idx]
            es_bajo = p["stock"] <= p["stock_minimo"]
            color = Color.PELIGRO_OSCURO if es_bajo else Color.ACENTO_OSCURO
            alerta = " ⚠ (Stock Crítico)" if es_bajo else ""
            self.lbl_info_prod.config(
                text=f"Stock: {p['stock']}{alerta} | Precio: S/ {p['precio_venta']:.2f}",
                foreground=color
            )

    def agregar_al_carrito(self):
        idx = self.combo_producto.current()
        if idx < 0 or idx >= len(self.productos_cache):
            messagebox.showwarning("Atención", "Seleccione un producto válido de la lista.", parent=self)
            return

        prod = self.productos_cache[idx]
        try:
            cant = int(self.spin_cantidad.get())
            if cant <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atención", "Ingrese una cantidad entera positiva mayor a cero.", parent=self)
            return

        # Validar stock disponible
        cant_en_carrito = sum(item["cantidad"] for item in self.carrito if item["producto_id"] == prod["id"])
        if cant_en_carrito + cant > prod["stock"]:
            messagebox.showerror(
                "Stock Insuficiente",
                f"No hay stock suficiente para '{prod['nombre']}'.\n"
                f"• Stock disponible en almacén: {prod['stock']} unidad(es)\n"
                f"• Ya tiene en el carrito: {cant_en_carrito} unidad(es)\n"
                f"• Intenta agregar: {cant} unidad(es)",
                parent=self
            )
            return

        item_existente = next((it for it in self.carrito if it["producto_id"] == prod["id"]), None)
        if item_existente:
            item_existente["cantidad"] += cant
            item_existente["subtotal"] = round(item_existente["cantidad"] * item_existente["precio_unitario"], 2)
            item_existente["total"] = item_existente["subtotal"]
        else:
            subt = round(cant * float(prod["precio_venta"]), 2)
            self.carrito.append({
                "producto_id": prod["id"],
                "codigo": prod["codigo"],
                "nombre": prod["nombre"],
                "precio_unitario": float(prod["precio_venta"]),
                "cantidad": cant,
                "subtotal": subt,
                "total": subt
            })

        self.spin_cantidad.set(1)
        self.renderizar_carrito()

    def modificar_cantidad_item(self):
        """Permite cambiar la cantidad de un ítem agregado en el carrito validando stock."""
        sel = self.tree_carrito.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto del carrito para modificar su cantidad.", parent=self)
            return

        idx = self.tree_carrito.index(sel[0])
        item = self.carrito[idx]

        # Consultar stock actual del producto en SQLite
        prod_db = ProductoModel.obtener_por_id(item["producto_id"])
        stock_max = prod_db["stock"] if prod_db else 0

        nueva_cant = simpledialog.askinteger(
            "Modificar Cantidad",
            f"Producto: {item['nombre']}\nStock disponible en almacén: {stock_max}\n\nIngrese la nueva cantidad:",
            initialvalue=item["cantidad"],
            minvalue=1,
            maxvalue=stock_max,
            parent=self
        )

        if nueva_cant is not None:
            if nueva_cant > stock_max:
                messagebox.showerror(
                    "Stock Excedido",
                    f"La cantidad solicitada ({nueva_cant}) supera el stock disponible en almacén ({stock_max}).",
                    parent=self
                )
                return
            item["cantidad"] = nueva_cant
            item["subtotal"] = round(nueva_cant * item["precio_unitario"], 2)
            item["total"] = item["subtotal"]
            self.renderizar_carrito()

    def quitar_item(self):
        sel = self.tree_carrito.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto del carrito para quitar.", parent=self)
            return
        idx = self.tree_carrito.index(sel[0])
        self.carrito.pop(idx)
        self.renderizar_carrito()

    def vaciar_carrito(self):
        if self.carrito and messagebox.askyesno("Confirmar", "¿Desea vaciar todos los productos del carrito actual?", parent=self):
            self.carrito.clear()
            self.renderizar_carrito()

    def renderizar_carrito(self):
        for row in self.tree_carrito.get_children():
            self.tree_carrito.delete(row)

        for i, item in enumerate(self.carrito, start=1):
            self.tree_carrito.insert("", "end", values=(
                i,
                item["codigo"],
                item["nombre"],
                item["cantidad"],
                f"S/ {item['precio_unitario']:.2f}",
                f"S/ {item['subtotal']:.2f}",
                f"S/ {item['total']:.2f}"
            ))

        self.recalcular_totales()

    def recalcular_totales(self):
        subtotal_bruto = sum(item["subtotal"] for item in self.carrito)
        tipo_desc = self.var_tipo_descuento.get()
        valor_desc_str = self.entry_descuento.get().strip()

        monto_descuento = 0.0
        try:
            val = float(valor_desc_str) if valor_desc_str else 0.0
            if val < 0:
                raise ValueError
        except ValueError:
            self.lbl_alerta_desc.config(text="⚠ Ingrese un valor numérico válido mayor o igual a cero.")
            val = 0.0

        if tipo_desc == "PORCENTAJE":
            if val > 100:
                self.lbl_alerta_desc.config(text="⚠ El porcentaje no puede superar el 100%.")
                val = 100.0
            else:
                self.lbl_alerta_desc.config(text="Límite: de 0% a 100%")
            monto_descuento = round(subtotal_bruto * (val / 100.0), 2)
        elif tipo_desc == "MONTO":
            if val > subtotal_bruto:
                self.lbl_alerta_desc.config(text=f"⚠ El descuento no puede exceder el subtotal (S/ {subtotal_bruto:.2f}).")
                val = subtotal_bruto
            else:
                self.lbl_alerta_desc.config(text=f"Límite: hasta S/ {subtotal_bruto:.2f}")
            monto_descuento = round(val, 2)
        else:
            self.lbl_alerta_desc.config(text="")
            monto_descuento = 0.0

        subtotal_neto = max(0.0, round(subtotal_bruto - monto_descuento, 2))
        igv_pct = 18.0 if self.var_aplicar_igv.get() else 0.0
        igv = round(subtotal_neto * (igv_pct / 100.0), 2)
        total_final = round(subtotal_neto + igv, 2)

        self.lbl_subtotal_bruto.config(text=f"Subtotal Bruto: S/ {subtotal_bruto:.2f}")
        self.lbl_descuento_aplicado.config(text=f"Descuento: -S/ {monto_descuento:.2f}")
        self.lbl_igv.config(text=f"IGV ({int(igv_pct)}%): S/ {igv:.2f}")
        self.lbl_total_final.config(text=f"TOTAL A PAGAR: S/ {total_final:.2f}")

    def procesar_venta(self):
        # 1. Protección estricta anti-doble clic
        if self.procesando_venta:
            return
        self.procesando_venta = True
        self.btn_cobrar.config(state="disabled")

        try:
            # 2. Validar carrito no vacío
            if not self.carrito:
                messagebox.showwarning("Carrito Vacío", "Agregue al menos un producto al carrito antes de confirmar la venta.", parent=self)
                return

            # 3. Validar selección de cliente
            c_idx = self.combo_cliente.current()
            if c_idx < 0:
                messagebox.showwarning("Atención", "Seleccione un cliente para la venta.", parent=self)
                return

            cliente = self.clientes_cache[c_idx]
            tipo_comprobante = self.combo_comprobante.get()
            metodo_pago = self.combo_pago.get()
            igv_pct = 18.0 if self.var_aplicar_igv.get() else 0.0

            # 4. Obtener y validar descuento
            tipo_desc = self.var_tipo_descuento.get()
            try:
                val_desc = float(self.entry_descuento.get().strip() or "0")
                if val_desc < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error en Descuento", "El valor del descuento debe ser un número positivo.", parent=self)
                return

            # 5. Estructurar ítems para transacción
            items_venta = [
                {
                    "producto_id": it["producto_id"],
                    "cantidad": it["cantidad"],
                    "precio_unitario": it["precio_unitario"]
                }
                for it in self.carrito
            ]

            # 6. Ejecutar transacción atómica en SQLite con VentaModel
            usuario_id = self.usuario_sesion.get("id")
            venta_id, error = VentaModel.registrar_venta(
                cliente_id=cliente["id"],
                tipo_comprobante=tipo_comprobante,
                metodo_pago=metodo_pago,
                items=items_venta,
                tipo_descuento=tipo_desc,
                valor_descuento=val_desc,
                impuesto_porcentaje=igv_pct,
                usuario_id=usuario_id
            )

            # 7. Si falló la validación de stock o transacción, mostrar mensaje y detener
            if error:
                messagebox.showerror("No se Pudo Registrar la Venta", error, parent=self)
                return

            # 8. Obtener venta confirmada y generar comprobante en PDF con ReportLab
            venta_completa = VentaModel.obtener_venta_completa(venta_id)
            
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            comprobantes_dir = os.path.join(base_dir, "comprobantes")
            os.makedirs(comprobantes_dir, exist_ok=True)

            num_seguro = venta_completa["numero_comprobante"].replace("/", "_").replace("-", "_")
            pdf_path = os.path.join(comprobantes_dir, f"Comprobante_{num_seguro}.pdf")

            try:
                PDFService.generar_comprobante_pdf(venta_completa, pdf_path)
                exito_pdf = True
            except Exception as e:
                exito_pdf = False
                msg_pdf_error = str(e)

            # 9. Limpiar carrito y actualizar catálogo
            self.carrito.clear()
            self.renderizar_carrito()
            self.actualizar_datos()
            self.var_tipo_descuento.set("NINGUNO")
            self._on_cambio_tipo_descuento()

            if self.callback_producto_actualizado:
                self.callback_producto_actualizado()

            # 10. Mostrar ventana modal de resumen y descarga de PDF
            self._mostrar_resumen_modal(venta_completa, pdf_path, exito_pdf)

        finally:
            # Re-habilitar botón y liberar bandera anti-doble clic
            self.procesando_venta = False
            self.btn_cobrar.config(state="normal")

    def _mostrar_resumen_modal(self, venta, pdf_path, exito_pdf):
        """Muestra una ventana modal elegante con el resumen de la venta confirmada."""
        modal = tk.Toplevel(self)
        modal.title(f"Venta Confirmada - {venta['tipo_comprobante']} {venta['numero_comprobante']}")
        modal.geometry("520x480")
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        frame = ttk.Frame(modal, padding=20)
        frame.pack(fill="both", expand=True)

        lbl_ico = ttk.Label(frame, text="✔ ¡VENTA COMPLETADA EXITOSAMENTE!", font=("Segoe UI", 12, "bold"), foreground=Color.EXITO)
        lbl_ico.pack(pady=(0, 10))

        frame_card = ttk.LabelFrame(frame, text=" Resumen de Transacción ", padding=12)
        frame_card.pack(fill="both", expand=True)

        filas = [
            ("N° Comprobante:", f"{venta['tipo_comprobante']} {venta['numero_comprobante']}"),
            ("Fecha y Hora:", venta["fecha"]),
            ("Cliente:", f"{venta['cliente_nombre']} ({venta.get('numero_documento', '-')})"),
            ("Vendedor Responsable:", self.usuario_sesion.get("nombre_completo", "Admin")),
            ("Método de Pago:", venta["metodo_pago"]),
            ("Subtotal Bruto:", f"S/ {venta['subtotal']:.2f}"),
            ("Descuento Aplicado:", f"-S/ {venta['descuento']:.2f}"),
            ("Impuesto (IGV):", f"S/ {venta['impuesto']:.2f}"),
            ("TOTAL FINAL PAGADO:", f"S/ {venta['total']:.2f}")
        ]

        for i, (campo, valor) in enumerate(filas):
            lbl_c = ttk.Label(frame_card, text=campo, font=("Segoe UI", 9, "bold" if "TOTAL" in campo else "normal"))
            lbl_c.grid(row=i, column=0, sticky="w", pady=2)

            color_v = Color.TEAL if "TOTAL" in campo else (Color.PELIGRO_OSCURO if "Descuento" in campo else Color.OSCURO)
            font_v = ("Segoe UI", 11, "bold") if "TOTAL" in campo else ("Segoe UI", 9)
            lbl_v = ttk.Label(frame_card, text=valor, font=font_v, foreground=color_v)
            lbl_v.grid(row=i, column=1, sticky="e", pady=2, padx=(20, 0))

        frame_btn = ttk.Frame(frame)
        frame_btn.pack(fill="x", pady=(15, 0))

        if exito_pdf:
            btn_pdf = ttk.Button(
                frame_btn,
                text="🖨 Abrir Comprobante PDF (ReportLab)",
                command=lambda: os.startfile(pdf_path)
            )
            btn_pdf.pack(fill="x", pady=2)

        btn_cerrar = ttk.Button(frame_btn, text="Aceptar y Continuar", command=modal.destroy)
        btn_cerrar.pack(fill="x", pady=2)
