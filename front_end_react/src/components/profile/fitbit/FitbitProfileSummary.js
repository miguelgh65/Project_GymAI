// src/components/profile/fitbit/FitbitProfileSummary.js
import React from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Box 
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faRunning, 
  faFireAlt, 
  faHeartbeat, 
  faBed 
} from '@fortawesome/free-solid-svg-icons';

function FitbitProfileSummary({ profileData, activityData, sleepData }) {
  if (!profileData || !profileData.user) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No hay datos de perfil disponibles
        </Typography>
      </Box>
    );
  }

  const user = profileData.user;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Datos Personales
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body1">
                <strong>Nombre:</strong> {user.displayName}
              </Typography>
              <Typography variant="body1">
                <strong>Edad:</strong> {user.age} años
              </Typography>
              <Typography variant="body1">
                <strong>Género:</strong> {user.gender === 'MALE' ? 'Masculino' : 'Femenino'}
              </Typography>
              <Typography variant="body1">
                <strong>Altura:</strong> {user.height} cm
              </Typography>
              <Typography variant="body1">
                <strong>Peso:</strong> {user.weight} kg
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Datos de Fitness
            </Typography>
            {activityData ? (
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <FontAwesomeIcon icon={faRunning} size="2x" color="#1976d2" />
                    <Typography variant="h5" sx={{ mt: 1 }}>
                      {activityData.summary?.steps || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pasos
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <FontAwesomeIcon icon={faFireAlt} size="2x" color="#e91e63" />
                    <Typography variant="h5" sx={{ mt: 1 }}>
                      {activityData.summary?.caloriesOut || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Calorías
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <FontAwesomeIcon icon={faHeartbeat} size="2x" color="#f44336" />
                    <Typography variant="h5" sx={{ mt: 1 }}>
                      {activityData.summary?.restingHeartRate || '-'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      FC Reposo
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <FontAwesomeIcon icon={faBed} size="2x" color="#9c27b0" />
                    <Typography variant="h5" sx={{ mt: 1 }}>
                      {sleepData?.summary?.totalMinutesAsleep 
                        ? Math.floor(sleepData.summary.totalMinutesAsleep / 60) + 'h ' + (sleepData.summary.totalMinutesAsleep % 60) + 'm'
                        : '-'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Sueño
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            ) : (
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="body1" color="text.secondary">
                  No hay datos de actividad disponibles
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

export default FitbitProfileSummary;