def calcular_estado_cuenta(cursor, dni_evento):
    """Calcula unidades canceladas y saldo a precio de hoy."""
    consulta = "SELECT cantidad_adultos, cantidad_adolescentes, valor_cubierto_actual FROM eventos WHERE dni_cliente = %s"
    cursor.execute(consulta, (dni_evento,))
    evento = cursor.fetchone()
    if not evento: return None

    total_unidades = evento['cantidad_adultos'] + (evento['cantidad_adolescentes'] * 0.5)
    
    cursor.execute("SELECT SUM(unidades_canceladas) as pagado FROM pagos_cuotas WHERE dni_evento = %s", (dni_evento,))
    pagado = cursor.fetchone()['pagado'] or 0
    
    pendientes = total_unidades - pagado
    return {
        "unidades_totales": total_unidades,
        "unidades_pagadas": pagado,
        "unidades_pendientes": pendientes,
        "saldo_hoy": pendientes * evento['valor_cubierto_actual']
    }

def obtener_resumen_unidades(cursor, dni_evento):
    """Calcula el balance de unidades contratadas vs pagadas."""
    try:
        # 1. Obtener datos base del evento
        sql_evento = "SELECT nombre_cliente, total_cubiertos_contratados, valor_cubierto_actual FROM eventos WHERE dni_cliente = %s"
        cursor.execute(sql_evento, (dni_evento,))
        evento = cursor.fetchone()
        
        if not evento:
            return None

        # 2. Obtener la suma de unidades ya pagadas (congeladas)
        sql_pagos = "SELECT SUM(unidades_canceladas) as pagadas FROM pagos_cuotas WHERE dni_evento = %s"
        cursor.execute(sql_pagos, (dni_evento,))
        resultado_pagos = cursor.fetchone()
        
        # Manejo de nulos para evitar el error 500
        unidades_pagadas = float(resultado_pagos['pagadas']) if resultado_pagos and resultado_pagos['pagadas'] else 0.0
        
        # 3. Cálculos finales
        unidades_totales = float(evento['total_cubiertos_contratados'])
        unidades_restantes = max(0, unidades_totales - unidades_pagadas)
        precio_hoy = float(evento['valor_cubierto_actual'])
        
        return {
            "cliente": evento['nombre_cliente'],
            "total_contratado": unidades_totales,
            "unidades_pagadas": unidades_pagadas,
            "unidades_restantes": unidades_restantes,
            "valor_cuota_hoy": precio_hoy,
            "monto_para_cancelar_total": unidades_restantes * precio_hoy
        }
    except Exception as e:
        print(f"Error en finanzas.py: {str(e)}")
        return None