// src/components/nutrition/meal-plans/EnhancedMealPlanForm.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, Checkbox, FormControlLabel,
  CircularProgress, Alert, Grid, Autocomplete, Card, CardContent,
  InputAdornment, Divider, Paper, Tabs, Tab, IconButton,
  Tooltip, Chip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faSave, faCalculator, faUtensils, faArrowLeft, 
  faSpinner, faInfoCircle, faTrash, faBowlFood
} from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { MealPlanService, MealService } from '../../../services/nutrition';
import { getNutritionSummary } from '../../../utils/nutrition-utils';

// Componente para mostrar macros
const MacroSummary = ({ macros }) => {
  if (!macros) return <Typography variant="body2">No hay datos disponibles</Typography>;
  
  return (
    <Box sx={{ mt: 2, mb: 2 }}>
      <Grid container spacing={1}>
        <Grid item xs={12}>
          <Typography variant="subtitle1" fontWeight="bold">
            Total: {macros.calories} kcal
          </Typography>
        </Grid>
        <Grid item xs={4}>
          <Typography variant="body2">
            Proteínas: {macros.macros.proteins.grams}g ({macros.macros.proteins.percentage}%)
          </Typography>
        </Grid>
        <Grid item xs={4}>
          <Typography variant="body2">
            Carbos: {macros.macros.carbs.grams}g ({macros.macros.carbs.percentage}%)
          </Typography>
        </Grid>
        <Grid item xs={4}>
          <Typography variant="body2">
            Grasas: {macros.macros.fats.grams}g ({macros.macros.fats.percentage}%)
          </Typography>
        </Grid>
      </Grid>
    </Box>
  );
};

// Componente para el selector de comidas
const MealSelector = ({ meals, mealType, onSelect, selectedMeal, quantity, onQuantityChange, onRemove }) => {
  const [searchText, setSearchText] = useState('');
  
  return (
    <Grid container spacing={1} alignItems="center" sx={{ mb: 2 }}>
      <Grid item xs={12} sm={3}>
        <Typography variant="body2">{mealType}:</Typography>
      </Grid>
      <Grid item xs={7} sm={5}>
        <Autocomplete
          options={meals || []}
          getOptionLabel={(option) => option.meal_name || option.name || ''}
          value={selectedMeal}
          onChange={(event, newValue) => onSelect(mealType, newValue)}
          inputValue={searchText}
          onInputChange={(event, value) => setSearchText(value)}
          isOptionEqualToValue={(option, value) => option?.id === value?.id}
          renderInput={(params) => (
            <TextField
              {...params}
              variant="outlined"
              placeholder="Selecciona o busca una comida"
              size="small"
              fullWidth
            />
          )}
        />
      </Grid>
      <Grid item xs={3} sm={2}>
        <TextField
          type="number"
          label="Cantidad"
          value={quantity || ''}
          onChange={(e) => onQuantityChange(mealType, e.target.value)}
          size="small"
          fullWidth
          InputProps={{
            endAdornment: <InputAdornment position="end">g</InputAdornment>,
            inputProps: { min: 0, step: 10 }
          }}
          disabled={!selectedMeal}
        />
      </Grid>
      <Grid item xs={2} sm={1}>
        <Tooltip title="Quitar comida">
          <IconButton 
            color="error" 
            size="small" 
            onClick={() => onRemove(mealType)}
            disabled={!selectedMeal}
          >
            <FontAwesomeIcon icon={faTrash} />
          </IconButton>
        </Tooltip>
      </Grid>
    </Grid>
  );
};

// Componente para un día de comidas
const DayMeals = ({ dayName, mealData, meals, onChange, onQuantityChange, onRemove }) => {
  // Calcular macros totales del día
  const calculateDayMacros = () => {
    // Filtrar comidas seleccionadas con cantidades
    const selectedMeals = Object.entries(mealData)
      .filter(([_, data]) => data.meal && data.quantity)
      .map(([_, data]) => {
        // Calcular macros proporcionales a la cantidad
        const ratio = data.quantity / 100; // Las cantidades se expresan en gramos, macros típicamente por 100g
        const mealMacros = {
          calories: data.meal.calories * ratio,
          proteins: data.meal.proteins * ratio,
          carbohydrates: data.meal.carbohydrates * ratio,
          fats: data.meal.fats * ratio
        };
        return mealMacros;
      });
    
    // Sumar todos los macros
    if (selectedMeals.length === 0) return null;
    
    const totalMacros = selectedMeals.reduce((total, current) => ({
      calories: total.calories + current.calories,
      proteins: total.proteins + current.proteins,
      carbohydrates: total.carbohydrates + current.carbohydrates,
      fats: total.fats + current.fats
    }), { calories: 0, proteins: 0, carbohydrates: 0, fats: 0 });
    
    return getNutritionSummary(totalMacros);
  };

  const dayMacros = calculateDayMacros();
  
  return (
    <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
      <Typography variant="h6" gutterBottom>{dayName}</Typography>
      
      {/* Selectores para cada comida del día */}
      <MealSelector 
        meals={meals}
        mealType="Desayuno"
        onSelect={(mealType, meal) => onChange(dayName, mealType, meal)}
        selectedMeal={mealData.Desayuno?.meal || null}
        quantity={mealData.Desayuno?.quantity || ''}
        onQuantityChange={(mealType, quantity) => onQuantityChange(dayName, mealType, quantity)}
        onRemove={(mealType) => onRemove(dayName, mealType)}
      />
      
      <MealSelector 
        meals={meals}
        mealType="Almuerzo"
        onSelect={(mealType, meal) => onChange(dayName, mealType, meal)}
        selectedMeal={mealData.Almuerzo?.meal || null}
        quantity={mealData.Almuerzo?.quantity || ''}
        onQuantityChange={(mealType, quantity) => onQuantityChange(dayName, mealType, quantity)}
        onRemove={(mealType) => onRemove(dayName, mealType)}
      />
      
      <MealSelector 
        meals={meals}
        mealType="Comida"
        onSelect={(mealType, meal) => onChange(dayName, mealType, meal)}
        selectedMeal={mealData.Comida?.meal || null}
        quantity={mealData.Comida?.quantity || ''}
        onQuantityChange={(mealType, quantity) => onQuantityChange(dayName, mealType, quantity)}
        onRemove={(mealType) => onRemove(dayName, mealType)}
      />
      
      <MealSelector 
        meals={meals}
        mealType="Merienda"
        onSelect={(mealType, meal) => onChange(dayName, mealType, meal)}
        selectedMeal={mealData.Merienda?.meal || null}
        quantity={mealData.Merienda?.quantity || ''}
        onQuantityChange={(mealType, quantity) => onQuantityChange(dayName, mealType, quantity)}
        onRemove={(mealType) => onRemove(dayName, mealType)}
      />
      
      <MealSelector 
        meals={meals}
        mealType="Cena"
        onSelect={(mealType, meal) => onChange(dayName, mealType, meal)}
        selectedMeal={mealData.Cena?.meal || null}
        quantity={mealData.Cena?.quantity || ''}
        onQuantityChange={(mealType, quantity) => onQuantityChange(dayName, mealType, quantity)}
        onRemove={(mealType) => onRemove(dayName, mealType)}
      />
      
      {/* Resumen de macros del día */}
      <Divider sx={{ my: 2 }} />
      
      {Object.values(mealData).some(item => item.meal) ? (
        <>
          <Typography variant="subtitle2" gutterBottom>Macros totales del día:</Typography>
          {dayMacros ? (
            <MacroSummary macros={dayMacros} />
          ) : (
            <Typography variant="body2" color="text.secondary">
              Añade comidas para ver los macros del día
            </Typography>
          )}
        </>
      ) : (
        <Alert severity="info" icon={<FontAwesomeIcon icon={faBowlFood} />} sx={{ mt: 1 }}>
          No hay comidas asignadas para este día
        </Alert>
      )}
    </Paper>
  );
};

// Componente principal del formulario
const EnhancedMealPlanForm = ({ editId, onSaveSuccess }) => {
  const navigate = useNavigate();
  const isEditing = Boolean(editId);
  
  // Estados principales del formulario
  const [planName, setPlanName] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [loading, setLoading] = useState(false);
  const [loadingMeals, setLoadingMeals] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [availableMeals, setAvailableMeals] = useState([]);
  const [debug, setDebug] = useState(null);
  
  // Estado para las tabs de días
  const [currentDay, setCurrentDay] = useState(0);
  
  // Estado para las comidas por día
  const [weekMeals, setWeekMeals] = useState({
    Lunes: { Desayuno: {}, Almuerzo: {}, Comida: {}, Merienda: {}, Cena: {} },
    Martes: { Desayuno: {}, Almuerzo: {}, Comida: {}, Merienda: {}, Cena: {} },
    Miércoles: { Desayuno: {}, Almuerzo: {}, Comida: {}, Merienda: {}, Cena: {} },
    Jueves: { Desayuno: {}, Almuerzo: {}, Comida: {}, Merienda: {}, Cena: {} },
    Viernes: { Desayuno: {}, Almuerzo: {}, Comida: {}, Merienda: {}, Cena: {} },
    Sábado: { Desayuno: {}, Almuerzo: {}, Comida: {}, Merienda: {}, Cena: {} },
    Domingo: { Desayuno: {}, Almuerzo: {}, Comida: {}, Merienda: {}, Cena: {} }
  });
  
  const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  
  // Cargar comidas disponibles
  useEffect(() => {
    const fetchMeals = async () => {
      try {
        setLoadingMeals(true);
        const response = await MealService.getAll();
        
        // Normalizar las estructuras de datos para manejar diferentes formatos de respuesta
        let meals = [];
        if (Array.isArray(response)) {
          meals = response;
        } else if (response.meals && Array.isArray(response.meals)) {
          meals = response.meals;
        }
        
        console.log("Comidas cargadas:", meals);
        setAvailableMeals(meals);
      } catch (err) {
        console.error("Error al cargar comidas:", err);
        setError("No se pudieron cargar las comidas disponibles.");
      } finally {
        setLoadingMeals(false);
      }
    };
    
    fetchMeals();
  }, []);
  
  // Si estamos editando, cargar el plan existente
  useEffect(() => {
    if (isEditing && editId) {
      const loadPlan = async () => {
        try {
          setLoading(true);
          setError(null);
          console.log(`Cargando plan con ID: ${editId}`);
          
          const data = await MealPlanService.getById(editId);
          console.log("Datos del plan cargado:", data);
          
          // Normalizar datos
          setPlanName(data.plan_name || data.name || '');
          setIsActive(Boolean(data.is_active));
          
          // Inicializar el estado de las comidas por día
          const newWeekMeals = { ...weekMeals };
          
          // Si el plan tiene items, mapeamos cada uno a su día y tipo de comida
          if (data.items && Array.isArray(data.items) && data.items.length > 0) {
            console.log(`Cargando ${data.items.length} items del plan`);
            
            // Esperar a que las comidas estén cargadas para asociarlas con los items
            await new Promise(resolve => {
              const checkMeals = () => {
                if (availableMeals.length > 0) {
                  resolve();
                } else {
                  setTimeout(checkMeals, 500);
                }
              };
              checkMeals();
            });
            
            data.items.forEach(item => {
              // Mapeo: meal_time -> meal_type para compatibilidad
              const meal_type = item.meal_time || item.meal_type;
              const day_of_week = item.day_of_week;
              
              // Buscar la comida completa basada en meal_id
              const meal = availableMeals.find(m => m.id === item.meal_id);
              
              if (meal && newWeekMeals[day_of_week] && meal_type) {
                newWeekMeals[day_of_week][meal_type] = {
                  meal: meal,
                  quantity: item.quantity || 100
                };
              }
            });
            
            console.log("Comidas del plan cargadas:", newWeekMeals);
            setWeekMeals(newWeekMeals);
          } else {
            console.log("El plan no tiene items");
          }
        } catch (err) {
          console.error("Error al cargar el plan:", err);
          setError(err.message || 'Error al cargar el plan.');
        } finally {
          setLoading(false);
        }
      };
      
      loadPlan();
    }
  }, [isEditing, editId, availableMeals]);
  
  // Manejador para cambiar de día
  const handleDayChange = (event, newDay) => {
    setCurrentDay(newDay);
  };
  
  // Manejador para seleccionar una comida
  const handleMealSelect = (day, mealType, selectedMeal) => {
    console.log(`Seleccionando comida para ${day} - ${mealType}:`, selectedMeal);
    
    if (!selectedMeal) {
      // Si no hay comida seleccionada, limpiamos ese espacio
      setWeekMeals(prev => {
        const newWeekMeals = { ...prev };
        newWeekMeals[day][mealType] = {};
        return newWeekMeals;
      });
      return;
    }
    
    setWeekMeals(prev => {
      const newWeekMeals = { ...prev };
      newWeekMeals[day][mealType] = {
        meal: selectedMeal,
        quantity: newWeekMeals[day][mealType].quantity || 100 // Valor por defecto si no existe
      };
      return newWeekMeals;
    });
  };
  
  // Manejador para cambiar la cantidad de una comida
  const handleQuantityChange = (day, mealType, quantity) => {
    const numQuantity = parseFloat(quantity);
    if (isNaN(numQuantity) || numQuantity < 0) return;
    
    setWeekMeals(prev => {
      const newWeekMeals = { ...prev };
      if (newWeekMeals[day][mealType].meal) {
        newWeekMeals[day][mealType].quantity = numQuantity;
      }
      return newWeekMeals;
    });
  };
  
  // Manejador para quitar una comida
  const handleRemoveMeal = (day, mealType) => {
    setWeekMeals(prev => {
      const newWeekMeals = { ...prev };
      newWeekMeals[day][mealType] = {};
      return newWeekMeals;
    });
  };
  
  // Generador de estructura para guardar
  const generatePlanItems = () => {
    const items = [];
    
    // Recorrer cada día de la semana
    Object.entries(weekMeals).forEach(([day, meals]) => {
      // Recorrer cada tipo de comida del día
      Object.entries(meals).forEach(([mealType, data]) => {
        // Solo incluir si hay una comida y una cantidad válida
        if (data.meal && data.quantity) {
          items.push({
            meal_id: data.meal.id,
            day_of_week: day,
            meal_type: mealType,  // Usar como tipo de comida
            meal_time: mealType,  // También enviar como meal_time para compatibilidad
            quantity: data.quantity
          });
        }
      });
    });
    
    return items;
  };
  
  // Manejador para guardar el plan
  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!planName.trim()) {
      setError("El nombre del plan es obligatorio");
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    const planItems = generatePlanItems();
    
    // Verificar si hay al menos un item
    if (planItems.length === 0) {
      setError("Debes añadir al menos una comida al plan");
      setLoading(false);
      return;
    }
    
    console.log(`${planItems.length} items en el plan`);
    setDebug(`Items: ${JSON.stringify(planItems, null, 2)}`);
    
    const planData = {
      plan_name: planName,
      is_active: isActive,
      items: planItems
    };
    
    console.log("Guardando plan con datos:", planData);
    
    try {
      if (isEditing) {
        await MealPlanService.update(editId, planData);
        setSuccess('Plan actualizado con éxito.');
      } else {
        await MealPlanService.create(planData);
        setSuccess('Plan creado con éxito.');
      }
      
      // Limpiar cache
      MealPlanService.clearCache();
      
      // Redirigir después de un éxito
      setTimeout(() => {
        if (onSaveSuccess) {
          onSaveSuccess();
        } else {
          navigate('/nutrition');
          localStorage.setItem('nutrition_tab', '0'); // Volver a la lista de planes
          window.location.reload();
        }
      }, 1500);
    } catch (err) {
      console.error("Error al guardar el plan:", err);
      setError(err.message || 'Error al guardar el plan.');
    } finally {
      setLoading(false);
    }
  };
  
  // Calcular macros totales del plan
  const calculateTotalMacros = () => {
    let totalCalories = 0;
    let totalProteins = 0;
    let totalCarbs = 0;
    let totalFats = 0;
    
    Object.values(weekMeals).forEach(dayMeals => {
      Object.values(dayMeals).forEach(mealData => {
        if (mealData.meal && mealData.quantity) {
          const ratio = mealData.quantity / 100;
          totalCalories += (mealData.meal.calories || 0) * ratio;
          totalProteins += (mealData.meal.proteins || 0) * ratio;
          totalCarbs += (mealData.meal.carbohydrates || 0) * ratio;
          totalFats += (mealData.meal.fats || 0) * ratio;
        }
      });
    });
    
    return {
      calories: Math.round(totalCalories),
      proteins: Math.round(totalProteins * 10) / 10,
      carbohydrates: Math.round(totalCarbs * 10) / 10,
      fats: Math.round(totalFats * 10) / 10
    };
  };
  
  const totalMacros = calculateTotalMacros();
  const macroSummary = getNutritionSummary(totalMacros);
  
  // Calcular el número total de comidas en el plan
  const totalMeals = Object.values(weekMeals).reduce((count, dayMeals) => {
    return count + Object.values(dayMeals).filter(meal => meal.meal).length;
  }, 0);
  
  if (loading && isEditing && !availableMeals.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 4, flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <CircularProgress />
        <Typography>Cargando plan de comidas...</Typography>
      </Box>
    );
  }
  
  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5">
              {isEditing ? 'Editar Plan de Nutrición' : 'Crear Nuevo Plan de Nutrición'}
            </Typography>
            
            <Button
              variant="outlined"
              startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
              onClick={() => {
                navigate('/nutrition');
                localStorage.setItem('nutrition_tab', '0'); // Volver a la lista de planes
                window.location.reload();
              }}
            >
              Volver
            </Button>
          </Box>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}
          
          {debug && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <pre style={{ fontSize: '0.7rem', whiteSpace: 'pre-wrap' }}>{debug}</pre>
            </Alert>
          )}
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={8}>
              <TextField
                required
                fullWidth
                id="planName"
                label="Nombre del Plan"
                value={planName}
                onChange={(e) => setPlanName(e.target.value)}
                margin="normal"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    color="primary"
                  />
                }
                label="Plan Activo"
                sx={{ mt: 2 }}
              />
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Macros Totales del Plan <FontAwesomeIcon icon={faCalculator} />
            </Typography>
            
            {totalMeals > 0 ? (
              <>
                <Typography variant="body2" gutterBottom>
                  {totalMeals} comidas planificadas en total
                </Typography>
                <MacroSummary macros={macroSummary} />
              </>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                Añade comidas al plan para ver los macros totales
              </Alert>
            )}
          </Box>
        </CardContent>
      </Card>
      
      <Box sx={{ mb: 3 }}>
        <Paper sx={{ width: '100%' }}>
          <Tabs
            value={currentDay}
            onChange={handleDayChange}
            variant="scrollable"
            scrollButtons="auto"
            aria-label="Días de la semana"
          >
            {daysOfWeek.map((day, index) => {
              // Contar comidas por día para mostrar en la pestaña
              const mealCount = Object.values(weekMeals[day]).filter(item => item.meal).length;
              
              return (
                <Tab 
                  key={day} 
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {day}
                      {mealCount > 0 && (
                        <Chip 
                          size="small" 
                          label={mealCount} 
                          color="primary" 
                          sx={{ ml: 1, height: 20, fontSize: '0.7rem' }} 
                        />
                      )}
                    </Box>
                  } 
                  id={`day-tab-${index}`} 
                  aria-controls={`day-tabpanel-${index}`} 
                />
              );
            })}
          </Tabs>
          
          <Box p={2}>
            {loadingMeals ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 3, alignItems: 'center', gap: 2 }}>
                <CircularProgress size={24} />
                <Typography>Cargando comidas disponibles...</Typography>
              </Box>
            ) : availableMeals.length === 0 ? (
              <Alert severity="warning" sx={{ mb: 2 }}>
                No hay comidas disponibles. Por favor, crea algunas comidas primero.
              </Alert>
            ) : (
              daysOfWeek.map((day, index) => (
                <div
                  key={day}
                  role="tabpanel"
                  hidden={currentDay !== index}
                  id={`day-tabpanel-${index}`}
                  aria-labelledby={`day-tab-${index}`}
                >
                  {currentDay === index && (
                    <DayMeals
                      dayName={day}
                      mealData={weekMeals[day]}
                      meals={availableMeals}
                      onChange={handleMealSelect}
                      onQuantityChange={handleQuantityChange}
                      onRemove={handleRemoveMeal}
                    />
                  )}
                </div>
              ))
            )}
          </Box>
        </Paper>
      </Box>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3, mb: 2 }}>
        <Button
          variant="outlined"
          onClick={() => {
            navigate('/nutrition');
            localStorage.setItem('nutrition_tab', '0');
            window.location.reload();
          }}
        >
          Cancelar
        </Button>
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={loading || !planName.trim() || loadingMeals || totalMeals === 0}
          startIcon={loading ? <CircularProgress size={20} /> : <FontAwesomeIcon icon={faSave} />}
        >
          {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
        </Button>
      </Box>
    </Box>
  );
};

export default EnhancedMealPlanForm;