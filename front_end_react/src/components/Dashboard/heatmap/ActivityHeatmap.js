// src/components/Dashboard/heatmap/ActivityHeatmap.js
import React, { useEffect, useRef, useState, useCallback } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import { Card, CardContent, Typography, Box, Divider, CircularProgress } from '@mui/material';

function ActivityHeatmap() {
  const heatmapRef = useRef(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [loadingHeatmap, setLoadingHeatmap] = useState(true);
  const [heatmapError, setHeatmapError] = useState(null);

  // Cargar datos del heatmap
  const loadActivityHeatmap = useCallback(async () => {
    setLoadingHeatmap(true);
    setHeatmapError(null);
    try {
      const year = new Date().getFullYear();
      const response = await axios.get(`/api/calendar_heatmap?year=${year}`);
      if (response.data.success && Array.isArray(response.data.data)) {
        setHeatmapData(response.data.data);
      } else {
        throw new Error(response.data.message || "Respuesta inválida del heatmap");
      }
    } catch (error) {
      console.error('Error al cargar datos de actividad:', error);
      setHeatmapError("Error al cargar mapa de actividad.");
    } finally {
      setLoadingHeatmap(false);
    }
  }, []);

  // Efecto para cargar datos al montar
  useEffect(() => {
    loadActivityHeatmap();
  }, [loadActivityHeatmap]);

  // Efecto para dibujar el mapa cuando los datos cambien
  useEffect(() => {
    if (!heatmapData || !heatmapRef.current || loadingHeatmap || typeof d3 === 'undefined') {
      return; // No hacer nada si no hay datos, ref, o d3, o si está cargando
    }

    const data = heatmapData;
    const container = heatmapRef.current;
    container.innerHTML = ''; // Limpiar previo

    if (data.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #757575;">No hay datos de actividad para mostrar este año</div>';
        return;
    }

    try {
      // --- Lógica D3.js (simplificada de tu código original) ---
      const width = container.clientWidth > 0 ? container.clientWidth : 800;
      const cellSize = Math.min(width / 55, 16); // Ajustar divisor y tamaño max
      const cellMargin = 2;
      const height = (cellSize * 7) + 40;

      const maxCount = Math.max(...data.map(d => d.count), 1);
      const colorScale = d3.scaleSequential(d3.interpolateBlues).domain([0, maxCount]); // Interpolador más simple

      const svg = d3.select(container).append('svg')
          .attr('width', '100%')
          .attr('height', height)
          .attr('viewBox', `0 0 ${width} ${height}`)
          .style('font-family', "'Roboto', sans-serif");

      const year = new Date(data[0]?.date || `${new Date().getFullYear()}-01-01`).getFullYear();
      const countByDateStr = new Map(data.map(d => [d.date, d.count]));

      const daysGroup = svg.append("g").attr("transform", "translate(20, 20)");

      daysGroup.selectAll("rect")
          .data(d3.timeDays(new Date(year, 0, 1), new Date(year + 1, 0, 1)))
          .join("rect")
          .attr("width", cellSize - cellMargin)
          .attr("height", cellSize - cellMargin)
          .attr("rx", 3).attr("ry", 3)
          .attr("x", d => d3.timeWeek.count(d3.timeYear(d), d) * cellSize)
          .attr("y", d => d.getDay() * cellSize)
          .attr("fill", d => colorScale(countByDateStr.get(d3.timeFormat('%Y-%m-%d')(d)) || 0))
          .style('stroke', '#eee') // Borde más suave
          .style('stroke-width', 0.5)
          .append("title")
          .text(d => `${d3.timeFormat('%d/%m/%Y')(d)}: ${countByDateStr.get(d3.timeFormat('%Y-%m-%d')(d)) || 0} ej.`);

      const monthLabels = svg.append("g").attr("transform", "translate(20, 10)");
      d3.timeMonths(new Date(year, 0, 1), new Date(year + 1, 0, 1)).forEach(month => {
          monthLabels.append("text")
              .attr("x", d3.timeWeek.count(d3.timeYear(month), month) * cellSize)
              .attr("y", 0)
              .style("font-size", "10px")
              .style("fill", "#555")
              .text(d3.timeFormat('%b')(month));
      });
      // --- Fin Lógica D3.js ---

    } catch (error) {
      console.error("Error al crear el mapa de calor D3:", error);
      container.innerHTML = `<div style="padding: 20px; text-align: center; color: #757575;">Error al renderizar mapa</div>`;
    }

  }, [heatmapData, loadingHeatmap]); // Depender de los datos y estado de carga

  return (
    <Card className="chart-container full-width" elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom>Mapa de Actividad</Typography>
        <Divider sx={{ mb: 2 }} />
        <Box height={180} position="relative">
          {loadingHeatmap && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress size={30} />
            </Box>
          )}
          {heatmapError && !loadingHeatmap && (
             <Typography sx={{ textAlign: 'center', color: 'error.main', pt: 2 }}>{heatmapError}</Typography>
          )}
          {/* El div para D3 */}
          <div ref={heatmapRef} style={{ width: '100%', height: '100%' }}></div>
        </Box>
      </CardContent>
    </Card>
  );
}

export default ActivityHeatmap;