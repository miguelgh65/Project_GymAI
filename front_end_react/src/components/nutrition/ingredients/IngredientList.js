import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, Card, CardContent, 
  Table, TableBody, TableCell, TableContainer, TableHead, 
  TableRow, Paper, CircularProgress, Alert, IconButton, Tooltip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faSearch, faEdit, faTrash, faSync } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { faLeaf } from '@fortawesome/free-solid-svg-icons';
import { IngredientService } from '../../../services/NutritionService';

function IngredientList() {
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteError, setDeleteError] = useState(null);
  const navigate = useNavigate();

  // Load ingredients on component mount
  useEffect(() => {
    refreshIngredients();
  }, []);
  
  const refreshIngredients = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await IngredientService.getAll(searchTerm);
      console.log('Raw API response:', result);
      
      // Handle different response formats
      let ingredientsList = [];
      if (Array.isArray(result)) {
        ingredientsList = result;
      } else if (result && Array.isArray(result.ingredients)) {
        ingredientsList = result.ingredients;
      } else if (result && typeof result === 'object') {
        // Fallback: try to detect ingredient data in the response
        ingredientsList = Object.values(result).find(val => Array.isArray(val)) || [];
      }
      
      // Normalize ingredient data
      const normalizedIngredients = ingredientsList.map(ing => ({
        id: ing.id,
        ingredient_name: ing.ingredient_name || ing.name || `Ingredient ${ing.id}`,
        calories: typeof ing.calories === 'number' ? ing.calories : 0,
        proteins: typeof ing.proteins === 'number' ? ing.proteins : 0,
        carbohydrates: typeof ing.carbohydrates === 'number' ? ing.carbohydrates : 0,
        fats: typeof ing.fats === 'number' ? ing.fats : 0
      }));
      
      console.log('Normalized ingredients:', normalizedIngredients);
      setIngredients(normalizedIngredients);
    } catch (err) {
      console.error('Error loading ingredients:', err);
      setError('Error al cargar ingredientes. Por favor, intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    refreshIngredients();
  };
  
  const handleCreateNew = () => {
    navigate('/nutrition');
    // Using localStorage to indicate the tab to open
    localStorage.setItem('nutrition_tab', '6'); // "Añadir Ingrediente" tab
    window.location.reload();
  };
  
  const handleEdit = (id) => {
    // Implement edit navigation logic
    console.log(`Edit ingredient: ${id}`);
    // This would typically navigate to an edit form
    // For now we'll just reload the nutrition page at the add ingredient tab
    navigate('/nutrition');
    localStorage.setItem('nutrition_tab', '6');
    localStorage.setItem('edit_ingredient_id', id);
    window.location.reload();
  };
  
  const handleDelete = async (id, name) => {
    if (window.confirm(`¿Estás seguro que deseas eliminar el ingrediente "${name}"?`)) {
      try {
        setDeleteError(null);
        await IngredientService.delete(id);
        refreshIngredients();
      } catch (err) {
        console.error('Error deleting ingredient:', err);
        setDeleteError(err.response?.data?.detail || 'Error al eliminar ingrediente');
      }
    }
  };
  
  // Render empty state when no ingredients
  const renderEmptyState = () => (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        No hay ingredientes disponibles
      </Typography>
      <Button
        variant="outlined"
        startIcon={<FontAwesomeIcon icon={faPlus} />}
        onClick={handleCreateNew}
        sx={{ mt: 2 }}
      >
        Añadir tu primer ingrediente
      </Button>
    </Box>
  );
  
  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h1">
              <FontAwesomeIcon icon={faLeaf} style={{ marginRight: '10px' }} />
              Ingredientes
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                variant="outlined"
                startIcon={<FontAwesomeIcon icon={faSync} />}
                onClick={refreshIngredients}
              >
                Actualizar
              </Button>
              <Button 
                variant="contained" 
                color="primary" 
                startIcon={<FontAwesomeIcon icon={faPlus} />}
                onClick={handleCreateNew}
              >
                Nuevo Ingrediente
              </Button>
            </Box>
          </Box>
          
          <Box component="form" onSubmit={handleSearchSubmit} sx={{ display: 'flex', mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Buscar ingredientes..."
              value={searchTerm}
              onChange={handleSearchChange}
              variant="outlined"
              size="small"
              sx={{ mr: 1 }}
            />
            <Button 
              type="submit"
              variant="outlined" 
              startIcon={<FontAwesomeIcon icon={faSearch} />}
            >
              Buscar
            </Button>
          </Box>
          
          {(error || deleteError) && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setDeleteError(null)}>
              {error || deleteError}
            </Alert>
          )}
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
              <CircularProgress />
            </Box>
          ) : ingredients.length === 0 ? (
            renderEmptyState()
          ) : (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Nombre</TableCell>
                    <TableCell align="right">Calorías</TableCell>
                    <TableCell align="right">Proteínas (g)</TableCell>
                    <TableCell align="right">Carbohidratos (g)</TableCell>
                    <TableCell align="right">Grasas (g)</TableCell>
                    <TableCell align="center">Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {ingredients.map((ingredient) => (
                    <TableRow key={ingredient.id}>
                      <TableCell>{ingredient.ingredient_name}</TableCell>
                      <TableCell align="right">{ingredient.calories}</TableCell>
                      <TableCell align="right">{ingredient.proteins}</TableCell>
                      <TableCell align="right">{ingredient.carbohydrates}</TableCell>
                      <TableCell align="right">{ingredient.fats}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="Editar">
                          <IconButton 
                            size="small" 
                            color="primary"
                            onClick={() => handleEdit(ingredient.id)}
                          >
                            <FontAwesomeIcon icon={faEdit} />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Eliminar">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDelete(ingredient.id, ingredient.ingredient_name)}
                          >
                            <FontAwesomeIcon icon={faTrash} />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default IngredientList;