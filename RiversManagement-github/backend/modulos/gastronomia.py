# modulos/gastronomia.py

def obtener_opciones_menu(cursor, categoria):
    """
    Recupera los platos disponibles según la categoría seleccionada.
    """
    try:
        # Se utiliza el cursor en modo diccionario heredado del servidor.py
        cursor.execute("SELECT id_plato, nombre_plato FROM catalogo_platos WHERE categoria = %s", (categoria,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error en obtener_opciones_menu ({categoria}): {str(e)}")
        return []

def guardar_seleccion_cliente(db, cursor, dni_evento, lista_platos):
    """
    Actualiza la diagramación del menú para un cliente específico.
    """
    try:
        # 1. Limpiamos selecciones previas para este DNI (Evita duplicados)
        # Se utiliza 'dni_evento' para coincidir con la estructura de la tabla en el VPS
        cursor.execute("DELETE FROM evento_seleccion_menu WHERE dni_evento = %s", (dni_evento,))
        
        # 2. Insertamos los nuevos platos seleccionados
        if lista_platos:
            sql = "INSERT INTO evento_seleccion_menu (dni_evento, id_plato) VALUES (%s, %s)"
            # Preparamos los datos para una ejecución eficiente
            datos_insertar = [(dni_evento, id_plato) for id_plato in lista_platos]
            cursor.executemany(sql, datos_insertar)
        
        db.commit()
        return True
    except Exception as e:
        # Si algo falla en el VPS, deshacemos los cambios para proteger la base de datos
        db.rollback()
        print(f"Error crítico en guardar_seleccion_cliente para DNI {dni_evento}: {str(e)}")
        raise e