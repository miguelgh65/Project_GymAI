// src/components/nutrition/meal-plans/MealPlanForm/PlanSummary.js
import React from 'react';
import { 
  Typography, Grid, Paper, Box, Chip, Divider
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFire, faDrumstickBite, faAppleAlt, faOilCan
} from '@fortawesome/free-solid-svg-icons';

const PlanSummary = ({ items, days, targetCalories, targetProtein, targetCarbs, targetFat }) => {
  // Función para agrupar items por día
  const groupItemsByDay = () => {
    const grouped = {};
    
    days.forEach(day => {
      grouped[day] = items.filter(item => item.day_of_week === day);
    });
    
    return grouped;
  };
  
  // Función para calcular totales para un día
  const calculateDayTotals = (dayItems) => {
    const totals = {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    };
    
    dayItems.forEach(item => {
      if (item.calories) totals.calories += item.calories;
      if (item.protein_g) totals.protein_g += item.protein_g;
      if (item.carbohydrates_g) totals.carbs_g += item.carbohydrates_g;
      if (item.fat_g) totals.fat_g += item.fat_g;
    });
    
    return totals;
  };
  
  // Función para calcular totales del plan
  const calculatePlanTotals = () => {
    const totals = {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    };
    
    items.forEach(item => {
      if (item.calories) totals.calories += item.calories;
      if (item.protein_g) totals.protein_g += item.protein_g;
      if (item.carbohydrates_g) totals.carbs_g += item.carbohydrates_g;
      if (item.fat_g) totals.fat_g += item.fat_g;
    });
    
    return totals;
  };
  
  // Calcular porcentaje de progreso para los objetivos
  const calculateProgress = (totals) => {
    const progress = {
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0
    };
    
    if (targetCalories && totals.calories) {
      progress.calories = Math.min(100, Math.round((totals.calories / parseFloat(targetCalories)) * 100));
    }
    
    if (targetProtein && totals.protein_g) {
      progress.protein = Math.min(100, Math.round((totals.protein_g / parseFloat(targetProtein)) * 100));
    }
    
    if (targetCarbs && totals.carbs_g) {
      progress.carbs = Math.min(100, Math.round((totals.carbs_g / parseFloat(targetCarbs)) * 100));
    }
    
    if (targetFat && totals.fat_g) {
      progress.fat = Math.min(100, Math.round((totals.fat_g / parseFloat(targetFat)) * 100));
    }
    
    return progress;
  };
  
  // Obtener datos agrupados
  const groupedItems = groupItemsByDay();
  const planTotals = calculatePlanTotals();
  const progress = calculateProgress(planTotals);
  
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>Resumen del Plan</Typography>
      
      {/* Progreso total del plan */}
      {(targetCalories || targetProtein || targetCarbs || targetFat) && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Progreso del Plan Completo:
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
                      {planTotals.calories} / {targetCalories} kcal
                    </Typography>
                  </Box>
                  <Box sx={{ 
                    height: 8, 
                    width: '100%', 
                    bgcolor: 'grey.300',
                    borderRadius: 1,
                    position: 'relative'
                  }}>
                    <Box sx={{ 
                      height: '100%', 
                      width: `${progress.calories}%`,
                      bgcolor: progress.calories > 100 ? 'error.main' : 'primary.main',
                      borderRadius: 1
                    }} />
                  </Box>
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
                      {planTotals.protein_g} / {targetProtein}g
                    </Typography>
                  </Box>
                  <Box sx={{ 
                    height: 8, 
                    width: '100%', 
                    bgcolor: 'grey.300',
                    borderRadius: 1,
                    position: 'relative'
                  }}>
                    <Box sx={{ 
                      height: '100%', 
                      width: `${progress.protein}%`,
                      bgcolor: progress.protein > 100 ? 'error.main' : 'success.main',
                      borderRadius: 1
                    }} />
                  </Box>
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
                      {planTotals.carbs_g} / {targetCarbs}g
                    </Typography>
                  </Box>
                  <Box sx={{ 
                    height: 8, 
                    width: '100%', 
                    bgcolor: 'grey.300',
                    borderRadius: 1,
                    position: 'relative'
                  }}>
                    <Box sx={{ 
                      height: '100%', 
                      width: `${progress.carbs}%`,
                      bgcolor: progress.carbs > 100 ? 'error.main' : 'info.main',
                      borderRadius: 1
                    }} />
                  </Box>
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
                      {planTotals.fat_g} / {targetFat}g
                    </Typography>
                  </Box>
                  <Box sx={{ 
                    height: 8, 
                    width: '100%', 
                    bgcolor: 'grey.300',
                    borderRadius: 1,
                    position: 'relative'
                  }}>
                    <Box sx={{ 
                      height: '100%', 
                      width: `${progress.fat}%`,
                      bgcolor: progress.fat > 100 ? 'error.main' : 'warning.main',
                      borderRadius: 1
                    }} />
                  </Box>
                </Box>
              </Grid>
            )}
          </Grid>
        </Box>
      )}
      
      <Divider sx={{ my: 2 }} />
      
      {/* Resumen por día */}
      <Typography variant="subtitle2" gutterBottom>
        Comidas por Día:
      </Typography>
      
      <Grid container spacing={2}>
        {days.map((day) => {
          const dayItems = groupedItems[day] || [];
          const dayTotals = calculateDayTotals(dayItems);
          
          return (
            <Grid item key={day} xs={6} sm={4} md={3} lg={12/7}>
              <Paper 
                elevation={0} 
                variant="outlined"
                sx={{ 
                  p: 1.5, 
                  textAlign: 'center',
                  borderColor: dayItems.length ? 'primary.main' : 'grey.300',
                  borderWidth: dayItems.length ? 2 : 1
                }}
              >
                <Typography variant="subtitle2">{day}</Typography>
                <Chip 
                  label={`${dayItems.length} comidas`} 
                  color={dayItems.length ? "primary" : "default"}
                  size="small"
                  sx={{ mt: 1, mb: 1 }}
                />
                {dayItems.length > 0 && (
                  <Typography variant="caption" display="block" color="text.secondary">
                    {dayTotals.calories} kcal | P: {dayTotals.protein_g}g | 
                    C: {dayTotals.carbs_g}g | G: {dayTotals.fat_g}g
                  </Typography>
                )}
              </Paper>
            </Grid>
          );
        })}
      </Grid>
    </Paper>
  );
};

export default PlanSummary;