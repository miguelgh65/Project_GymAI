// src/components/profile/fitbit/FitbitSleepData.js
import React from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Divider,
  CircularProgress 
} from '@mui/material';
import { 
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

function FitbitSleepData({ sleepData }) {
  const formatSleepData = () => {
    if (!sleepData || !sleepData.sleep || sleepData.sleep.length === 0) {
      return [];
    }
    
    // Usar el primer registro de sueño
    const sleep = sleepData.sleep[0];
    
    if (!sleep.levels || !sleep.levels.summary) {
      return [];
    }
    
    const summary = sleep.levels.summary;
    
    return [
      { name: 'Profundo', minutes: summary.deep?.minutes || 0 },
      { name: 'Ligero', minutes: summary.light?.minutes || 0 },
      { name: 'REM', minutes: summary.rem?.minutes || 0 },
      { name: 'Despierto', minutes: summary.wake?.minutes || 0 }
    ];
  };

  const sleepDataFormatted = formatSleepData();
  
  if (!sleepData || !sleepData.sleep || sleepData.sleep.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No hay datos de sueño disponibles
        </Typography>
      </Box>
    );
  }

  const sleep = sleepData.sleep[0];
  const sleepDuration = sleep.duration / 60000; // convertir de ms a minutos
  const sleepEfficiency = sleep.efficiency;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Resumen de Sueño
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Duración Total
              </Typography>
              <Typography variant="h5">
                {Math.floor(sleepDuration / 60)}h {Math.round(sleepDuration % 60)}m
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body2" color="text.secondary">
                Hora de Inicio
              </Typography>
              <Typography variant="body1">
                {new Date(sleep.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Hora de Fin
              </Typography>
              <Typography variant="body1">
                {new Date(sleep.endTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body2" color="text.secondary">
                Eficiencia del Sueño
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ position: 'relative', display: 'inline-flex', mr: 2 }}>
                  <CircularProgress
                    variant="determinate"
                    value={sleepEfficiency}
                    size={60}
                    thickness={5}
                    sx={{ color: sleepEfficiency > 90 ? 'success.main' : sleepEfficiency > 80 ? 'info.main' : 'warning.main' }}
                  />
                  <Box
                    sx={{
                      top: 0,
                      left: 0,
                      bottom: 0,
                      right: 0,
                      position: 'absolute',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography variant="body2" component="div" color="text.secondary">
                      {sleepEfficiency}%
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {sleepEfficiency > 90 ? 'Excelente' : sleepEfficiency > 80 ? 'Buena' : 'Regular'}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Fases del Sueño
            </Typography>
            
            <Box sx={{ height: 300, mt: 2 }}>
              {sleepDataFormatted.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={sleepDataFormatted}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis label={{ value: 'Minutos', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value) => [`${value} minutos`, 'Duración']} />
                    <Legend />
                    <Bar 
                      dataKey="minutes" 
                      name="Minutos" 
                      fill="#8884d8" 
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <Typography variant="body1" color="text.secondary">
                    No hay datos de fases del sueño disponibles
                  </Typography>
                </Box>
              )}
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                <strong>Sueño Profundo:</strong> Fase de recuperación física, importante para el sistema inmunológico y hormonal.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>REM:</strong> Fase asociada con el procesamiento emocional y la consolidación de la memoria.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

export default FitbitSleepData;