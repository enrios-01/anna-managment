def obtener_opciones_menu(cursor, categoria):
    cursor.execute("SELECT id_plato, nombre_plato FROM catalogo_platos WHERE categoria = %s", (categoria,))
    return cursor.fetchall()

# modulos/gastronomia.py

def guardar_seleccion_cliente(db, cursor, dni_evento, lista_platos):
    try:
        # 1. Limpiamos selecciones previas para este DNI
        cursor.execute("DELETE FROM evento_seleccion_menu WHERE dni_evento = %s", (dni_evento,))
        
        # 2. Insertamos los nuevos platos seleccionados
        sql = "INSERT INTO evento_seleccion_menu (dni_evento, id_plato) VALUES (%s, %s)"
        for id_plato in lista_platos:
            cursor.execute(sql, (dni_evento, id_plato))
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e