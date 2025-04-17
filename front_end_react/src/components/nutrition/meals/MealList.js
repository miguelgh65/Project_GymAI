// front_end_react/src/components/nutrition/meals/MealList.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, CircularProgress, Alert, Grid, Paper, 
  Card, CardContent, CardMedia, CardActions, Button,
  IconButton, Chip, Tooltip, TextField, InputAdornment
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faPlus, faEdit, faTrash, faSearch, 
  faSync, faUtensils, faInfoCircle 
} from '@fortawesome/free-solid-svg-icons';
import { MealService } from '../../../services/NutritionService';
import { useNavigate } from 'react-router-dom';

const MealList = () => {
  const [meals, setMeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadMeals();
  }, []);

  const loadMeals = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await MealService.getAll(searchTerm);
      console.log("Comidas cargadas:", response);
      
      // Obtener comidas del objeto de respuesta
      let mealsList = [];
      if (response && response.meals) {
        mealsList = response.meals;
      } else if (Array.isArray(response)) {
        mealsList = response;
      }
      
      // Normalizar datos para visualización consistente
      const normalizedMeals = mealsList.map(meal => ({
        id: meal.id,
        name: meal.meal_name || meal.name || `Comida ${meal.id}`,
        description: meal.description || meal.recipe || meal.ingredients || '',
        calories: meal.calories || 0,
        proteins: meal.proteins || 0,
        carbohydrates: meal.carbohydrates || 0,
        fats: meal.fats || 0,
        image_url: meal.image_url || 'https://www.themealdb.com/images/media/meals/vwrpps1503068729.jpg'
      }));
      
      setMeals(normalizedMeals);
    } catch (err) {
      console.error("Error al cargar comidas:", err);
      setError("No se pudieron cargar las comidas. Por favor, intenta de nuevo más tarde.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadMeals();
  };

  const handleCreateMeal = () => {
    navigate('/nutrition');
    localStorage.setItem('nutrition_tab', '4'); // "Crear Comida" tab
    window.location.reload();
  };

  const handleEditMeal = (id) => {
    navigate('/nutrition');
    localStorage.setItem('nutrition_edit_meal_id', id);
    localStorage.setItem('nutrition_tab', '4'); // "Crear Comida" tab para edición
    window.location.reload();
  };

  const handleDeleteMeal = async (id, name) => {
    if (window.confirm(`¿Estás seguro que deseas eliminar la comida "${name}"?`)) {
      try {
        await MealService.delete(id);
        loadMeals(); // Recargar la lista
      } catch (err) {
        console.error(`Error al eliminar comida ${id}:`, err);
        setError(`No se pudo eliminar la comida "${name}". ${err.message}`);
      }
    }
  };

  const renderMealCard = (meal) => (
    <Card 
      elevation={2} 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'scale(1.02)',
          boxShadow: 3
        }
      }}
    >
      <CardMedia
        component="img"
        height="150"
        image={meal.image_url}
        alt={meal.name}
        sx={{ objectFit: 'cover' }}
      />
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" component="div" gutterBottom>
          {meal.name}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" noWrap sx={{ mb: 2 }}>
          {meal.description}
        </Typography>
        
        <Grid container spacing={1} sx={{ mt: 1 }}>
          <Grid item xs={6}>
            <Chip 
              size="small" 
              label={`${meal.calories} kcal`} 
              color="primary"
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
          </Grid>
          <Grid item xs={6}>
            <Chip 
              size="small" 
              label={`Prot: ${meal.proteins}g`} 
              color="success"
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
          </Grid>
          <Grid item xs={6}>
            <Chip 
              size="small" 
              label={`Carbs: ${meal.carbohydrates}g`} 
              color="info"
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
          </Grid>
          <Grid item xs={6}>
            <Chip 
              size="small" 
              label={`Grasas: ${meal.fats}g`} 
              color="warning"
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
          </Grid>
        </Grid>
      </CardContent>
      <CardActions sx={{ justifyContent: 'flex-end', p: 1 }}>
        <Tooltip title="Editar comida">
          <IconButton 
            size="small" 
            color="primary"
            onClick={() => handleEditMeal(meal.id)}
          >
            <FontAwesomeIcon icon={faEdit} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Eliminar comida">
          <IconButton 
            size="small" 
            color="error"
            onClick={() => handleDeleteMeal(meal.id, meal.name)}
          >
            <FontAwesomeIcon icon={faTrash} />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  );

  // Estado vacío - Sin comidas
  const renderEmptyState = () => (
    <Box sx={{ textAlign: 'center', py: 6, px: 2 }}>
      <Typography variant="h6" gutterBottom color="text.secondary">
        No hay comidas disponibles
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph sx={{ maxWidth: 500, mx: 'auto', mb: 4 }}>
        Crea tu primera comida para empezar a añadirla a tus planes de nutrición.
      </Typography>
      <Button
        variant="contained"
        size="large"
        startIcon={<FontAwesomeIcon icon={faPlus} />}
        onClick={handleCreateMeal}
      >
        Crear Primera Comida
      </Button>
    </Box>
  );

  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h1">
              <FontAwesomeIcon icon={faUtensils} style={{ marginRight: '10px' }} />
              Comidas Disponibles
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button 
                variant="outlined"
                startIcon={<FontAwesomeIcon icon={faSync} />}
                onClick={loadMeals}
              >
                Actualizar
              </Button>
              <Button 
                variant="contained" 
                color="primary"
                startIcon={<FontAwesomeIcon icon={faPlus} />}
                onClick={handleCreateMeal}
              >
                Nueva Comida
              </Button>
            </Box>
          </Box>
          
          <Box component="form" onSubmit={handleSearchSubmit} sx={{ display: 'flex', mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Buscar comidas..."
              value={searchTerm}
              onChange={handleSearchChange}
              variant="outlined"
              size="small"
              sx={{ mr: 1 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <FontAwesomeIcon icon={faSearch} />
                  </InputAdornment>
                ),
              }}
            />
            <Button 
              type="submit"
              variant="outlined" 
              startIcon={<FontAwesomeIcon icon={faSearch} />}
            >
              Buscar
            </Button>
          </Box>
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
              <Button size="small" sx={{ ml: 2 }} onClick={loadMeals}>
                Reintentar
              </Button>
            </Alert>
          )}
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 6 }}>
              <CircularProgress size={40} />
              <Typography sx={{ ml: 2 }}>Cargando comidas...</Typography>
            </Box>
          ) : (
            meals.length === 0 ? (
              renderEmptyState()
            ) : (
              <Grid container spacing={3}>
                {meals.map((meal) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={meal.id}>
                    {renderMealCard(meal)}
                  </Grid>
                ))}
              </Grid>
            )
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default MealList;