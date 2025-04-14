// src/components/profile/fitbit/FitbitActivityData.js
import React from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Box 
} from '@mui/material';

function FitbitActivityData({ activityData }) {
  if (!activityData) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No hay datos de actividad disponibles
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Resumen de Actividad
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={6}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Pasos
                  </Typography>
                  <Typography variant="h6">
                    {activityData.summary?.steps || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Objetivo: {activityData.goals?.steps || '-'}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={6}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Distancia
                  </Typography>
                  <Typography variant="h6">
                    {activityData.summary?.distances?.[0]?.distance || 0} km
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={6}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Pisos
                  </Typography>
                  <Typography variant="h6">
                    {activityData.summary?.floors || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Objetivo: {activityData.goals?.floors || '-'}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={6}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Calorías
                  </Typography>
                  <Typography variant="h6">
                    {activityData.summary?.caloriesOut || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Objetivo: {activityData.goals?.caloriesOut || '-'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Zonas de Actividad
            </Typography>
            {activityData.summary?.heartRateZones ? (
              <Box sx={{ mt: 2 }}>
                {activityData.summary.heartRateZones.map((zone, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">{zone.name}</Typography>
                      <Typography variant="body2">{zone.minutes} min</Typography>
                    </Box>
                    <Box
                      sx={{
                        height: 10,
                        width: '100%',
                        bgcolor: 'grey.200',
                        borderRadius: 5,
                        overflow: 'hidden'
                      }}
                    >
                      <Box
                        sx={{
                          height: '100%',
                          width: `${Math.min((zone.minutes / 30) * 100, 100)}%`,
                          bgcolor: index === 0 ? '#94d2bd' : 
                                index === 1 ? '#5fa8d3' : 
                                index === 2 ? '#f28482' : '#d00000',
                          borderRadius: 5
                        }}
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="body1" color="text.secondary">
                  No hay datos de zonas de actividad disponibles
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Actividades Registradas
            </Typography>
            {activityData.activities && activityData.activities.length > 0 ? (
              <Box sx={{ mt: 2 }}>
                {activityData.activities.map((activity, index) => (
                  <Box 
                    key={index} 
                    sx={{ 
                      p: 2, 
                      mb: 2, 
                      border: '1px solid', 
                      borderColor: 'divider',
                      borderRadius: 1,
                      bgcolor: 'background.paper'
                    }}
                  >
                    <Typography variant="subtitle1">
                      {activity.name}
                    </Typography>
                    <Grid container spacing={2} sx={{ mt: 0.5 }}>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          Duración
                        </Typography>
                        <Typography variant="body1">
                          {Math.floor(activity.duration / 60000)} min
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          Calorías
                        </Typography>
                        <Typography variant="body1">
                          {activity.calories}
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          Distancia
                        </Typography>
                        <Typography variant="body1">
                          {activity.distance ? `${activity.distance} ${activity.distanceUnit}` : '-'}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                ))}
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="body1" color="text.secondary">
                  No hay actividades registradas para este día
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

export default FitbitActivityData;