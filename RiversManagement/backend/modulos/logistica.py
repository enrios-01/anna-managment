# Módulo Logístico - Rivers Management
def registrar_salida_bebidas(db, cursor, dni_evento, lista_bebidas):
    """lista_bebidas es un dict con {nombre_bebida: cantidad}"""
    sql = "INSERT INTO inventario_bebidas_evento (dni_evento, nombre_bebida, cantidad_enviada) VALUES (%s, %s, %s)"
    for bebida, cant in lista_bebidas.items():
        cursor.execute(sql, (dni_evento, bebida, cant))
    db.commit()

def cerrar_inventario_evento(db, cursor, dni_evento, nombre_bebida, retorno_llenos, retorno_vacios, rotas):
    """Actualiza el retorno al finalizar el evento"""
    sql = """UPDATE inventario_bebidas_evento 
             SET cantidad_retorno_llenos = %s, cantidad_retorno_vacios = %s, unidades_rotas = %s
             WHERE dni_evento = %s AND nombre_bebida = %s"""
    cursor.execute(sql, (retorno_llenos, retorno_vacios, rotas, dni_evento, nombre_bebida))
    db.commit()