-- Rivers Management - Esquema de Base de Datos FULL
CREATE DATABASE IF NOT EXISTS rivers_management;
USE rivers_management;

-- Tabla de Empresas para personalización
CREATE TABLE empresas (
    id_empresa INT AUTO_INCREMENT PRIMARY KEY,
    nombre_catering VARCHAR(100) NOT NULL,
    logo_ruta VARCHAR(255),
    iva_defecto DECIMAL(5,2) DEFAULT 21.00
);

-- Tabla Principal de Eventos con TODOS los campos del index.html
CREATE TABLE eventos (
    dni_cliente VARCHAR(20) PRIMARY KEY,
    id_empresa INT,
    nombre_cliente VARCHAR(100) NOT NULL,
    telefono VARCHAR(50),
    direccion_cliente VARCHAR(150),
    email VARCHAR(120),
    vendedor VARCHAR(100),
    fecha_evento DATE NOT NULL,
    tipo_evento VARCHAR(50),
    salon VARCHAR(100),
    direccion_salon VARCHAR(150),
    
    -- Invitados y Dietas Especiales
    cantidad_adultos INT DEFAULT 0,
    adultos_vegetarianos INT DEFAULT 0,
    adultos_celiacos INT DEFAULT 0,
    cantidad_adolescentes INT DEFAULT 0,
    adolescentes_vegetarianos INT DEFAULT 0,
    cantidad_menores INT DEFAULT 0,
    cubiertos_sin_cargo INT DEFAULT 0,
    
    -- Horarios Logísticos
    hora_montaje TIME,
    hora_servicio TIME,
    
    -- Finanzas
    valor_cubierto_actual DECIMAL(12,2) NOT NULL,
    iva_porcentaje DECIMAL(5,2) DEFAULT 21.00,
    FOREIGN KEY (id_empresa) REFERENCES empresas(id_empresa)
);

-- Registro de Pagos (Lógica Anti-Inflación por Unidades)
CREATE TABLE pagos_cuotas (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    dni_evento VARCHAR(20),
    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto_dinero DECIMAL(12,2) NOT NULL,
    valor_cubierto_momento DECIMAL(12,2) NOT NULL,
    unidades_canceladas DECIMAL(10,4) NOT NULL, 
    FOREIGN KEY (dni_evento) REFERENCES eventos(dni_cliente)
);

-- Tablas de Catálogo y Selección
CREATE TABLE catalogo_platos (
    id_plato INT AUTO_INCREMENT PRIMARY KEY,
    id_empresa INT,
    nombre_plato VARCHAR(150) NOT NULL,
    categoria ENUM('Buffet', 'Platos', 'Dulce') NOT NULL,
    FOREIGN KEY (id_empresa) REFERENCES empresas(id_empresa)
);

CREATE TABLE ingredientes_plato (
    id_ingrediente INT AUTO_INCREMENT PRIMARY KEY,
    id_plato INT,
    nombre_insumo VARCHAR(100),
    unidad_medida VARCHAR(20),
    cantidad_por_persona DECIMAL(10,4),
    FOREIGN KEY (id_plato) REFERENCES catalogo_platos(id_plato)
);

CREATE TABLE evento_seleccion_menu (
    id_seleccion INT AUTO_INCREMENT PRIMARY KEY,
    dni_evento VARCHAR(20),
    id_plato INT,
    FOREIGN KEY (dni_evento) REFERENCES eventos(dni_cliente),
    FOREIGN KEY (id_plato) REFERENCES catalogo_platos(id_plato)
);

USE rivers_management;

-- Actualizamos la tabla eventos con las columnas de seguimiento de unidades
ALTER TABLE eventos 
ADD COLUMN total_cubiertos_contratados DECIMAL(10,2) DEFAULT 0 AFTER adultos_sin_cargo,
ADD COLUMN unidades_pagadas DECIMAL(10,2) DEFAULT 0 AFTER total_cubiertos_contratados,
ADD COLUMN unidades_restantes DECIMAL(10,2) DEFAULT 0 AFTER unidades_pagadas;

-- La tabla pagos_cuotas ya tiene 'unidades_canceladas', que es lo que alimenta esto.

-- Inserción necesaria para que el sistema arranque
INSERT INTO empresas (nombre_catering) VALUES ('Anna Management');