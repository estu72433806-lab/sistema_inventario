"""
Punto de entrada del Sistema de Inventario y Ventas - TechStore Computadoras.
Orden de arranque: esquema de base -> datos de demostración -> login -> aplicación.
"""
from database.schema import init_db
from database.seed import insertar_datos_demo
from ui.login import LoginWindow
from ui.app import MainApplication


def iniciar_login():
    """Muestra el login; al autenticarse abre la ventana principal."""
    def on_login_exitoso(usuario_sesion):
        app = MainApplication(usuario_sesion, on_logout=iniciar_login)
        app.mainloop()

    login_win = LoginWindow(on_login_success=on_login_exitoso)
    login_win.mainloop()


def main():
    init_db()
    insertar_datos_demo()
    iniciar_login()


if __name__ == "__main__":
    main()
