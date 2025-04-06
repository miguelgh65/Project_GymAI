// src/components/Dashboard/charts/RepsChart.js
import React, { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';
import { es } from 'date-fns/locale';
import { Card, CardContent, Typography, Box, Divider } from '@mui/material';

Chart.register(...registerables);

const processTimeSeriesData = (data, valueKey) => {
    // ... (misma función que en WeightProgressionChart) ...
     if (!data || !Array.isArray(data) || data.length === 0) return [];
    return data
      .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item[valueKey] === 'number')
      .map(item => ({ x: new Date(item.fecha), y: item[valueKey] }))
      .sort((a, b) => a.x - b.x);
};

function RepsChart({ data = [] }) {
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
      chartInstanceRef.current = null;
    }

    if (chartRef.current && data.length > 0) {
      const ctx = chartRef.current.getContext('2d');
      const chartData = processTimeSeriesData(data, 'total_reps');

      chartInstanceRef.current = new Chart(ctx, {
        type: 'line',
        data: {
          datasets: [{ label: 'Repeticiones Totales', data: chartData, borderColor: '#e67e22', backgroundColor: 'rgba(230, 126, 34, 0.1)', fill: true, tension: 0.2 }]
        },
         options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: {} }, // Tooltip por defecto
            scales: { x: { type: 'time', time: { unit: 'day', tooltipFormat: 'PPP', locale: es }, title: { display: true, text: 'Fecha' }}, y: { beginAtZero: true, title: { display: true, text: 'Repeticiones' }} }
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
    <Card className="chart-container secondary-chart" elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom>Repeticiones</Typography>
        <Divider sx={{ mb: 2 }} />
        <Box height={250} position="relative">
          <canvas ref={chartRef}></canvas>
          {data.length === 0 && ( <Typography sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'text.secondary' }}>(Sin datos)</Typography>)}
        </Box>
      </CardContent>
    </Card>
  );
}

export default RepsChart;