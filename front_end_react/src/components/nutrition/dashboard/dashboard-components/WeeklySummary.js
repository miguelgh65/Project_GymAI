// src/components/nutrition/dashboard/dashboard-components/WeeklySummary.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, 
  Paper, LinearProgress, CircularProgress, Alert
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChartLine, faFire, faDrumstickBite, faAppleAlt, faOilCan
} from '@fortawesome/free-solid-svg-icons';
import TrackingService from '../../../../services/nutrition/TrackingService';
import { NutritionCalculator } from '../../../../services/NutritionService';

const WeeklySummary = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [weeklyData, setWeeklyData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [userProfile, setUserProfile] = useState(null);

  // Cargar datos al montar el componente
  useEffect(() => {
    loadData();
  }, []);

  // Cargar datos de la semana y perfil
  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Cargar perfil nutricional
      const profileData = await NutritionCalculator.getProfile();
      if (profileData) {
        setUserProfile(profileData.profile || profileData);
      }
      
      // Cargar datos de la semana
      const weekData = await TrackingService.getTrackingForWeek();
      setWeeklyData(weekData || []);
      
      // Cargar resumen semanal
      const summaryData = await TrackingService.getWeeklySummary();
      setSummary(summaryData);
      
    } catch (err) {
      console.error("Error al cargar datos semanales:", err);
      setError("No se pudieron cargar los datos semanales.");
    } finally {
      setLoading(false);
    }
  };

  // Calcular progreso de calorías
  const calculateCalorieProgress = () => {
    if (!userProfile || !weeklyData.length) return 0;
    
    const targetCalories = userProfile.goal_calories || userProfile.daily_calories || 0;
    if (!targetCalories) return 0;
    
    const totalConsumed = weeklyData.reduce((sum, day) => {
      return sum + (day.actual_calories || 0);
    }, 0);
    
    const targetWeeklyCalories = targetCalories * 7;
    const progress = (totalConsumed / targetWeeklyCalories) * 100;
    return Math.min(progress, 100);
  };

  // Calcular progreso de proteínas
  const calculateProteinProgress = () => {
    if (!userProfile || !summary) return 0;
    
    const targetProtein = userProfile.target_protein_g || userProfile.proteins_grams || 0;
    if (!targetProtein) return 0;
    
    const daysTracked = summary.total_days_tracked || 0;
    if (daysTracked === 0) return 0;
    
    // Este cálculo es aproximado ya que el backend no proporciona proteínas directamente
    // Idealmente, obtendríamos esto de los planes de comida o del seguimiento
    const avgCalories = summary.average_calories || 0;
    const estimatedProtein = (avgCalories * 0.3) / 4; // Estimación: 30% de calorías de proteína
    
    const progress = (estimatedProtein / targetProtein) * 100;
    return Math.min(progress, 100);
  };

  if (loading) {
    return (
      <Card elevation={3}>
        <CardContent sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <FontAwesomeIcon icon={faChartLine} style={{ marginRight: '10px' }} />
          Resumen Semanal
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {!weeklyData.length && !error ? (
          <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
            No hay datos de seguimiento registrados para esta semana.
          </Typography>
        ) : (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  <FontAwesomeIcon icon={faFire} style={{ marginRight: '8px' }} />
                  Calorías Consumidas
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {summary?.total_days_tracked ? (
                    `${Math.round(summary.average_calories || 0)} kcal en promedio por día (${summary.total_days_tracked} días)`
                  ) : 'Sin datos de seguimiento'}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={calculateCalorieProgress()} 
                  sx={{ height: 10, borderRadius: 5 }} 
                />
                <Typography variant="caption" sx={{ display: 'block', mt: 1, textAlign: 'right' }}>
                  {Math.round(calculateCalorieProgress())}% del objetivo semanal
                </Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  <FontAwesomeIcon icon={faDrumstickBite} style={{ marginRight: '8px' }} />
                  Proteínas Consumidas
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {userProfile?.target_protein_g ? (
                    `Objetivo: ${userProfile.target_protein_g}g por día`
                  ) : 'No hay objetivo de proteínas establecido'}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={calculateProteinProgress()} 
                  color="success"
                  sx={{ height: 10, borderRadius: 5 }} 
                />
                <Typography variant="caption" sx={{ display: 'block', mt: 1, textAlign: 'right' }}>
                  {Math.round(calculateProteinProgress())}% del objetivo semanal
                </Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={12}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Comidas Completadas Esta Semana
                </Typography>
                
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  {summary && Object.entries(summary.meals_completion || {}).map(([meal, count]) => (
                    <Grid item xs={4} sm={2.4} key={meal}>
                      <Box 
                        sx={{ 
                          p: 1, 
                          textAlign: 'center',
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1
                        }}
                      >
                        <Typography variant="h6" color="primary">{count}</Typography>
                        <Typography variant="caption">{meal}</Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
                
                {summary?.total_excess_deficit !== undefined && (
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      Balance calórico semanal: 
                      <span style={{ 
                        color: summary.total_excess_deficit <= 0 ? '#4caf50' : '#f44336',
                        marginLeft: '8px'
                      }}>
                        {summary.total_excess_deficit} kcal
                      </span>
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        )}
      </CardContent>
    </Card>
  );
};

export default WeeklySummary;