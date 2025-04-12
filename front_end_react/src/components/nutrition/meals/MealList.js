import React, { useState } from 'react';
import { 
  Box, Typography, Card, CardContent, 
  Table, TableBody, TableCell, TableContainer, TableHead, 
  TableRow, Paper, CircularProgress, Alert, IconButton, Tooltip, Button
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faSearch, faEdit, faTrash } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { useMeals } from '../../../hooks/useMeals';
import NutritionFilters from '../shared/NutritionFilters';
import { MealService } from '../../../services/NutritionService';
function MealList() {
  const { meals, loading, error, searchTerm, handleSearch, refreshMeals } = useMeals();
  const [deleteError, setDeleteError] = useState(null);
  const navigate = useNavigate();
  
  const handleCreateNew = () => {
    navigate('/nutrition/meals/new');
  };
  
  const handleEdit = (id) => {
    navigate(`/nutrition/meals/${id}/edit`);
  };
  
  const handleDelete = async (id, name) => {
    if (window.confirm(`¿Estás seguro que deseas eliminar la comida "${name}"?`)) {
      try {
        setDeleteError(null);
        await MealService.delete(id);
        refreshMeals();
      } catch (err) {
        console.error('Error deleting meal:', err);
        setDeleteError(err.response?.data?.detail || 'Error al eliminar comida');
      }
    }
  };
  
  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h1">
              Comidas
            </Typography>
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<FontAwesomeIcon icon={faPlus} />}
              onClick={handleCreateNew}
            >
              Nueva Comida
            </Button>
          </Box>
          
          <NutritionFilters 
            onSearch={handleSearch} 
            searchPlaceholder="Buscar comidas..."
          />
          
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
                    <TableCell>Descripción</TableCell>
                    <TableCell align="right">Calorías</TableCell>
                    <TableCell align="center">Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {meals.length > 0 ? (
                    meals.map((meal) => (
                      <TableRow key={meal.id}>
                        <TableCell>{meal.name}</TableCell>
                        <TableCell>{meal.description || '-'}</TableCell>
                        <TableCell align="right">{meal.calories} kcal</TableCell>
                        <TableCell align="center">
                          <Tooltip title="Editar">
                            <IconButton 
                              size="small" 
                              color="primary"
                              onClick={() => handleEdit(meal.id)}
                            >
                              <FontAwesomeIcon icon={faEdit} />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Eliminar">
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => handleDelete(meal.id, meal.name)}
                            >
                              <FontAwesomeIcon icon={faTrash} />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} align="center">
                        No se encontraron comidas
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

export default MealList;