// src/components/nutrition/meal-plans/MealPlanForm/PlanBasicInfo.js
import React from 'react';
import { 
  Typography, TextField, FormControlLabel, Checkbox,
  Grid, Paper
} from '@mui/material';

const PlanBasicInfo = ({ name, description, isActive, onChange }) => {
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>Información General</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <TextField
            required
            fullWidth
            id="planName"
            label="Nombre del Plan"
            name="planName"
            value={name}
            onChange={(e) => onChange('name', e.target.value)}
            error={!name.trim()}
            helperText={!name.trim() ? "El nombre es obligatorio" : ""}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="description"
            label="Descripción (Opcional)"
            name="description"
            value={description}
            onChange={(e) => onChange('description', e.target.value)}
            multiline
            rows={1}
          />
        </Grid>
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Checkbox
                checked={isActive}
                onChange={(e) => onChange('is_active', e.target.checked)}
                name="isActive"
                color="primary"
              />
            }
            label="Plan Activo"
          />
        </Grid>
      </Grid>
    </Paper>
  );
};

export default PlanBasicInfo;