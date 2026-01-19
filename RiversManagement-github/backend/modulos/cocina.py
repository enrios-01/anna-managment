# modulos/cocina.py

def calcular_insumos_totales(cursor, dni_evento):
    """Calcula la cantidad bruta de insumos basada en el total de personas."""
    try:
        # 1. Obtener la suma total de personas (Pax)
        # Se requiere el cursor con dictionary=True desde servidor.py
        cursor.execute("""
            SELECT (cantidad_adultos + cantidad_adolescentes + cantidad_menores) as total 
            FROM eventos WHERE dni_cliente = %s
        """, (dni_evento,))
        
        resultado = cursor.fetchone()
        if not resultado:
            return []
            
        total_pax = float(resultado['total'])
        
        # 2. Calcular insumos según el catálogo de ingredientes
        sql = """
            SELECT i.nombre_insumo, SUM(i.cantidad_por_persona * %s) as total_necesario, i.unidad_medida
            FROM evento_seleccion_menu s
            JOIN ingredientes_plato i ON s.id_plato = i.id_plato
            WHERE s.dni_evento = %s
            GROUP BY i.nombre_insumo, i.unidad_medida
        """
        cursor.execute(sql, (total_pax, dni_evento))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error en cocina.calcular_insumos_totales (DNI {dni_evento}): {str(e)}")
        return []

def calcular_lista_compras(cursor, dni_evento):
    """Calcula kilos/unidades basándose en la regla de recepción (Adultos + 20% Adolescentes)."""
    try:
        # Regla de negocio de Rivers Management: Los adolescentes cuentan como 0.20 para compras
        # Se utiliza JOIN con 'evento_seleccion_menu' para consistencia con el front
        sql = """
            SELECT r.insumo, 
                   SUM(r.gramos_por_persona * (e.cantidad_adultos + (e.cantidad_adolescentes * 0.20))) as total_calculado
            FROM evento_seleccion_menu em
            JOIN eventos e ON em.dni_evento = e.dni_cliente
            JOIN recetas r ON em.id_plato = r.id_plato
            WHERE e.dni_cliente = %s
            GROUP BY r.insumo
        """
        cursor.execute(sql, (dni_evento,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error en cocina.calcular_lista_compras (DNI {dni_evento}): {str(e)}")
        return []