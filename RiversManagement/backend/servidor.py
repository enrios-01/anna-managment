from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from modulos import gastronomia, cocina, logistica, finanzas

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- RUTA: REGISTRO DE EVENTO (CORREGIDA) ---
def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="", 
        database="rivers_management"
    )

@app.route('/api/evento/registro', methods=['POST'])
def registrar_evento():
    datos = request.json
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Lógica Rivers Management: Unidades Contratadas
        # Adultos + (Adolescentes / 2) - Sin Cargo
        adultos = float(datos.get('adultos', 0))
        adolescentes = float(datos.get('adolescentes', 0))
        sin_cargo = float(datos.get('sin_cargo', 0))
        total_unidades = adultos + (adolescentes * 0.5) - sin_cargo
        
        # SQL Corregido: Se agregaron los campos faltantes y se sincronizaron los 18 marcadores %s
        sql = """INSERT INTO eventos (
                    dni_cliente, id_empresa, nombre_cliente, tipo_evento, celular, 
                    correo, domicilio_cliente, salon, direccion_salon, vendedor, 
                    fecha_evento, horario_inicio, horario_fin, cantidad_adultos, 
                    adultos_vegetarianos, cantidad_adolescentes, cantidad_menores, 
                    cubiertos_sin_cargo, total_cubiertos_contratados, valor_cubierto_actual
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        valores = (
            datos['dni'], 
            1, 
            datos['nombre'], 
            datos.get('tipo_evento'),
            datos.get('telefono'), 
            datos.get('email'),
            datos.get('domicilio'), # Nuevo campo
            datos.get('salon'), 
            datos.get('direccion_salon'),
            datos.get('vendedor'),
            datos['fecha_evento'],
            datos.get('horario_inicio'),
            datos.get('horario_fin'),
            adultos,
            datos.get('adultos_vege', 0),
            adolescentes,
            datos.get('menores', 0),
            sin_cargo,
            total_unidades,
            datos['valor_cubierto']
        )
        
        cursor.execute(sql, valores)
        
        # --- Lógica de Pago Inicial ---
        pago_inicial = float(datos.get('pagos_realizados', 0))
        if pago_inicial > 0:
            # Se calcula cuántos cubiertos se cancelan con el IVA incluido (1.21)
            unidades_pagadas = pago_inicial / (float(datos['valor_cubierto']) * 1.21)
            cursor.execute("""INSERT INTO pagos_cuotas 
                            (dni_evento, monto_dinero, valor_cubierto_momento, unidades_canceladas) 
                            VALUES (%s, %s, %s, %s)""",
                           (datos['dni'], pago_inicial, datos['valor_cubierto'], unidades_pagadas))

        db.commit()
        return jsonify({"mensaje": "Evento registrado con éxito"}), 201
    except Exception as e:
        print(f"Error en registro: {str(e)}")
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()

@app.route('/api/evento/ficha_completa/<dni>', methods=['GET'])
def ficha_completa(dni):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Obtener datos del evento y calcular total abonado en pesos
        # Traemos la suma de dinero directamente de la base de datos para evitar errores de redondeo en el front
        sql_base = """
            SELECT *, 
            DATE_FORMAT(fecha_evento, '%Y-%m-%d') as fecha_iso,
            (SELECT IFNULL(SUM(monto_dinero), 0) FROM pagos_cuotas WHERE dni_evento = eventos.dni_cliente) as total_abonado_pesos,
            (SELECT IFNULL(SUM(unidades_canceladas), 0) FROM pagos_cuotas WHERE dni_evento = eventos.dni_cliente) as unidades_pagas
            FROM eventos 
            WHERE dni_cliente = %s
        """
        cursor.execute(sql_base, (dni,))
        evento = cursor.fetchone()

        if not evento:
            return jsonify({"error": "Evento no encontrado"}), 404

        # Limpieza de tipos de datos para JSON (Convertimos a float/int para evitar errores de serialización)
        evento['total_abonado_pesos'] = float(evento['total_abonado_pesos'])
        evento['unidades_pagas'] = float(evento['unidades_pagas'])
        evento['total_cubiertos_contratados'] = float(evento['total_cubiertos_contratados'])
        evento['valor_cubierto_actual'] = float(evento['valor_cubierto_actual'])

        # 2. Historial de Pagos (Para el bloque de "Entregas Realizadas")
        # Aquí mostramos el dinero tal cual entró, como un adelanto de cuota
        cursor.execute("""
            SELECT id_pago, monto_dinero, unidades_canceladas, 
            DATE_FORMAT(fecha_pago, '%d/%m/%Y') as fecha_pago 
            FROM pagos_cuotas 
            WHERE dni_evento = %s 
            ORDER BY id_pago DESC
        """, (dni,))
        pagos = cursor.fetchall()
        
        # Formateamos los pagos para asegurar que el dinero llegue como entero
        for p in pagos:
            p['monto_dinero'] = int(p['monto_dinero'])
            p['unidades_canceladas'] = float(p['unidades_canceladas'])
            
        evento['historial_pagos'] = pagos

        # 3. Bloque de Adicionales (Concepto, Cantidad, Fecha, Precio y Pago)
        sql_adic = """
            SELECT id_adicional, concepto, cantidad, precio_unitario, pago_realizado, 
            DATE_FORMAT(fecha_adicional, '%d/%m/%Y') as fecha_formato
            FROM evento_adicionales 
            WHERE dni_evento = %s
        """
        cursor.execute(sql_adic, (dni,))
        adicionales = cursor.fetchall()
        
        for a in adicionales:
            a['precio_unitario'] = int(a['precio_unitario'])
            a['pago_realizado'] = int(a['pago_realizado'])
            a['cantidad'] = float(a['cantidad'])
            
        evento['lista_adicionales'] = adicionales

        # 4. Menú Elegido
        sql_menu = """
            SELECT p.nombre_plato, p.categoria 
            FROM evento_seleccion_menu s
            JOIN catalogo_platos p ON s.id_plato = p.id_plato 
            WHERE s.dni_evento = %s
        """
        cursor.execute(sql_menu, (dni,))
        evento['menu_elegido'] = cursor.fetchall()
        
        # 5. Cálculo de Auditoría Interna (Opcional, pero ayuda al front)
        # Monto Total Pactado = (Cubiertos * Precio) * IVA
        monto_contrato = (evento['total_cubiertos_contratados'] * evento['valor_cubierto_actual']) * 1.21
        evento['monto_total_contrato'] = round(monto_contrato)

        return jsonify(evento)

    except Exception as e:
        print(f"Error en ficha_completa para DNI {dni}: {str(e)}")
        return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500
    
    finally:
        db.close()

# --- RUTA: LISTA DE EVENTOS (SIN CAMBIOS) ---
@app.route('/api/eventos/lista', methods=['GET'])
def obtener_lista_eventos():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """SELECT dni_cliente, nombre_cliente, 
                 DATE_FORMAT(fecha_evento, '%Y-%m-%d') as fecha_evento, 
                 total_cubiertos_contratados,
                 (total_cubiertos_contratados - (SELECT IFNULL(SUM(unidades_canceladas),0) 
                 FROM pagos_cuotas WHERE dni_evento = eventos.dni_cliente)) as unidades_restantes
                 FROM eventos ORDER BY fecha_evento ASC"""
        cursor.execute(sql)
        eventos = cursor.fetchall()
        return jsonify(eventos)
    finally:
        db.close()

# --- RUTA: RESUMEN FINANCIERO (ACTUALIZADA) ---
@app.route('/api/evento/resumen/<dni>', methods=['GET'])
def resumen_unidades(dni):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        resumen = finanzas.obtener_resumen_unidades(cursor, dni)
        if resumen:
            # Añadimos los campos logísticos al JSON de respuesta para la ficha.html
            cursor.execute("SELECT tipo_evento, salon, vendedor FROM eventos WHERE dni_cliente = %s", (dni,))
            info_extra = cursor.fetchone()
            if info_extra:
                resumen.update(info_extra)
            return jsonify(resumen), 200
        else:
            return jsonify({"error": "No se encontró el evento"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

# --- RUTAS DE GASTRONOMÍA ---
@app.route('/api/gastronomia/opciones/<categoria>', methods=['GET'])
def listar_opciones(categoria):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        sql = "SELECT id_plato, nombre_plato FROM catalogo_platos WHERE categoria = %s"
        cursor.execute(sql, (categoria,))
        return jsonify(cursor.fetchall())
    finally:
        db.close()

@app.route('/api/gastronomia/seleccionar', methods=['POST'])
def guardar_seleccion():
    datos = request.json  # Recibe {dni: '...', platos: [id1, id2]}
    db = conectar()
    cursor = db.cursor()
    try:
        # Usamos datos['dni'] porque así viene del fetch en ficha.html
        gastronomia.guardar_seleccion_cliente(db, cursor, datos['dni'], datos['platos'])
        return jsonify({"mensaje": "Menú guardado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

# Actualiza la ruta registrar_pago en servidor.py
@app.route('/api/evento/registrar_pago', methods=['POST'])
def registrar_pago():
    data = request.json
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT valor_cubierto_actual FROM eventos WHERE dni_cliente = %s", (data['dni'],))
        valor_actual = float(cursor.fetchone()[0])
        
        # 1. Calculamos unidades con máxima precisión primero
        monto = float(data['monto'])
        unidades = monto / (valor_actual * 1.21)
        
        # 2. IMPORTANTE: Guardamos con 4 decimales para precisión interna, 
        # pero el front usará 2 para el historial.
        sql = """INSERT INTO pagos_cuotas (dni_evento, monto_dinero, valor_cubierto_momento, unidades_canceladas) 
                 VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql, (data['dni'], monto, valor_actual, round(unidades, 4)))
        
        db.commit()
        return jsonify({"mensaje": "Pago registrado"}), 201
    finally:
        db.close()
@app.route('/api/evento/verificar_estado/<dni>')
def verificar_estado(dni):
    db = conectar()
    cursor = db.cursor()
    try:
        # CORRECCIÓN: Cambiar 'seleccion_menus' por 'evento_seleccion_menu'
        # También cambiamos 'dni_cliente' por 'dni_evento' para que coincida con la tabla
        cursor.execute("SELECT COUNT(*) FROM evento_seleccion_menu WHERE dni_evento = %s", (dni,))
        resultado = cursor.fetchone()
        tiene_menu = resultado[0] > 0
        return jsonify({"tiene_menu": tiene_menu})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/evento/adicional/nuevo', methods=['POST'])
def nuevo_adicional():
    data = request.json
    db = conectar()
    cursor = db.cursor()
    try:
        # Insertamos el nuevo servicio adicional
        sql = """INSERT INTO evento_adicionales 
                 (dni_evento, concepto, cantidad, precio_unitario, pago_realizado, fecha_adicional) 
                 VALUES (%s, %s, %s, %s, 0, CURDATE())"""
        cursor.execute(sql, (
            data['dni'], 
            data['concepto'], 
            data['cantidad'], 
            data['precio']
        ))
        db.commit()
        return jsonify({"mensaje": "Adicional cargado con éxito"}), 201
    except Exception as e:
        print(f"Error en adicional: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/evento/actualizar_notas', methods=['POST'])
def actualizar_notas():
    data = request.json
    db = conectar()
    cursor = db.cursor()
    try:
        sql = "UPDATE eventos SET notas_evento = %s WHERE dni_cliente = %s"
        cursor.execute(sql, (data['notas'], data['dni']))
        db.commit()
        return jsonify({"mensaje": "Notas actualizadas"}), 200
    finally:
        db.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Buscamos el usuario en la base de datos
        sql = "SELECT * FROM usuarios WHERE nombre_usuario = %s AND clave = %s"
        cursor.execute(sql, (data['usuario'], data['clave']))
        user = cursor.fetchone()

        if user:
            # Login exitoso
            return jsonify({
                "status": "success",
                "nombre": user['nombre_completo'],
                "rol": user['rol']
            }), 200
        else:
            # Credenciales incorrectas
            return jsonify({"status": "error", "mensaje": "Usuario o clave incorrectos"}), 401
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)