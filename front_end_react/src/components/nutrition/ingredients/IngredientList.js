import React, { useState } from 'react';
import { 
  Box, Typography, TextField, Button, Card, CardContent, 
  Table, TableBody, TableCell, TableContainer, TableHead, 
  TableRow, Paper, CircularProgress, Alert, IconButton, Tooltip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faSearch, faEdit, faTrash } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { useIngredients } from '../../../hooks/useIngredients';
import { faLeaf } from '@fortawesome/free-solid-svg-icons';
import { IngredientService } from 'services/NutritionService'; 
function IngredientList() {
  const { ingredients, loading, error, searchTerm, handleSearch, refreshIngredients } = useIngredients();
  const [localSearch, setLocalSearch] = useState('');
  const [deleteError, setDeleteError] = useState(null);
  const navigate = useNavigate();
  
  const handleSearchChange = (e) => {
    setLocalSearch(e.target.value);
  };
  
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    handleSearch(localSearch);
  };
  
  const handleCreateNew = () => {
    navigate('/nutrition/ingredients/new');
  };
  
  const handleEdit = (id) => {
    navigate(`/nutrition/ingredients/${id}/edit`);
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
  
  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h1">
              <FontAwesomeIcon icon={faLeaf} style={{ marginRight: '10px' }} />
              Ingredientes
            </Typography>
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<FontAwesomeIcon icon={faPlus} />}
              onClick={handleCreateNew}
            >
              Nuevo Ingrediente
            </Button>
          </Box>
          
          <Box component="form" onSubmit={handleSearchSubmit} sx={{ display: 'flex', mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Buscar ingredientes..."
              value={localSearch}
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
                  {ingredients.length > 0 ? (
                    ingredients.map((ingredient) => (
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
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        No se encontraron ingredientes
                      </TableCell>
                    </TableRow>
                  )}
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