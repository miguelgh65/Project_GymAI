import React from 'react';
import { TextField, Grid, Typography, Box } from '@mui/material';

/**
 * Componente para mostrar y editar los objetivos nutricionales del plan.
 * @param {object} targets - Objeto con { target_calories, target_protein_g, target_carbs_g, target_fat_g }
 * @param {function} onChange - Callback que se llama con el objeto de targets actualizado.
 * @param {object} errors - Objeto con errores de validación para los campos.
 */
function NutritionTargetInputs({ targets, onChange, errors, disabled }) { // Añadido disabled prop
  const handleChange = (event) => {
    const { name, value } = event.target;
    // Permitir borrar el campo, convertir a número si no está vacío
    const numericValue = value === '' ? '' : Number(value);
    if (value === '' || (!isNaN(numericValue) && numericValue >= 0)) {
        onChange({ ...targets, [name]: numericValue });
    }
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom>Target Macros</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            label="Calories"
            name="target_calories"
            type="number"
            value={targets?.target_calories ?? ''} // Usar optional chaining y ??
            onChange={handleChange}
            error={!!errors?.target_calories}
            helperText={errors?.target_calories}
            fullWidth
            inputProps={{ min: 0 }}
            disabled={disabled} // Aplicar disabled
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            label="Protein (g)"
            name="target_protein_g"
            type="number"
            value={targets?.target_protein_g ?? ''}
            onChange={handleChange}
            error={!!errors?.target_protein_g}
            helperText={errors?.target_protein_g}
            fullWidth
             inputProps={{ min: 0 }}
             disabled={disabled} // Aplicar disabled
          />
        </Grid>
         <Grid item xs={12} sm={6} md={3}>
          <TextField
            label="Carbs (g)"
            name="target_carbs_g"
            type="number"
            value={targets?.target_carbs_g ?? ''}
            onChange={handleChange}
             error={!!errors?.target_carbs_g}
             helperText={errors?.target_carbs_g}
            fullWidth
             inputProps={{ min: 0 }}
             disabled={disabled} // Aplicar disabled
          />
        </Grid>
         <Grid item xs={12} sm={6} md={3}>
          <TextField
            label="Fat (g)"
            name="target_fat_g"
            type="number"
            value={targets?.target_fat_g ?? ''}
            onChange={handleChange}
             error={!!errors?.target_fat_g}
             helperText={errors?.target_fat_g}
            fullWidth
             inputProps={{ min: 0 }}
             disabled={disabled} // Aplicar disabled
          />
        </Grid>
      </Grid>
    </Box>
  );
}

export default NutritionTargetInputs;