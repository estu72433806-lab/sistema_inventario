# Sistema de Inventario y Ventas - TechStore Computadoras (Modo Híbrido)

Aplicación de escritorio para Windows desarrollada en **Python 3 con Tkinter, SQLite Local y PostgreSQL en la Nube**.
Diseñada con arquitectura **Offline-First (Modo Híbrido)**: opera al 100% desconectada sin internet mediante SQLite local, y se sincroniza bidireccionalmente con PostgreSQL cuando existe conexión disponible.

---

## 🚀 1. Instalación y Ejecución

### Requisitos:
* Python 3.8 o superior instalado en Windows (marcar *"Add Python to PATH"* durante la instalación).

### Instalación de Dependencias:
Abre una terminal o PowerShell en la carpeta del proyecto y ejecuta:
```bash
pip install -r requirements.txt
```
*(Incluye `reportlab`, `openpyxl`, `pyinstaller` y `psycopg2-binary`).*

### Ejecutar la Aplicación:
```bash
python main.py
```

---

## 🌐 2. Arquitectura de Modo Híbrido (SQLite + PostgreSQL)

El sistema soporta dos modos de funcionamiento que alternan automáticamente sin interrumpir la operación del negocio:

### 1. MODO LOCAL (Offline / Sin Internet):
* Cuando no hay internet o el servidor PostgreSQL no está disponible, el sistema opera con **SQLite** local (`data/inventario_tienda.db`).
* Permite:
  * Iniciar sesión con cuentas previamente sincronizadas.
  * Consultar y registrar productos, clientes y proveedores.
  * Realizar ventas con carrito interactivo, descuentos y cálculo de IGV.
  * Descontar stock y registrar movimientos en el Kardex local.
  * Generar comprobantes en PDF con ReportLab.
  * Guardar todos los cambios localmente con identificadores únicos globales (**UUID**) y estado `sincronizado = 0` (pendiente).

### 2. MODO EN LÍNEA (Conectado a PostgreSQL):
* Cuando hay conexión a internet y PostgreSQL está configurado, el sistema se conecta mediante consultas parametrizadas seguras.
* Permite compartir catálogo, clientes y registrar ventas centralizadas entre múltiples computadoras autorizadas.
* Indicador visual en tiempo real en la barra inferior: `🟢 Modo: En Línea (PostgreSQL Nube)` vs `🟡 Modo: SQLite Local (Offline)`.

### 3. SINCRONIZACIÓN AUTOMÁTICA E IDEMPOTENTE:
* Al hacer clic en **"🔄 Sincronizar"** (o al recuperar la conexión):
  1. Envía los registros pendientes (`ventas`, `detalle_ventas`, `movimientos_stock`, `productos`, `clientes`, `proveedores`, `usuarios`) a PostgreSQL.
  2. **Sin duplicados**: Cada registro posee un `uuid` global (`VARCHAR(36) UNIQUE`). Si se reintenta la sincronización, PostgreSQL ignora registros ya existentes sin duplicar ventas ni salidas de stock.
  3. **Descarga de novedades**: Descarga productos o actualizaciones registradas desde otras computadoras hacia el SQLite local.
  4. Al finalizar exitosamente, marca los registros locales como `sincronizado = 1`.
  5. **Resiliencia ante fallos**: Si la conexión se interrumpe a mitad del proceso, la transacción se revierte (`ROLLBACK`) y todos los datos locales permanecen intactos como pendientes para el próximo intento.

### 4. REGLA DE DETECCIÓN DE CONFLICTOS:
* Si un producto o cliente fue modificado en la computadora local y simultáneamente modificado en la nube:
  * El sistema **no sobreescribe a ciegas** ninguno de los dos registros.
  * Detecta el conflicto comparando la `fecha_modificacion`.
  * Registra la discrepancia en la tabla `conflictos_sincronizacion` (en SQLite y PostgreSQL).
  * Informa al usuario para revisión manual.

---

## 🔒 3. Configuración Segura de PostgreSQL (Nube / Servidor)

Las credenciales **nunca se guardan en el código fuente**. Se gestionan mediante:

### Opción A: Desde la Interfaz Gráfica (Recomendada)
1. Inicia el sistema y haz clic en el botón superior **"☁ Config Nube"**.
2. Completa los campos:
   * **Host:** Dirección del servidor (ej: `ep-xyz.us-east-2.aws.neon.tech` o `localhost`).
   * **Puerto:** `5432`
   * **Base de Datos:** Nombre de la base (ej: `techstore_db` o `neondb`).
   * **Usuario:** Usuario de PostgreSQL (ej: `postgres` o `neondb_owner`).
   * **Contraseña:** Contraseña segura (oculta con botón para visualizar).
   * **Modo SSL:** Selecciona `require` para servicios cloud (Neon, Supabase) o `prefer` para local.
3. Haz clic en **"🔍 Probar Conexión"** para verificar la comunicación.
4. Haz clic en **"💾 Guardar Parámetros"** (se almacenará en `config_db.json`, excluido automáticamente de Git).

### Opción B: Archivo de Configuración Local
Copia la plantilla `config_db.example.json` a `config_db.json` y edita los valores:
```json
{
    "pg_host": "ep-example.us-east-2.aws.neon.tech",
    "pg_port": 5432,
    "pg_database": "techstore_db",
    "pg_user": "postgres",
    "pg_password": "TU_PASSWORD_AQUI",
    "pg_sslmode": "require",
    "timeout_segundos": 4
}
```

### Opción C: Variables de Entorno del Sistema
Configura las variables estándar en Windows o en tu terminal:
```bash
set PG_HOST=ep-example.us-east-2.aws.neon.tech
set PG_PORT=5432
set PG_DATABASE=techstore_db
set PG_USER=postgres
set PG_PASSWORD=tu_password
set PG_SSLMODE=require
```

> **¿No tienes un servidor PostgreSQL todavía?**
> Puedes crear una base de datos PostgreSQL gratuita en la nube en menos de 2 minutos en servicios como **[Neon.tech](https://neon.tech)** o **[Supabase.com](https://supabase.com)** (ambos compatibles con SSL `require`). Si no configuras PostgreSQL, el sistema seguirá operando al 100% en **Modo Local (SQLite)** sin errores.

---

## 🔑 4. Credenciales de Acceso al Sistema

Al iniciar por primera vez, el sistema crea automáticamente las cuentas de acceso:

* **Administrador:**
  * Usuario: `admin` | Contraseña: `admin123`
  * *Permisos:* Control total del sistema, configuración de usuarios, costos de compra y eliminación.
* **Vendedor:**
  * Usuario: `vendedor` | Contraseña: `ven123`
  * *Permisos:* Operación de ventas (POS), consulta de catálogo y clientes (precios de compra y eliminación bloqueados).

*(Las contraseñas se almacenan protegidas mediante hash criptográfico PBKDF2-HMAC-SHA256 con salt).*

---

## 🧪 5. Pruebas Automatizadas

Todas las pruebas están en `tests/`. Para ejecutarlas todas y ver un resumen:
```bash
python run_tests.py
```

| Archivo | Qué verifica | Requiere |
|---|---|---|
| `test_auth_and_db.py` | Login, roles, hash de contraseñas, base SQLite | — |
| `test_complete_system.py` | 14 pruebas integrales: ventas, stock, reportes, PDF, permisos | — |
| `test_modules.py` | Productos, contactos, Kardex, alertas de stock mínimo | — |
| `test_sales_module.py` | POS, descuentos, IGV, rollback de stock, comprobantes | — |
| `test_reports_and_receipts.py` | Reportes Excel y comprobantes PDF | — |
| `test_sku_and_replenishment.py` | Generación de SKU y asistente de reposición | — |
| `test_hybrid_sync.py` | Modo híbrido, conflictos y sincronización con PostgreSQL | `psycopg2` |
| `test_user_and_cloud_improvements.py` | Gestión de usuarios e interfaz de configuración en la nube | Tkinter |

Las pruebas generan archivos en `comprobantes/` y `documentos_generados/` (carpetas ignoradas por Git).

---

## 🗂️ 6. Estructura del Proyecto

```
TechStore/
├── main.py                  # Punto de entrada (arranque: BD -> demo -> login -> app)
├── run_tests.py             # Ejecuta todas las pruebas de tests/
├── config_db.example.json   # Plantilla de configuración de PostgreSQL
├── requirements.txt
├── database/                # Conexión, esquema SQLite, esquema PostgreSQL, datos demo
│   ├── db.py                # Conexión SQLite (archivo en data/)
│   ├── schema.py            # Tablas y migraciones
│   ├── seed.py              # Datos de demostración (solo si las tablas están vacías)
│   ├── pg_config.py         # Credenciales (variables de entorno o config_db.json)
│   ├── pg_db.py             # Conexión a PostgreSQL
│   └── pg_schema.py        # Esquema para la nube
├── models/                  # Reglas de negocio y acceso a datos por entidad
├── services/                # Sincronización, PDF, Excel, reposición
├── ui/                      # Interfaz Tkinter
│   ├── theme.py             # Paleta de colores y estilos ttk (edita aquí la apariencia)
│   ├── login.py / app.py    # Login y ventana principal
│   └── views/               # Una vista por módulo
├── tests/                   # Pruebas automatizadas
├── tools/                   # Generadores de documentación (Word, PowerPoint, capturas)
├── docs/                    # Manual, presentación y capturas de la guía
└── data/                    # Base SQLite (inventario_tienda.db) y su script SQL
```

---

## 📦 7. Generación del Ejecutable para Windows (.exe) con PyInstaller

Para compilar la aplicación en un archivo `.exe` independiente que funcione en cualquier computadora con Windows sin necesidad de instalar Python:

1. Asegúrate de tener las dependencias instaladas:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta el comando de compilación:
   ```bash
   pyinstaller --noconsole --onefile --name "TechStore_Sistema" main.py
   ```
   * `--noconsole`: Oculta la ventana de comandos negra de fondo para un acabado profesional.
   * `--onefile`: Empaqueta el intérprete de Python, Tkinter, ReportLab, openpyxl, psycopg2 y todos los módulos en un único archivo ejecutable.
   * `--name "TechStore_Sistema"`: Asigna el nombre al archivo ejecutable.
3. El archivo generado se ubicará en:
   ```
   dist/TechStore_Sistema.exe
   ```
4. Al hacer doble clic en `TechStore_Sistema.exe`, la aplicación creará automáticamente `data/inventario_tienda.db` en su directorio y permitirá operar tanto en Modo Local como en Modo Nube.
