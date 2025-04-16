// src/components/nutrition/meal-plans/MealPlanList.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, IconButton, CircularProgress, Alert, Button, 
  Card, CardContent, Chip, Grid, Paper, Divider, Switch, FormControlLabel
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faEdit, faTrash, faPlus, faClipboardList, 
  faCalendarWeek, faSync, faUtensils, faInfoCircle
} from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { MealPlanService } from '../../../services/nutrition';

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
      MealPlanService.clearCache();
      
      const response = await MealPlanService.getAll(showActive ? true : null);
      console.log("Respuesta de planes:", response);
      
      // Obtener planes de la respuesta
      const plans = response?.meal_plans || [];
      
      // Logs para depuración
      console.log(`Encontrados ${plans.length} planes, incluyendo planes locales: ${plans.some(p => p.id.toString().startsWith('local-'))}`);
      
      // Indicar si sólo usamos planes locales
      setUsingLocalOnly(response.fromCache || response.fromLocalOnly || false);
      
      // Guardar planes en el estado
      setMealPlans(plans);
      
      // Verificar almacenamiento local como respaldo
      if (plans.length === 0) {
        console.log("No hay planes de la API, verificando almacenamiento local");
        try {
          // Acceso directo al almacenamiento local
          const localStorageKey = 'local_meal_plans';
          const localData = localStorage.getItem(localStorageKey);
          
          if (localData) {
            const localPlans = JSON.parse(localData);
            console.log(`Encontrados ${localPlans.length} planes locales`, localPlans);
            
            if (localPlans.length > 0) {
              const filteredPlans = showActive 
                ? localPlans.filter(p => p.is_active) 
                : localPlans;
                
              if (filteredPlans.length > 0) {
                console.log("Usando planes del almacenamiento local", filteredPlans);
                setMealPlans(filteredPlans);
                setUsingLocalOnly(true);
              }
            }
          }
        } catch (localErr) {
          console.error("Error al verificar almacenamiento local:", localErr);
        }
      }
    } catch (err) {
      console.error("Error al cargar planes de comida:", err);
      setError(err.message || 'Error al cargar los planes de comida.');
      
      // Intento directo al almacenamiento local como último recurso
      try {
        const localStorageKey = 'local_meal_plans';
        const localData = localStorage.getItem(localStorageKey);
        
        if (localData) {
          const localPlans = JSON.parse(localData);
          const filteredPlans = showActive 
            ? localPlans.filter(p => p.is_active) 
            : localPlans;
          
          if (filteredPlans.length > 0) {
            console.log("Usando planes locales después de error", filteredPlans);
            setMealPlans(filteredPlans);
            setUsingLocalOnly(true);
          }
        }
      } catch (localErr) {
        console.error("Error al acceder al almacenamiento local:", localErr);
      }
    } finally {
      setLoading(false);
    }
  };

  // Cargar planes al inicio
  useEffect(() => {
    fetchMealPlans();
  }, [showActive]);

  // Eliminar un plan
  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este plan de comida?')) {
      try {
        await MealPlanService.delete(id);
        
        // Limpiar caché y refrescar
        MealPlanService.clearCache();
        fetchMealPlans();
      } catch (err) {
        console.error("Error al eliminar plan:", err);
        setError(err.message || 'Error al eliminar el plan.');
      }
    }
  };

  // Crear un nuevo plan
  const handleCreateNew = () => {
    if (onCreateNew) {
      onCreateNew();
    } else {
      // Crear un plan local directamente
      createLocalPlan();
    }
  };
  
  // Crear un plan local directamente
  const createLocalPlan = async () => {
    try {
      // Pedir nombre del plan
      const planName = prompt("Nombre del plan de comida:", "Mi plan de comidas");
      
      // Cancelar si no hay nombre
      if (!planName) return;
      
      setLoading(true);
      
      // Crear plan básico
      const newPlan = {
        plan_name: planName,
        name: planName,
        is_active: true,
        items: [],
        description: 'Plan creado localmente'
      };
      
      // Guardar en almacenamiento local directamente
      try {
        const storageKey = 'local_meal_plans';
        const existingPlansJSON = localStorage.getItem(storageKey);
        const existingPlans = existingPlansJSON ? JSON.parse(existingPlansJSON) : [];
        
        // Crear plan local con ID temporal
        const newLocalPlan = {
          ...newPlan,
          id: `local-${Date.now()}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        // Añadir a planes existentes
        existingPlans.push(newLocalPlan);
        localStorage.setItem(storageKey, JSON.stringify(existingPlans));
        
        // También intentar método del servicio
        MealPlanService.clearCache();
        await MealPlanService.create(newPlan);
        
        // Refrescar la lista
        fetchMealPlans();
      } catch (localErr) {
        console.error("Error al guardar en almacenamiento local:", localErr);
        throw localErr;
      }
    } catch (err) {
      console.error("Error al crear plan local:", err);
      setError("Error al crear plan local: " + (err.message || "Error desconocido"));
    } finally {
      setLoading(false);
    }
  };

  // Editar un plan existente
  const handleEdit = (id) => {
    if (onEdit) {
      onEdit(id);
    } else {
      // Navegación alternativa
      localStorage.setItem('nutrition_edit_plan_id', id);
      localStorage.setItem('nutrition_tab', '1');
      navigate('/nutrition');
      window.location.reload();
    }
  };

  // Estado vacío
  const renderEmptyState = () => (
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
  );

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
              renderEmptyState()
            ) : (
              <Grid container spacing={3}>
                {mealPlans.map((plan) => (
                  <Grid item xs={12} md={6} lg={4} key={plan.id}>
                    <Paper 
                      elevation={2} 
                      sx={{ 
                        p: 2, 
                        height: '100%', 
                        position: 'relative',
                        border: plan.id.toString().startsWith('local-') ? '1px dashed #1976d2' : 'none'
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
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(plan.id)}
                            sx={{ ml: 1 }}
                          >
                            <FontAwesomeIcon icon={faTrash} />
                          </IconButton>
                        </Box>
                      </Box>
                      
                      {plan.id.toString().startsWith('local-') && (
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