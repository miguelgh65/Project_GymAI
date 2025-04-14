// src/components/profile/fitbit/FitbitHeartRate.js
import React from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Divider 
} from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHeartbeat } from '@fortawesome/free-solid-svg-icons';

function FitbitHeartRate({ heartRateData, selectedDate }) {
  const formatHeartRateData = () => {
    if (!heartRateData || !heartRateData['activities-heart-intraday'] || !heartRateData['activities-heart-intraday'].dataset) {
      return [];
    }
    
    // Tomar una muestra de puntos para no sobrecargar el gráfico
    const dataset = heartRateData['activities-heart-intraday'].dataset;
    const sampledData = [];
    
    // Tomar un punto cada 10 minutos aproximadamente
    for (let i = 0; i < dataset.length; i += 10) {
      sampledData.push({
        time: dataset[i].time,
        value: dataset[i].value
      });
    }
    
    return sampledData;
  };

  const heartRateDataFormatted = formatHeartRateData();
  
  if (heartRateDataFormatted.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No hay datos de frecuencia cardíaca disponibles
        </Typography>
      </Box>
    );
  }

  // Obtener valores de resumen
  const heartRateSummary = heartRateData['activities-heart'][0].value || {};

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Resumen Cardíaco
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Frecuencia Cardíaca en Reposo
              </Typography>
              <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', color: '#e91e63' }}>
                <FontAwesomeIcon icon={faHeartbeat} style={{ marginRight: 8 }} />
                {heartRateSummary.restingHeartRate || '-'} bpm
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body2" color="text.secondary">
                Zonas Cardíacas
              </Typography>
              
              {heartRateSummary.heartRateZones && 
               heartRateSummary.heartRateZones.map((zone, index) => (
                <Box key={index} sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    {zone.name} ({zone.min}-{zone.max} bpm)
                  </Typography>
                  <Typography variant="body1">
                    {zone.minutes || 0} minutos
                  </Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Frecuencia Cardíaca Intradía
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {selectedDate}
            </Typography>
            
            <Box sx={{ height: 300, mt: 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={heartRateDataFormatted}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={['dataMin - 10', 'dataMax + 10']} />
                  <Tooltip 
                    formatter={(value) => [`${value} bpm`, 'Ritmo Cardíaco']}
                    labelFormatter={(time) => `Hora: ${time}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    name="Frecuencia Cardíaca" 
                    stroke="#e91e63" 
                    activeDot={{ r: 8 }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                La frecuencia cardíaca en reposo es un indicador clave de la salud cardiovascular. 
                Un valor más bajo generalmente indica un corazón más eficiente y mejor forma física.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

export default FitbitHeartRate;