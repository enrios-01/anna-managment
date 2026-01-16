# modulos/resumen.py

def obtener_ficha_completa(cursor, dni):
    # Traemos datos base del evento
    sql_evento = """SELECT *, DATE_FORMAT(fecha_evento, '%Y-%m-%d') as fecha_iso 
                    FROM eventos WHERE dni_cliente = %s"""
    cursor.execute(sql_evento, (dni,))
    evento = cursor.fetchone()
    
    if not evento: return None

    # Traemos platos ya seleccionados
    sql_menu = """SELECT p.id_plato, p.nombre_plato, p.categoria 
                  FROM seleccion_menus s
                  JOIN catalogo_platos p ON s.id_plato = p.id_plato
                  WHERE s.dni_cliente = %s"""
    cursor.execute(sql_menu, (dni,))
    evento['menu_elegido'] = cursor.fetchall()

    # Traemos historial de pagos
    sql_pagos = "SELECT * FROM pagos_cuotas WHERE dni_evento = %s ORDER BY fecha_pago DESC"
    cursor.execute(sql_pagos, (dni,))
    evento['historial_pagos'] = cursor.fetchall()

    return evento