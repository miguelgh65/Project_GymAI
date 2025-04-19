// src/components/nutrition/dashboard/dashboard-components/WeeklySummary.js
import React from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, 
  Paper, LinearProgress
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChartLine, faFire, faDrumstickBite
} from '@fortawesome/free-solid-svg-icons';

const WeeklySummary = () => {
  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <FontAwesomeIcon icon={faChartLine} style={{ marginRight: '10px' }} />
          Resumen Semanal
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Próximamente: Una vista resumida de tu progreso alimenticio semanal comparado con tus objetivos.
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                <FontAwesomeIcon icon={faFire} style={{ marginRight: '8px' }} />
                Calorías Consumidas
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Próximamente: Seguimiento de tus calorías consumidas vs. objetivo
              </Typography>
              <LinearProgress variant="determinate" value={0} sx={{ height: 10, borderRadius: 5 }} />
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                <FontAwesomeIcon icon={faDrumstickBite} style={{ marginRight: '8px' }} />
                Proteínas Consumidas
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Próximamente: Seguimiento de proteínas consumidas vs. objetivo
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={0} 
                color="success"
                sx={{ height: 10, borderRadius: 5 }} 
              />
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default WeeklySummary;