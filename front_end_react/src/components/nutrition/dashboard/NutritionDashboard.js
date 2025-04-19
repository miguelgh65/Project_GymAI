// src/components/nutrition/dashboard/NutritionDashboard.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, Alert, CircularProgress, Grid } from '@mui/material';
import { NutritionCalculator, MealPlanService } from '../../../services/NutritionService';
import { useNavigate } from 'react-router-dom';

// Importaciones de componentes modulares
import ProfileMissing from './dashboard-components/ProfileMissing';
import ProfileSummary from './dashboard-components/ProfileSummary';
import DailyTracking from './dashboard-components/DailyTracking';
import PlanSelector from './dashboard-components/PlanSelector';
import WeeklySummary from './dashboard-components/WeeklySummary';

const NutritionDashboard = ({ user }) => {
  const [profile, setProfile] = useState(null);
  const [activePlans, setActivePlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  
  useEffect(() => {
    loadProfile();
    loadActivePlans();
  }, []);

  // En el método loadProfile del componente NutritionDashboard.js
const loadProfile = async () => {
  try {
    setLoading(true);
    console.log("Intentando cargar perfil nutricional...");
    const profileData = await NutritionCalculator.getProfile();
    console.log("Datos brutos del perfil:", profileData);
    
    if (profileData) {
      // Extraer directamente los valores específicos de la base de datos
      // Imprimimos todos los nombres de campo para depuración
      console.log("Nombres de campo disponibles:", Object.keys(profileData));
      
      // Extraer con más detalle los valores que necesitamos
      const goal_calories = profileData.daily_calories !== undefined ? 
        Number(profileData.daily_calories) : profileData.goal_calories !== undefined ? 
        Number(profileData.goal_calories) : 0;
      
      const target_protein_g = profileData.proteins_grams !== undefined ? 
        Number(profileData.proteins_grams) : profileData.target_protein_g !== undefined ? 
        Number(profileData.target_protein_g) : 0;
      
      const target_carbs_g = profileData.carbs_grams !== undefined ? 
        Number(profileData.carbs_grams) : profileData.target_carbs_g !== undefined ? 
        Number(profileData.target_carbs_g) : 0;
      
      const target_fat_g = profileData.fats_grams !== undefined ? 
        Number(profileData.fats_grams) : profileData.target_fat_g !== undefined ? 
        Number(profileData.target_fat_g) : 0;
      
      console.log("Valores extraídos del perfil:", {
        goal_calories,
        target_protein_g, 
        target_carbs_g,
        target_fat_g
      });
      
      // Normalizar nombres de campos para compatibilidad
      const normalizedProfile = {
        ...profileData,
        goal_calories,
        target_protein_g,
        target_carbs_g, 
        target_fat_g
      };
      
      console.log("Perfil normalizado:", normalizedProfile);
      setProfile(normalizedProfile);
    }
  } catch (err) {
    console.error("Error al cargar perfil nutricional:", err);
    setError("No se pudo cargar tu perfil nutricional.");
  } finally {
    setLoading(false);
  }
};

  const loadActivePlans = async () => {
    try {
      const plansResponse = await MealPlanService.getAll(true);
      if (plansResponse && plansResponse.meal_plans) {
        setActivePlans(plansResponse.meal_plans);
      }
    } catch (err) {
      console.error("Error cargando planes activos:", err);
    }
  };

  const goToMacroCalculator = () => {
    localStorage.setItem('nutrition_tab', '8');
    window.location.reload();
  };

  const createPlanWithProfile = () => {
    if (!profile || !hasTargets) {
      setError("El perfil nutricional no tiene objetivos completos");
      return;
    }
    
    localStorage.setItem('temp_nutrition_targets', JSON.stringify({
      target_calories: profile.goal_calories,
      target_protein_g: profile.target_protein_g,
      target_carbs_g: profile.target_carbs_g,
      target_fat_g: profile.target_fat_g
    }));
    
    navigate('/nutrition');
    localStorage.setItem('nutrition_tab', '2');
    window.location.reload();
  };

  const hasProfile = profile !== null;
  // Cambiar la condición hasTargets para ser más flexible
const hasTargets = hasProfile && 
profile.goal_calories !== undefined && profile.goal_calories !== null &&
profile.target_protein_g !== undefined && profile.target_protein_g !== null &&
profile.target_carbs_g !== undefined && profile.target_carbs_g !== null &&
profile.target_fat_g !== undefined && profile.target_fat_g !== null;
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom>Dashboard Nutricional</Typography>
      
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      
      {!hasProfile ? (
        <ProfileMissing onGoToCalculator={goToMacroCalculator} />
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <ProfileSummary 
              profile={profile} 
              onRecalculate={goToMacroCalculator} 
              onCreatePlan={createPlanWithProfile}
              hasTargets={hasTargets}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <DailyTracking />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <PlanSelector 
              profile={profile}
              activePlans={activePlans}
              hasTargets={hasTargets}
              onRefreshPlans={loadActivePlans}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <WeeklySummary />
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default NutritionDashboard;