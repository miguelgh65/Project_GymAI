// src/components/nutrition/dashboard/dashboard-components/WeeklySummary.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, 
  Paper, LinearProgress, CircularProgress, Alert,
  Divider, Tooltip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChartLine, faFire, faDrumstickBite, faAppleAlt, faOilCan,
  faCalendarWeek, faCheckCircle
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

  // Renderizar barra de progreso de calorías
  const renderCalorieProgress = () => {
    if (!summary) return null;
    
    // Usar los nuevos campos del resumen mejorado
    const plannedCalories = summary.planned_calories || 0;
    const consumedCalories = summary.consumed_calories || 0;
    const progressPercentage = summary.completion_percentage || 0;
    
    // Si no hay calorías planeadas, no mostrar progreso
    if (plannedCalories === 0) return null;
    
    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Progreso calórico semanal:
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Box sx={{ minWidth: 150 }}>
            <Typography variant="body2">
              {consumedCalories} / {plannedCalories} kcal
            </Typography>
          </Box>
          
          <Box sx={{ width: '100%', ml: 1 }}>
            <LinearProgress
              variant="determinate"
              value={Math.min(progressPercentage, 100)}
              color={progressPercentage > 110 ? "error" : 
                     progressPercentage > 100 ? "warning" : 
                     progressPercentage > 90 ? "success" : "primary"}
              sx={{ height: 10, borderRadius: 5 }}
            />
          </Box>
          
          <Box sx={{ minWidth: 50, textAlign: 'right', ml: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {progressPercentage}%
            </Typography>
          </Box>
        </Box>
        
        {progressPercentage > 100 ? (
          <Typography variant="caption" color="warning.main">
            Has superado tu objetivo semanal de calorías en un {progressPercentage - 100}%
          </Typography>
        ) : progressPercentage < 70 ? (
          <Typography variant="caption" color="error.main">
            Estás por debajo de tu objetivo semanal. Solo has consumido el {progressPercentage}% de tus calorías meta.
          </Typography>
        ) : (
          <Typography variant="caption" color="success.main">
            Buen progreso! Has consumido el {progressPercentage}% de tus calorías objetivo semanales.
          </Typography>
        )}
      </Box>
    );
  };

  // Renderizar barra de progreso de proteínas
  const renderProteinProgress = () => {
    if (!summary) return null;
    
    // Usar los nuevos campos del resumen mejorado
    const plannedProtein = summary.planned_protein || 0;
    const consumedProtein = summary.consumed_protein || 0;
    const progressPercentage = summary.protein_completion_percentage || 0;
    
    // Si no hay proteínas planeadas, no mostrar progreso
    if (plannedProtein === 0) return null;
    
    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Progreso de proteínas semanal:
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Box sx={{ minWidth: 150 }}>
            <Typography variant="body2">
              {consumedProtein} / {plannedProtein}g
            </Typography>
          </Box>
          
          <Box sx={{ width: '100%', ml: 1 }}>
            <LinearProgress
              variant="determinate"
              value={Math.min(progressPercentage, 100)}
              color={progressPercentage > 110 ? "warning" : 
                     progressPercentage > 100 ? "success" : 
                     progressPercentage > 80 ? "success" : "primary"}
              sx={{ height: 10, borderRadius: 5 }}
            />
          </Box>
          
          <Box sx={{ minWidth: 50, textAlign: 'right', ml: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {progressPercentage}%
            </Typography>
          </Box>
        </Box>
        
        {progressPercentage < 80 ? (
          <Typography variant="caption" color="warning.main">
            Considera aumentar tu consumo de proteínas para alcanzar tu objetivo semanal.
          </Typography>
        ) : (
          <Typography variant="caption" color="success.main">
            ¡Excelente! Has consumido el {progressPercentage}% de tus proteínas objetivo semanales.
          </Typography>
        )}
      </Box>
    );
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
          <Box>
            {/* Mostrar barras de progreso mejoradas */}
            {renderCalorieProgress()}
            {renderProteinProgress()}
            
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    <FontAwesomeIcon icon={faFire} style={{ marginRight: '8px' }} />
                    Resumen Calórico
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {summary?.total_days_tracked ? (
                      `${Math.round(summary.average_calories || 0)} kcal en promedio por día (${summary.total_days_tracked} días)`
                    ) : 'Sin datos de seguimiento'}
                  </Typography>
                  
                  {summary?.total_excess_deficit !== undefined && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" fontWeight="medium" sx={{
                        color: summary.total_excess_deficit <= 0 ? 'success.main' : 'warning.main'
                      }}>
                        Balance semanal: {summary.total_excess_deficit} kcal
                      </Typography>
                    </Box>
                  )}
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
                      `Objetivo: ${userProfile.target_protein_g}g por día (${userProfile.target_protein_g * 7}g semanales)`
                    ) : 'No hay objetivo de proteínas establecido'}
                  </Typography>
                  
                  {summary?.consumed_protein !== undefined && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" fontWeight="medium">
                        Total consumido: {summary.consumed_protein}g
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
              
              <Grid item xs={12}>
                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    <FontAwesomeIcon icon={faCalendarWeek} style={{ marginRight: '8px' }} />
                    Comidas Completadas Esta Semana
                  </Typography>
                  
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    {summary && Object.entries(summary.meals_completion || {}).map(([meal, count]) => {
                      const totalPossible = 7; // Una comida por día de la semana
                      const percentage = Math.round((count / totalPossible) * 100);
                      
                      return (
                        <Grid item xs={6} sm={4} md={2.4} key={meal}>
                          <Tooltip title={`${count} de ${totalPossible} días (${percentage}%)`}>
                            <Box 
                              sx={{ 
                                p: 1, 
                                textAlign: 'center',
                                border: '1px solid',
                                borderColor: percentage >= 80 ? 'success.main' : 'divider',
                                borderRadius: 1,
                                backgroundColor: percentage >= 80 ? 'success.light' : 'background.paper',
                              }}
                            >
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                                <FontAwesomeIcon 
                                  icon={faCheckCircle} 
                                  style={{ 
                                    marginRight: '5px', 
                                    color: percentage >= 80 ? '#2e7d32' : '#757575',
                                    opacity: percentage >= 80 ? 1 : 0.5
                                  }} 
                                />
                                <Typography variant="body2" fontWeight="medium">{meal}</Typography>
                              </Box>
                              <Typography variant="h6" color={percentage >= 80 ? 'success.dark' : 'text.primary'}>
                                {count}/{totalPossible}
                              </Typography>
                              <LinearProgress 
                                variant="determinate" 
                                value={percentage} 
                                color={percentage >= 80 ? "success" : "primary"}
                                sx={{ height: 5, borderRadius: 5, mt: 1 }}
                              />
                            </Box>
                          </Tooltip>
                        </Grid>
                      );
                    })}
                  </Grid>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default WeeklySummary;