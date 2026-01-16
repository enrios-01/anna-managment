def calcular_insumos_totales(cursor, dni_evento):
    cursor.execute("SELECT (cantidad_adultos + cantidad_adolescentes + cantidad_menores) as total FROM eventos WHERE dni_cliente = %s", (dni_evento,))
    total_pax = cursor.fetchone()['total']
    
    sql = """
        SELECT i.nombre_insumo, SUM(i.cantidad_por_persona * %s) as total_necesario, i.unidad_medida
        FROM evento_seleccion_menu s
        JOIN ingredientes_plato i ON s.id_plato = i.id_plato
        WHERE s.dni_evento = %s
        GROUP BY i.nombre_insumo, i.unidad_medida
    """
    cursor.execute(sql, (total_pax, dni_evento))
    return cursor.fetchall()

def calcular_lista_compras(cursor, dni_evento):
    """Calcula kilos/unidades basándose en la regla de recepción del Excel."""
    sql = """
        SELECT r.insumo, 
               SUM(r.gramos_por_persona * (e.cantidad_adultos + (e.cantidad_adolescentes * 0.20))) as total_calculado
        FROM evento_menu em
        JOIN eventos e ON em.dni_evento = e.dni_cliente
        JOIN recetas r ON em.id_plato = r.id_plato
        WHERE e.dni_cliente = %s
        GROUP BY r.insumo
    """
    cursor.execute(sql, (dni_evento,))
    return cursor.fetchall()