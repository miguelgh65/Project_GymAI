// src/components/nutrition/meal-plans/MealPlanForm/NutritionTargets.js
import React from 'react';
import { 
  Typography, TextField, Grid, Paper
} from '@mui/material';

const NutritionTargets = ({ calories, protein, carbs, fat, profile, onChange }) => {
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>Objetivos Nutricionales</Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            label="Calorías objetivo (kcal)"
            type="number"
            value={calories}
            onChange={(e) => onChange('calories', e.target.value)}
            InputProps={{ inputProps: { min: 0 } }}
            helperText={profile?.goal_calories ? 
                       `Tu perfil: ${profile.goal_calories} kcal` : ''}
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
            helperText={profile?.target_protein_g ? 
                       `Tu perfil: ${profile.target_protein_g}g` : ''}
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
            helperText={profile?.target_carbs_g ? 
                       `Tu perfil: ${profile.target_carbs_g}g` : ''}
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
            helperText={profile?.target_fat_g ? 
                       `Tu perfil: ${profile.target_fat_g}g` : ''}
          />
        </Grid>
      </Grid>
    </Paper>
  );
};

export default NutritionTargets;