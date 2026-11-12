"""
Vista del Panel Principal (Dashboard):
Muestra métricas en tiempo real de SQLite:
- Ventas del día (monto recaudado y conteo de transacciones).
- Cantidad de productos registrados activos.
- Productos con stock igual o menor al stock mínimo.
Incluye accesos directos a todos los módulos según el rol del usuario conectado.
"""
import tkinter as tk
from tkinter import ttk
from models.venta import VentaModel
from models.producto import ProductoModel
from ui.theme import Color

class DashboardView(ttk.Frame):
    def __init__(self, parent, usuario_sesion, on_navegar=None, on_abrir_asistente=None, on_abrir_config_nube=None):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion
        self.on_navegar = on_navegar
        self.on_abrir_asistente = on_abrir_asistente
        self.on_abrir_config_nube = on_abrir_config_nube
        self._construir_ui()
        self.actualizar_metricas()

    def _construir_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # 1. Bienvenida y Rol
        frame_bienvenida = tk.Frame(self, bg=Color.BLANCO, padx=20, pady=12, highlightbackground=Color.BORDE, highlightthickness=1)
        frame_bienvenida.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        nombre = self.usuario_sesion.get("nombre_completo", "Usuario")
        rol = self.usuario_sesion.get("rol", "vendedor").upper()

        lbl_hola = tk.Label(
            frame_bienvenida,
            text=f"👋 ¡Bienvenido al Sistema, {nombre}!",
            font=("Segoe UI", 13, "bold"),
            bg=Color.BLANCO,
            fg=Color.OSCURO
        )
        lbl_hola.pack(side="left")

        color_rol = Color.EXITO if rol == "ADMINISTRADOR" else Color.ADVERTENCIA_OSCURO
        lbl_badge_rol = tk.Label(
            frame_bienvenida,
            text=f"Rol: {rol}",
            font=("Segoe UI", 9, "bold"),
            bg=Color.FONDO_ALT,
            fg=color_rol,
            padx=10,
            pady=3
        )
        lbl_badge_rol.pack(side="right")

        # 2. Tarjetas de Métricas en Tiempo Real (Datos reales de SQLite + Estado Híbrido)
        frame_cards = ttk.Frame(self, padding=5)
        frame_cards.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        for i in range(4):
            frame_cards.columnconfigure(i, weight=1)

        self.card_ventas = self._crear_tarjeta_metrica(
            frame_cards, 0,
            titulo="VENTAS DEL DÍA",
            valor_inicial="S/ 0.00",
            subtitulo="0 venta(s) registradas hoy",
            color_fondo=Color.ACENTO
        )

        self.card_productos = self._crear_tarjeta_metrica(
            frame_cards, 1,
            titulo="PRODUCTOS ACTIVOS",
            valor_inicial="0",
            subtitulo="Componentes en catálogo",
            color_fondo=Color.TEAL
        )

        self.card_stock_alerta = self._crear_tarjeta_metrica(
            frame_cards, 2,
            titulo="ALERTA STOCK BAJO (💡 ASISTENTE)",
            valor_inicial="0",
            subtitulo="Clic para abrir Asistente de Reposición",
            color_fondo=Color.PELIGRO_OSCURO,
            on_click=self._abrir_asistente
        )

        self.card_sync = self._crear_tarjeta_metrica(
            frame_cards, 3,
            titulo="MODO HÍBRIDO (NUBE)",
            valor_inicial="LOCAL",
            subtitulo="0 pendientes de sincronizar",
            color_fondo=Color.TEXTO_SUAVE,
            on_click=self._abrir_config_nube
        )

        # 3. Contenedor de Accesos Rápidos (Tiles de navegación)
        frame_accesos = ttk.LabelFrame(self, text=" Accesos Rápidos a Módulos del Sistema ", padding=15)
        frame_accesos.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        for col in range(3):
            frame_accesos.columnconfigure(col, weight=1)
        for row in range(2):
            frame_accesos.rowconfigure(row, weight=1)

        es_admin = (self.usuario_sesion.get("rol") == "administrador")

        modulos = [
            ("🛒 Punto de Venta (POS)", "Emitir boletas, aplicar descuentos y cobrar", 4, 0, 0),
            ("📦 Inventario de Productos", "Catálogo, precios de venta y control de stock", 1, 0, 1),
            ("🔄 Movimientos de Stock", "Entradas de mercadería y ajustes por pérdida/daño", 2, 0, 2),
            ("👥 Clientes y Proveedores", "Directorio unificado de contactos y mayoristas", 3, 1, 0),
            ("📊 Reportes y Exportación", "Ventas por fechas, Excel (.xlsx) y comprobantes PDF", 5, 1, 1),
        ]

        # El módulo de usuarios solo se agrega si el rol es administrador
        if es_admin:
            modulos.append(("👤 Gestión de Usuarios", "Creación de cuentas, roles y control de acceso", 6, 1, 2))

        for titulo, desc, tab_index, r, c in modulos:
            self._crear_boton_modulo(frame_accesos, titulo, desc, tab_index, r, c)

    def _crear_tarjeta_metrica(self, parent, col, titulo, valor_inicial, subtitulo, color_fondo, on_click=None):
        card = tk.Frame(parent, bg=color_fondo, padx=16, pady=12, relief="flat", cursor="hand2" if on_click else "")
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        lbl_tit = tk.Label(card, text=titulo, font=("Segoe UI", 8, "bold"), fg=Color.ACENTO_PALIDO, bg=color_fondo, cursor="hand2" if on_click else "")
        lbl_tit.pack(anchor="w")

        lbl_val = tk.Label(card, text=valor_inicial, font=("Segoe UI", 18, "bold"), fg=Color.BLANCO, bg=color_fondo, cursor="hand2" if on_click else "")
        lbl_val.pack(anchor="w", pady=(2, 0))

        lbl_sub = tk.Label(card, text=subtitulo, font=("Segoe UI", 8), fg=Color.ACENTO_PALIDO, bg=color_fondo, cursor="hand2" if on_click else "")
        lbl_sub.pack(anchor="w", pady=(2, 0))

        if on_click:
            for w in (card, lbl_tit, lbl_val, lbl_sub):
                w.bind("<Button-1>", lambda e: on_click())

        return {"valor": lbl_val, "sub": lbl_sub}

    def _abrir_asistente(self):
        if self.on_abrir_asistente:
            self.on_abrir_asistente()
        else:
            from ui.views.asistente_reposicion_dialog import AsistenteReposicionDialog
            AsistenteReposicionDialog(self)

    def _abrir_config_nube(self):
        if self.on_abrir_config_nube:
            self.on_abrir_config_nube()
        else:
            from ui.views.config_nube_dialog import ConfigNubeDialog
            ConfigNubeDialog(self)

    def _crear_boton_modulo(self, parent, titulo, descripcion, tab_index, row, col):
        frame_tile = tk.Frame(parent, bg=Color.BLANCO, padx=12, pady=10, relief="solid", bd=1, highlightbackground=Color.GRIS_CLARO)
        frame_tile.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        lbl_t = tk.Label(frame_tile, text=titulo, font=("Segoe UI", 10, "bold"), fg=Color.OSCURO, bg=Color.BLANCO)
        lbl_t.pack(anchor="w")

        lbl_d = tk.Label(frame_tile, text=descripcion, font=("Segoe UI", 8), fg=Color.GRIS_OSCURO, bg=Color.BLANCO, wraplength=260, justify="left")
        lbl_d.pack(anchor="w", pady=(3, 8))

        btn = ttk.Button(
            frame_tile,
            text="Acceder al Módulo →",
            command=lambda idx=tab_index: self._navegar(idx)
        )
        btn.pack(anchor="w")

    def _navegar(self, tab_index):
        if self.on_navegar:
            self.on_navegar(tab_index)

    def actualizar_metricas(self):
        """Consulta datos reales de SQLite y actualiza las tarjetas."""
        try:
            metricas = VentaModel.obtener_metricas_dashboard()

            # Ventas de hoy
            tot_hoy = metricas["ventas_hoy_total"]
            cnt_hoy = metricas["ventas_hoy_count"]
            self.card_ventas["valor"].config(text=f"S/ {tot_hoy:,.2f}")
            self.card_ventas["sub"].config(text=f"{cnt_hoy} venta(s) registradas hoy")

            # Productos activos
            prods = metricas["total_productos"]
            self.card_productos["valor"].config(text=str(prods))
            self.card_productos["sub"].config(text=f"{prods} componentes en catálogo activo")

            # Stock bajo
            bajos = metricas["stock_bajo_count"]
            self.card_stock_alerta["valor"].config(text=str(bajos))
            if bajos > 0:
                self.card_stock_alerta["sub"].config(text=f"⚠ {bajos} producto(s) en nivel crítico!")
            else:
                self.card_stock_alerta["sub"].config(text="✔ Niveles de inventario óptimos")

            # Estado Híbrido & Sincronización
            from services.sync_service import SyncService
            from database.pg_config import tiene_credenciales_pg
            pendientes = SyncService.obtener_conteo_pendientes()
            info_sync = SyncService.obtener_info_ultima_sincronizacion()
            ult_sync = info_sync.get("ultima_sincronizacion", "Nunca")
            tiene_cred = tiene_credenciales_pg()

            if not tiene_cred:
                self.card_sync["valor"].config(text="LOCAL (SQLite)")
                self.card_sync["sub"].config(text="Nube sin configurar (Clic aquí)")
            else:
                modo, _ = SyncService.obtener_estado_conexion()
                if modo == "EN_LINEA":
                    self.card_sync["valor"].config(text="EN LÍNEA 🟢")
                    if pendientes == 0:
                        self.card_sync["sub"].config(text="Al día (0 pendientes)")
                    else:
                        self.card_sync["sub"].config(text=f"⚠ {pendientes} por subir (Clic aquí)")
                else:
                    self.card_sync["valor"].config(text="LOCAL 🟡")
                    self.card_sync["sub"].config(text=f"{pendientes} pendientes (Offline)")
        except Exception as e:
            print(f"Aviso al cargar métricas de dashboard: {e}")
