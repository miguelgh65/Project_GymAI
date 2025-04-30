// src/components/Dashboard/Dashboard.js
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Box, Typography, Alert, Grid, CircularProgress } from '@mui/material';

// Importar sub-componentes
import FilterSection from './FilterSection';
import MetricsGrid from './MetricsGrid';
import SessionsTable from './SessionsTable';
import WeightProgressionChart from './charts/WeightProgressionChart';
import VolumeChart from './charts/VolumeChart';
import RepsChart from './charts/RepsChart';
import E1RMProgressionChart from './charts/e1RMProgressionChart'; // <<< IMPORTAR NUEVO GRÁFICO
import ActivityHeatmap from './heatmap/ActivityHeatmap';

// Importar CSS
import './Dashboard.css';

// --- Función Auxiliar --- (Podría ir a un archivo utils)
const formatDate = (date) => {
  const d = new Date(date);
  let month = '' + (d.getMonth() + 1);
  let day = '' + d.getDate();
  const year = d.getFullYear();
  if (month.length < 2) month = '0' + month;
  if (day.length < 2) day = '0' + day;
  return [year, month, day].join('-');
};

function Dashboard() {
  // --- Estados ---
  const [exerciseList, setExerciseList] = useState([]);
  const [selectedExercise, setSelectedExercise] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [metricsData, setMetricsData] = useState({});
  const [sessionData, setSessionData] = useState([]); // Datos para los gráficos y tabla
  const [loadingExercises, setLoadingExercises] = useState(true); // Carga inicial de ejercicios
  const [loadingChartData, setLoadingChartData] = useState(false); // Carga al aplicar filtros
  const [error, setError] = useState(null);
  const [apiResponse, setApiResponse] = useState(null); // Guardar toda la respuesta

  // --- Carga Inicial ---
  const loadExercises = useCallback(async () => {
    setLoadingExercises(true);
    setError(null);
    try {
      const response = await axios.get('/api/ejercicios_stats'); // Llama sin params
      let exercises = response.data?.ejercicios_disponibles;
      if (!exercises || exercises.length === 0) {
         exercises = response.data?.ejercicios || response.data?.data || [];
      }
      if (exercises && exercises.length > 0) {
        setExerciseList(exercises);
      } else {
        console.warn("No se encontraron ejercicios. Usando fallback.");
        setExerciseList(["press banca", "press militar", "sentadilla"]);
      }
    } catch (err) {
      console.error('Error al cargar ejercicios:', err);
      setError("Error al cargar la lista de ejercicios.");
      setExerciseList(["press banca", "press militar"]);
    } finally {
      setLoadingExercises(false);
    }
  }, []);

  useEffect(() => {
    // Establecer fechas iniciales
    const today = new Date();
    const monthAgo = new Date(today);
    monthAgo.setMonth(monthAgo.getMonth() - 1);
    setDateFrom(formatDate(monthAgo));
    setDateTo(formatDate(today));
    // Cargar lista de ejercicios al montar
    loadExercises();
  }, [loadExercises]);

  // --- Aplicar Filtros ---
  const applyFilters = useCallback(async () => {
    if (!selectedExercise) {
      setError("Por favor, selecciona un ejercicio.");
      return;
    }
    if (dateFrom && dateTo && new Date(dateFrom) > new Date(dateTo)) {
      setError("La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.");
      return;
    }

    setLoadingChartData(true);
    setError(null);
    setSessionData([]); // Limpiar datos previos
    setMetricsData({});
    setApiResponse(null); // Limpiar respuesta completa previa

    try {
      let url = `/api/ejercicios_stats?ejercicio=${encodeURIComponent(selectedExercise)}`;
      if (dateFrom) url += `&desde=${dateFrom}`;
      if (dateTo) url += `&hasta=${dateTo}`;

      const response = await axios.get(url);
      setApiResponse(response.data); // Guardar toda la respuesta

      if (response.data.success) {
        const data = response.data.datos; // Usar siempre 'datos' según tu backend corregido
        const summary = response.data.resumen;

        if (data && Array.isArray(data) && data.length > 0) {
          console.log(`Datos recibidos para ${selectedExercise}: ${data.length} entradas`);
          setSessionData(data);
          if (summary) {
             setMetricsData(summary);
          } else {
              // Calcular resumen básico si no viene
              setMetricsData({
                  total_sesiones: data.length,
                  max_weight_ever: Math.max(0, ...data.map(d => d.max_peso || 0)),
                  max_volume_session: Math.max(0, ...data.map(d => d.volumen || 0)),
                  // Añadir más cálculos si es necesario
              });
          }
        } else {
          console.log(`No hay datos para ${selectedExercise} en el período seleccionado.`);
          // setSessionData([]); // Ya limpiado arriba
          // setMetricsData({}); // Ya limpiado arriba
          setError(
            <div>
              <p>No hay datos para <strong>{selectedExercise}</strong> en el período.</p>
              {/* ... sugerencias ... */}
            </div>
          );
        }
      } else {
        setError(`Error API: ${response.data.message || "No se pudieron cargar los datos"}`);
      }
    } catch (err) {
      console.error('Error al aplicar filtros:', err);
      setError(`Error al cargar datos: ${err.message || 'Error desconocido'}`);
    } finally {
      setLoadingChartData(false);
    }
  }, [selectedExercise, dateFrom, dateTo]);

  // --- Renderizado ---
  return (
    <Box className="dashboard-container">
      {/* Encabezado */}
      <Box className="dashboard-header">
        <Typography variant="h4" component="h1" gutterBottom>
          <i className="fas fa-chart-line" style={{ marginRight: '12px' }}></i>
          Dashboard de Análisis
        </Typography>
        <Typography variant="subtitle1" color="textSecondary" gutterBottom>
          Visualiza tu progreso y métricas de entrenamiento
        </Typography>
      </Box>

      {/* Filtros */}
      <FilterSection
        exerciseList={exerciseList}
        selectedExercise={selectedExercise}
        onExerciseChange={setSelectedExercise}
        dateFrom={dateFrom}
        onDateFromChange={setDateFrom}
        dateTo={dateTo}
        onDateToChange={setDateTo}
        onApplyFilters={applyFilters}
        loading={loadingChartData || loadingExercises} // Deshabilitar si carga algo
        loadingExercises={loadingExercises} // Para mostrar spinner en select
      />

      {/* Alerta de Error */}
      {error && (
        <Alert severity="warning" sx={{ mt: 2, mb: 2 }} onClose={() => setError(null)}>
          {typeof error === 'string' ? error : error}
        </Alert>
      )}

      {/* Contenido Principal (Métricas, Gráficos, Tabla) */}
      {loadingChartData ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '40vh' }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Cargando datos del gráfico...</Typography>
        </Box>
      ) : (
        <Grid container spacing={3} className="dashboard-content">
          {/* Métricas */}
          <Grid item xs={12} md={3}>
            <MetricsGrid metricsData={metricsData} />
          </Grid>

          {/* Gráfico Principal */}
          <Grid item xs={12} md={9}>
            <WeightProgressionChart data={sessionData} />
          </Grid>
          {/* <<< NUEVO: Gráfico e1RM >>> */}
           <Grid item xs={12} md={9}> {/* Ocupa el mismo espacio que el de peso */}
             <E1RMProgressionChart data={sessionData} />
           </Grid>

          {/* Tabla Sesiones */}
          <Grid item xs={12} lg={6}>
             <SessionsTable sessionData={sessionData} />
          </Grid>

          {/* Gráfico Volumen */}
          <Grid item xs={12} sm={6} lg={3}>
             <VolumeChart data={sessionData} />
          </Grid>

          {/* Gráfico Repeticiones */}
           <Grid item xs={12} sm={6} lg={3}>
             <RepsChart data={sessionData} />
          </Grid>

           {/* Mapa de Calor */}
           <Grid item xs={12}>
             <ActivityHeatmap />
           </Grid>
        </Grid>
      )}
    </Box>
  );
}

export default Dashboard;