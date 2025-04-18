// front_end_react/src/components/nutrition/meal-plans/MealPlanList.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, CircularProgress, Alert, Grid, Paper, 
  Card, CardContent, Button, IconButton, Chip, Divider,
  FormControlLabel, Switch
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faPlus, faEdit, faTrash, faSync, faUtensils, 
  faInfoCircle, faClipboardList, faCalendarWeek
} from '@fortawesome/free-solid-svg-icons';
import { MealPlanService } from '../../../services/NutritionService';
import { useNavigate } from 'react-router-dom';

const MealPlanList = ({ onCreateNew, onEdit }) => {
  const [mealPlans, setMealPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showActive, setShowActive] = useState(true);
  const [usingLocalOnly, setUsingLocalOnly] = useState(false);
  const navigate = useNavigate();

  // Función para cargar planes de comida
  const fetchMealPlans = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log("Cargando planes de comida...");
      
      // Limpiar caché para obtener datos frescos
      if (MealPlanService.clearCache) {
        MealPlanService.clearCache();
      }
      
      const response = await MealPlanService.getAll(showActive ? true : null);
      console.log("Respuesta de planes:", response);
      
      // Obtener planes de la respuesta
      const plans = response?.meal_plans || [];
      
      // Guardar planes en el estado
      setMealPlans(plans);
      
      // Indicar si sólo usamos planes locales
      setUsingLocalOnly(response.fromCache || response.fromLocalStorage || false);
      
    } catch (err) {
      console.error("Error al cargar planes de comida:", err);
      setError(err.message || 'Error al cargar los planes de comida.');
    } finally {
      setLoading(false);
    }
  };

  // Cargar planes al inicio
  useEffect(() => {
    fetchMealPlans();
  }, [showActive]);

  // Eliminar un plan - VERSIÓN DIRECTA Y SIMPLE
  const handleDelete = async (id, name) => {
    if (!id) {
      console.error("ID de plan inválido:", id);
      return;
    }
    
    if (window.confirm(`¿Estás seguro que deseas eliminar el plan de comida "${name || `Plan ${id}`}"?`)) {
      try {
        console.log(`Intentando eliminar plan con ID: ${id}`);
        setLoading(true);
        
        // Implementación directa del delete
        if (!MealPlanService.delete) {
          // Si el método no está definido en el servicio, lo implementamos aquí
          console.log("Método delete no encontrado en MealPlanService, usando implementación directa");
          
          // Para planes locales
          if (id.toString().startsWith('local-')) {
            const localData = localStorage.getItem('local_meal_plans');
            if (localData) {
              const localPlans = JSON.parse(localData);
              const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
              localStorage.setItem('local_meal_plans', JSON.stringify(filteredPlans));
            }
          } else {
            // Para planes en el backend
            const API_BASE = '/api/nutrition';
            await fetch(`${API_BASE}/meal-plans/${id}`, {
              method: 'DELETE',
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
              }
            });
          }
        } else {
          // Usar el método del servicio si existe
          await MealPlanService.delete(id);
        }
        
        // Mostrar mensaje de éxito y actualizar lista
        alert(`Plan "${name || `Plan ${id}`}" eliminado con éxito`);
        
        // Limpiar caché y refrescar lista
        if (MealPlanService.clearCache) {
          MealPlanService.clearCache();
        }
        fetchMealPlans();
      } catch (err) {
        console.error(`Error al eliminar plan ${id}:`, err);
        setError(`No se pudo eliminar el plan. Error: ${err.message || 'Error desconocido'}`);
        setLoading(false);
      }
    }
  };

  // Crear un nuevo plan
  const handleCreateNew = () => {
    if (onCreateNew) {
      onCreateNew();
    } else {
      navigate('/nutrition');
      localStorage.setItem('nutrition_tab', '1'); // Tab de creación
      window.location.reload();
    }
  };
  
  // Editar un plan existente
  const handleEdit = (id) => {
    if (onEdit) {
      onEdit(id);
    } else {
      localStorage.setItem('nutrition_edit_plan_id', id);
      localStorage.setItem('nutrition_tab', '1'); // Tab de edición
      navigate('/nutrition');
      window.location.reload();
    }
  };

  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h1">
              <FontAwesomeIcon icon={faClipboardList} style={{ marginRight: '10px' }} />
              Planes de Comida
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button 
                variant="outlined"
                startIcon={<FontAwesomeIcon icon={faSync} />}
                onClick={fetchMealPlans}
              >
                Actualizar
              </Button>
              <FormControlLabel 
                control={
                  <Switch 
                    checked={showActive} 
                    onChange={() => setShowActive(!showActive)}
                    color="primary"
                  />
                } 
                label="Solo planes activos" 
              />
              <Button 
                variant="contained" 
                color="primary"
                startIcon={<FontAwesomeIcon icon={faPlus} />}
                onClick={handleCreateNew}
              >
                Nuevo Plan
              </Button>
            </Box>
          </Box>
          
          {usingLocalOnly && (
            <Alert severity="info" sx={{ mb: 3 }}>
              <FontAwesomeIcon icon={faInfoCircle} style={{ marginRight: '8px' }} />
              Mostrando planes guardados localmente. Algunos cambios pueden no estar sincronizados con el servidor.
            </Alert>
          )}
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
              <Button size="small" sx={{ ml: 2 }} onClick={fetchMealPlans}>
                Reintentar
              </Button>
            </Alert>
          )}
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 6 }}>
              <CircularProgress size={40} />
              <Typography sx={{ ml: 2 }}>Cargando planes de comida...</Typography>
            </Box>
          ) : (
            mealPlans.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 6, px: 2 }}>
                <Typography variant="h6" gutterBottom color="text.secondary">
                  No hay planes de comida
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph sx={{ maxWidth: 500, mx: 'auto', mb: 4 }}>
                  Crea tu primer plan de comida para organizar tus comidas diarias y alcanzar tus objetivos nutricionales.
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<FontAwesomeIcon icon={faPlus} />}
                  onClick={handleCreateNew}
                >
                  Crear Primer Plan de Comida
                </Button>
              </Box>
            ) : (
              <Grid container spacing={3}>
                {mealPlans.map((plan) => (
                  <Grid item xs={12} md={6} lg={4} key={plan.id || Math.random()}>
                    <Paper 
                      elevation={2} 
                      sx={{ 
                        p: 2, 
                        height: '100%', 
                        position: 'relative',
                        border: plan.id?.toString().startsWith('local-') ? '1px dashed #1976d2' : 'none'
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="h6">
                          {plan.plan_name || plan.name || `Plan ${plan.id}`}
                        </Typography>
                        <Chip 
                          label={plan.is_active ? "Activo" : "Inactivo"} 
                          color={plan.is_active ? "success" : "default"}
                          size="small"
                        />
                      </Box>
                      
                      <Divider sx={{ mb: 2 }} />
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <FontAwesomeIcon icon={faCalendarWeek} style={{ marginRight: '5px' }} />
                        {plan.items && plan.items.length > 0 
                          ? `${plan.items.length} comidas programadas` 
                          : "Sin comidas programadas"}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                        <Button 
                          variant="outlined" 
                          size="small"
                          startIcon={<FontAwesomeIcon icon={faUtensils} />}
                          onClick={() => {
                            navigate(`/nutrition`);
                            localStorage.setItem('nutrition_tab', '2'); // Calendario
                            window.location.reload();
                          }}
                        >
                          Ver Plan
                        </Button>
                        <Box>
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleEdit(plan.id)}
                          >
                            <FontAwesomeIcon icon={faEdit} />
                          </IconButton>
                          
                          {/* BOTÓN DE ELIMINAR - CONEXIÓN DIRECTA Y ROBUSTA */}
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => {
                              console.log(`Clic en botón borrar para plan ${plan.id}`);
                              handleDelete(plan.id, plan.plan_name || plan.name);
                            }}
                            sx={{ ml: 1 }}
                          >
                            <FontAwesomeIcon icon={faTrash} />
                          </IconButton>
                        </Box>
                      </Box>
                      
                      {plan.id?.toString().startsWith('local-') && (
                        <Chip 
                          label="Guardado localmente" 
                          size="small" 
                          variant="outlined"
                          color="primary"
                          sx={{ position: 'absolute', top: '8px', right: '8px', fontSize: '0.6rem' }}
                        />
                      )}
                    </Paper>
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

export default MealPlanList;