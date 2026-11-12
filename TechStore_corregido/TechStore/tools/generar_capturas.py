import _path  # noqa: F401  (prepara rutas del proyecto)
import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script para generar capturas de pantalla reales en alta resolución del sistema TechStore.
Captura cada una de las 10 vistas clave y las guarda en la carpeta 'capturas_guia/'.
"""
import os
import sys
import time
import ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

os.makedirs('capturas_guia', exist_ok=True)

def capturar_ventana(window, nombre_archivo):
    window.update()
    time.sleep(0.2)
    window.update_idletasks()
    
    hwnd = user32.GetParent(window.winfo_id()) or window.winfo_id()
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = max(100, rect.right - rect.left)
    h = max(100, rect.bottom - rect.top)

    hdc_window = user32.GetWindowDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
    hbm = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    gdi32.SelectObject(hdc_mem, hbm)

    user32.PrintWindow(hwnd, hdc_mem, 2)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wintypes.DWORD * 3)]

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, ctypes.byref(bmi), 0)

    im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    im = im.convert('RGB')
    ruta = os.path.join('capturas_guia', nombre_archivo)
    im.save(ruta)
    print(f"[OK] Captura guardada: {ruta} ({w}x{h})")

    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hwnd, hdc_window)

def generar_todas_las_capturas():
    from database.schema import init_db
    init_db()

    # 1. Captura de LoginWindow
    print("Capturando Login...")
    from ui.login import LoginWindow
    win_login = LoginWindow(on_login_success=lambda u: None)
    win_login.entry_usuario.insert(0, "admin")
    win_login.entry_password.insert(0, "admin123")
    capturar_ventana(win_login, "01_login.png")
    win_login.destroy()

    # 2. Captura de MainApplication y sus pestañas
    print("Capturando MainApplication y módulos...")
    from ui.app import MainApplication
    sesion_admin = {
        "id": 1,
        "username": "admin",
        "nombre_completo": "Administrador del Sistema",
        "rol": "administrador"
    }

    app = MainApplication(usuario_sesion=sesion_admin)
    app.geometry("1240x780")
    app.update()

    # Pestaña 0: Dashboard
    app.notebook.select(0)
    app.update()
    time.sleep(0.2)
    capturar_ventana(app, "02_dashboard.png")

    # Pestaña 1: Inventario de Productos
    app.notebook.select(1)
    app.vista_productos.sugerir_sku(silencioso=True)
    app.vista_productos.widgets["entry_nombre"].delete(0, tk.END)
    app.vista_productos.widgets["entry_nombre"].insert(0, "Laptop Lenovo Legion Pro 5 16\" WQXGA")
    app.vista_productos.widgets["entry_marca"].delete(0, tk.END)
    app.vista_productos.widgets["entry_marca"].insert(0, "Lenovo")
    app.vista_productos.widgets["entry_pcompra"].delete(0, tk.END)
    app.vista_productos.widgets["entry_pcompra"].insert(0, "5200.00")
    app.vista_productos.widgets["entry_pventa"].delete(0, tk.END)
    app.vista_productos.widgets["entry_pventa"].insert(0, "6150.00")
    app.vista_productos.widgets["entry_stock"].delete(0, tk.END)
    app.vista_productos.widgets["entry_stock"].insert(0, "8")
    app.vista_productos.widgets["entry_stock_min"].delete(0, tk.END)
    app.vista_productos.widgets["entry_stock_min"].insert(0, "2")
    app.update()
    time.sleep(0.2)
    capturar_ventana(app, "03_inventario_productos.png")

    # Modal: Asistente de Reposición
    print("Capturando Asistente de Reposición...")
    from ui.views.asistente_reposicion_dialog import AsistenteReposicionDialog
    dlg_reposicion = AsistenteReposicionDialog(app)
    dlg_reposicion.geometry("1180x680")
    dlg_reposicion.update()
    time.sleep(0.3)
    hijos = dlg_reposicion.tree.get_children()
    if hijos:
        dlg_reposicion.tree.selection_set(hijos[0])
        dlg_reposicion.tree.see(hijos[0])
        dlg_reposicion._on_producto_seleccionado()
        dlg_reposicion.update()
        time.sleep(0.2)
    capturar_ventana(dlg_reposicion, "04_asistente_reposicion.png")
    dlg_reposicion.destroy()

    # Pestaña 2: Movimientos de Stock (Kardex)
    app.notebook.select(2)
    app.vista_movimientos.spin_cantidad.delete(0, tk.END)
    app.vista_movimientos.spin_cantidad.insert(0, "10")
    app.vista_movimientos.combo_motivo.set("Recepción de reposición por stock mínimo")
    app.vista_movimientos.entry_referencia.delete(0, tk.END)
    app.vista_movimientos.entry_referencia.insert(0, "Factura F001-49210")
    app.update()
    time.sleep(0.2)
    capturar_ventana(app, "05_movimientos_kardex.png")

    # Pestaña 3: Clientes y Proveedores
    app.notebook.select(3)
    app.update()
    time.sleep(0.2)
    capturar_ventana(app, "06_contactos.png")

    # Pestaña 4: Punto de Venta (POS)
    app.notebook.select(4)
    if app.vista_ventas.productos_cache:
        p_ej = app.vista_ventas.productos_cache[0]
        app.vista_ventas.carrito = [{
            "producto_id": p_ej["id"],
            "codigo": p_ej["codigo"],
            "nombre": p_ej["nombre"],
            "cantidad": 2,
            "precio_unitario": p_ej["precio_venta"],
            "subtotal": round(2 * p_ej["precio_venta"], 2),
            "total": round(2 * p_ej["precio_venta"], 2)
        }]
        app.vista_ventas.renderizar_carrito()
        app.vista_ventas.recalcular_totales()
    app.update()
    time.sleep(0.2)
    capturar_ventana(app, "07_punto_venta_pos.png")

    # Pestaña 5: Reportes y Exportación
    app.notebook.select(5)
    app.update()
    time.sleep(0.2)
    capturar_ventana(app, "08_reportes_excel.png")

    # Pestaña 6: Gestión de Usuarios Mejorada
    print("Capturando Gestión de Usuarios Mejorada...")
    if hasattr(app, 'vista_usuarios'):
        app.notebook.select(6)
        app.vista_usuarios.ent_nombre.delete(0, tk.END)
        app.vista_usuarios.ent_nombre.insert(0, "Carlos Mendoza Flores")
        app.vista_usuarios.ent_username.delete(0, tk.END)
        app.vista_usuarios.ent_username.insert(0, "cmendoza")
        app.vista_usuarios.combo_rol.set(app.vista_usuarios.ROL_VENDEDOR_DISPLAY)
        app.vista_usuarios._on_rol_cambiado()
        app.vista_usuarios.ent_pwd.delete(0, tk.END)
        app.vista_usuarios.ent_pwd.insert(0, "Tech2026!")
        app.vista_usuarios.ent_pwd.config(show="")
        app.update()
        time.sleep(0.3)
        capturar_ventana(app, "09_usuarios.png")

    # Modal: Configuración de Nube Mejorada
    print("Capturando Configuración de Nube...")
    from ui.views.config_nube_dialog import ConfigNubeDialog
    dlg_nube = ConfigNubeDialog(app)
    dlg_nube.geometry("640x660")
    dlg_nube.ent_url.delete(0, tk.END)
    dlg_nube.ent_url.insert(0, "postgresql://neondb_owner:claveSegura@ep-cool-fog-123.us-east-2.aws.neon.tech/neondb?sslmode=require")
    dlg_nube.update()
    time.sleep(0.3)
    capturar_ventana(dlg_nube, "10_config_nube.png")
    dlg_nube.destroy()

    app.destroy()
    print("¡Todas las 10 capturas se generaron exitosamente!")

if __name__ == "__main__":
    generar_todas_las_capturas()
