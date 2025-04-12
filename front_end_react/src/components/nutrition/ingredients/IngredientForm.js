import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, Card, CardContent, 
  CardActions, Grid, Alert, CircularProgress, Divider 
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSave, faArrowLeft, faPlusCircle, faEdit } from '@fortawesome/free-solid-svg-icons';
import { useNavigate, useParams } from 'react-router-dom';
import { IngredientService } from '../../../services/NutritionService';

function IngredientForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = Boolean(id);
  
  const [formData, setFormData] = useState({
    ingredient_name: '',
    calories: '',
    proteins: '',
    carbohydrates: '',
    fats: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formSuccess, setFormSuccess] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  
  useEffect(() => {
    if (isEditing) {
      loadIngredient();
    }
  }, [id]);
  
  const loadIngredient = async () => {
    try {
      setLoading(true);
      const ingredient = await IngredientService.getById(id);
      setFormData({
        ingredient_name: ingredient.ingredient_name || '',
        calories: ingredient.calories || '',
        proteins: ingredient.proteins || '',
        carbohydrates: ingredient.carbohydrates || '',
        fats: ingredient.fats || ''
      });
    } catch (err) {
      console.error('Error loading ingredient:', err);
      setFormError('No se pudo cargar el ingrediente. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };
  
  const validateForm = () => {
    const errors = {};
    
    if (!formData.ingredient_name.trim()) {
      errors.ingredient_name = 'El nombre del ingrediente es obligatorio';
    }
    
    const numericFields = ['calories', 'proteins', 'carbohydrates', 'fats'];
    numericFields.forEach(field => {
      if (formData[field] === '') {
        errors[field] = 'Este campo es obligatorio';
      } else if (isNaN(formData[field]) || parseFloat(formData[field]) < 0) {
        errors[field] = 'Debe ser un número mayor o igual a 0';
      }
    });
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear validation error when field is updated
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setFormError(null);
    setFormSuccess(false);
    
    try {
      // Convert numeric fields to numbers
      const numericData = {
        ...formData,
        calories: parseFloat(formData.calories),
        proteins: parseFloat(formData.proteins),
        carbohydrates: parseFloat(formData.carbohydrates),
        fats: parseFloat(formData.fats)
      };
      
      if (isEditing) {
        await IngredientService.update(id, numericData);
      } else {
        await IngredientService.create(numericData);
      }
      
      setFormSuccess(true);
      
      // Navigate back after short delay if successful
      setTimeout(() => {
        navigate('/nutrition/ingredients');
      }, 1500);
    } catch (err) {
      console.error('Error saving ingredient:', err);
      setFormError(err.response?.data?.detail || 'Error al guardar el ingrediente');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <form onSubmit={handleSubmit}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5" component="h1">
                <FontAwesomeIcon icon={isEditing ? faEdit : faPlusCircle} style={{ marginRight: '10px' }} />
                {isEditing ? 'Editar Ingrediente' : 'Nuevo Ingrediente'}
              </Typography>
            </Box>
            
            <Divider sx={{ mb: 3 }} />
            
            {formError && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {formError}
              </Alert>
            )}
            
            {formSuccess && (
              <Alert severity="success" sx={{ mb: 3 }}>
                {isEditing ? 'Ingrediente actualizado exitosamente' : 'Ingrediente creado exitosamente'}
              </Alert>
            )}
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  name="ingredient_name"
                  label="Nombre del Ingrediente"
                  value={formData.ingredient_name}
                  onChange={handleChange}
                  fullWidth
                  required
                  error={Boolean(validationErrors.ingredient_name)}
                  helperText={validationErrors.ingredient_name}
                  disabled={loading}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  name="calories"
                  label="Calorías (por 100g)"
                  type="number"
                  value={formData.calories}
                  onChange={handleChange}
                  fullWidth
                  required
                  inputProps={{ min: 0, step: "0.1" }}
                  error={Boolean(validationErrors.calories)}
                  helperText={validationErrors.calories}
                  disabled={loading}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  name="proteins"
                  label="Proteínas (g por 100g)"
                  type="number"
                  value={formData.proteins}
                  onChange={handleChange}
                  fullWidth
                  required
                  inputProps={{ min: 0, step: "0.1" }}
                  error={Boolean(validationErrors.proteins)}
                  helperText={validationErrors.proteins}
                  disabled={loading}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  name="carbohydrates"
                  label="Carbohidratos (g por 100g)"
                  type="number"
                  value={formData.carbohydrates}
                  onChange={handleChange}
                  fullWidth
                  required
                  inputProps={{ min: 0, step: "0.1" }}
                  error={Boolean(validationErrors.carbohydrates)}
                  helperText={validationErrors.carbohydrates}
                  disabled={loading}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  name="fats"
                  label="Grasas (g por 100g)"
                  type="number"
                  value={formData.fats}
                  onChange={handleChange}
                  fullWidth
                  required
                  inputProps={{ min: 0, step: "0.1" }}
                  error={Boolean(validationErrors.fats)}
                  helperText={validationErrors.fats}
                  disabled={loading}
                />
              </Grid>
            </Grid>
          </CardContent>
          
          <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
            <Button
              variant="outlined"
              startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
              onClick={() => navigate('/nutrition/ingredients')}
              disabled={loading}
              sx={{ mr: 1 }}
            >
              Cancelar
            </Button>
            
            <Button
              type="submit"
              variant="contained"
              color="primary"
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
              disabled={loading}
            >
              {loading ? 'Guardando...' : 'Guardar'}
            </Button>
          </CardActions>
        </form>
      </Card>
    </Box>
  );
}

export default IngredientForm;