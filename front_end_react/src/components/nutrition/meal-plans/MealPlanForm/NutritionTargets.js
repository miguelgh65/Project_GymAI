// src/components/nutrition/meal-plans/MealPlanForm/NutritionTargets.js
import React, { useEffect } from 'react';
import { 
  Typography, TextField, Grid, Paper, Box, Alert, IconButton, Tooltip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle, faSync } from '@fortawesome/free-solid-svg-icons';

const NutritionTargets = ({ calories, protein, carbs, fat, profile, onChange }) => {
  // Esta función normaliza los campos del perfil para garantizar que obtenemos los valores
  // sin importar la estructura con la que vengan del backend
  const normalizeProfileValues = (profile) => {
    if (!profile) return null;
    
    const normalized = { ...profile };
    
    // Asegurar que tenemos todos los campos necesarios, buscar en diferentes posibles ubicaciones
    
    // Calorías
    normalized.goal_calories = profile.goal_calories || 
                              profile.daily_calories || 
                              profile.target_calories || 
                              0;
    
    // Proteínas (varias formas en que puede aparecer el campo)
    normalized.target_protein_g = profile.target_protein_g || 
                                 profile.proteins_grams || 
                                 (profile.macros?.protein?.grams) || 
                                 profile.proteins || 
                                 0;
    
    // Carbohidratos
    normalized.target_carbs_g = profile.target_carbs_g || 
                               profile.carbs_grams || 
                               (profile.macros?.carbs?.grams) || 
                               profile.carbohydrates || 
                               0;
    
    // Grasas
    normalized.target_fat_g = profile.target_fat_g || 
                             profile.fats_grams || 
                             (profile.macros?.fat?.grams) || 
                             profile.fats || 
                             0;
    
    console.log("Perfil normalizado:", normalized);
    return normalized;
  };
  
  // Normalizar el perfil
  const normalizedProfile = normalizeProfileValues(profile);

  // Efecto para cargar objetivos al iniciar
  useEffect(() => {
    // Verificar localStorage primero
    if ((!calories || !protein || !carbs || !fat) && localStorage.getItem('temp_nutrition_targets')) {
      try {
        const savedTargets = JSON.parse(localStorage.getItem('temp_nutrition_targets'));
        
        // Solo actualizamos los valores que estén vacíos
        if (savedTargets) {
          if (!calories && savedTargets.target_calories) {
            onChange('calories', savedTargets.target_calories.toString());
          }
          if (!protein && savedTargets.target_protein_g) {
            onChange('protein', savedTargets.target_protein_g.toString());
          }
          if (!carbs && savedTargets.target_carbs_g) {
            onChange('carbs', savedTargets.target_carbs_g.toString());
          }
          if (!fat && savedTargets.target_fat_g) {
            onChange('fat', savedTargets.target_fat_g.toString());
          }
        }
      } catch (error) {
        console.error("Error parsing saved nutrition targets:", error);
      }
    }
    
    // Si no hay valores establecidos y tenemos un perfil normalizado, usar esos valores
    if (normalizedProfile) {
      if (!calories && normalizedProfile.goal_calories) {
        onChange('calories', normalizedProfile.goal_calories.toString());
      }
      if (!protein && normalizedProfile.target_protein_g) {
        onChange('protein', normalizedProfile.target_protein_g.toString());
      }
      if (!carbs && normalizedProfile.target_carbs_g) {
        onChange('carbs', normalizedProfile.target_carbs_g.toString());
      }
      if (!fat && normalizedProfile.target_fat_g) {
        onChange('fat', normalizedProfile.target_fat_g.toString());
      }
    }
  }, [calories, protein, carbs, fat, normalizedProfile, onChange]);

  // Función para aplicar todos los objetivos del perfil normalizado
  const applyProfileTargets = () => {
    if (!normalizedProfile) return;
    
    if (normalizedProfile.goal_calories) {
      onChange('calories', normalizedProfile.goal_calories.toString());
    }
    if (normalizedProfile.target_protein_g) {
      onChange('protein', normalizedProfile.target_protein_g.toString());
    }
    if (normalizedProfile.target_carbs_g) {
      onChange('carbs', normalizedProfile.target_carbs_g.toString());
    }
    if (normalizedProfile.target_fat_g) {
      onChange('fat', normalizedProfile.target_fat_g.toString());
    }
  };

  // Comprobar si hay un perfil con objetivos
  const hasProfileTargets = normalizedProfile && (
    normalizedProfile.goal_calories || 
    normalizedProfile.target_protein_g || 
    normalizedProfile.target_carbs_g || 
    normalizedProfile.target_fat_g
  );

  // Función auxiliar para calcular el porcentaje de macronutrientes
  const calculatePercentage = (primary, secondary, tertiary, primaryMultiplier, secondaryMultiplier, tertiaryMultiplier) => {
    // Convertir a números para asegurar cálculo correcto
    const primaryValue = Number(primary) || 0;
    const secondaryValue = Number(secondary) || 0;
    const tertiaryValue = Number(tertiary) || 0;
    
    // Calcular calorías para cada macronutriente
    const primaryCal = primaryValue * primaryMultiplier;
    const secondaryCal = secondaryValue * secondaryMultiplier;
    const tertiaryCal = tertiaryValue * tertiaryMultiplier;
    
    // Calcular el total de calorías
    const total = primaryCal + secondaryCal + tertiaryCal;
    
    // Evitar división por cero
    if (total === 0) return 0;
    
    // Devolver el porcentaje redondeado
    return Math.round((primaryCal / total) * 100);
  };

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Objetivos Nutricionales</Typography>
        
        {hasProfileTargets && (
          <Tooltip title="Aplicar todos los objetivos de tu perfil nutricional">
            <IconButton 
              size="small" 
              color="primary" 
              onClick={applyProfileTargets}
              sx={{ ml: 1 }}
            >
              <FontAwesomeIcon icon={faSync} />
            </IconButton>
          </Tooltip>
        )}
      </Box>
      
      {!hasProfileTargets && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <FontAwesomeIcon icon={faInfoCircle} style={{ marginRight: '8px' }} />
          No tienes un perfil nutricional configurado. Puedes establecer tus objetivos manualmente o calcularlos en la pestaña "Calculadora".
        </Alert>
      )}
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            label="Calorías objetivo (kcal)"
            type="number"
            value={calories}
            onChange={(e) => onChange('calories', e.target.value)}
            InputProps={{ inputProps: { min: 0 } }}
            helperText={normalizedProfile?.goal_calories ? 
                       `Tu perfil: ${normalizedProfile.goal_calories} kcal` : ''}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            label="Proteínas objetivo (g)"
            type="number"
            value={protein}
            onChange={(e) => onChange('protein', e.target.value)}
            InputProps={{ inputProps: { min: 0 } }}
            helperText={normalizedProfile?.target_protein_g ? 
                       `Tu perfil: ${normalizedProfile.target_protein_g}g` : ''}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            label="Carbohidratos objetivo (g)"
            type="number"
            value={carbs}
            onChange={(e) => onChange('carbs', e.target.value)}
            InputProps={{ inputProps: { min: 0 } }}
            helperText={normalizedProfile?.target_carbs_g ? 
                       `Tu perfil: ${normalizedProfile.target_carbs_g}g` : ''}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            label="Grasas objetivo (g)"
            type="number"
            value={fat}
            onChange={(e) => onChange('fat', e.target.value)}
            InputProps={{ inputProps: { min: 0 } }}
            helperText={normalizedProfile?.target_fat_g ? 
                       `Tu perfil: ${normalizedProfile.target_fat_g}g` : ''}
          />
        </Grid>
      </Grid>
      
      {calories && protein && carbs && fat && (
        <Box mt={2} pt={2} borderTop="1px dashed" borderColor="divider">
          <Typography variant="body2" color="text.secondary">
            Distribución: Proteínas {calculatePercentage(protein, carbs, fat, 4, 4, 9)}%, 
            Carbohidratos {calculatePercentage(carbs, protein, fat, 4, 4, 9)}%, 
            Grasas {calculatePercentage(fat, protein, carbs, 9, 4, 4)}%
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            Los objetivos se reparten entre los 7 días de la semana. 
            Objetivo diario: {Math.round(Number(calories) / 7)} kcal, 
            {Math.round(Number(protein) / 7)}g proteína, 
            {Math.round(Number(carbs) / 7)}g carbohidratos, 
            {Math.round(Number(fat) / 7)}g grasas
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default NutritionTargets;