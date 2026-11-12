# Cambios realizados

## Correcciones de funcionamiento
- **Instalación nueva fallaba al arrancar**: el INSERT del administrador por defecto
  tenía 10 columnas y solo 9 valores (`9 values for 10 columns`). Corregido en `database/schema.py`.
- **Datos de demostración sin `uuid`**: productos y movimientos de demo se insertaban sin UUID,
  lo que rompía la sincronización con PostgreSQL. Ahora `database/seed.py` los genera con UUID.
- **Pruebas que colisionaban**: los códigos de prueba usaban `time.time()` en segundos; dos pruebas
  en el mismo segundo generaban el mismo código. Ahora usan `time.time_ns()`.

## Estructura
- `main.py` solo orquesta el arranque (BD -> demo -> login -> app).
- `database/seed.py`: datos de demostración separados del arranque.
- `data/`: base SQLite (`inventario_tienda.db`) + scripts `inventario_tienda.sql` y `postgres_schema.sql`.
  Si existe la base antigua en la raíz, se mueve automáticamente a `data/` la primera vez.
- `tests/`: todas las pruebas. Ejecutar todas con `python run_tests.py`.
- `tools/`: generadores de Word, PowerPoint y capturas (escriben en `docs/`).
- `docs/`: manual, presentación y capturas.

## Estilos
- `ui/theme.py`: paleta de colores (`Color`) y estilos ttk (`aplicar_tema`). Botones de acento,
  peligro y éxito disponibles con `style="Accent.TButton"`, `"Danger.TButton"`, `"Success.TButton"`.
- Los ~210 colores literales de la interfaz ahora usan `Color.*`; cambiar la paleta es editar un solo archivo.

## Formularios (nueva distribución)
- `ui/widgets.py`: componentes compartidos. `Formulario` (etiquetas a la izquierda, campos a la derecha,
  títulos de sección, notas de ayuda y barra de botones con estilos primario / secundario / peligro / éxito)
  y `EncabezadoVista`.
- Formularios reconstruidos con esos componentes:
  - Productos (datos, precios, inventario y detalle en secciones).
  - Clientes y proveedores (identificación y contacto).
  - Registro de movimientos de stock (tipo de operación, producto, detalle).
  - Usuarios (datos personales, acceso al sistema, contraseña y acciones).
  - Configuración de nube (credenciales de PostgreSQL con su modo SSL).
  - Filtros de reportes en tres filas (fechas, búsqueda y exportación).
  - Punto de venta: cabecera y selector de producto con la etiqueta encima del campo.
- Los nombres de campos y botones se conservan, así que la lógica de cada vista no cambió.
- Las pruebas de `test_complete_system.py` ahora cargan los usuarios demo antes de correr.
