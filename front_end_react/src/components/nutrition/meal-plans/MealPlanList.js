// front_end_react/src/components/nutrition/meal-plans/MealPlanList.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, CircularProgress, Alert, Grid, Paper, 
  Card, CardContent, Button, IconButton, Chip, Divider,
  FormControlLabel, Switch, List, ListItem, ListItemText,
  ListItemIcon, Collapse
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faPlus, faEdit, faTrash, faSync, faUtensils, 
  faInfoCircle, faClipboardList, faCalendarWeek,
  faEye, faChevronDown, faChevronUp, faCoffee,
  faSun, faCookie, faMoon, faEllipsisH, faFire
} from '@fortawesome/free-solid-svg-icons';
import { MealPlanService } from '../../../services/NutritionService';
import { useNavigate } from 'react-router-dom';

const MealPlanList = ({ onCreateNew, onEdit }) => {
  const [mealPlans, setMealPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showActive, setShowActive] = useState(true);
  const [usingLocalOnly, setUsingLocalOnly] = useState(false);
  const [expandedPlanId, setExpandedPlanId] = useState(null);
  const navigate = useNavigate();

  // Iconos para tipos de comida
  const mealTypeIcons = {
    'Desayuno': faCoffee,
    'Almuerzo': faSun,
    'Comida': faUtensils,
    'Merienda': faCookie,
    'Cena': faMoon,
    'Otro': faEllipsisH
  };

  // Función para cargar planes de comida con sus items
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
      
      // Cargar detalles completos para cada plan
      const detailedPlans = await Promise.all(
        plans.map(async (plan) => {
          try {
            // Cargar plan completo con sus items
            const fullPlan = await MealPlanService.getById(plan.id);
            console.log(`Plan ${plan.id} cargado con items:`, fullPlan);
            return fullPlan;
          } catch (err) {
            console.error(`Error al cargar detalles del plan ${plan.id}:`, err);
            return plan; // Devolver el plan básico si hay error
          }
        })
      );
      
      // Guardar planes en el estado
      setMealPlans(detailedPlans);
      
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

  // Eliminar un plan
  const handleDelete = async (id, name) => {
    if (!id) {
      console.error("ID de plan inválido:", id);
      return;
    }
    
    if (window.confirm(`¿Estás seguro que deseas eliminar el plan de comida "${name || `Plan ${id}`}"?`)) {
      try {
        console.log(`Intentando eliminar plan con ID: ${id}`);
        setLoading(true);
        
        // Usar el método del servicio si existe
        await MealPlanService.delete(id);
        
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

  // Ver detalle de plan
  const handleViewPlan = (id) => {
    navigate(`/nutrition/meal-plans/${id}`);
  };
  
  // Expandir/contraer plan para ver comidas
  const handleToggleExpand = (id) => {
    setExpandedPlanId(expandedPlanId === id ? null : id);
  };
  
  // Agrupar comidas por día y tipo
  const groupMealsByDayAndType = (items = []) => {
    const grouped = {};
    
    items.forEach(item => {
      const day = item.day_of_week || 'Sin día';
      const type = item.meal_type?.replace('MealTime.', '') || 'Comida';
      
      if (!grouped[day]) {
        grouped[day] = {};
      }
      
      if (!grouped[day][type]) {
        grouped[day][type] = [];
      }
      
      grouped[day][type].push(item);
    });
    
    return grouped;
  };
  
  // Obtener icono para tipo de comida
  const getMealTypeIcon = (type) => {
    return mealTypeIcons[type] || faUtensils;
  };
  
  // Calcular calorías totales del plan
  const calculatePlanCalories = (items = []) => {
    return items.reduce((total, item) => total + (item.calories || 0), 0);
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
                {mealPlans.map((plan) => {
                  const hasItems = plan.items && plan.items.length > 0;
                  const totalCalories = calculatePlanCalories(plan.items);
                  const groupedItems = groupMealsByDayAndType(plan.items);
                  const isExpanded = expandedPlanId === plan.id;
                  
                  return (
                    <Grid item xs={12} md={6} lg={4} key={plan.id || Math.random()}>
                      <Paper 
                        elevation={2} 
                        sx={{ 
                          height: '100%', 
                          position: 'relative',
                          border: plan.id?.toString().startsWith('local-') ? '1px dashed #1976d2' : 'none',
                          display: 'flex',
                          flexDirection: 'column'
                        }}
                      >
                        <CardContent sx={{ p: 2, pb: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="h6" noWrap sx={{ maxWidth: '70%' }}>
                              {plan.plan_name || plan.name || `Plan ${plan.id}`}
                            </Typography>
                            <Chip 
                              label={plan.is_active ? "Activo" : "Inactivo"} 
                              color={plan.is_active ? "success" : "default"}
                              size="small"
                            />
                          </Box>
                          
                          <Divider sx={{ mb: 2 }} />
                          
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
                              <FontAwesomeIcon icon={faCalendarWeek} style={{ marginRight: '5px' }} />
                              {hasItems ? `${plan.items.length} comidas programadas` : "Sin comidas programadas"}
                            </Typography>
                            
                            {hasItems && (
                              <Chip 
                                icon={<FontAwesomeIcon icon={faFire} />}
                                label={`${totalCalories} kcal`}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                            )}
                          </Box>
                          
                          {plan.target_calories && (
                            <Typography variant="body2" color="text.secondary">
                              Objetivo: {plan.target_calories} kcal
                              {plan.target_protein_g && ` | P: ${plan.target_protein_g}g`}
                              {plan.target_carbs_g && ` | C: ${plan.target_carbs_g}g`}
                              {plan.target_fat_g && ` | G: ${plan.target_fat_g}g`}
                            </Typography>
                          )}
                          
                          {hasItems && (
                            <Button 
                              fullWidth
                              size="small"
                              onClick={() => handleToggleExpand(plan.id)}
                              endIcon={<FontAwesomeIcon icon={isExpanded ? faChevronUp : faChevronDown} />}
                              sx={{ mt: 1, textTransform: 'none' }}
                            >
                              {isExpanded ? 'Ocultar comidas' : 'Ver comidas'}
                            </Button>
                          )}
                          
                          <Collapse in={isExpanded && hasItems}>
                            <Box sx={{ mt: 1, maxHeight: '300px', overflow: 'auto' }}>
                              {Object.entries(groupedItems).map(([day, types]) => (
                                <Box key={day} sx={{ mb: 2 }}>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                                    {day}
                                  </Typography>
                                  
                                  {Object.entries(types).map(([type, meals]) => (
                                    <Box key={type} sx={{ ml: 2, mb: 1 }}>
                                      <Typography variant="body2" sx={{ 
                                        display: 'flex', 
                                        alignItems: 'center',
                                        color: 'primary.main',
                                        fontWeight: 500
                                      }}>
                                        <FontAwesomeIcon 
                                          icon={getMealTypeIcon(type)} 
                                          style={{ marginRight: '8px' }} 
                                        />
                                        {type}
                                      </Typography>
                                      
                                      <List dense disablePadding>
                                        {meals.map((meal, idx) => (
                                          <ListItem key={idx} disableGutters sx={{ pl: 4 }}>
                                            <ListItemText
                                              primary={meal.meal_name || `Comida ${meal.meal_id}`}
                                              secondary={
                                                <>
                                                  {meal.quantity} {meal.unit || 'g'}
                                                  {meal.calories && ` | ${meal.calories} kcal`}
                                                </>
                                              }
                                              primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                                              secondaryTypographyProps={{ variant: 'caption' }}
                                            />
                                          </ListItem>
                                        ))}
                                      </List>
                                    </Box>
                                  ))}
                                </Box>
                              ))}
                            </Box>
                          </Collapse>
                        </CardContent>
                        
                        <Box sx={{ 
                          mt: 'auto', 
                          p: 2, 
                          pt: 1,
                          display: 'flex', 
                          justifyContent: 'space-between'
                        }}>
                          <Button 
                            variant="outlined" 
                            size="small"
                            startIcon={<FontAwesomeIcon icon={faEye} />}
                            onClick={() => handleViewPlan(plan.id)}
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
                  );
                })}
              </Grid>
            )
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default MealPlanList;