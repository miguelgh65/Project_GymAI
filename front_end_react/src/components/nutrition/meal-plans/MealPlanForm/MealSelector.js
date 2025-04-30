// src/components/nutrition/meal-plans/MealPlanForm/MealSelector.js
import React, { useState } from 'react';
import { 
  Typography, TextField, Button, Grid, Autocomplete,
  Paper, Box
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faPlus, faCoffee, faSun, 
  faUtensils, faCookie, faMoon, faEllipsisH
} from '@fortawesome/free-solid-svg-icons';

const MealSelector = ({ meals, onAddMeal }) => {
  const [selectedMeal, setSelectedMeal] = useState(null);
  const [quantity, setQuantity] = useState('100');
  const [unit, setUnit] = useState('g');
  const [mealType, setMealType] = useState('Desayuno');
  
  // Lista de tipos de comida
  const mealTypes = [
    { value: 'Desayuno', label: 'Desayuno', icon: faCoffee },
    { value: 'Almuerzo', label: 'Almuerzo', icon: faSun },
    { value: 'Comida', label: 'Comida', icon: faUtensils },
    { value: 'Merienda', label: 'Merienda', icon: faCookie },
    { value: 'Cena', label: 'Cena', icon: faMoon },
    { value: 'Otro', label: 'Otro', icon: faEllipsisH }
  ];
  
  const handleAddClick = () => {
    if (!selectedMeal) return;
    
    onAddMeal(selectedMeal, quantity, unit, mealType);
    
    // Restablecer selección
    setSelectedMeal(null);
    setQuantity('100');
  };
  
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>Añadir Comidas al Plan</Typography>
      
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} md={4}>
          <Autocomplete
            options={meals || []}
            getOptionLabel={(option) => option?.name || option?.meal_name || ''}
            value={selectedMeal}
            onChange={(event, newValue) => setSelectedMeal(newValue)}
            isOptionEqualToValue={(option, value) => option?.id === value?.id}
            renderInput={(params) => (
              <TextField {...params} label="Seleccionar Comida" required fullWidth />
            )}
            renderOption={(props, option) => (
              <li {...props}>
                <Box>
                  <Typography variant="body2">
                    {option.name || option.meal_name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {option.calories || '?'} kcal | P: {option.protein_g || option.proteins || '?'}g | 
                    C: {option.carbohydrates_g || option.carbohydrates || '?'}g | 
                    G: {option.fat_g || option.fats || '?'}g
                  </Typography>
                </Box>
              </li>
            )}
          />
        </Grid>
        <Grid item xs={6} md={2}>
          <TextField
            select
            label="Tipo de Comida"
            value={mealType}
            onChange={(e) => setMealType(e.target.value)}
            fullWidth
            SelectProps={{ native: true }}
          >
            {mealTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={3} md={2}>
          <TextField
            label="Cantidad"
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            fullWidth
            inputProps={{ min: 0, step: "any" }}
          />
        </Grid>
        <Grid item xs={3} md={2}>
          <TextField
            label="Unidad"
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            fullWidth
            placeholder="g"
          />
        </Grid>
        <Grid item xs={12} md={2}>
          <Button
            variant="contained"
            onClick={handleAddClick}
            startIcon={<FontAwesomeIcon icon={faPlus} />}
            fullWidth
            disabled={!selectedMeal}
            sx={{ height: '56px' }}
          >
            Añadir
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default MealSelector;