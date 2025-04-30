// src/components/nutrition/dashboard/dashboard-components/ProfileSummary.js
import React from 'react';
import { 
  Box, Typography, Card, CardContent, Button, Grid, 
  Paper, Divider, Chip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faCalculator, faPlus, faChartPie
} from '@fortawesome/free-solid-svg-icons';

const ProfileSummary = ({ profile, onRecalculate, onCreatePlan, hasTargets }) => {
    const calculateMacroPercentages = () => {
        if (!profile) return { protein: 0, carbs: 0, fat: 0 };
        
        // Asegurar que todos son números y tienen valores positivos
        const proteinGrams = Math.max(0, Number(profile.target_protein_g) || 0);
        const carbsGrams = Math.max(0, Number(profile.target_carbs_g) || 0);
        const fatGrams = Math.max(0, Number(profile.target_fat_g) || 0);
        
        console.log("Valores para cálculo de porcentajes:", {
          proteinGrams,
          carbsGrams,
          fatGrams
        });
        
        const proteinCals = proteinGrams * 4;
        const carbsCals = carbsGrams * 4;
        const fatCals = fatGrams * 9;
        const totalCals = proteinCals + carbsCals + fatCals;
        
        console.log("Calorías calculadas:", {
          proteinCals,
          carbsCals,
          fatCals,
          totalCals
        });
        
        if (totalCals === 0) return { protein: 0, carbs: 0, fat: 0 };
        
        return {
          protein: Math.round((proteinCals / totalCals) * 100) || 0,
          carbs: Math.round((carbsCals / totalCals) * 100) || 0,
          fat: Math.round((fatCals / totalCals) * 100) || 0
        };
      };
  
  const macroPercentages = calculateMacroPercentages();
  
  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <FontAwesomeIcon icon={faChartPie} style={{ marginRight: '10px' }} />
          Tus Objetivos Nutricionales
        </Typography>
        
        <Box sx={{ mt: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Objetivo Diario: {profile.goal_calories || 0} kcal
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Basado en tus características físicas, nivel de actividad y meta de {profile.goal || 'mantenimiento'}.
                </Typography>
              </Box>
              
              <Divider sx={{ mb: 2 }} />
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#e8f5e9' }}>
                <Typography variant="h5" color="#2e7d32">
                  {profile.target_protein_g || 0}g
                </Typography>
                <Typography variant="body2">Proteínas</Typography>
                <Typography variant="caption" display="block">
                  {macroPercentages.protein}% de calorías
                </Typography>
                <Chip 
                  label={`Diario`}
                  size="small"
                  color="success"
                  sx={{ mt: 1 }}
                />
              </Paper>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#e3f2fd' }}>
                <Typography variant="h5" color="#1565c0">
                  {profile.target_carbs_g || 0}g
                </Typography>
                <Typography variant="body2">Carbohidratos</Typography>
                <Typography variant="caption" display="block">
                  {macroPercentages.carbs}% de calorías
                </Typography>
                <Chip 
                  label={`Diario`}
                  size="small"
                  color="primary"
                  sx={{ mt: 1 }}
                />
              </Paper>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#fff3e0' }}>
                <Typography variant="h5" color="#e65100">
                  {profile.target_fat_g || 0}g
                </Typography>
                <Typography variant="body2">Grasas</Typography>
                <Typography variant="caption" display="block">
                  {macroPercentages.fat}% de calorías
                </Typography>
                <Chip 
                  label={`Diario`}
                  size="small"
                  color="warning"
                  sx={{ mt: 1 }}
                />
              </Paper>
            </Grid>
          </Grid>
        </Box>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<FontAwesomeIcon icon={faCalculator} />}
            onClick={onRecalculate}
          >
            Recalcular Objetivos
          </Button>
          
          <Button
            variant="outlined"
            color="primary"
            startIcon={<FontAwesomeIcon icon={faPlus} />}
            onClick={onCreatePlan}
            disabled={!hasTargets}
          >
            Crear Plan con Estos Objetivos
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ProfileSummary;