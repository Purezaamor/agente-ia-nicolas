import os
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain.tools import tool

DB_CONFIG = {
    "host": "localhost",
    "database": "agro_db",
    "user": "postgres",
    "password": "Macaco2010",
    "port": 5432,
}

def get_conn():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@tool
def registrar_campo_o_lote(establecimiento: str, renspa: str = "", nombre_lote: str = "", hectareas: float = 0, cultivo: str = "", campana: str = "", estado: str = "") -> str:
    """Registra o actualiza un establecimiento y opcionalmente un lote dentro de él."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO establecimientos (nombre, renspa)
        VALUES (%s, %s)
        ON CONFLICT (nombre) DO UPDATE SET renspa = COALESCE(NULLIF(%s, ''), establecimientos.renspa)
        RETURNING id;
    """, (establecimiento.strip(), renspa, renspa))
    est_id = cur.fetchone()["id"]

    if nombre_lote:
        cur.execute("""
            INSERT INTO lotes (establecimiento_id, nombre_lote, hectareas, cultivo_actual, campana, estado)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (est_id, nombre_lote.strip(), hectareas, cultivo, campana, estado))
    conn.commit()
    cur.close()
    conn.close()
    return f"Guardado correctamente: Establecimiento '{establecimiento}'" + (f" - Lote '{nombre_lote}' ({hectareas} ha, {cultivo})." if nombre_lote else ".")

@tool
def consultar_campos_y_lotes() -> str:
    """Consulta todos los establecimientos y lotes cargados en la base de datos."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.nombre AS establecimiento, e.renspa, l.nombre_lote, l.hectareas, l.cultivo_actual, l.campana, l.estado
        FROM establecimientos e
        LEFT JOIN lotes l ON e.id = l.establecimiento_id
        ORDER BY e.nombre, l.nombre_lote;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return "No hay establecimientos ni lotes cargados todavía."
    return str([dict(r) for r in rows])

@tool
def registrar_movimiento_hacienda(establecimiento: str, tipo_movimiento: str, categoria: str, cantidad: int, dte_numero: str = "", origen_destino: str = "", observaciones: str = "") -> str:
    """Registra un movimiento de hacienda. tipo_movimiento debe ser: INGRESO, EGRESO, NACIMIENTO o MORTANDAD."""
    tipo = tipo_movimiento.upper()
    if tipo not in ["INGRESO", "EGRESO", "NACIMIENTO", "MORTANDAD"]:
        return "Error: tipo_movimiento debe ser INGRESO, EGRESO, NACIMIENTO o MORTANDAD."
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO hacienda_movimientos (establecimiento, tipo_movimiento, categoria, cantidad, dte_numero, origen_destino, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, (establecimiento.strip(), tipo, categoria.strip().capitalize(), cantidad, dte_numero, origen_destino, observaciones))
    conn.commit()
    cur.close()
    conn.close()
    return f"Movimiento registrado: {tipo} de {cantidad} {categoria} en {establecimiento}."

@tool
def consultar_stock_hacienda() -> str:
    """Calcula el stock actual exacto de hacienda por establecimiento y categoría."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT establecimiento, categoria,
               SUM(CASE WHEN tipo_movimiento IN ('INGRESO', 'NACIMIENTO') THEN cantidad ELSE -cantidad END) AS stock_actual
        FROM hacienda_movimientos
        GROUP BY establecimiento, categoria
        HAVING SUM(CASE WHEN tipo_movimiento IN ('INGRESO', 'NACIMIENTO') THEN cantidad ELSE -cantidad END) <> 0
        ORDER BY establecimiento, categoria;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return "No hay stock de hacienda registrado."
    return str([dict(r) for r in rows])

@tool
def registrar_movimiento_contable(tipo: str, rubro: str, descripcion: str, monto: float, moneda: str = "ARS", establecimiento: str = "") -> str:
    """Registra un INGRESO o EGRESO contable."""
    t = tipo.upper()
    if t not in ["INGRESO", "EGRESO"]:
        return "Error: tipo debe ser INGRESO o EGRESO."
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO contabilidad (tipo, rubro, descripcion, monto, moneda, establecimiento)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (t, rubro, descripcion, monto, moneda.upper(), establecimiento))
    conn.commit()
    cur.close()
    conn.close()
    return f"Asiento contable guardado: {t} | {rubro} | {moneda.upper()} {monto:,.2f} ({descripcion})."

@tool
def consultar_resumen_contable() -> str:
    """Devuelve los últimos movimientos contables y el balance total por moneda."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT moneda,
               SUM(CASE WHEN tipo = 'INGRESO' THEN monto ELSE 0 END) AS total_ingresos,
               SUM(CASE WHEN tipo = 'EGRESO' THEN monto ELSE 0 END) AS total_egresos,
               SUM(CASE WHEN tipo = 'INGRESO' THEN monto ELSE -monto END) AS saldo
        FROM contabilidad
        GROUP BY moneda;
    """)
    totales = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT fecha, tipo, rubro, descripcion, monto, moneda, establecimiento FROM contabilidad ORDER BY id DESC LIMIT 15;")
    ultimos = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    if not totales:
        return "No hay movimientos contables registrados."
    return f"TOTALES: {totales}\nÚLTIMOS MOVIMIENTOS: {ultimos}"