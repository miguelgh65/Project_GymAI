import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Divider, Button,
  CircularProgress, Alert, Grid, Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faEdit, faTrash } from '@fortawesome/free-solid-svg-icons';
import { useNavigate, useParams } from 'react-router-dom';
import { IngredientService } from '../../../services/NutritionService';
import MacroDisplay from '../shared/MacroDisplay';

function IngredientDetail() {
  const [ingredient, setIngredient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { id } = useParams();
  const navigate = useNavigate();
  
  useEffect(() => {
    loadIngredient();
  }, [id]);
  
  const loadIngredient = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await IngredientService.getById(id);
      setIngredient(data);
    } catch (err) {
      console.error('Error loading ingredient:', err);
      setError('No se pudo cargar el ingrediente');
    } finally {
      setLoading(false);
    }
  };
  
  const handleEdit = () => {
    navigate(`/nutrition/ingredients/${id}/edit`);
  };
  
  const handleDelete = async () => {
    if (window.confirm('¿Estás seguro que deseas eliminar este ingrediente?')) {
      try {
        await IngredientService.delete(id);
        navigate('/nutrition/ingredients');
      } catch (err) {
        console.error('Error deleting ingredient:', err);
        setError(err.response?.data?.detail || 'Error al eliminar el ingrediente');
      }
    }
  };
  
  if (loading) {
    return (
      <Box sx={{ m: 2, display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Box sx={{ m: 2 }}>
        <Alert severity="error">{error}</Alert>
        <Button
          sx={{ mt: 2 }}
          variant="outlined"
          startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
          onClick={() => navigate('/nutrition/ingredients')}
        >
          Volver a Ingredientes
        </Button>
      </Box>
    );
  }
  
  if (!ingredient) {
    return (
      <Box sx={{ m: 2 }}>
        <Alert severity="info">El ingrediente no existe o ha sido eliminado.</Alert>
        <Button
          sx={{ mt: 2 }}
          variant="outlined"
          startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
          onClick={() => navigate('/nutrition/ingredients')}
        >
          Volver a Ingredientes
        </Button>
      </Box>
    );
  }
  
  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h1">
              {ingredient.ingredient_name}
            </Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<FontAwesomeIcon icon={faEdit} />}
                onClick={handleEdit}
                sx={{ mr: 1 }}
              >
                Editar
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<FontAwesomeIcon icon={faTrash} />}
                onClick={handleDelete}
              >
                Eliminar
              </Button>
            </Box>
          </Box>
          
          <Divider sx={{ mb: 3 }} />
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Detalles del Ingrediente</Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Calorías (por 100g):</Typography>
                  <Typography variant="body1" fontWeight="bold">{ingredient.calories}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Proteínas (g por 100g):</Typography>
                  <Typography variant="body1" fontWeight="bold">{ingredient.proteins}g</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Carbohidratos (g por 100g):</Typography>
                  <Typography variant="body1" fontWeight="bold">{ingredient.carbohydrates}g</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Grasas (g por 100g):</Typography>
                  <Typography variant="body1" fontWeight="bold">{ingredient.fats}g</Typography>
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <MacroDisplay
                calories={ingredient.calories}
                proteins={ingredient.proteins}
                carbs={ingredient.carbohydrates}
                fats={ingredient.fats}
                title="Distribución de Macros"
              />
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 3 }}>
            <Button
              variant="outlined"
              startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
              onClick={() => navigate('/nutrition/ingredients')}
            >
              Volver a Ingredientes
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default IngredientDetail;