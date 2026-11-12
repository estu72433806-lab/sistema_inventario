"""
Vista de Control de Movimientos de Stock (Kardex).
Maneja entradas de mercadería con proveedor y ajustes por pérdida, daño físico o inventario.
Actualiza el stock en tiempo real y muestra alertas de stock mínimo.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from models.producto import ProductoModel
from models.proveedor import ProveedorModel
from models.movimiento_stock import MovimientoStockModel
from ui.theme import Color
from ui.widgets import Formulario

class MovimientosStockView(ttk.Frame):
    def __init__(self, parent, usuario_sesion=None, callback_stock_actualizado=None):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion or {"id": 1, "username": "admin", "rol": "administrador"}
        self.callback_stock_actualizado = callback_stock_actualizado
        self.productos_cache = []
        self.proveedores_cache = []
        self._construir_ui()
        self.recargar_datos()

    def _construir_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Panel izquierdo: formulario de operación (entrada o ajuste)
        form = Formulario(self, "Registro de Operación de Stock")
        form.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        form.seccion("Tipo de operación")
        self.var_tipo_op = tk.StringVar(value="ENTRADA")
        frame_radios = ttk.Frame(form)
        ttk.Radiobutton(
            frame_radios, text="Entrada de mercadería (proveedor)",
            variable=self.var_tipo_op, value="ENTRADA", command=self._on_cambio_tipo_op
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            frame_radios, text="Ajuste por pérdida / daño (salida)",
            variable=self.var_tipo_op, value="SALIDA", command=self._on_cambio_tipo_op
        ).pack(anchor="w", pady=2)
        form.ancho(frame_radios, pady=(0, 4))

        form.seccion("Producto")
        self.combo_producto = form.campo("combo_producto", "Producto / componente",
                                         ttk.Combobox(form, state="readonly", width=34), requerido=True)
        self.combo_producto.bind("<<ComboboxSelected>>", self._on_producto_seleccionado)
        self.lbl_info_stock = ttk.Label(
            form, text="Stock actual: - | Stock mínimo: -",
            font=("Segoe UI", 9, "bold"), foreground=Color.ACENTO
        )
        form.ancho(self.lbl_info_stock, pady=(0, 4))

        form.seccion("Detalle")
        self.combo_proveedor = form.campo("combo_proveedor", "Proveedor mayorista",
                                          ttk.Combobox(form, state="readonly", width=34), requerido=True)
        self.lbl_proveedor = form.etiquetas["combo_proveedor"]
        self.spin_cantidad = form.campo("spin_cantidad", "Cantidad de unidades",
                                        ttk.Spinbox(form, from_=1, to=9999, width=15), requerido=True)
        self.spin_cantidad.set(1)
        self.combo_motivo = form.campo("combo_motivo", "Motivo del movimiento",
                                       ttk.Combobox(form, width=34), requerido=True)
        self.entry_referencia = form.campo("entry_referencia", "N° factura / guía / nota",
                                           ttk.Entry(form, width=34))
        self.lbl_ref = form.etiquetas["entry_referencia"]

        form.acciones([("procesar", "Registrar y actualizar stock", self.procesar_movimiento, "primario")])

        # Panel derecho: Historial (Kardex)
        frame_tabla = ttk.Frame(self, padding=10)
        frame_tabla.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        frame_tabla.rowconfigure(2, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

        # Barra de filtros y alertas
        frame_top = ttk.Frame(frame_tabla)
        frame_top.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_top, text="Filtrar tipo:").pack(side="left", padx=5)
        self.combo_filtro_tipo = ttk.Combobox(frame_top, values=["TODOS", "ENTRADA", "SALIDA"], state="readonly", width=12)
        self.combo_filtro_tipo.current(0)
        self.combo_filtro_tipo.pack(side="left", padx=5)
        self.combo_filtro_tipo.bind("<<ComboboxSelected>>", lambda e: self.cargar_historial())

        ttk.Label(frame_top, text="Buscar:").pack(side="left", padx=5)
        self.entry_buscar = ttk.Entry(frame_top, width=20)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.cargar_historial())

        btn_refrescar = ttk.Button(frame_top, text="Refrescar", command=self.recargar_datos)
        btn_refrescar.pack(side="left", padx=5)

        self.lbl_alerta_stock_general = ttk.Label(
            frame_top,
            text="",
            font=("Segoe UI", 9, "bold"),
            foreground=Color.PELIGRO_OSCURO
        )
        self.lbl_alerta_stock_general.pack(side="right", padx=10)

        # Tabla de Movimientos
        columnas = ("id", "fecha", "tipo", "producto", "cantidad", "motivo", "referencia", "proveedor", "usuario")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("fecha", text="Fecha y Hora")
        self.tree.heading("tipo", text="Operación")
        self.tree.heading("producto", text="Producto / Componente")
        self.tree.heading("cantidad", text="Cant.")
        self.tree.heading("motivo", text="Motivo")
        self.tree.heading("referencia", text="Doc. Referencia")
        self.tree.heading("proveedor", text="Proveedor Mayorista")
        self.tree.heading("usuario", text="Registrado Por")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("fecha", width=130, anchor="center")
        self.tree.column("tipo", width=80, anchor="center")
        self.tree.column("producto", width=220, anchor="w")
        self.tree.column("cantidad", width=55, anchor="center")
        self.tree.column("motivo", width=170, anchor="w")
        self.tree.column("referencia", width=120, anchor="center")
        self.tree.column("proveedor", width=160, anchor="w")
        self.tree.column("usuario", width=95, anchor="center")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=2, column=0, sticky="nsew")
        scroll_y.grid(row=2, column=1, sticky="ns")
        scroll_x.grid(row=3, column=0, sticky="ew")

        # Tags de colores para entradas (verde) y salidas (rojo)
        self.tree.tag_configure("ENTRADA", foreground=Color.EXITO)
        self.tree.tag_configure("SALIDA", foreground=Color.PELIGRO_OSCURO)

        self._on_cambio_tipo_op()

    def _on_cambio_tipo_op(self):
        op = self.var_tipo_op.get()
        if op == "ENTRADA":
            self.lbl_proveedor.config(text="Proveedor Mayorista *:")
            self.combo_proveedor.config(state="readonly")
            self.lbl_ref.config(text="N° Factura / Guía de Compra:")
            motivos = [
                "Compra / Recepción de mercadería mayorista",
                "Recepción de pedido especial",
                "Devolución o reposición de garantía",
                "Ingreso por corrección de inventario"
            ]
        else:
            self.lbl_proveedor.config(text="Proveedor (No aplica en pérdidas/daño):")
            self.combo_proveedor.config(state="disabled")
            self.lbl_ref.config(text="Nota o Reporte de Avería:")
            motivos = [
                "Daño físico / Componente averiado en tienda",
                "Pérdida / Faltante en recuento físico",
                "Envío de componente a garantía de marca",
                "Baja por obsolescencia o descarte"
            ]

        self.combo_motivo["values"] = motivos
        if motivos:
            self.combo_motivo.current(0)

    def recargar_datos(self):
        # 1. Cargar productos
        self.productos_cache = ProductoModel.listar_productos()
        opciones_p = [f"[{p['codigo']}] {p['nombre']} (Stock: {p['stock']})" for p in self.productos_cache]
        self.combo_producto["values"] = opciones_p
        if opciones_p:
            self.combo_producto.current(0)
            self._on_producto_seleccionado()

        # 2. Cargar proveedores
        self.proveedores_cache = ProveedorModel.listar_proveedores()
        opciones_prov = [f"{pr['ruc_dni']} - {pr['razon_social']}" for pr in self.proveedores_cache]
        self.combo_proveedor["values"] = opciones_prov
        if opciones_prov:
            self.combo_proveedor.current(0)

        # 3. Cargar historial y alertas
        self.cargar_historial()
        self._actualizar_alerta_general()

    def _on_producto_seleccionado(self, event=None):
        idx = self.combo_producto.current()
        if 0 <= idx < len(self.productos_cache):
            p = self.productos_cache[idx]
            es_bajo = p["stock"] <= p["stock_minimo"]
            color = Color.PELIGRO_OSCURO if es_bajo else Color.ACENTO
            alerta_txt = " ⚠ ¡STOCK BAJO!" if es_bajo else " ✔ Nivel OK"
            self.lbl_info_stock.config(
                text=f"Stock actual: {p['stock']} | Mínimo: {p['stock_minimo']}{alerta_txt}",
                foreground=color
            )

    def _actualizar_alerta_general(self):
        bajos = ProductoModel.obtener_productos_bajo_stock()
        if bajos:
            self.lbl_alerta_stock_general.config(
                text=f"⚠ Alerta: {len(bajos)} componente(s) con stock igual o menor al mínimo!",
                foreground=Color.PELIGRO_OSCURO
            )
        else:
            self.lbl_alerta_stock_general.config(
                text="✔ Todo el inventario se encuentra sobre el stock mínimo.",
                foreground=Color.EXITO
            )

    def cargar_historial(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        filtro = self.combo_filtro_tipo.get()
        tipo_filtro = None if filtro == "TODOS" else filtro
        busqueda = self.entry_buscar.get().strip()

        movimientos = MovimientoStockModel.listar_movimientos(
            tipo_movimiento=tipo_filtro,
            busqueda=busqueda,
            limite=150
        )

        for m in movimientos:
            tipo = m["tipo_movimiento"]
            tag = "ENTRADA" if tipo == "ENTRADA" else "SALIDA"
            signo = "+" if tipo == "ENTRADA" else "-"

            self.tree.insert("", "end", values=(
                m["id"],
                m["fecha"],
                m["tipo_movimiento"],
                f"[{m['producto_codigo']}] {m['producto_nombre']}",
                f"{signo}{m['cantidad']}",
                m["motivo"] or "-",
                m["referencia"] or "-",
                m["proveedor_nombre"] or "-",
                m["usuario_nombre"] or "Admin"
            ), tags=(tag,))

    def procesar_movimiento(self):
        p_idx = self.combo_producto.current()
        if p_idx < 0 or p_idx >= len(self.productos_cache):
            messagebox.showwarning("Atención", "Seleccione un producto para la operación.", parent=self)
            return

        producto = self.productos_cache[p_idx]

        try:
            cantidad = int(self.spin_cantidad.get())
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atención", "Ingrese una cantidad entera mayor a cero.", parent=self)
            return

        tipo_op = self.var_tipo_op.get()
        motivo = self.combo_motivo.get().strip()
        referencia = self.entry_referencia.get().strip()
        usuario_id = self.usuario_sesion.get("id")

        if not motivo:
            messagebox.showwarning("Atención", "Indique el motivo del movimiento.", parent=self)
            return

        if tipo_op == "ENTRADA":
            prov_idx = self.combo_proveedor.current()
            proveedor_id = self.proveedores_cache[prov_idx]["id"] if (0 <= prov_idx < len(self.proveedores_cache)) else None
            
            mov_id, err = MovimientoStockModel.registrar_entrada_mercaderia(
                producto_id=producto["id"],
                cantidad=cantidad,
                proveedor_id=proveedor_id,
                referencia=referencia or "Entrada Almacén",
                motivo=motivo,
                usuario_id=usuario_id
            )
            msg_exito = f"Se ingresaron {cantidad} unidades al stock de '{producto['nombre']}'."
        else: # SALIDA (Ajuste por daño o pérdida)
            mov_id, err = MovimientoStockModel.registrar_ajuste_stock(
                producto_id=producto["id"],
                cantidad=cantidad,
                motivo=motivo,
                tipo_movimiento="SALIDA",
                usuario_id=usuario_id,
                referencia=referencia or "Ajuste / Merma"
            )
            msg_exito = f"Se descontaron {cantidad} unidades por ajuste de '{producto['nombre']}'."

        if err:
            messagebox.showerror("Error en Movimiento de Stock", err, parent=self)
            return

        messagebox.showinfo("Operación Exitosa", f"{msg_exito}\nStock actualizado correctamente.", parent=self)
        self.entry_referencia.delete(0, tk.END)
        self.spin_cantidad.set(1)

        # Refrescar y notificar a la app
        self.recargar_datos()
        if self.callback_stock_actualizado:
            self.callback_stock_actualizado()

    def preparar_entrada_producto(self, producto_id, cantidad=1, proveedor_id=None):
        """Pre-configura el formulario de movimientos para una entrada recomendada de reposición."""
        self.var_tipo_op.set("ENTRADA")
        self._on_cambio_tipo_op()

        # Seleccionar producto
        for idx, p in enumerate(self.productos_cache):
            if p["id"] == producto_id:
                self.combo_producto.current(idx)
                self._on_producto_seleccionado()
                break

        # Seleccionar proveedor si se especificó
        if proveedor_id:
            for idx, pr in enumerate(self.proveedores_cache):
                if pr["id"] == proveedor_id:
                    self.combo_proveedor.current(idx)
                    break

        # Fijar cantidad sugerida
        self.spin_cantidad.delete(0, tk.END)
        self.spin_cantidad.insert(0, str(max(1, int(cantidad))))

        # Motivo y referencia
        self.combo_motivo.set("Recepción de reposición por stock mínimo")
        self.entry_referencia.delete(0, tk.END)
        self.entry_referencia.insert(0, "Orden de Reposición")
