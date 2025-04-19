// src/components/nutrition/meal-plans/MealPlanForm/ProgressSection.js
import React from 'react';
import { 
  Typography, Grid, LinearProgress, Box, Divider
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFire, faDrumstickBite, faAppleAlt, faOilCan
} from '@fortawesome/free-solid-svg-icons';

const ProgressSection = ({ 
  targetCalories, targetProtein, targetCarbs, targetFat, 
  items, activeDay 
}) => {
  // No mostrar nada si no hay objetivos configurados
  if (!targetCalories && !targetProtein && !targetCarbs && !targetFat) {
    return null;
  }
  
  // Función para calcular totales del día activo
  const calculateDayTotals = () => {
    const filteredItems = items.filter(item => item.day_of_week === activeDay);
    
    const totals = {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    };
    
    filteredItems.forEach(item => {
      if (item.calories) totals.calories += item.calories;
      if (item.protein_g) totals.protein_g += item.protein_g;
      if (item.carbohydrates_g) totals.carbs_g += item.carbohydrates_g;
      if (item.fat_g) totals.fat_g += item.fat_g;
    });
    
    return totals;
  };
  
  // Cálculos
  const dayTotals = calculateDayTotals();
  
  // Calcular el objetivo diario (dividiendo entre 7)
  const getDailyTarget = (value) => {
    if (!value) return 0;
    return Math.round(parseInt(value) / 7);
  };
  
  // Calcular el porcentaje de progreso
  const getProgress = (current, target) => {
    if (!target || target <= 0) return 0;
    return Math.min(100, (current / target) * 100);
  };
  
  // Calcular color según progreso
  const getProgressColor = (current, target) => {
    if (!target || target <= 0) return "primary";
    return current > target ? "error" : "primary";
  };
  
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle1" gutterBottom>
        Progreso para {activeDay}:
      </Typography>
      
      <Grid container spacing={2}>
        {targetCalories && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" display="block">
                  <FontAwesomeIcon icon={faFire} /> Calorías
                </Typography>
                <Typography variant="caption" display="block">
                  {dayTotals.calories} / {getDailyTarget(targetCalories)} kcal
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.calories, getDailyTarget(targetCalories))} 
                color={getProgressColor(dayTotals.calories, getDailyTarget(targetCalories))}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
        
        {targetProtein && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" display="block">
                  <FontAwesomeIcon icon={faDrumstickBite} /> Proteínas
                </Typography>
                <Typography variant="caption" display="block">
                  {dayTotals.protein_g} / {getDailyTarget(targetProtein)}g
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.protein_g, getDailyTarget(targetProtein))} 
                color={getProgressColor(dayTotals.protein_g, getDailyTarget(targetProtein))}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
        
        {targetCarbs && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" display="block">
                  <FontAwesomeIcon icon={faAppleAlt} /> Carbohidratos
                </Typography>
                <Typography variant="caption" display="block">
                  {dayTotals.carbs_g} / {getDailyTarget(targetCarbs)}g
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.carbs_g, getDailyTarget(targetCarbs))} 
                color={getProgressColor(dayTotals.carbs_g, getDailyTarget(targetCarbs))}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
        
        {targetFat && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" display="block">
                  <FontAwesomeIcon icon={faOilCan} /> Grasas
                </Typography>
                <Typography variant="caption" display="block">
                  {dayTotals.fat_g} / {getDailyTarget(targetFat)}g
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.fat_g, getDailyTarget(targetFat))} 
                color={getProgressColor(dayTotals.fat_g, getDailyTarget(targetFat))}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
      </Grid>
      
      <Divider sx={{ mt: 2 }} />
    </Box>
  );
};

export default ProgressSection;