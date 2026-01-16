function recalcular() {
    // Captura de valores
    const adultos = parseFloat(document.getElementById('adultos').value) || 0;
    const adolescentes = parseFloat(document.getElementById('adolescentes').value) || 0;
    const sinCargo = parseFloat(document.getElementById('sin_cargo').value) || 0;
    const valorCubierto = parseFloat(document.getElementById('valor_cubierto').value) || 0;
    const pagos = parseFloat(document.getElementById('pagos_realizados').value) || 0;
    const ivaPct = parseFloat(document.getElementById('iva_pct').value) / 100;

    // Lógica Rivers Management: Unidades de Cubierto
    const unidadesTotales = adultos + (adolescentes * 0.5) - sinCargo;
    const unidadesPagadas = valorCubierto > 0 ? (pagos / (valorCubierto * (1 + ivaPct))) : 0;
    const unidadesPendientes = Math.max(0, unidadesTotales - unidadesPagadas);

    // Cálculos Monetarios
    const subtotal = unidadesTotales * valorCubierto;
    const totalFacturado = subtotal * (1 + ivaPct);
    const restaPagar = Math.max(0, totalFacturado - pagos);

    // Inyectar en el HTML
    document.getElementById('calc_unidades').value = unidadesTotales.toFixed(2);
    document.getElementById('calc_pagados').value = unidadesPagadas.toFixed(2);
    document.getElementById('calc_pendientes').value = unidadesPendientes.toFixed(2);
    document.getElementById('calc_total_facturado').value = totalFacturado.toLocaleString('es-AR', {style: 'currency', currency: 'ARS'});
    document.getElementById('calc_resta_pagar').value = restaPagar.toLocaleString('es-AR', {style: 'currency', currency: 'ARS'});
}

async function enviarFormulario() {
    const datos = {
        dni: document.getElementById('dni').value,
        nombre: document.getElementById('nombre').value,
        fecha_evento: document.getElementById('fecha_evento').value,
        adultos: parseInt(document.getElementById('adultos').value),
        adolescentes: parseInt(document.getElementById('adolescentes').value),
        sin_cargo: parseInt(document.getElementById('sin_cargo').value),
        valor_cubierto: parseFloat(document.getElementById('valor_cubierto').value),
        pagos_realizados: parseFloat(document.getElementById('pagos_realizados').value),
        iva_porcentaje: parseFloat(document.getElementById('iva_pct').value)
    };

    if(!datos.dni || !datos.nombre) return alert("Complete DNI y Nombre");

    const res = await fetch('http://localhost:5000/api/evento/registro', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(datos)
    });

    if(res.ok) {
        alert("✅ Registro exitoso");
        window.location.href = `ficha.html?dni=${datos.dni}`;
    } else {
        const err = await res.json();
        alert("❌ Error: " + err.error);
    }
}