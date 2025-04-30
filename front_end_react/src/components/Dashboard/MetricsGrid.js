// src/components/Dashboard/MetricsGrid.js
import React from 'react';
import { Grid, Card, Box, Typography } from '@mui/material';

// Componente reutilizable para cada tarjeta de métrica
// (Definido aquí mismo ya que es pequeño y específico de este grid)
function MetricCard({ title, value, unit = '', iconClass, cardId }) {
  // Formatear valor (evitar NaN, mostrar 0 si no hay dato o es inválido)
  // Asegurarse que el valor es numérico antes de formatear o usar
  const numericValue = parseFloat(value);
  const displayValue = (numericValue !== undefined && numericValue !== null && !isNaN(numericValue)) ? numericValue : 0;

  // Formatear el número (ej: progreso con 1 decimal, el resto entero o con 2)
  let formattedValue;
  if (title.includes("Progreso")) {
      formattedValue = displayValue.toFixed(1); // 1 decimal para progreso
  } else if (Number.isInteger(displayValue)) {
      formattedValue = displayValue; // Entero si es entero
  } else {
      formattedValue = displayValue.toFixed(2); // 2 decimales si no es entero
  }


  // Clases para colores
  let valueClass = "metric-value";
  if (title.includes("Progreso") && displayValue > 0) valueClass += " positive";
  if (title.includes("Progreso") && displayValue < 0) valueClass += " negative";


  return (
    // Añadir un minHeight para consistencia si los títulos varían en longitud
    <Card className="metric-card" elevation={2} id={cardId} sx={{ display: 'flex', alignItems: 'center', p: 2, minHeight: '100px' }}>
      <Box className="metric-icon" sx={{ width: 40, height: 40, mr: 1.5 /* Ajustes menores de estilo */ }}>
        <i className={iconClass} style={{ fontSize: '1.2rem' }}></i> {/* Ajustar tamaño icono */}
      </Box>
      <Box className="metric-content">
        <Typography variant="body2" component="h3" sx={{ mb: 0.5, color: 'text.secondary' }}> {/* Título más pequeño */}
          {title}
        </Typography>
        <Typography variant="h5" component="p" className={valueClass} sx={{ fontWeight: 'bold' }}> {/* Poner p en lugar de h5 si es semánticamente mejor */}
          {formattedValue}{unit}
        </Typography>
      </Box>
    </Card>
  );
}


// Componente principal del Grid de Métricas
function MetricsGrid({ metricsData = {} }) { // Valor por defecto {}
  // Extraer los datos del objeto, incluyendo el nuevo e1RM
  const {
    total_sesiones,
    max_weight_ever,
    progress_percent,
    // max_volume_session, // Puedes decidir mostrarlo o no
    max_e1rm_ever // <<< Obtener el nuevo dato del resumen
  } = metricsData;

  // Definir las métricas a mostrar
  const metricsToShow = [
    { title: "Sesiones", value: total_sesiones, iconClass: "fas fa-calendar-check", cardId: "card-sessions" },
    { title: "Peso Máx.", value: max_weight_ever, unit: " kg", iconClass: "fas fa-dumbbell", cardId: "card-max-weight" },
    { title: "1RM Est. Máx", value: max_e1rm_ever, unit: " kg", iconClass: "fas fa-trophy", cardId: "card-e1rm" }, // <<< Nueva métrica
    { title: "Progreso Peso", value: progress_percent, unit: "%", iconClass: "fas fa-chart-line", cardId: "card-progress" },
    // { title: "Volumen Máx/Sesión", value: max_volume_session, unit: " kg", iconClass: "fas fa-weight-hanging", cardId: "card-volume" }, // Opcional
  ];

  return (
    // Usar Grid anidado para controlar mejor el layout en diferentes tamaños
    <Grid container spacing={2}>
      {metricsToShow.map((metric) => (
        // Ocupar mitad en móvil (xs=6), toda la columna en escritorio (md=12)
        <Grid item xs={6} md={12} key={metric.cardId || metric.title}>
          <MetricCard
            title={metric.title}
            value={metric.value}
            unit={metric.unit}
            iconClass={metric.iconClass}
            cardId={metric.cardId}
          />
        </Grid>
      ))}
    </Grid>
  );
}

export default MetricsGrid;