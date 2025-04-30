// src/components/Dashboard/charts/e1RMProgressionChart.js
import React, { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';
import { es } from 'date-fns/locale';
import { Card, CardContent, Typography, Box, Divider } from '@mui/material';

Chart.register(...registerables);

// Función auxiliar
const processTimeSeriesData = (data, valueKey) => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    return data
      .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item[valueKey] === 'number' && item[valueKey] > 0) // Filtrar e1RM > 0
      .map(item => ({ x: new Date(item.fecha), y: item[valueKey] }))
      .sort((a, b) => a.x - b.x);
};

function E1RMProgressionChart({ data = [] }) {
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
      chartInstanceRef.current = null;
    }

    if (chartRef.current && data.length > 0) {
      const ctx = chartRef.current.getContext('2d');
      // Usar la nueva clave 'max_e1rm_session' que añadimos en el backend
      const chartData = processTimeSeriesData(data, 'max_e1rm_session');

       if (chartData.length === 0) return; // No dibujar si no hay datos válidos de e1RM

      chartInstanceRef.current = new Chart(ctx, {
        type: 'line',
        data: {
          datasets: [{
            label: '1RM Estimado (Máx. Sesión)',
            data: chartData,
            borderColor: '#e74c3c', // Un color diferente
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            fill: true,
            tension: 0.2,
            pointRadius: 5,
            pointHoverRadius: 7
           }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top' }, tooltip: { mode: 'index', intersect: false, callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y} kg` }} },
            scales: { x: { type: 'time', time: { unit: 'day', tooltipFormat: 'PPP', locale: es }, title: { display: true, text: 'Fecha' }}, y: { beginAtZero: false, title: { display: true, text: 'e1RM (kg)' }} } // Empezar eje Y desde un valor razonable
        }
      });
    }
     return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [data]);

  return (
    <Card className="chart-container primary-chart" elevation={3}> {/* Puedes usar primary o secondary */}
      <CardContent>
        <Typography variant="h6" gutterBottom>Progresión 1RM Estimado</Typography>
        <Divider sx={{ mb: 2 }} />
        {/* Ajusta la altura si es necesario */}
        <Box height={350} position="relative">
          <canvas ref={chartRef}></canvas>
          {data.length === 0 && ( <Typography sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'text.secondary' }}>(Sin datos)</Typography>)}
        </Box>
      </CardContent>
    </Card>
  );
}

export default E1RMProgressionChart;