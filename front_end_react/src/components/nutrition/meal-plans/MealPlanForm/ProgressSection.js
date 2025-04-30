// src/components/nutrition/meal-plans/MealPlanForm/ProgressSection.js
import React from 'react';
import { 
  Box, Typography, Grid, LinearProgress, 
  Tooltip, Paper, Divider 
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFire, faDrumstickBite, faAppleAlt, faOilCan
} from '@fortawesome/free-solid-svg-icons';

const ProgressSection = ({ 
  targetCalories, targetProtein, targetCarbs, targetFat, 
  items, activeDay 
}) => {
  // Calcular totales del día activo
  const calculateDayTotals = () => {
    // Filtrar items para el día activo
    const filteredItems = items.filter(item => item.day_of_week === activeDay);
    console.log(`Items para ${activeDay}:`, filteredItems);
    
    const totals = {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    };
    
    // Procesar cada item sumando sus valores
    filteredItems.forEach(item => {
      // Para cada propiedad, verificar que es un número válido
      const itemCalories = parseFloat(item.calories) || 0;
      totals.calories += itemCalories;
      
      // Ser flexible con los nombres de las propiedades
      let protein = 0;
      if (item.protein_g !== undefined) protein = parseFloat(item.protein_g);
      else if (item.proteins !== undefined) protein = parseFloat(item.proteins);
      totals.protein_g += protein || 0;
      
      let carbs = 0;
      if (item.carbohydrates_g !== undefined) carbs = parseFloat(item.carbohydrates_g);
      else if (item.carbs_g !== undefined) carbs = parseFloat(item.carbs_g);
      else if (item.carbohydrates !== undefined) carbs = parseFloat(item.carbohydrates);
      totals.carbs_g += carbs || 0;
      
      let fat = 0;
      if (item.fat_g !== undefined) fat = parseFloat(item.fat_g);
      else if (item.fats !== undefined) fat = parseFloat(item.fats);
      else if (item.fats_g !== undefined) fat = parseFloat(item.fats_g);
      totals.fat_g += fat || 0;
    });
    
    console.log(`Totales calculados para ${activeDay}:`, totals);
    return totals;
  };
  
  // Cálculos
  const dayTotals = calculateDayTotals();
  
  // Calcular el objetivo diario (usar valores directamente, sin dividir)
  const getDailyTarget = (value) => {
    // Si no hay valor objetivo, devolver 0
    if (!value) return 0;
    
    // Convertir a número
    const numValue = parseFloat(value) || 0;
    return numValue;
  };
  
  // Calcular el porcentaje de progreso
  const getProgress = (current, target) => {
    // Convertir a números si son strings
    const numCurrent = parseFloat(current) || 0;
    const numTarget = parseFloat(target) || 0;
    
    if (!numTarget || numTarget <= 0) return 0;
    return Math.min(100, (numCurrent / numTarget) * 100);
  };
  
  // Calcular color según progreso
  const getProgressColor = (current, target) => {
    if (!target || target <= 0) return "primary";
    const percentage = (current / target) * 100;
    if (percentage > 110) return "error";
    if (percentage > 95) return "success"; 
    return "primary";
  };
  
  // Si no hay objetivos definidos, no mostrar nada
  if (!targetCalories && !targetProtein && !targetCarbs && !targetFat) {
    return null;
  }
  
  // Valores diarios objetivo
  const dailyCalories = getDailyTarget(targetCalories);
  const dailyProtein = getDailyTarget(targetProtein);
  const dailyCarbs = getDailyTarget(targetCarbs);
  const dailyFat = getDailyTarget(targetFat);
  
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Progreso para {activeDay}
      </Typography>
      
      <Grid container spacing={2}>
        {parseFloat(targetCalories) > 0 && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={faFire} style={{ marginRight: '8px', color: '#f44336' }} />
                  Calorías
                </Typography>
                <Tooltip title={`Objetivo diario: ${dailyCalories} kcal`}>
                  <Typography variant="body2" fontWeight="medium">
                    {Math.round(dayTotals.calories)} / {dailyCalories} kcal
                  </Typography>
                </Tooltip>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.calories, dailyCalories)} 
                color={getProgressColor(dayTotals.calories, dailyCalories)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
        
        {parseFloat(targetProtein) > 0 && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={faDrumstickBite} style={{ marginRight: '8px', color: '#4caf50' }} />
                  Proteínas
                </Typography>
                <Tooltip title={`Objetivo diario: ${dailyProtein}g`}>
                  <Typography variant="body2" fontWeight="medium">
                    {Math.round(dayTotals.protein_g)} / {dailyProtein}g
                  </Typography>
                </Tooltip>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.protein_g, dailyProtein)} 
                color={getProgressColor(dayTotals.protein_g, dailyProtein)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
        
        {parseFloat(targetCarbs) > 0 && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={faAppleAlt} style={{ marginRight: '8px', color: '#2196f3' }} />
                  Carbohidratos
                </Typography>
                <Tooltip title={`Objetivo diario: ${dailyCarbs}g`}>
                  <Typography variant="body2" fontWeight="medium">
                    {Math.round(dayTotals.carbs_g)} / {dailyCarbs}g
                  </Typography>
                </Tooltip>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.carbs_g, dailyCarbs)} 
                color={getProgressColor(dayTotals.carbs_g, dailyCarbs)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
        
        {parseFloat(targetFat) > 0 && (
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={faOilCan} style={{ marginRight: '8px', color: '#ff9800' }} />
                  Grasas
                </Typography>
                <Tooltip title={`Objetivo diario: ${dailyFat}g`}>
                  <Typography variant="body2" fontWeight="medium">
                    {Math.round(dayTotals.fat_g)} / {dailyFat}g
                  </Typography>
                </Tooltip>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(dayTotals.fat_g, dailyFat)} 
                color={getProgressColor(dayTotals.fat_g, dailyFat)}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>
        )}
      </Grid>
      
      <Box sx={{ mt: 2, pt: 2, borderTop: '1px dashed rgba(0, 0, 0, 0.12)' }}>
        <Typography variant="subtitle2" color="text.secondary">
          Progreso Semanal Total:
        </Typography>
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          {parseFloat(targetCalories) > 0 && (
            <Grid item xs={6} sm={3}>
              <Tooltip title={`${dayTotals.calories} de ${dailyCalories} kcal diarias`}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Calorías</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {Math.round((dayTotals.calories / dailyCalories) * 100) || 0}%
                  </Typography>
                </Box>
              </Tooltip>
            </Grid>
          )}
          
          {parseFloat(targetProtein) > 0 && (
            <Grid item xs={6} sm={3}>
              <Tooltip title={`${dayTotals.protein_g} de ${dailyProtein}g diarios`}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Proteínas</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {Math.round((dayTotals.protein_g / dailyProtein) * 100) || 0}%
                  </Typography>
                </Box>
              </Tooltip>
            </Grid>
          )}
          
          {parseFloat(targetCarbs) > 0 && (
            <Grid item xs={6} sm={3}>
              <Tooltip title={`${dayTotals.carbs_g} de ${dailyCarbs}g diarios`}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Carbohidratos</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {Math.round((dayTotals.carbs_g / dailyCarbs) * 100) || 0}%
                  </Typography>
                </Box>
              </Tooltip>
            </Grid>
          )}
          
          {parseFloat(targetFat) > 0 && (
            <Grid item xs={6} sm={3}>
              <Tooltip title={`${dayTotals.fat_g} de ${dailyFat}g diarios`}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Grasas</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {Math.round((dayTotals.fat_g / dailyFat) * 100) || 0}%
                  </Typography>
                </Box>
              </Tooltip>
            </Grid>
          )}
        </Grid>
      </Box>
    </Paper>
  );
};

export default ProgressSection;