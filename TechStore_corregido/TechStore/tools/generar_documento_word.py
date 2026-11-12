import _path  # noqa: F401  (prepara rutas del proyecto)
"""
Script para generar el documento Word 'Manual_de_Usuario_y_Guion_TechStore.docx'
con diseño ejecutivo profesional, tablas de datos para copiar y pegar,
guion de exposición paso a paso y capturas de pantalla reales embebidas.
"""
import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def aplicar_sombreado_celda(celda, color_hex):
    """Aplica color de fondo hexadecimal a una celda de tabla."""
    tcPr = celda._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def aplicar_bordes_celda(celda, top="none", bottom="none", left="none", right="none", color="CBD5E1", sz="8"):
    """Configura bordes específicos en una celda."""
    tcPr = celda._tc.get_or_add_tcPr()
    b_xml = (
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="{top}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{bottom}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{left}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{right}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(parse_xml(b_xml))

def agregar_caja_destacada(doc, titulo, texto_parrafos, tipo="guion"):
    """
    Crea una caja destacada (Callout box) estilizada.
    Tipos:
    - 'guion': Borde azul oscuro, fondo celeste tenue, icono de micrófono.
    - 'ejemplo': Borde ámbar/dorado, fondo crema suave, icono de portapapeles.
    - 'tip': Borde verde esmeralda, fondo verde tenue, icono de bombilla.
    """
    if tipo == "guion":
        b_color = "0284C7"
        bg_color = "F0F9FF"
        icono = "🎙️ GUION DE EXPOSICIÓN (QUÉ DECIR EN TU PRESENTACIÓN)"
        tit_color = RGBColor(2, 132, 199)
    elif tipo == "ejemplo":
        b_color = "D97706"
        bg_color = "FFFBEB"
        icono = "📋 DATOS PARA COPIAR Y PEGAR EN ESTA PANTALLA"
        tit_color = RGBColor(217, 119, 6)
    else:
        b_color = "15803D"
        bg_color = "F0FDF4"
        icono = "💡 CONSEJO CLAVE DE NEGOCIO Y TÉCNICO"
        tit_color = RGBColor(21, 128, 61)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    aplicar_sombreado_celda(cell, bg_color)
    aplicar_bordes_celda(cell, left="single", color=b_color, sz="24")

    # Título de la caja
    p_tit = cell.paragraphs[0]
    p_tit.paragraph_format.space_before = Pt(4)
    p_tit.paragraph_format.space_after = Pt(4)
    run_tit = p_tit.add_run(f"{icono}\n{titulo}")
    run_tit.bold = True
    run_tit.font.name = "Segoe UI"
    run_tit.font.size = Pt(10)
    run_tit.font.color.rgb = tit_color

    # Párrafos de texto
    for t in texto_parrafos:
        p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(t)
        run.font.name = "Segoe UI"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def agregar_captura_con_epigrafe(doc, ruta_relativa, epigrafe):
    """Inserta una captura de pantalla centrada con borde sutil y su epígrafe descriptivo."""
    ruta_completa = os.path.abspath(ruta_relativa)
    if not os.path.exists(ruta_completa):
        p_err = doc.add_paragraph(f"[Captura no encontrada: {ruta_relativa}]")
        p_err.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True
    
    run_img = p_img.add_run()
    run_img.add_picture(ruta_completa, width=Inches(6.2))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(8)
    run_cap = p_cap.add_run(f"📸 {epigrafe}")
    run_cap.font.name = "Segoe UI"
    run_cap.font.size = Pt(8.5)
    run_cap.font.italic = True
    run_cap.font.color.rgb = RGBColor(100, 116, 139)

def agregar_tabla_datos(doc, encabezados, filas, anchos=None):
    """Crea una tabla formateada profesionalmente para datos estructurados."""
    tbl = doc.add_table(rows=len(filas) + 1, cols=len(encabezados))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Cabecera
    for col_idx, h_text in enumerate(encabezados):
        celda = tbl.cell(0, col_idx)
        aplicar_sombreado_celda(celda, "0F172A") # Deep Slate
        aplicar_bordes_celda(celda, top="single", bottom="single", left="single", right="single", color="334155", sz="6")
        p = celda.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(h_text)
        run.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255, 255, 255)

    # Filas de datos
    for r_idx, fila in enumerate(filas, start=1):
        bg = "FFFFFF" if r_idx % 2 != 0 else "F8FAFC"
        for c_idx, val in enumerate(fila):
            celda = tbl.cell(r_idx, c_idx)
            aplicar_sombreado_celda(celda, bg)
            aplicar_bordes_celda(celda, top="single", bottom="single", left="single", right="single", color="E2E8F0", sz="4")
            p = celda.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(str(val))
            run.font.name = "Segoe UI"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(15, 23, 42)
            if c_idx == 0:
                run.bold = True

    if anchos:
        for row in tbl.rows:
            for idx, width in enumerate(anchos):
                row.cells[idx].width = width

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def construir_documento():
    doc = docx.Document()

    # 1. Configurar márgenes estándar de 2.5 cm
    for sec in doc.sections:
        sec.top_margin = Inches(0.9)
        sec.bottom_margin = Inches(0.9)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

        # Encabezado y Pie de página
        header = sec.header
        p_head = header.paragraphs[0]
        p_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_head = p_head.add_run("TechStore Computadoras | Manual de Usuario y Guion de Exposición v2.0")
        r_head.font.name = "Segoe UI"
        r_head.font.size = Pt(8)
        r_head.font.color.rgb = RGBColor(148, 163, 184)

        footer = sec.footer
        p_foot = footer.paragraphs[0]
        p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_foot = p_foot.add_run("Sistema de Inventario, Ventas y Asistente de Reposición Inteligente")
        r_foot.font.name = "Segoe UI"
        r_foot.font.size = Pt(8)
        r_foot.font.color.rgb = RGBColor(148, 163, 184)

    # -------------------------------------------------------------------------
    # PORTADA CORPORATIVA
    # -------------------------------------------------------------------------
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(40)
    p_pre.paragraph_format.space_after = Pt(6)
    r_pre = p_pre.add_run("MANUAL INTEGRAL DE OPERACIÓN Y GUION TÉCNICO DE EXPOSICIÓN")
    r_pre.bold = True
    r_pre.font.name = "Segoe UI"
    r_pre.font.size = Pt(11)
    r_pre.font.color.rgb = RGBColor(2, 132, 199)

    p_tit = doc.add_paragraph()
    p_tit.paragraph_format.space_before = Pt(0)
    p_tit.paragraph_format.space_after = Pt(12)
    r_tit = p_tit.add_run("SISTEMA TECHSTORE COMPUTADORAS")
    r_tit.bold = True
    r_tit.font.name = "Segoe UI"
    r_tit.font.size = Pt(26)
    r_tit.font.color.rgb = RGBColor(15, 23, 42)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(30)
    r_sub = p_sub.add_run("Gestión de Inventario, Punto de Venta (POS), Kardex, Código SKU Inteligente y Asistente de Reposición Basado en Demanda")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    # Tabla resumen de la portada
    datos_portada = [
        ["Propósito del Documento", "Manual práctico paso a paso, ejemplos de copiar y pegar, y guion oratorio de exposición."],
        ["Público Objetivo", "Usuarios del sistema, administradores, vendedores, jurado calificador y evaluadores."],
        ["Versión del Software", "Versión 2.0 (Con SKU inteligente automático y Asistente de Reposición)."],
        ["Base de Datos", "Arquitectura híbrida: SQLite local (alta velocidad offline) + PostgreSQL nube."],
        ["Fecha de Publicación", "Octubre 2026 | Edición Final para Exposición"]
    ]
    agregar_tabla_datos(doc, ["METADATO", "DETALLE DE LA VERSIÓN"], datos_portada, [Inches(2.2), Inches(4.3)])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # ÍNDICE GENERAL Y GUÍA DE LECTURA RÁPIDA
    # -------------------------------------------------------------------------
    h1 = doc.add_heading("Índice General y Metodología de la Guía", level=1)
    h1.paragraph_format.space_before = Pt(10)
    h1.paragraph_format.space_after = Pt(8)

    p_ind = doc.add_paragraph(
        "Esta guía fue diseñada con una estructura de doble propósito: servir como manual de uso inmediato "
        "(para que cualquier persona aprenda a operar el sistema en minutos) y como libreto o guion de exposición profesional "
        "(para que puedas presentar el proyecto ante un jurado, clientes o profesores explicando con soltura cada función)."
    )
    p_ind.paragraph_format.space_after = Pt(8)

    contenido_indice = [
        ["Módulo 0", "Acceso al Sistema (Login, Seguridad PBKDF2 y Roles de Usuario)", "Pág. 3"],
        ["Módulo 1", "Panel Principal (Dashboard) y Métricas en Tiempo Real de SQLite", "Pág. 4"],
        ["Módulo 2", "Inventario de Hardware y Generador de Código SKU Inteligente", "Pág. 5"],
        ["Módulo 3", "Asistente Inteligente de Reposición y Compras Basado en Demanda", "Pág. 7"],
        ["Módulo 4", "Control de Movimientos de Stock (Kardex, Entradas y Mermas)", "Pág. 9"],
        ["Módulo 5", "Directorio Unificado de Clientes y Proveedores Mayoristas", "Pág. 11"],
        ["Módulo 6", "Punto de Venta (POS), Descuentos y Comprobantes PDF con ReportLab", "Pág. 12"],
        ["Módulo 7", "Reportes Avanzados por Fechas y Exportación a Microsoft Excel (.xlsx)", "Pág. 14"],
        ["Módulo 8", "Gestión de Usuarios, Control de Accesos y Matriz de Permisos", "Pág. 15"],
        ["Módulo 9", "Arquitectura Híbrida y Sincronización en la Nube (PostgreSQL)", "Pág. 16"],
        ["Pitch Final", "Guion Maestro de Exposición en 5 Minutos y Preguntas Típicas del Jurado", "Pág. 17"]
    ]
    agregar_tabla_datos(doc, ["SECCIÓN", "CONTENIDO TEMÁTICO", "REFERENCIA"], contenido_indice, [Inches(1.2), Inches(4.3), Inches(1.0)])

    agregar_caja_destacada(doc, "CÓMO UTILIZAR ESTE DOCUMENTO", [
        "1. Bloques 'DATOS PARA COPIAR Y PEGAR': Contienen valores exactos (código, nombre, precios, cantidades) listos para pegar en los campos del software y probarlos de inmediato sin perder tiempo inventando datos.",
        "2. Bloques 'GUION DE EXPOSICIÓN': Contienen párrafos redactados en primera persona con las palabras exactas que debes pronunciar al exponer cada pantalla para sonar seguro, claro y profesional frente a tu audiencia.",
        "3. Capturas de pantalla: Muestran exactamente cómo luce la interfaz con datos cargados para que te ubiques al instante."
    ], tipo="tip")

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # MÓDULO 0: LOGIN Y ROLES
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 0: Inicio de Sesión y Matriz de Roles", level=1)
    
    doc.add_paragraph(
        "El acceso a TechStore está protegido mediante autenticación criptográfica. Las contraseñas nunca se almacenan "
        "en texto plano; se utiliza PBKDF2-HMAC-SHA256 con 100,000 iteraciones y una sal (salt) aleatoria de 16 bytes "
        "por cada usuario, cumpliendo con los estándares internacionales de ciberseguridad."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/01_login.png", "Pantalla de Inicio de Sesión (Login) con separación de roles.")

    agregar_caja_destacada(doc, "CREDENCIALES LISTAS PARA PROBAR EN EL LOGIN", [
        "• Administrador (Acceso Total): Usuario: 'admin' | Contraseña: 'admin123'",
        "• Vendedor (Punto de Venta / Costos Ocultos): Usuario: 'vendedor' | Contraseña: 'ven123'"
    ], tipo="ejemplo")

    agregar_caja_destacada(doc, "¿CÓMO EXPLICAR ESTA PANTALLA EN TU EXPOSICIÓN?", [
        "\"Buenos días jurado/profesor. Iniciamos en la pantalla de acceso seguro de TechStore. Aquí destacamos dos aspectos fundamentales: primero, la seguridad robusta mediante contraseñas hasheadas con PBKDF2 y salt individual, lo que impide que cualquier atacante que intercepte la base de datos pueda descifrarlas; y segundo, la separación estricta de roles: el Administrador tiene control gerencial de inventarios, costos y usuarios, mientras que el rol de Vendedor está diseñado para cobrar con rapidez, teniendo bloqueada la visibilidad de los costos de compra y la eliminación de productos para proteger el negocio.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 1: DASHBOARD
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 1: Panel Principal (Dashboard Ejecutivo)", level=1)
    
    doc.add_paragraph(
        "Al iniciar sesión, el sistema muestra el Panel Principal con cuatro tarjetas métricas calculadas en tiempo "
        "real desde SQLite y accesos directos hacia los módulos operativos."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/02_dashboard.png", "Dashboard Ejecutivo con métricas en tiempo real y accesos rápidos.")

    filas_dashboard = [
        ["VENTAS DEL DÍA", "Muestra el importe en Soles (S/) acumulado de las ventas del día y el conteo de comprobantes emitidos."],
        ["PRODUCTOS ACTIVOS", "Cantidad total de componentes de cómputo vigentes en el catálogo."],
        ["ALERTA STOCK BAJO", "Número de productos con existencias iguales o menores a su stock mínimo. ¡Al hacer clic en esta tarjeta, se abre directamente el Asistente de Reposición!"],
        ["MODO HÍBRIDO (NUBE)", "Indica si la base de datos está en modo local offline o conectada a PostgreSQL, y cuántos registros están pendientes de sincronizar."]
    ]
    agregar_tabla_datos(doc, ["TARJETA KPI", "SIGNIFICADO Y UTILIDAD OPERATIVA"], filas_dashboard, [Inches(2.2), Inches(4.3)])

    agregar_caja_destacada(doc, "¿QUÉ DECIR AL PRESENTAR EL DASHBOARD?", [
        "\"Al ingresar al sistema, lo primero que visualiza el gerente es el Dashboard en tiempo real. No requerimos botones de 'refrescar': cada venta o entrada de mercadería actualiza automáticamente estas cuatro tarjetas métricas. Lo más valioso para la tienda es la tarjeta de 'Alerta Stock Bajo', que identifica al instante los componentes en nivel crítico. Noten además que la tarjeta es interactiva: con solo hacer un clic sobre ella, el sistema nos abre directamente el Asistente Inteligente de Reposición.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 2: INVENTARIO Y SKU INTELIGENTE
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 2: Inventario y Generador de Código SKU Inteligente", level=1)
    
    doc.add_paragraph(
        "El módulo de Inventario centraliza el catálogo de hardware. Permite registrar nuevos componentes, actualizar precios, "
        "modificar stock y desactivar artículos mediante borrado lógico (conservando el historial de ventas y kardex)."
    )

    doc.add_paragraph(
        "Innovación central - Código SKU Inteligente:\n"
        "El sistema genera automáticamente códigos nemotécnicos en formato [CAT]-[MAR]-[001] analizando la categoría y la marca. "
        "Por ejemplo, para Laptops y Equipos de marca Lenovo, propone automáticamente 'LAP-LEN-001', o el siguiente correlativo "
        "libre ('LAP-LEN-002', etc.), comprobando en toda la base de datos que no exista duplicidad."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/03_inventario_productos.png", "Inventario con botón '⚡ Sugerir SKU' y botón '💡 Asistente de Reposición'.")

    # Tabla Copiar y Pegar para Inventario
    filas_ej_producto = [
        ["Código / SKU *", "LAP-LEN-001", "Presiona el botón '⚡ Sugerir SKU' o escribe este código. El sistema verifica que sea único."],
        ["Nombre del Producto *", "Laptop Lenovo Legion Pro 5 16\" WQXGA", "Nombre comercial y modelo exacto del equipo."],
        ["Categoría *", "Laptops y Equipos", "Selecciona del menú desplegable."],
        ["Proveedor Preferido", "20100123456 - Deltron Importaciones S.A.", "Mayorista principal al que se le compra este modelo."],
        ["Marca / Fabricante", "Lenovo", "Marca del fabricante (genera el prefijo nemotécnico)."],
        ["Precio de Compra (S/) *", "5200.00", "Costo unitario mayorista de adquisición (solo visible para admin)."],
        ["Precio de Venta (S/) *", "6150.00", "Precio al público para boleta o factura."],
        ["Stock Actual *", "8", "Existencias físicas iniciales en almacén."],
        ["Stock Mínimo (Alerta) *", "2", "Límite de seguridad. Si el stock llega a 2 o menos, se activa la alerta."],
        ["Descripción", "Intel Core i7-13700HX, 16GB RAM DDR5, SSD 1TB NVMe, RTX 4060 8GB", "Ficha técnica del equipo."]
    ]
    agregar_tabla_datos(doc, ["CAMPO A LLENAR", "VALOR PARA COPIAR Y PEGAR", "EXPLICACIÓN RÁPIDA"], filas_ej_producto, [Inches(1.8), Inches(2.2), Inches(2.5)])

    agregar_caja_destacada(doc, "DEMOSTRACIÓN EN VIVO DEL SKU INTELIGENTE", [
        "1. Selecciona la categoría 'Laptops y Equipos'.",
        "2. En el campo 'Marca / Fabricante', escribe 'Lenovo'.",
        "3. Observa cómo el campo de código se llena automáticamente con 'LAP-LEN-001' (o el siguiente correlativo libre).",
        "4. Si borras el código y presionas el botón '⚡ Sugerir SKU', el sistema lo recalcula al instante.",
        "5. Intento de duplicado: Si intentas registrar un producto con un código que ya existe, el sistema te muestra un mensaje amigable avisándote del código repetido y sugiriéndote usar el botón 'Sugerir SKU'."
    ], tipo="ejemplo")

    agregar_caja_destacada(doc, "¿QUÉ DECIR AL EXPONER EL MÓDULO DE INVENTARIO?", [
        "\"Uno de los problemas más graves en una tienda de tecnología es el desorden en los códigos de producto. Como pueden observar en pantalla, en TechStore implementamos un generador de SKU inteligente. Cuando seleccionamos la categoría 'Laptops y Equipos' y la marca 'Lenovo', el sistema interpreta automáticamente las 3 letras de categoría 'LAP' y las 3 letras de marca 'LEN', y busca en la base de datos el último correlativo registrado para sugerir 'LAP-LEN-001'. Si ese código ya estuviera en uso, el sistema avanza automáticamente a 'LAP-LEN-002'. Esto elimina al 100% los códigos duplicados y agiliza la labor del encargado de almacén.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 3: ASISTENTE DE REPOSICIÓN
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 3: Asistente Inteligente de Reposición y Compras", level=1)
    
    doc.add_paragraph(
        "El Asistente Inteligente de Reposición es la herramienta analítica estrella de TechStore. "
        "En lugar de ser un simple listado de alertas estáticas, aplica un modelo de cálculo de inventarios que "
        "evalúa las existencias físicas actuales frente a las ventas reales de los últimos 30 días, "
        "calculando la demanda diaria promedio (unidades/día) y los días de autonomía de stock antes del desabastecimiento."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/04_asistente_reposicion.png", "Asistente Inteligente con KPIs ejecutivos, justificación detallada y exportación a Excel.")

    filas_urgencias = [
        ["🔴 CRÍTICO", "Stock = 0", "Agotamiento total. Quiebre de stock activo en tienda."],
        ["🟠 URGENTE", "Stock <= Mínimo / 2 o Autonomía <= 3 días", "Quedan menos de la mitad del mínimo o se agotará en menos de 72 horas."],
        ["🟡 ALERTA", "Stock <= Stock Mínimo", "Alcanzó el nivel de seguridad de reserva establecido."],
        ["🔵 PREVENTIVO", "Stock > Mínimo pero Autonomía <= 7 días", "Hay stock disponible pero su alta rotación de ventas causará desabastecimiento pronto."]
    ]
    agregar_tabla_datos(doc, ["NIVEL", "CRITERIO DE CÁLCULO", "DESCRIPCIÓN DEL ESTADO"], filas_urgencias, [Inches(1.5), Inches(2.3), Inches(2.7)])

    agregar_caja_destacada(doc, "EJEMPLO REAL DEL ANÁLISIS CALCULADO POR EL ASISTENTE", [
        "• Componente en evaluación: RAM DDR5 32GB 6000MHz (Código: RAM-TEST-001)",
        "• Existencias actuales: 1 unidad | Stock mínimo de reserva: 2 unidades",
        "• Historial de ventas: 2 unidades vendidas en los últimos 30 días (Ritmo: 0.07 un/día).",
        "• Autonomía estimada: ~14.3 días antes de quedarse en 0.",
        "• Recomendación del sistema: Comprar 4 unidades al proveedor Deltron Importaciones S.A.",
        "• Presupuesto requerido: S/ 1,520.00 (calculado a precio mayorista de compra).",
        "• Justificación mostrada en pantalla: 'Stock actual de 1 un. con ventas de 2 un. en los últimos 30 días. Se recomienda adquirir 4 un. para asegurar una cobertura de 30 días y salvaguardar el stock mínimo (2 un.).'"
    ], tipo="ejemplo")

    agregar_caja_destacada(doc, "¿CÓMO EXPLICAR EL ASISTENTE DE REPOSICIÓN ANTE EL JURADO?", [
        "\"Esta pantalla representa una de las mayores ventajas competitivas de TechStore. En los sistemas tradicionales, el software solo te avisa con un número en rojo cuando ya no hay stock. En TechStore fuimos mucho más allá: construimos un Asistente Inteligente de Compras. El sistema analiza las ventas registradas en los últimos 30 días, calcula la velocidad diaria de rotación de cada producto y determina cuántos días de autonomía nos quedan. Además, según el horizonte de cobertura que elijamos —por ejemplo 30 o 45 días—, nos calcula con precisión matemática cuántas unidades debemos comprarle a cada mayorista y qué presupuesto de inversión en Soles necesitamos. Y fíjense en la usabilidad: con solo presionar el botón 'Registrar Entrada de Mercadería', el sistema nos traslada a la pestaña de Kardex con el producto, el proveedor y la cantidad ya precargados, listos para confirmar.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 4: MOVIMIENTOS Y KARDEX
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 4: Movimientos de Stock y Kardex de Auditoría", level=1)
    
    doc.add_paragraph(
        "Cada ingreso o salida de mercadería queda auditado en el Kardex con fecha, hora, tipo de movimiento, "
        "producto, cantidad, motivo, proveedor y usuario que ejecutó la operación. El stock se actualiza inmediatamente en SQLite."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/05_movimientos_kardex.png", "Módulo de Kardex con formulario de entrada/ajuste e historial detallado.")

    filas_ej_kardex = [
        ["Tipo de Operación *", "📥 Entrada de Mercadería (Proveedor)", "Selecciona 'Entrada' para recepción de compras."],
        ["Producto / Componente *", "Seleccionar de la lista desplegable", "Muestra el stock actual y mínimo del producto."],
        ["Proveedor Mayorista *", "20100123456 - Deltron Importaciones S.A.", "Distribuidor mayorista que despacha la orden."],
        ["Cantidad de Unidades *", "10", "Número de piezas ingresadas físicamente a almacén."],
        ["Motivo del Movimiento *", "Recepción de reposición por stock mínimo", "Justificación comercial de la operación."],
        ["N° Factura / Guía / Nota", "Factura F001-0049210", "Documento tributario de referencia."]
    ]
    agregar_tabla_datos(doc, ["CAMPO KARDEX", "VALOR DE EJEMPLO PARA COPIAR", "OBSERVACIÓN"], filas_ej_kardex, [Inches(1.8), Inches(2.5), Inches(2.2)])

    agregar_caja_destacada(doc, "¿QUÉ DECIR AL EXPONER EL MÓDULO DE KARDEX?", [
        "\"El módulo de Movimientos de Stock garantiza la auditoría integral de la mercadería. Manejamos dos tipos de operaciones: Entradas de mercadería asociadas obligatoriamente a un proveedor mayorista con su factura o guía de remisión; y Ajustes por pérdida o daño físico, donde un técnico puede justificar, por ejemplo, una memoria RAM dañada. Cada fila del historial registra quién hizo el movimiento y a qué hora exacta, garantizando que no existan descuadres de inventario.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 5: CONTACTOS
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 5: Directorio Unificado de Clientes y Proveedores", level=1)
    
    doc.add_paragraph(
        "Centraliza los datos de los clientes (DNI/RUC, teléfono, dirección, correo) y de los proveedores mayoristas "
        "en dos pestañas dedicadas, facilitando la emisión de comprobantes y las órdenes de compra."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/06_contactos.png", "Directorio unificado de Clientes y Proveedores Mayoristas.")

    filas_contactos = [
        ["Cliente Nuevo", "DNI", "48192033", "María Elena Ramos Quispe", "987654321", "m.ramos@empresa.com", "Av. Arequipa 2450, Lince"],
        ["Proveedor Nuevo", "RUC", "20556677889", "Tech Wholesale Perú S.A.C.", "01-6543210", "ventas@techwholesale.local", "Av. Nicolás de Piérola 1280"]
    ]
    agregar_tabla_datos(doc, ["TIPO", "DOC", "NÚMERO", "NOMBRE / RAZÓN SOCIAL", "TELÉFONO", "EMAIL", "DIRECCIÓN"], filas_contactos)

    agregar_caja_destacada(doc, "¿QUÉ DECIR EN LA PRESENTACIÓN DE CONTACTOS?", [
        "\"En el módulo de Contactos manejamos la base de datos de compradores y mayoristas. Contamos además con un cliente por defecto llamado 'Público General / Venta Rápida' con DNI '00000000', lo que permite a los cajeros atender clientes de mostrador al paso en menos de 5 segundos sin obligarlos a registrar todos sus datos.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 6: PUNTO DE VENTA (POS)
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 6: Punto de Venta (POS) y Facturación", level=1)
    
    doc.add_paragraph(
        "El Punto de Venta está optimizado para cobrar con rapidez y seguridad transaccional. "
        "Posee validación estricta de stock en tiempo real y protección mediante reversión atómica (Rollback): "
        "si se intenta vender más unidades de las existentes o se interrumpe la operación, no se descuenta ningún producto "
        "y el inventario se conserva intacto."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/07_punto_venta_pos.png", "Punto de Venta (POS) con carrito dinámico, descuentos y emisión de boleta/factura.")

    filas_pos = [
        ["Cliente *", "Público General / Venta Rápida", "Permite venta rápida o seleccionar cliente con DNI/RUC."],
        ["Comprobante *", "Boleta (o Factura)", "Genera el correlativo siguiente (ej: B-000008 o F-000008)."],
        ["Método de Pago *", "Billetera Digital (Yape/Plin)", "Opciones: Efectivo, Tarjeta, Transferencia, Yape/Plin."],
        ["Producto", "Seleccionar de la lista desplegable", "Indica el stock disponible en almacén."],
        ["Cantidad", "1", "Se agrega al carrito interactivo."],
        ["Descuento", "Tipo: MONTO | Valor: 20.00", "Permite rebaja fija en Soles o porcentaje (%). Valida que no supere el total ni el 100%."]
    ]
    agregar_tabla_datos(doc, ["CAMPO DEL POS", "VALOR DE EJEMPLO", "COMPORTAMIENTO DEL SISTEMA"], filas_pos, [Inches(1.8), Inches(2.4), Inches(2.3)])

    agregar_caja_destacada(doc, "¿QUÉ DECIR AL EXPONER EL PUNTO DE VENTA?", [
        "\"Pasamos ahora al corazón operativo de la tienda: el Punto de Venta. Aquí la prioridad es la seguridad y la velocidad. Seleccionamos el cliente, el tipo de comprobante y el método de pago. Agregamos los componentes al carrito y aplicamos descuentos de ser necesario. Pero quiero que noten esta validación de seguridad: si un cajero intenta vender más unidades de las que hay físicamente en almacén, el sistema bloquea inmediatamente la venta y ejecuta un Rollback automático en SQLite. Al confirmar la venta, en una sola fracción de segundo el sistema descuenta el stock de almacén, registra la salida en el Kardex y genera automáticamente la Boleta o Factura en PDF profesional utilizando ReportLab.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 7: REPORTES Y EXCEL
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 7: Reportes Gerenciales y Exportación a Excel", level=1)
    
    doc.add_paragraph(
        "Permite filtrar ventas por cualquier rango de fechas con validación estricta de formato AAAA-MM-DD "
        "y exportar reportes ejecutivos en formato nativo de Microsoft Excel (.xlsx) generados con openpyxl."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/08_reportes_excel.png", "Módulo de Reportes con métricas consolidadas y botones de exportación a Excel.")

    agregar_caja_destacada(doc, "EJEMPLO DE FILTRO POR FECHAS PARA COPIAR", [
        "• Fecha Inicio: 2026-10-01",
        "• Fecha Fin: 2026-10-28 (o la fecha del día actual)",
        "• Al presionar 'Filtrar por Fechas', se recalculan los 4 indicadores: Total Recaudado, Cantidad de Ventas, Descuentos Totales y Ticket Promedio.",
        "• Botón 'Exportar Inventario a Excel': Genera la lista valorizada completa con celdas resaltadas en rojo para stock crítico.",
        "• Botón 'Exportar Ventas a Excel': Genera una planilla detallada ítem por ítem con subtotales, descuentos y fórmulas de totales."
    ], tipo="ejemplo")

    agregar_caja_destacada(doc, "¿QUÉ DECIR EN LA SECCIÓN DE REPORTES?", [
        "\"Para la toma de decisiones gerenciales, el módulo de Reportes consolida la facturación, los descuentos concedidos y el ticket promedio por cliente. Lo más potente es la exportación a Excel: con un solo clic generamos hojas de cálculo limpias, con colores corporativos, formatos de moneda y fórmulas automáticas, listas para ser enviadas a contabilidad o a gerencia general.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 8: USUARIOS Y PERMISOS (VERSIÓN MEJORADA)
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 8: Gestión de Usuarios y Matriz de Roles (Versión Mejorada)", level=1)
    
    doc.add_paragraph(
        "Disponible únicamente para usuarios con rol de Administrador. Este módulo ha sido completamente renovado para "
        "hacer la gestión de personal intuitiva, asistida y libre de confusiones para cualquier persona que nunca haya utilizado "
        "un sistema de inventario."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/09_usuarios.png", "Gestión de Usuarios con sugerencia de login, contraseñas, tarjeta de permisos y tabla interactiva.")

    filas_permisos = [
        ["Acceso al Punto de Venta (POS) y cobro", "✔ Sí permitido (Total)", "✔ Sí permitido (Total)"],
        ["Consulta de Catálogo de Hardware y Stock", "✔ Sí permitido (Total)", "✔ Sí permitido (Total)"],
        ["Ver Precios de Compra (Costos Mayoristas)", "✔ Visible y editable", "❌ OCULTO Y BLOQUEADO (Protegido)"],
        ["Modificar o Desactivar Productos", "✔ Sí permitido", "❌ BLOQUEADO (Protegido)"],
        ["Gestión y Creación de Otros Usuarios", "✔ Sí permitido", "❌ PESTAÑA OCULTA"],
        ["Ver Reportes Financieros y Ganancias", "✔ Sí permitido", "❌ PESTAÑA OCULTA"],
        ["Acceso al Asistente de Reposición", "✔ Sí permitido", "✔ Sí permitido"]
    ]
    agregar_tabla_datos(doc, ["ACCIONES / PERMISOS DEL SISTEMA", "ROL ADMINISTRADOR", "ROL VENDEDOR"], filas_permisos, [Inches(3.1), Inches(1.7), Inches(1.7)])

    agregar_caja_destacada(doc, "NUEVAS FACILIDADES INTELIGENTES EN EL FORMULARIO", [
        "• Botón '⚡ Sugerir Login': Al escribir el nombre del empleado (ej. 'Carlos Mendoza Flores'), el sistema genera automáticamente un nombre de usuario limpio (ej. 'cmendoza') comprobando que no exista en la base de datos.",
        "• Botón '🎲 Clave': Genera una contraseña temporal segura y fácil de recordar (ej. 'Tech2026!') para entregar al nuevo colaborador en su primer día.",
        "• Botón '👁': Permite visualizar la contraseña para verificar que esté bien escrita sin errores de tipeo.",
        "• Tarjeta Dinámica de Permisos: Al cambiar el rol a 'Vendedor', la tarjeta explica en tiempo real que los costos de compra mayoristas están ocultos para proteger las utilidades de la tienda.",
        "• Ordenamiento de Tabla: Haz clic sobre ID, Usuario, Nombre Completo, Rol, Estado o Fecha para ordenar en orden ascendente (▲) o descendente (▼).",
        "• Buscador y Filtros: Campo de búsqueda en vivo y filtros por Rol (Administrador/Vendedor) y Estado (Activos/Desactivados).",
        "• Botón '🔄 Reactivar Usuario': Permite recuperar empleados suspendidos con un solo clic. El Administrador Principal ID 1 se encuentra 100% blindado contra desactivaciones accidentales."
    ], tipo="ejemplo")

    agregar_caja_destacada(doc, "¿QUÉ DECIR AL EXPONER LA GESTIÓN DE USUARIOS?", [
        "\"En la gestión de usuarios implementamos una de las mejoras más solicitadas: hacerla intuitiva para quienes nunca han usado un sistema de inventario. "
        "Primero, agregamos asistentes automáticos: al escribir el nombre del empleado, el botón '⚡ Sugerir Login' genera un usuario único libre de duplicados, y el botón '🎲 Clave' propone una contraseña segura temporal. "
        "Segundo, la Tarjeta Dinámica de Permisos: al seleccionar el rol 'Vendedor', el sistema le explica al usuario en lenguaje humano qué puede hacer (vender y consultar stock) y qué tiene protegido (los costos de compra de las computadoras y las ganancias están ocultos). "
        "Y tercero, el orden total: la tabla permite ordenar por cualquier columna haciendo clic en su cabecera (▲/▼), filtrar en tiempo real por búsqueda o estado, y reactivar cuentas suspendidas con un solo clic, manteniendo siempre blindado al Administrador principal ID 1.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # MÓDULO 9: CONEXIÓN Y RESPALDO HÍBRIDO EN LA NUBE (NUEVO)
    # -------------------------------------------------------------------------
    doc.add_heading("Módulo 9: Conexión y Respaldo Híbrido en la Nube (PostgreSQL)", level=1)
    
    doc.add_paragraph(
        "Permite operar con arquitectura híbrida: velocidad local instantánea en SQLite y sincronización central en PostgreSQL. "
        "La interfaz ha sido rediseñada para ofrecer máxima claridad y facilidad de conexión sin necesidad de conocimientos técnicos."
    )

    agregar_captura_con_epigrafe(doc, "capturas_guia/10_config_nube.png", "Configuración de Nube con asistente de URL directa, semáforo en vivo y sincronización.")

    agregar_caja_destacada(doc, "CARACTERÍSTICAS DEL ASISTENTE Y SEMÁFORO DE NUBE", [
        "• Asistente '⚡ Desglosar URL': Permite pegar el enlace directo ('Connection String' de Neon.tech, Supabase o Render) y desglosa automáticamente servidor, puerto, base de datos, usuario, contraseña y modo SSL.",
        "• Semáforo de Estado en Tiempo Real: Indica con claridad 🟢 Modo En Línea (PostgreSQL Nube), 🟡 Modo Local (Offline) o ⚪ Nube No Configurada.",
        "• Contador de Pendientes: Informa con precisión cuántos registros locales faltan por sincronizar.",
        "• Diagnósticos Amigables: Traduce errores de red a explicaciones claras en español (verificar internet, revisar espacios en contraseñas o activar SSL 'require').",
        "• Botón '🔄 Sincronizar Ahora': Permite ejecutar la sincronización y verificar el resultado inmediatamente sin tener que cerrar la ventana.",
        "• Arquitectura 100% Offline-First: Si en la tienda se corta el internet o la luz, la tienda no se detiene; sigue facturando en local y cuando vuelve la red, se sincroniza con 1 clic sin duplicados mediante UUIDs."
    ], tipo="ejemplo")

    agregar_caja_destacada(doc, "¿QUÉ DECIR AL EXPONER LA CONEXIÓN EN LA NUBE?", [
        "\"Finalizamos con nuestra arquitectura de Continuidad Operativa: el Modo Híbrido SQLite + PostgreSQL en la nube. "
        "Para que conectar la nube no sea complicado, añadimos el 'Asistente de Pegado de URL': si el dueño crea una base de datos gratuita en Neon.tech o Supabase, solo pega su enlace de conexión y presiona '⚡ Desglosar URL'. El sistema extrae servidor, puerto, base de datos y usuario automáticamente. "
        "El semáforo visual muestra si estamos en línea o en modo local. "
        "¿Y cuál es la mayor ventaja para el negocio? Si en la tienda se corta el internet o la luz, la tienda no se detiene: sigue vendiendo normalmente en SQLite local. Y cuando regresa el internet, presionamos 'Sincronizar' y todo sube a la nube sin duplicados gracias a nuestros identificadores globales UUID.\""
    ], tipo="guion")

    # -------------------------------------------------------------------------
    # SECCIÓN FINAL: GUION DE EXPOSICIÓN ORAL (PITCH DE 5 MINUTOS)
    # -------------------------------------------------------------------------
    doc.add_page_break()
    doc.add_heading("Guion Maestro de Exposición Oral (Pitch de 5 Minutos)", level=1)

    doc.add_paragraph(
        "Utiliza este guion cronometrado para tu presentación final. Está redactado en lenguaje claro y estructurado "
        "para captar la atención del jurado y demostrar la solidez técnica y de negocio del proyecto."
    )

    filas_pitch = [
        ["Minuto 1: Introducción de Impacto", 
         "\"Buenos días jurado y profesores. Hoy presentamos TechStore, un sistema especializado para tiendas de hardware y computación. Gestionar tecnología es complejo: los componentes son costosos, tienen múltiples marcas y un quiebre de stock significa perder ventas de miles de Soles. TechStore resuelve esto combinando alta velocidad local offline con SQLite, seguridad criptográfica y un motor analítico de inventarios.\""],
        
        ["Minuto 2: Inventario y SKU Inteligente", 
         "\"En el módulo de Inventario mostramos nuestra primera innovación: el generador de Código SKU Inteligente. Al registrar una laptop Lenovo, el sistema propone de forma automática 'LAP-LEN-001' y comprueba en toda la base de datos que el código no esté repetido. Esto estandariza el almacén y previene errores humanos de digitación.\""],
        
        ["Minuto 3: La Joya: Asistente de Reposición", 
         "\"Aquí está la joya de nuestro sistema: el Asistente Inteligente de Reposición. A diferencia de otros sistemas que solo pintan números en rojo, TechStore analiza el histórico de ventas de los últimos 30 días, calcula la demanda diaria y nos dice cuántos días de stock nos quedan. Además, según la cobertura que deseemos, calcula exactamente cuántas unidades comprar y cuánto presupuesto requerimos, enlazándonos directamente con el proveedor mayorista y el Kardex.\""],
        
        ["Minuto 4: Venta en POS y Transacción Segura", 
         "\"En el Punto de Venta demostramos la rapidez comercial. Agregamos artículos, aplicamos descuentos y validamos el stock en tiempo real. Si alguien intenta vender más piezas de las existentes, el sistema bloquea la venta mediante Rollback transaccional. Al cobrar, se descuenta el stock de inmediato y se genera el comprobante en PDF con ReportLab.\""],
        
        ["Minuto 5: Usuarios, Nube Híbrida y Cierre", 
         "\"En Usuarios y Nube destacamos la usabilidad para principiantes: generador automático de login y contraseñas, tarjeta de permisos donde el vendedor tiene ocultos los costos de compra, y un asistente para conectar PostgreSQL en la nube con un solo enlace. Si se corta el internet, la tienda sigue vendiendo en local sin detenerse. TechStore es una solución robusta, segura y lista para producción. Muchas gracias, quedamos atentos a sus preguntas.\""],
    ]
    agregar_tabla_datos(doc, ["TIEMPO ESTIMADO", "GUION EXACTO A PRONUNCIAR"], filas_pitch, [Inches(1.8), Inches(4.7)])

    # Preguntas frecuentes del jurado
    doc.add_heading("Banco de Preguntas Típicas del Jurado y Respuestas Infalibles", level=2)
    
    filas_preguntas = [
        ["1. ¿Qué pasa si la tienda se queda sin conexión a internet?", 
         "El sistema funciona al 100% offline gracias a SQLite local. Las ventas, movimientos y alertas siguen operando sin interrupción. Cuando vuelve la conexión, el servicio de sincronización híbrido sube los cambios pendientes a PostgreSQL sin duplicados mediante UUIDs."],
        
        ["2. ¿Cómo garantizan que el código SKU no se repita nunca?", 
         "Mediante una doble capa: primero, la función 'generar_sku_sugerido' busca el número más alto y verifica disponibilidad con 'es_codigo_disponible'; y segundo, la columna 'codigo' en la tabla productos tiene restricción UNIQUE en SQLite."],
        
        ["3. ¿Por qué el Asistente de Reposición es mejor que una simple alerta?", 
         "Porque una alerta estática solo te avisa cuando el daño está hecho. Nuestro Asistente evalúa la velocidad de rotación diaria (Ventas 30d / 30), calcula los días de autonomía restante y determina cuántas piezas comprar para 15, 30 o 60 días según la demanda habitual."],
        
        ["4. ¿Cómo evitan que los cajeros vendan productos que no hay en almacén?", 
         "A través de validación atómica en VentaModel. Antes de insertar la cabecera, se verifica el stock de cada ítem con SELECT. Si cualquiera no alcanza, se ejecuta un conn.rollback() y se cancela la transacción entera."],
        
        ["5. ¿Qué sucede si un administrador desactiva un producto o cliente?", 
         "Aplicamos Borrado Lógico (activo = 0). El registro desaparece de los selectores de venta, pero su historial en compras, ventas pasadas y Kardex permanece 100% intacto para auditoría tributaria y contable."],

        ["6. ¿Por qué es seguro el almacenamiento de contraseñas en TechStore?", 
         "Porque utilizamos PBKDF2-HMAC-SHA256 con 100,000 rondas de derivación y una sal criptográfica individual de 16 bytes. Esto neutraliza ataques de tablas Rainbow y fuerza bruta."],

        ["7. ¿Cómo protegieron los costos mayoristas frente al personal de ventas?", 
         "Mediante separación estricta de permisos. Cuando un usuario inicia sesión con rol 'vendedor', el software oculta los precios de compra, bloquea reportes de ganancias y desactiva la gestión de usuarios."],

        ["8. ¿Cómo facilitaron la configuración en la nube para principiantes?", 
         "Creamos el Asistente de Desglose de URL: el usuario solo pega el enlace 'postgresql://...' de Neon o Supabase y el sistema extrae automáticamente servidor, puerto, base de datos y usuario sin errores."]
    ]
    agregar_tabla_datos(doc, ["PREGUNTA POSIBLE DEL JURADO", "RESPUESTA TÉCNICA Y DE NEGOCIO"], filas_preguntas, [Inches(2.2), Inches(4.3)])

    # Guardar documento
    nombre_archivo = "Manual_de_Usuario_y_Guion_TechStore.docx"
    doc.save(nombre_archivo)
    print(f"[OK] Documento Word generado con éxito: {os.path.abspath(nombre_archivo)}")
    return os.path.abspath(nombre_archivo)

if __name__ == "__main__":
    construir_documento()

