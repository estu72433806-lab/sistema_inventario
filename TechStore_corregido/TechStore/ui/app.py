"""
Ventana Principal de la Aplicación TechStore con control de roles y permisos.
Integra:
- Panel Principal (Dashboard con datos reales de SQLite y accesos rápidos)
- Inventario de Productos
- Movimientos de Stock (Kardex)
- Clientes y Proveedores (Contactos unificados)
- Punto de Venta (POS) con ReportLab PDF
- Reportes con Rango de Fechas y Excel (.xlsx) con openpyxl
- Gestión de Usuarios (exclusivo para Administrador)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ui.views.dashboard_view import DashboardView
from ui.views.productos_view import ProductosView
from ui.views.movimientos_view import MovimientosStockView
from ui.views.contactos_view import ContactosView
from ui.views.ventas_view import VentasView
from ui.views.reportes_view import ReportesView
from ui.views.usuarios_view import UsuariosView
from ui.views.config_nube_dialog import ConfigNubeDialog
from services.sync_service import SyncService
from models.usuario import UsuarioModel
from ui.theme import aplicar_tema
from ui.theme import Color

class MainApplication(tk.Tk):
    def __init__(self, usuario_sesion, on_logout=None):
        super().__init__()
        self.usuario_sesion = usuario_sesion
        self.on_logout = on_logout

        self.title("TechStore - Sistema de Inventario y Ventas Para Tienda de Computadoras")
        self.geometry("1240x780")
        self.minsize(1080, 660)
        self._configurar_estilos()
        self._construir_interfaz()

    def _configurar_estilos(self):
        self.style = aplicar_tema(self)

    def _construir_interfaz(self):
        # 1. Barra de Encabezado Superior
        frame_header = tk.Frame(self, bg=Color.OSCURO, height=60, padx=20, pady=10)
        frame_header.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            frame_header,
            text="💻 TECHSTORE COMPUTADORAS",
            font=("Segoe UI", 14, "bold"),
            fg=Color.ACENTO_CLARO,
            bg=Color.OSCURO
        )
        lbl_logo.pack(side="left")

        # Indicador de Usuario y Rol
        rol_display = self.usuario_sesion.get("rol", "").upper()
        nombre_display = self.usuario_sesion.get("nombre_completo", "Usuario")
        color_badge = "#22c55e" if rol_display == "ADMINISTRADOR" else Color.ADVERTENCIA

        frame_user = tk.Frame(frame_header, bg=Color.OSCURO_2, padx=10, pady=4)
        frame_user.pack(side="right", padx=(10, 0))

        lbl_user_icon = tk.Label(
            frame_user,
            text="👤",
            font=("Segoe UI Emoji", 11),
            bg=Color.OSCURO_2,
            fg=Color.ACENTO_CLARO
        )
        lbl_user_icon.pack(side="left", padx=(0, 5))

        lbl_user_info = tk.Label(
            frame_user,
            text=f"{nombre_display}  [{rol_display}]",
            font=("Segoe UI", 9, "bold"),
            bg=Color.OSCURO_2,
            fg=color_badge
        )
        lbl_user_info.pack(side="left")

        btn_logout = tk.Button(
            frame_user,
            text="Cerrar Sesión",
            command=self.cerrar_sesion,
            font=("Segoe UI", 8, "bold"),
            bg=Color.PELIGRO,
            fg=Color.BLANCO,
            activebackground=Color.PELIGRO_HOVER,
            activeforeground=Color.BLANCO,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn_logout.pack(side="left", padx=(10, 0))

        self.lbl_reloj = tk.Label(
            frame_header,
            text="",
            font=("Segoe UI", 9),
            fg=Color.GRIS_CLARO,
            bg=Color.OSCURO
        )
        self.lbl_reloj.pack(side="right", padx=(10, 15))
        self._actualizar_reloj()

        # Botones de Sincronización y Configuración Nube
        self.btn_sync = tk.Button(
            frame_header,
            text="🔄 Sincronizar",
            command=self.sincronizar_ahora,
            font=("Segoe UI", 8, "bold"),
            bg="#10b981",
            fg=Color.BLANCO,
            activebackground=Color.EXITO_2,
            activeforeground=Color.BLANCO,
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        self.btn_sync.pack(side="right", padx=(0, 8))

        self.btn_config_nube = tk.Button(
            frame_header,
            text="☁ Config Nube",
            command=self.abrir_config_nube,
            font=("Segoe UI", 8, "bold"),
            bg=Color.ACENTO,
            fg=Color.BLANCO,
            activebackground=Color.ACENTO_OSCURO,
            activeforeground=Color.BLANCO,
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        self.btn_config_nube.pack(side="right", padx=(0, 6))

        btn_asistente_header = tk.Button(
            frame_header,
            text="💡 Reposición",
            command=self.abrir_asistente_reposicion,
            font=("Segoe UI", 8, "bold"),
            bg=Color.AMBAR,
            fg=Color.BLANCO,
            activebackground=Color.ADVERTENCIA_OSCURO,
            activeforeground=Color.BLANCO,
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_asistente_header.pack(side="right", padx=(0, 6))

        # 2. Contenedor de Pestañas (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Vistas
        self.vista_dashboard = DashboardView(
            self.notebook,
            usuario_sesion=self.usuario_sesion,
            on_navegar=self.navegar_a_pestana,
            on_abrir_asistente=self.abrir_asistente_reposicion,
            on_abrir_config_nube=self.abrir_config_nube
        )
        self.vista_productos = ProductosView(
            self.notebook,
            usuario_sesion=self.usuario_sesion,
            on_registrar_entrada=self.transferir_a_entrada_reposicion
        )
        self.vista_movimientos = MovimientosStockView(
            self.notebook,
            usuario_sesion=self.usuario_sesion,
            callback_stock_actualizado=self._on_datos_actualizados
        )
        self.vista_contactos = ContactosView(self.notebook, usuario_sesion=self.usuario_sesion)
        self.vista_ventas = VentasView(self.notebook, usuario_sesion=self.usuario_sesion, callback_producto_actualizado=self._on_datos_actualizados)
        self.vista_reportes = ReportesView(self.notebook, usuario_sesion=self.usuario_sesion)

        # Pestañas principales
        self.notebook.add(self.vista_dashboard, text="🏠 Inicio")
        self.notebook.add(self.vista_productos, text="📦 Inventario de Productos")
        self.notebook.add(self.vista_movimientos, text="🔄 Movimientos de Stock (Kardex)")
        self.notebook.add(self.vista_contactos, text="👥 Clientes y Proveedores")
        self.notebook.add(self.vista_ventas, text="🛒 Punto de Venta (POS)")
        self.notebook.add(self.vista_reportes, text="📊 Reportes y Exportación")

        # Pestaña de usuarios solo para Administrador
        es_admin = (self.usuario_sesion.get("rol") == "administrador")
        if es_admin:
            self.vista_usuarios = UsuariosView(self.notebook, usuario_sesion=self.usuario_sesion)
            self.notebook.add(self.vista_usuarios, text="👤 Usuarios")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_cambio_pestana)

        # 3. Barra de Estado Inferior Híbrida
        frame_status = tk.Frame(self, bg=Color.BORDE, height=26, padx=10)
        frame_status.pack(fill="x", side="bottom")

        self.lbl_status_modo = tk.Label(
            frame_status,
            text="🟡 Modo: SQLite Local (Offline)",
            font=("Segoe UI", 8, "bold"),
            bg=Color.BORDE,
            fg=Color.ADVERTENCIA_OSCURO
        )
        self.lbl_status_modo.pack(side="left")

        lbl_sep1 = tk.Label(frame_status, text=" | ", font=("Segoe UI", 8), bg=Color.BORDE, fg=Color.GRIS)
        lbl_sep1.pack(side="left")

        self.lbl_status_pendientes = tk.Label(
            frame_status,
            text="0 pendientes",
            font=("Segoe UI", 8),
            bg=Color.BORDE,
            fg=Color.TEXTO_SUAVE
        )
        self.lbl_status_pendientes.pack(side="left")

        lbl_sep2 = tk.Label(frame_status, text=" | ", font=("Segoe UI", 8), bg=Color.BORDE, fg=Color.GRIS)
        lbl_sep2.pack(side="left")

        lbl_status_db = tk.Label(
            frame_status,
            text=f"Sesión: {self.usuario_sesion.get('username')}",
            font=("Segoe UI", 8),
            bg=Color.BORDE,
            fg=Color.GRIS_PIZARRA
        )
        lbl_status_db.pack(side="left")

        lbl_status_info = tk.Label(
            frame_status,
            text="Sistema Híbrido: SQLite Local + PostgreSQL Nube",
            font=("Segoe UI", 8),
            bg=Color.BORDE,
            fg=Color.GRIS_OSCURO
        )
        lbl_status_info.pack(side="right")

        self.actualizar_estado_sync()

    def _actualizar_reloj(self):
        ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.lbl_reloj.config(text=f"📅 {ahora}")
        self.after(1000, self._actualizar_reloj)

    def navegar_a_pestana(self, indice):
        """Permite a los accesos directos del dashboard saltar a la pestaña correspondiente."""
        try:
            self.notebook.select(indice)
        except Exception:
            pass

    def _on_cambio_pestana(self, event=None):
        """Sincroniza y recarga los datos al cambiar de pestaña."""
        indice = self.notebook.index(self.notebook.select())
        if indice == 0:
            self.vista_dashboard.actualizar_metricas()
        elif indice == 1:
            self.vista_productos.cargar_selectores()
            self.vista_productos.cargar_productos()
        elif indice == 2:
            self.vista_movimientos.recargar_datos()
        elif indice == 3:
            self.vista_contactos.recargar_datos()
        elif indice == 4:
            self.vista_ventas.actualizar_datos()
        elif indice == 5:
            self.vista_reportes.cargar_ventas()
            self.vista_reportes.actualizar_indicadores()
        elif indice == 6 and hasattr(self, 'vista_usuarios'):
            self.vista_usuarios.cargar_usuarios()

    def _on_datos_actualizados(self):
        """Notificación disparada tras registrar ventas o movimientos de inventario."""
        self.vista_dashboard.actualizar_metricas()
        self.vista_productos.cargar_productos()
        self.vista_movimientos.recargar_datos()
        self.vista_ventas.actualizar_datos()
        self.vista_reportes.cargar_ventas()
        self.vista_reportes.actualizar_indicadores()
        self.actualizar_estado_sync()

    def actualizar_estado_sync(self):
        """Actualiza los indicadores visuales del modo híbrido y los registros pendientes."""
        try:
            from database.pg_config import tiene_credenciales_pg
            pendientes = SyncService.obtener_conteo_pendientes()
            modo, detalle = SyncService.obtener_estado_conexion()
            tiene_cred = tiene_credenciales_pg()

            if modo == "EN_LINEA":
                self.lbl_status_modo.config(text="🟢 Modo: En Línea (PostgreSQL Nube)", fg=Color.EXITO)
                if hasattr(self, 'btn_config_nube'):
                    self.btn_config_nube.config(text="☁ Nube: En Línea 🟢", bg=Color.EXITO_2)
            else:
                self.lbl_status_modo.config(text="🟡 Modo: SQLite Local (Offline)", fg=Color.ADVERTENCIA_OSCURO)
                if hasattr(self, 'btn_config_nube'):
                    if tiene_cred:
                        self.btn_config_nube.config(text="☁ Nube: Local 🟡", bg=Color.AMBAR)
                    else:
                        self.btn_config_nube.config(text="☁ Conectar Nube ⚙", bg=Color.ACENTO)

            if pendientes == 0:
                self.lbl_status_pendientes.config(text="✔ Sincronizado (0 pendientes)", fg=Color.EXITO)
            else:
                self.lbl_status_pendientes.config(text=f"⚠ {pendientes} pendiente(s) de sincronizar", fg=Color.PELIGRO_OSCURO)
        except Exception:
            pass

    def sincronizar_ahora(self):
        """Ejecuta la sincronización y retroalimenta al usuario."""
        self.btn_sync.config(state="disabled", text="⏳ Sincronizando...")
        self.update_idletasks()
        try:
            res = SyncService.sincronizar_todo()
            if res["exito"]:
                messagebox.showinfo("Sincronización Exitosa", res["mensaje"])
            else:
                messagebox.showwarning("Aviso de Sincronización", res["mensaje"])
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al sincronizar: {str(e)}")
        finally:
            self.btn_sync.config(state="normal", text="🔄 Sincronizar")
            self._on_datos_actualizados()
            self.actualizar_estado_sync()

    def abrir_config_nube(self):
        """Abre la ventana modal para configurar la base de datos PostgreSQL en la nube."""
        ConfigNubeDialog(self, on_guardado=self.actualizar_estado_sync)

    def abrir_asistente_reposicion(self, producto_id_foco=None):
        """Abre la ventana interactiva del Asistente Inteligente de Reposición."""
        from ui.views.asistente_reposicion_dialog import AsistenteReposicionDialog
        AsistenteReposicionDialog(
            self,
            on_registrar_entrada=self.transferir_a_entrada_reposicion,
            producto_id_foco=producto_id_foco
        )

    def transferir_a_entrada_reposicion(self, producto_id, cantidad, proveedor_id=None):
        """Navega a Movimientos de Stock y pre-configura la entrada sugerida."""
        self.navegar_a_pestana(2)
        self.vista_movimientos.preparar_entrada_producto(producto_id, cantidad, proveedor_id)

    def cerrar_sesion(self):
        confirmar = messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión actual?")
        if confirmar:
            self.destroy()
            if self.on_logout:
                self.on_logout()
