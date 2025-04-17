import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, TextField, Button, CircularProgress, Alert, Paper, Typography, Grid, Tabs, Tab } from '@mui/material';
import { format, addDays, startOfWeek, eachDayOfInterval, parseISO, isValid } from 'date-fns';

// --- Importar los NUEVOS componentes y hooks ---
import NutritionTargetInputs from './form-components/NutritionTargetInputs';
import DayMealSelector from './form-components/DayMealSelector';
import MealSearchInput from './form-components/MealSearchInput';
import TotalPlanSummary from './form-components/TotalPlanSummary';
import useNutritionCalculations from '../../../hooks/useNutritionCalculations'; // Nuevo hook

// --- Importar hooks y servicios EXISTENTES ---
import { useMealPlanFormState } from '../../../hooks/useMealPlanFormState';
import { useAvailableMeals } from '../../../hooks/useAvailableMeals';
// import MealPlanService from '../../../services/nutrition/MealPlanService'; // No se usa directamente si useMealPlanFormState lo maneja

// *** Asegúrate de que useMealPlanFormState devuelve una estructura como esta: ***
// const {
//   plan: { id, name, description, start_date, end_date, target_calories, target_protein_g, target_carbs_g, target_fat_g, days }, // days = { 'YYYY-MM-DD': [mealItem] } mealItem necesita un id único (e.g., meal_plan_item_id o generado)
//   setPlan,
//   isLoading, // Estado de carga general (lectura inicial, guardado)
//   error, // Error general
//   handleChange, // Para campos base como name, description
//   handleDateChange, // Para start_date, end_date (si no se usan DatePickers externos)
//   addMealToDay, // Firma: (date: string, meal: object) => void - debe asignar un ID único si no viene
//   removeMealFromDay, // Firma: (date: string, mealItemId: number | string) => void - elimina por id
//   updateMealQuantity, // Firma: (date: string, mealItemId: number | string, quantity: number) => void
//   saveMealPlan, // Función para guardar/actualizar el plan entero -> devuelve boolean (éxito/fallo)
// } = useMealPlanFormState(planId);
// *******************************************************************************

function EnhancedMealPlanForm() {
  const { planId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(planId);

  // --- Hook principal para estado y lógica del formulario ---
  const {
    plan,
    setPlan, // Necesario para actualizar targets
    isLoading: isFormLoading, // Renombrar isLoading de este hook para claridad
    error: formError,
    handleChange: handleBaseChange, // Para name, description
    // handleDateChange, // Asumiendo que no se usa directamente si hay DatePickers
    addMealToDay: addMealToDayState,
    removeMealFromDay: removeMealFromDayState,
    updateMealQuantity: updateMealQuantityState,
    saveMealPlan
  } = useMealPlanFormState(planId);

  // --- Hook para obtener comidas disponibles ---
  const { availableMeals = [], isLoading: mealsLoading, error: mealsError } = useAvailableMeals(); // Default a []

  // --- Hook para calcular macros (basado en plan.days) ---
  // Asegurarse que plan y plan.days existen antes de pasarlo
  const { dailyTotals, planTotal } = useNutritionCalculations(plan?.days);

  // --- Estado local para la UI (semana, tabs) ---
  // Intenta inicializar con start_date del plan, si es válido, sino con hoy.
  const getInitialDate = () => {
    if (plan?.start_date) {
        const parsedDate = parseISO(plan.start_date);
        if (isValid(parsedDate)) {
            return parsedDate;
        }
    }
    return new Date();
  }
  const [currentWeekStart, setCurrentWeekStart] = useState(() => startOfWeek(getInitialDate(), { weekStartsOn: 1 }));
  const [activeTab, setActiveTab] = useState(0);

  // Actualiza la semana inicial si el plan se carga después del montaje inicial
  useEffect(() => {
      setCurrentWeekStart(startOfWeek(getInitialDate(), { weekStartsOn: 1 }));
      setActiveTab(0); // Reset tab al cargar plan
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan?.start_date]); // Dependencia en start_date del plan cargado

  // --- Callbacks para pasar a los sub-componentes ---
  const handleTargetsChange = useCallback((newTargets) => {
    // Actualiza solo los campos de targets en el estado principal del plan
    setPlan(prevPlan => ({
        ...prevPlan,
        target_calories: newTargets.target_calories,
        target_protein_g: newTargets.target_protein_g,
        target_carbs_g: newTargets.target_carbs_g,
        target_fat_g: newTargets.target_fat_g,
    }));
  }, [setPlan]);

  const handleAddMealToDay = useCallback((mealToAdd) => {
    // Añade la comida al día que está actualmente visible en el tab
    const currentWeekDates = eachDayOfInterval({ start: currentWeekStart, end: addDays(currentWeekStart, 6) });
    if (currentWeekDates && currentWeekDates[activeTab]) {
        const dateString = format(currentWeekDates[activeTab], 'yyyy-MM-dd');
        // ¡IMPORTANTE! Asume que 'mealToAdd' de availableMeals tiene la info necesaria
        // y que addMealToDayState en el hook se encarga de añadirlo correctamente
        // y asigna un ID único si es necesario (meal_plan_item_id o uno temporal).
        addMealToDayState(dateString, mealToAdd);
    } else {
        console.error("Cannot add meal, current date not selected.");
        // Podrías mostrar un error al usuario aquí
    }
  }, [activeTab, currentWeekStart, addMealToDayState]);

    const handleRemoveMeal = useCallback((date, mealItemId) => {
        removeMealFromDayState(date, mealItemId);
    }, [removeMealFromDayState]);

    const handleUpdateQuantity = useCallback((date, mealItemId, newQuantity) => {
        // Asegurar que la cantidad es un número antes de pasarla al hook
        const quantity = Number(newQuantity);
        if (!isNaN(quantity)) {
            updateMealQuantityState(date, mealItemId, quantity);
        }
    }, [updateMealQuantityState]);

  // --- Lógica de UI (semana/tabs) ---
  // Memoizar las fechas de la semana actual para evitar recálculos innecesarios
  const currentWeekDates = useMemo(() => eachDayOfInterval({ start: currentWeekStart, end: addDays(currentWeekStart, 6) }), [currentWeekStart]);

  const handleWeekChange = useCallback((direction) => {
      setCurrentWeekStart(prev => addDays(prev, direction * 7));
      setActiveTab(0); // Reset tab al cambiar semana
  }, []);

  const handleTabChange = useCallback((event, newValue) => {
      setActiveTab(newValue);
  }, []);

  // --- Submit ---
  const handleSubmit = async (event) => {
    event.preventDefault();
    // Validaciones adicionales podrían ir aquí si no están en el hook
    const success = await saveMealPlan(); // saveMealPlan viene del hook useMealPlanFormState
    if (success) {
      navigate('/nutrition/meal-plans'); // O a la vista de detalle
    }
    // El hook useMealPlanFormState debería manejar el estado de carga/error durante el guardado
  };

  // --- Renderizado ---
  // Mostrar carga inicial si el plan se está cargando y aún no tenemos un ID (en modo edición)
  const showInitialLoading = isEditing && isFormLoading && !plan?.id;
  // Mostrar error si la carga inicial falló
  const showInitialError = isEditing && formError && !plan?.id;
  // Estado general para deshabilitar campos mientras se carga/guarda
  const isUIDisabled = isFormLoading;


  if (showInitialLoading) return <Box sx={{display: 'flex', justifyContent: 'center', p: 5}}><CircularProgress /></Box>;
  if (showInitialError) return <Alert severity="error" sx={{m: 2}}>Error loading plan: {formError}</Alert>;

  return (
    <Paper sx={{ p: { xs: 1, sm: 2, md: 3 }, mt: 2 }}>
      <Typography variant="h4" gutterBottom>{isEditing ? 'Edit Meal Plan' : 'Create New Meal Plan'}</Typography>
      <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
        <Grid container spacing={3}>
           {/* Campos básicos del plan */}
            <Grid item xs={12} md={6}>
                 <TextField
                    name="name" label="Plan Name" required fullWidth
                    value={plan?.name || ''} onChange={handleBaseChange}
                    disabled={isUIDisabled}
                 />
            </Grid>
             <Grid item xs={12} md={6}>
                <TextField
                    name="description" label="Description" fullWidth
                    value={plan?.description || ''} onChange={handleBaseChange}
                    disabled={isUIDisabled} multiline maxRows={3}
                />
            </Grid>
            {/* TODO: Añadir Date Pickers para start_date y end_date si se usan */}
            {/* <Grid item xs={12} sm={6}> <DatePicker label="Start Date" value={plan?.start_date} onChange={(newDate) => handleDateChange('start_date', newDate)} disabled={isUIDisabled} /> </Grid> */}
            {/* <Grid item xs={12} sm={6}> <DatePicker label="End Date" value={plan?.end_date} onChange={(newDate) => handleDateChange('end_date', newDate)} disabled={isUIDisabled} /> </Grid> */}

             {/* Inputs de Objetivos (nuevo componente) */}
            <Grid item xs={12}>
                 <NutritionTargetInputs
                    targets={{
                        target_calories: plan?.target_calories,
                        target_protein_g: plan?.target_protein_g,
                        target_carbs_g: plan?.target_carbs_g,
                        target_fat_g: plan?.target_fat_g,
                    }}
                    onChange={handleTargetsChange}
                    errors={null} // TODO: Pasar errores si hay validación específica aquí
                    disabled={isUIDisabled}
                 />
            </Grid>

             {/* Búsqueda de comidas (nuevo componente) */}
            <Grid item xs={12}>
                <MealSearchInput
                    availableMeals={availableMeals}
                    isLoading={mealsLoading} // Carga específica de las comidas
                    error={mealsError}
                    onAddMeal={handleAddMealToDay}
                    disabled={isUIDisabled}
                />
            </Grid>

             {/* Navegación Semana/Días */}
            <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1, borderTop: '1px solid lightgray', borderBottom: '1px solid lightgray', py: 1 }}>
                 <Button onClick={() => handleWeekChange(-1)} disabled={isUIDisabled}>{'< Prev Week'}</Button>
                 <Typography variant="subtitle1" sx={{ textAlign: 'center', flexGrow: 1 }}>Week starting: {format(currentWeekStart, 'MMM d, yyyy')}</Typography>
                 <Button onClick={() => handleWeekChange(1)} disabled={isUIDisabled}>{'Next Week >'}</Button>
            </Grid>
            <Grid item xs={12} sx={{borderBottom: '1px solid lightgray', mb: 1}}>
                 <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto" aria-label="day tabs">
                    {currentWeekDates.map((date, index) => (
                        <Tab key={index} label={format(date, 'EEE d')} disabled={isUIDisabled} id={`day-tab-${index}`} aria-controls={`day-tabpanel-${index}`} />
                    ))}
                 </Tabs>
            </Grid>

             {/* Selector de Comidas del Día (nuevo componente) */}
             <Grid item xs={12}>
                 {currentWeekDates.map((date, index) => {
                    const dateString = format(date, 'yyyy-MM-dd');
                    // El contenido del tab solo se monta si está activo para optimizar rendimiento
                    return (
                        <Box
                            key={dateString}
                            role="tabpanel"
                            hidden={activeTab !== index}
                            id={`day-tabpanel-${index}`}
                            aria-labelledby={`day-tab-${index}`}
                            sx={{ pt: 2, ...(activeTab !== index && { display: 'none' }) }} // Ocultar completamente si no está activo
                        >
                            {/* Renderizar el contenido solo cuando el tab esté activo */}
                            {activeTab === index && (
                                <DayMealSelector
                                    date={dateString}
                                    // Asegurarse que plan.days exista y tenga el formato correcto { date: [item] }
                                    meals={plan?.days?.[dateString] || []}
                                    dailyTotal={dailyTotals[dateString]} // Pasar totales diarios del hook de cálculo
                                    onRemoveMeal={handleRemoveMeal}
                                    onUpdateQuantity={handleUpdateQuantity}
                                    // Pasar targets si es necesario para DayMealSelector
                                    // targetMacros={ {calories: plan?.target_calories / 7, ...} } // Ejemplo de target diario
                                    disabled={isUIDisabled}
                                />
                            )}
                        </Box>
                    );
                })}
            </Grid>

            {/* Resumen Total (nuevo componente) */}
            <Grid item xs={12}>
                <TotalPlanSummary
                    totalMacros={planTotal} // Pasar totales del hook de cálculo
                    // Pasar targets si es necesario para el resumen
                     targetMacros={{
                         calories: plan?.target_calories,
                         protein_g: plan?.target_protein_g,
                         carbohydrates_g: plan?.target_carbs_g,
                         fat_g: plan?.target_fat_g
                     }}
                 />
             </Grid>

            {/* Botón Guardar y Errores */}
            <Grid item xs={12}>
                 {/* Mostrar error general del formulario (e.g., fallo al guardar) */}
                 {formError && !showInitialError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
                 <Button type="submit" variant="contained" color="primary" disabled={isUIDisabled} sx={{ mt: 1, mb: 2 }}>
                    {/* Mostrar progreso si está guardando (asumiendo que isFormLoading cubre esto) */}
                    {isUIDisabled && !showInitialLoading ? <CircularProgress size={24} /> : (isEditing ? 'Update Plan' : 'Create Plan')}
                 </Button>

            </Grid>
        </Grid>
      </Box>
    </Paper>
  );
}

export default EnhancedMealPlanForm;