# modulos/logistica.py

def registrar_salida_bebidas(db, cursor, dni_evento, lista_bebidas):
    """
    Registra el envío de stock al salón.
    lista_bebidas: dict {nombre_bebida: cantidad}
    """
    try:
        # Usamos executemany para mayor eficiencia en red remota
        sql = """INSERT INTO inventario_bebidas_evento 
                 (dni_evento, nombre_bebida, cantidad_enviada) 
                 VALUES (%s, %s, %s)"""
        
        # Preparamos los datos para una sola transacción
        datos_insertar = [(dni_evento, bebida, cant) for bebida, cant in lista_bebidas.items()]
        
        if datos_insertar:
            cursor.executemany(sql, datos_insertar)
            db.commit()
            return True
    except Exception as e:
        db.rollback()
        print(f"Error en logistica.registrar_salida (DNI {dni_evento}): {str(e)}")
        raise e

def cerrar_inventario_evento(db, cursor, dni_evento, nombre_bebida, retorno_llenos, retorno_vacios, rotas):
    """
    Actualiza el retorno de stock y registra mermas (unidades rotas)
    """
    try:
        sql = """UPDATE inventario_bebidas_evento 
                 SET cantidad_retorno_llenos = %s, 
                     cantidad_retorno_vacios = %s, 
                     unidades_rotas = %s
                 WHERE dni_evento = %s AND nombre_bebida = %s"""
        
        cursor.execute(sql, (
            float(retorno_llenos), 
            float(retorno_vacios), 
            float(rotas), 
            dni_evento, 
            nombre_bebida
        ))
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error en logistica.cerrar_inventario (DNI {dni_evento}): {str(e)}")
        return False