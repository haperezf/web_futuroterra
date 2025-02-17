$(document).ready(function() {

    // Valores iniciales del estado
    var state = {
      p80: 100,
      sag_water: 1350,
      sag_speed: 9,
      sag_pressure: 7700,
      stockpile_level: 25,
      sump_level: 90,
      hardness: 35,
      solids_feeding: 70,
      pebble: 400,
      gran_gt_100: 20,
      gran_lt_30: 40,
      porcentaje_fino: 70,
      consumo_energia_pct: 100,
      edad_liner: 3
    };
  
    // Función auxiliar: inicializa un slider de jQuery UI
    function initSlider(sliderId, displayId, options, keyName) {
      $("#" + sliderId).slider({
        value: options.value,
        min: options.min,
        max: options.max,
        step: options.step,
        // Llamar a simulate() durante el movimiento (puede ser muy frecuente)
        slide: function(event, ui) {
          $("#" + displayId).text(ui.value);
          state[keyName] = ui.value;
        },
        // Llamar a simulate() cuando se termina el cambio
        change: function(event, ui) {
          $("#" + displayId).text(ui.value);
          state[keyName] = ui.value;
          console.log("Cambio en slider:", keyName, ui.value);
          simulate();
        }
      });
      $("#" + displayId).text($("#" + sliderId).slider("value"));
    }
  
    // Inicialización de sliders (con los rangos especificados)
    initSlider("p80_slider", "p80_val", { min: 50, max: 150, step: 1, value: state.p80 }, "p80");
    initSlider("sag_water_slider", "sag_water_val", { min: 750, max: 2000, step: 50, value: state.sag_water }, "sag_water");
    initSlider("sag_speed_slider", "sag_speed_val", { min: 1, max: 20, step: 0.1, value: state.sag_speed }, "sag_speed");
    initSlider("sag_pressure_slider", "sag_pressure_val", { min: 7300, max: 8100, step: 100, value: state.sag_pressure }, "sag_pressure");
    initSlider("stockpile_level_slider", "stockpile_level_val", { min: 5, max: 35, step: 1, value: state.stockpile_level }, "stockpile_level");
    initSlider("sump_level_slider", "sump_level_val", { min: 60, max: 100, step: 5, value: state.sump_level }, "sump_level");
    initSlider("hardness_slider", "hardness_val", { min: 20, max: 50, step: 1, value: state.hardness }, "hardness");
    initSlider("solids_feeding_slider", "solids_feeding_val", { min: 55, max: 80, step: 1, value: state.solids_feeding }, "solids_feeding");
    initSlider("pebble_slider", "pebble_val", { min: 0, max: 900, step: 50, value: state.pebble }, "pebble");
    initSlider("gran_gt_100_slider", "gran_gt_100_val", { min: 5, max: 40, step: 1, value: state.gran_gt_100 }, "gran_gt_100");
    initSlider("gran_lt_30_slider", "gran_lt_30_val", { min: 25, max: 75, step: 1, value: state.gran_lt_30 }, "gran_lt_30");
    initSlider("porcentaje_fino_slider", "porcentaje_fino_val", { min: 0, max: 100, step: 1, value: state.porcentaje_fino }, "porcentaje_fino");
    initSlider("consumo_energia_pct_slider", "consumo_energia_pct_val", { min: 0, max: 200, step: 1, value: state.consumo_energia_pct }, "consumo_energia_pct");
    initSlider("edad_liner_slider", "edad_liner_val", { min: 1, max: 5, step: 1, value: state.edad_liner }, "edad_liner");
  
    // Inicialización de Canvas Gauges usando RadialGauge
    var energyGauge = new RadialGauge({
      renderTo: 'energyGauge',
      width: 300,
      height: 300,
      units: "MW",
      minValue: 0,
      maxValue: 50000,
      majorTicks: ["0", "10000", "20000", "30000", "40000", "50000"],
      minorTicks: 2,
      value: 0,
      title: "Energía",
      animationRule: "linear",
      animationDuration: 500,
      colorPlate: "#fff",
      borders: false,
      needleType: "line",
      needleWidth: 2,
      valueBox: true
    }).draw();
  
    var maintenanceGauge = new RadialGauge({
      renderTo: 'maintenanceGauge',
      width: 300,
      height: 300,
      units: "%",
      minValue: 0,
      maxValue: 100,
      majorTicks: ["0", "20", "40", "60", "80", "100"],
      minorTicks: 2,
      value: 0,
      title: "Mantenimiento",
      animationRule: "linear",
      animationDuration: 500,
      colorPlate: "#fff",
      borders: false,
      needleType: "line",
      needleWidth: 2,
      valueBox: true
    }).draw();
  
    // Función que envía el estado actual al backend y actualiza los gauges.
    function simulate() {
      console.log("Ejecutando simulate() con estado:", state);
      $.ajax({
        url: "/simulate",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(state),
        success: function(response) {
          console.log("Respuesta recibida:", response);
          energyGauge.value = response.energy_consumption;
          energyGauge.update();
          maintenanceGauge.value = response.mantenimiento_prob * 100;
          maintenanceGauge.update();
        },
        error: function(error) {
          console.error("Error en la simulación:", error);
        }
      });
    }
  
    // Se realiza una simulación inicial para actualizar los gauges.
    simulate();
  });
  