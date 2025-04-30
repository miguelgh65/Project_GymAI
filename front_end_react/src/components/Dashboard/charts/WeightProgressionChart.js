// src/components/Dashboard/charts/WeightProgressionChart.js
import React, { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';
import { es } from 'date-fns/locale';
import { Card, CardContent, Typography, Box, Divider } from '@mui/material';

// Registrar componentes necesarios (debe hacerse una vez, pero seguro aquí)
Chart.register(...registerables);

// Función auxiliar (podría ir a utils)
const processTimeSeriesData = (data, valueKey) => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    return data
      .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item[valueKey] === 'number')
      .map(item => ({
        x: new Date(item.fecha),
        y: item[valueKey]
      }))
      .sort((a, b) => a.x - b.x);
};

function WeightProgressionChart({ data = [] }) { // Valor por defecto []
  const chartRef = useRef(null); // Ref para el canvas
  const chartInstanceRef = useRef(null); // Ref para el objeto Chart

  useEffect(() => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy(); // Destruir gráfico anterior
      chartInstanceRef.current = null;
    }

    if (chartRef.current && data.length > 0) {
      const ctx = chartRef.current.getContext('2d');
      const chartData = processTimeSeriesData(data, 'max_peso');
      const avgData = processTimeSeriesData(data, 'avg_peso');

      chartInstanceRef.current = new Chart(ctx, {
        type: 'line',
        data: {
          datasets: [
             { label: 'Peso Máximo', data: chartData, borderColor: '#3498db', backgroundColor: 'rgba(52, 152, 219, 0.1)', borderWidth: 3, fill: false, tension: 0.2, pointRadius: 5, pointHoverRadius: 7 },
             { label: 'Peso Promedio', data: avgData, borderColor: '#9b59b6', backgroundColor: 'rgba(155, 89, 182, 0.1)', borderWidth: 2, borderDash: [5, 5], fill: false, tension: 0.2, pointRadius: 4, pointHoverRadius: 6 }
          ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top' }, tooltip: { mode: 'index', intersect: false, callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y} kg` }} },
            scales: { x: { type: 'time', time: { unit: 'day', tooltipFormat: 'PPP', locale: es }, title: { display: true, text: 'Fecha' }}, y: { title: { display: true, text: 'Peso (kg)' }} }
        }
      });
    }

    // Función de limpieza para destruir el gráfico al desmontar
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [data]); // Re-ejecutar el efecto cuando los datos cambien

  return (
    <Card className="chart-container primary-chart" elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom>Progresión de Peso</Typography>
        <Divider sx={{ mb: 2 }} />
        <Box height={350} position="relative">
           {/* Renderizar siempre el canvas, Chart.js lo maneja */}
          <canvas ref={chartRef}></canvas>
          {data.length === 0 && (
             <Typography sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'text.secondary' }}>
                (Sin datos para mostrar)
             </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

export default WeightProgressionChart;