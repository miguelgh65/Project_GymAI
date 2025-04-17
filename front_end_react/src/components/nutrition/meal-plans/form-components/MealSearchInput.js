import React, { useEffect } from 'react';
import {
  Autocomplete,
  TextField,
  CircularProgress,
  Typography,
  Paper,
  Box,
  Chip,
  ListItem,
  ListItemText,
} from '@mui/material';
// Importar FontAwesomeIcon y los iconos necesarios
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faBowlFood, faSearch } from '@fortawesome/free-solid-svg-icons';

/**
 * Componente mejorado para buscar comidas disponibles y añadirlas al plan.
 * Usa Autocomplete de MUI para implementar un desplegable con filtro.
 * 
 * @param {Array} availableMeals - Lista de comidas disponibles desde el hook useAvailableMeals.
 * @param {boolean} isLoading - Estado de carga de las comidas.
 * @param {string|null} error - Mensaje de error si la carga falló.
 * @param {function} onAddMeal - Callback llamado con el objeto 'meal' cuando se selecciona una comida.
 * @param {boolean} disabled - Si el componente debe estar deshabilitado.
 */
function MealSearchInput({ availableMeals = [], isLoading, error, onAddMeal, disabled }) {
  // Agregamos un log para ver qué tipo de datos estamos recibiendo
  useEffect(() => {
    console.log("MealSearchInput recibió availableMeals:", availableMeals);
    if (availableMeals && availableMeals.length > 0) {
      console.log("Primer elemento:", availableMeals[0]);
      console.log("Tipo de primer elemento:", Array.isArray(availableMeals[0]) ? "Array" : "Objeto");
    }
  }, [availableMeals]);

  // Procesar los datos para manejar cualquier formato
  const processedMeals = React.useMemo(() => {
    if (!availableMeals || availableMeals.length === 0) {
      return [];
    }

    try {
      return availableMeals.map((meal, index) => {
        try {
          // Si es un array (tupla SQL), convertirlo a objeto
          if (Array.isArray(meal)) {
            return {
              id: meal[0],
              name: meal[1] || 'Sin nombre',
              recipe: meal[2] || '',
              ingredients: meal[3] || '',
              calories: typeof meal[4] === 'number' ? meal[4] : parseFloat(meal[4] || 0),
              protein_g: typeof meal[5] === 'number' ? meal[5] : parseFloat(meal[5] || 0),
              carbohydrates_g: typeof meal[6] === 'number' ? meal[6] : parseFloat(meal[6] || 0),
              fat_g: typeof meal[7] === 'number' ? meal[7] : parseFloat(meal[7] || 0),
              image_url: meal[8] || ''
            };
          } 
          
          // Si ya es un objeto, asegurarse de que tenga todas las propiedades
          return {
            id: meal.id,
            name: meal.name || meal.meal_name || 'Sin nombre',
            calories: typeof meal.calories === 'number' ? meal.calories : parseFloat(meal.calories || 0),
            protein_g: typeof meal.protein_g === 'number' ? meal.protein_g : 
                       typeof meal.proteins === 'number' ? meal.proteins : 
                       parseFloat(meal.protein_g || meal.proteins || 0),
            carbohydrates_g: typeof meal.carbohydrates_g === 'number' ? meal.carbohydrates_g : 
                             typeof meal.carbohydrates === 'number' ? meal.carbohydrates : 
                             parseFloat(meal.carbohydrates_g || meal.carbohydrates || 0),
            fat_g: typeof meal.fat_g === 'number' ? meal.fat_g : 
                   typeof meal.fats === 'number' ? meal.fats : 
                   parseFloat(meal.fat_g || meal.fats || 0)
          };
        } catch (e) {
          console.error(`Error procesando meal[${index}]:`, e, meal);
          return null;
        }
      }).filter(meal => meal !== null); // Filtrar elementos que fallaron
    } catch (e) {
      console.error("Error general procesando availableMeals:", e);
      return [];
    }
  }, [availableMeals]);

  // Loguear los resultados procesados
  useEffect(() => {
    if (processedMeals.length > 0) {
      console.log(`Procesadas ${processedMeals.length} comidas:`, processedMeals[0]);
    }
  }, [processedMeals]);

  return (
    <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        <FontAwesomeIcon icon={faBowlFood} style={{ marginRight: '10px' }} />
        Search & Add Meals
      </Typography>
      
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error loading meals: {error}
        </Typography>
      )}
      
      <Autocomplete
        id="meal-search-autocomplete"
        options={processedMeals}
        getOptionLabel={(option) => option.name || ''}
        loading={isLoading}
        disabled={disabled}
        onChange={(event, selectedMeal) => {
          if (selectedMeal) {
            console.log("Comida seleccionada:", selectedMeal);
            onAddMeal(selectedMeal);
            // Reset la selección (opcional, dependiendo de UX)
            event.target.blur();
            return false; // Para resetear la selección
          }
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Search and select meals to add"
            placeholder="Type to search meals..."
            fullWidth
            InputProps={{
              ...params.InputProps,
              startAdornment: (
                <FontAwesomeIcon icon={faSearch} style={{ marginRight: '10px', color: '#757575' }} />
              ),
              endAdornment: (
                <>
                  {isLoading ? <CircularProgress color="inherit" size={20} /> : null}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
          />
        )}
        renderOption={(props, option) => (
          <ListItem
            {...props}
            sx={{ 
              borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
              '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
              cursor: 'pointer',
              py: 1
            }}
          >
            <ListItemText
              primary={
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body1">{option.name}</Typography>
                  <FontAwesomeIcon icon={faPlus} style={{ color: '#1976d2' }} />
                </Box>
              }
              secondary={
                <Box mt={0.5}>
                  <Chip 
                    label={`${option.calories || 0} cal`} 
                    size="small" 
                    sx={{ mr: 0.5, backgroundColor: 'rgba(76, 175, 80, 0.1)' }} 
                  />
                  <Chip 
                    label={`P: ${option.protein_g || 0}g`} 
                    size="small" 
                    sx={{ mr: 0.5, backgroundColor: 'rgba(33, 150, 243, 0.1)' }} 
                  />
                  <Chip 
                    label={`C: ${option.carbohydrates_g || 0}g`} 
                    size="small" 
                    sx={{ mr: 0.5, backgroundColor: 'rgba(255, 152, 0, 0.1)' }} 
                  />
                  <Chip 
                    label={`F: ${option.fat_g || 0}g`} 
                    size="small" 
                    sx={{ backgroundColor: 'rgba(244, 67, 54, 0.1)' }} 
                  />
                </Box>
              }
            />
          </ListItem>
        )}
        noOptionsText={
          <Typography sx={{ textAlign: 'center', py: 2, color: 'text.secondary' }}>
            No meals found. Try different search terms.
          </Typography>
        }
      />
      
      {processedMeals.length === 0 && !isLoading && !error && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
          No meals available. Add some meals first or check your connection.
        </Typography>
      )}
    </Paper>
  );
}

export default MealSearchInput;