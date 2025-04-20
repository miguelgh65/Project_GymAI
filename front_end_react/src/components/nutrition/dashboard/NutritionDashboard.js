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

  // Función corregida para cargar correctamente los macros
  const loadProfile = async () => {
    try {
      setLoading(true);
      console.log("Intentando cargar perfil nutricional...");
      const response = await NutritionCalculator.getProfile();
      console.log("Respuesta completa del perfil:", response);
      
      // Verificar si tenemos la respuesta dentro de un objeto 'profile'
      const profileData = response.profile || response;
      
      if (profileData) {
        console.log("Datos del perfil:", profileData);
        console.log("Campos disponibles:", Object.keys(profileData));
        
        // Crear objeto normalizado
        let normalizedProfile = { ...profileData };
        
        // 1. Extraer macros del objeto anidado si existe
        if (profileData.macros) {
          console.log("Macros disponibles en formato anidado:", profileData.macros);
          
          // Extraer proteínas
          if (profileData.macros.protein && profileData.macros.protein.grams !== undefined) {
            normalizedProfile.target_protein_g = Number(profileData.macros.protein.grams);
          }
          
          // Extraer carbohidratos
          if (profileData.macros.carbs && profileData.macros.carbs.grams !== undefined) {
            normalizedProfile.target_carbs_g = Number(profileData.macros.carbs.grams);
          }
          
          // Extraer grasas
          if (profileData.macros.fat && profileData.macros.fat.grams !== undefined) {
            normalizedProfile.target_fat_g = Number(profileData.macros.fat.grams);
          }
        }
        
        // 2. Si no se encontraron macros anidados o son 0, intentar con campos directos
        if (!normalizedProfile.target_protein_g) {
          normalizedProfile.target_protein_g = Number(profileData.proteins_grams || profileData.target_protein_g || 0);
        }
        
        if (!normalizedProfile.target_carbs_g) {
          normalizedProfile.target_carbs_g = Number(profileData.carbs_grams || profileData.target_carbs_g || 0);
        }
        
        if (!normalizedProfile.target_fat_g) {
          normalizedProfile.target_fat_g = Number(profileData.fats_grams || profileData.target_fat_g || 0);
        }
        
        // Extraer calorías - probar varios posibles nombres de campo
        normalizedProfile.goal_calories = Number(
          profileData.goal_calories || 
          profileData.daily_calories || 
          0
        );
        
        console.log("Valores de macros extraídos:", {
          goal_calories: normalizedProfile.goal_calories,
          target_protein_g: normalizedProfile.target_protein_g,
          target_carbs_g: normalizedProfile.target_carbs_g,
          target_fat_g: normalizedProfile.target_fat_g
        });
        
        console.log("Perfil normalizado final:", normalizedProfile);
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
  
  // Verificar que todos los objetivos nutricionales existen y son mayores que 0
  const hasTargets = hasProfile && 
    profile.goal_calories > 0 &&
    profile.target_protein_g > 0 &&
    profile.target_carbs_g > 0 &&
    profile.target_fat_g > 0;
  
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