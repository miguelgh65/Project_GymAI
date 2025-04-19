// src/components/nutrition/meal-plans/MealPlanForm/index.js
// ****** ARCHIVO CORREGIDO (Versión Semana Actual) ******

import React, { useState, useEffect, useCallback } from 'react'; // Añadido useCallback
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Alert, CircularProgress, Button } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faSave } from '@fortawesome/free-solid-svg-icons';
// Importar date-fns para manejo de fechas
import { format, parseISO, startOfWeek, addDays, isValid } from 'date-fns';
// Importar servicios (asegúrate que las rutas son correctas desde esta ubicación)
import { MealService, MealPlanService, NutritionCalculator } from '../../../../services/NutritionService';

// Importar subcomponentes
import PlanBasicInfo from './PlanBasicInfo';
import NutritionTargets from './NutritionTargets';
import DaySelectorTabs from './DaySelectorTabs';
import MealSelector from './MealSelector';
import DayMealsList from './DayMealsList';
import ProgressSection from './ProgressSection'; // Revisa si necesita adaptación a fechas
import PlanSummary from './PlanSummary'; // Revisa si necesita adaptación a fechas

const MealPlanForm = ({ editId, onSaveSuccess }) => {
  const { planId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(planId || editId);
  const id = planId || editId;

  // Estado principal del formulario
  const [planName, setPlanName] = useState('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [items, setItems] = useState([]); // Guardará objetos con plan_date

  // Estado para objetivos nutricionales
  const [targetCalories, setTargetCalories] = useState('');
  const [targetProtein, setTargetProtein] = useState('');
  const [targetCarbs, setTargetCarbs] = useState('');
  const [targetFat, setTargetFat] = useState('');
  const [userNutritionProfile, setUserNutritionProfile] = useState(null);

  // Estado para comidas disponibles
  const [availableMeals, setAvailableMeals] = useState([]);

  // Estado de control del formulario
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Estado para la navegación de pestañas de días (0=Lunes, ..., 6=Domingo)
  const [activeTab, setActiveTab] = useState(0);

  const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

  // --- Funciones Auxiliares ---

  // Calcula la fecha 'YYYY-MM-DD' para la pestaña activa, basada en la semana actual
  // ¡¡ATENCIÓN!!: Si necesitas manejar semanas pasadas/futuras, esta lógica debe cambiar.
  const getActiveDateString = useCallback(() => {
      const today = new Date();
      // Obtiene el Lunes de la semana actual (weekStartsOn: 1 para Lunes)
      const startOfCurrentWeek = startOfWeek(today, { weekStartsOn: 1 });
      // Añade los días correspondientes a la pestaña activa (0=Lunes, 1=Martes...)
      const targetDate = addDays(startOfCurrentWeek, activeTab);
      return format(targetDate, 'yyyy-MM-dd');
  }, [activeTab]); // Depende solo de la pestaña activa

  // --- Efectos (Carga de datos) ---

  // Cargar perfil nutricional (sin cambios)
  useEffect(() => {
    const loadNutritionProfile = async () => {
        try {
          const profile = await NutritionCalculator.getProfile();
          if (profile) {
            console.log("Perfil nutricional cargado:", profile);
            setUserNutritionProfile(profile);
            // Pre-rellenar targets si no están definidos
            if (!targetCalories && profile.goal_calories) setTargetCalories(profile.goal_calories.toString());
            if (!targetProtein && profile.target_protein_g) setTargetProtein(profile.target_protein_g.toString());
            if (!targetCarbs && profile.target_carbs_g) setTargetCarbs(profile.target_carbs_g.toString());
            if (!targetFat && profile.target_fat_g) setTargetFat(profile.target_fat_g.toString());
          }
          // ... manejo de targets temporales ...
        } catch (error) {
          console.error("Error al cargar perfil nutricional:", error);
        }
      };
      loadNutritionProfile();
  }, []); // Cargar perfil solo una vez

  // Cargar datos del plan si estamos editando
  useEffect(() => {
    if (isEditing && id) {
      setLoading(true);
      MealPlanService.getById(id)
        .then(data => {
          console.log("Datos del plan cargados para editar:", data);
          setPlanName(data.plan_name || data.name || '');
          setDescription(data.description || '');
          setIsActive(data.is_active !== undefined ? data.is_active : true);
          if (data.target_calories) setTargetCalories(data.target_calories.toString());
          if (data.target_protein_g) setTargetProtein(data.target_protein_g.toString());
          if (data.target_carbs_g) setTargetCarbs(data.target_carbs_g.toString());
          if (data.target_fat_g) setTargetFat(data.target_fat_g.toString());

          // Mapear items asegurando que tengan plan_date y ID único para el estado
          if (data.items && Array.isArray(data.items)) {
            const loadedItems = data.items.map(item => {
              let plan_date = null;
              if (item.plan_date && isValid(parseISO(item.plan_date))) {
                plan_date = format(parseISO(item.plan_date), 'yyyy-MM-dd');
              } else {
                 console.warn(`Item ${item.id || item.meal_id} no tiene plan_date válido, será descartado.`);
                 return null;
              }

              return {
                id: item.id || `loaded_${item.meal_id}_${Date.now()}`, // ID único para React state
                meal_plan_item_id: item.id, // ID real de la BD
                meal_id: item.meal_id,
                meal_name: item.meal_name || 'Comida Desconocida',
                plan_date: plan_date, // <-- Fecha correcta
                meal_type: item.meal_type?.replace('MealTime.', '') || 'Comida',
                quantity: item.quantity || 100,
                unit: item.unit || 'g',
                calories: item.calories, // Asume que vienen del backend
                protein_g: item.protein_g,
                carbohydrates_g: item.carbohydrates_g,
                fat_g: item.fat_g
              };
            }).filter(item => item !== null);
            setItems(loadedItems);
          } else {
             setItems([]); // Asegurar que sea un array vacío si no hay items
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("Error fetching meal plan:", err);
          setError(err.message || 'Error al cargar el plan.');
          setLoading(false);
        });
    } else {
       // Resetear estado si no estamos editando
       setPlanName('');
       setDescription('');
       setIsActive(true);
       setItems([]);
       // Mantener targets del perfil si existen, si no, vacíos
       setTargetCalories(userNutritionProfile?.goal_calories?.toString() || '');
       setTargetProtein(userNutritionProfile?.target_protein_g?.toString() || '');
       setTargetCarbs(userNutritionProfile?.target_carbs_g?.toString() || '');
       setTargetFat(userNutritionProfile?.target_fat_g?.toString() || '');
       setError(null);
       setSuccess(null);
       setActiveTab(0); // Volver a Lunes
    }
    // Recargar perfil si cambiamos entre crear/editar (opcional, depende de si puede cambiar)
    // O solo depender de 'id' y 'isEditing'
  }, [id, isEditing, userNutritionProfile]); // Añadido userNutritionProfile como dependencia por si resetea targets

  // Cargar comidas disponibles (sin cambios)
  useEffect(() => {
    MealService.getAll()
      .then(response => {
        const meals = response.meals || [];
        console.log(`Cargadas ${meals.length} comidas disponibles`);
        setAvailableMeals(meals);
      })
      .catch(err => {
        console.error("Error fetching available meals:", err);
        setError("Error al cargar el listado de comidas disponibles.");
      });
  }, []);

  // --- Manejadores de Eventos ---

  const handleBasicInfoChange = useCallback((field, value) => {
    switch (field) {
      case 'name': setPlanName(value); break;
      case 'description': setDescription(value); break;
      case 'is_active': setIsActive(value); break;
      default: break;
    }
  }, []);

  const handleTargetsChange = useCallback((field, value) => {
    // Validar que solo sean números o vacío
    const numericRegex = /^[0-9]*\.?[0-9]*$/;
    if (value === '' || numericRegex.test(value)) {
        switch (field) {
            case 'calories': setTargetCalories(value); break;
            case 'protein': setTargetProtein(value); break;
            case 'carbs': setTargetCarbs(value); break;
            case 'fat': setTargetFat(value); break;
            default: break;
        }
    }
  }, []);

  const handleAddMeal = useCallback((meal, quantity, unit, mealType) => {
    // Validar cantidad
    const numQuantity = parseFloat(quantity);
    if (isNaN(numQuantity) || numQuantity <= 0) {
        setError("La cantidad debe ser un número positivo.");
        return; // No añadir si la cantidad es inválida
    }
    setError(null); // Limpiar error si la cantidad es válida

    const factor = numQuantity / 100;
    const targetDateString = getActiveDateString(); // Obtener fecha de la pestaña activa
    const tempId = `temp_${Date.now()}_${Math.random()}`; // ID único para el estado

    const newItem = {
      id: tempId,
      meal_plan_item_id: null,
      meal_id: meal.id,
      meal_name: meal.name || meal.meal_name || 'Comida Desconocida',
      plan_date: targetDateString, // Fecha calculada
      meal_type: mealType,
      quantity: numQuantity, // Cantidad validada
      unit: unit || 'g',
      // Calcular macros basados en la cantidad
      calories: meal.calories ? Math.round(meal.calories * factor) : 0,
      protein_g: meal.protein_g || meal.proteins ? Math.round((meal.protein_g || meal.proteins) * factor * 10) / 10 : 0,
      carbohydrates_g: meal.carbohydrates_g || meal.carbohydrates ? Math.round((meal.carbohydrates_g || meal.carbohydrates) * factor * 10) / 10 : 0,
      fat_g: meal.fat_g || meal.fats ? Math.round((meal.fat_g || meal.fats) * factor * 10) / 10 : 0
    };

    console.log("MealPlanForm - Añadiendo item al estado:", newItem);
    setItems(prevItems => [...prevItems, newItem]);
  }, [activeTab, getActiveDateString]); // Depender de activeTab y la función de fecha

  const handleRemoveMeal = useCallback((itemToRemoveId) => {
    setItems(prevItems => prevItems.filter(item => item.id !== itemToRemoveId));
  }, []);

  const handleSubmit = useCallback(async () => { // Usar useCallback
    if (!planName.trim()) {
      setError("El nombre del plan es obligatorio.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    // Mapear items asegurando que plan_date esté presente y sea válido
    const itemsToSubmit = items.map(item => {
        if (!item.plan_date || !isValid(parseISO(item.plan_date))) {
             console.error("Item inválido encontrado durante el guardado (falta fecha válida):", item);
             // Lanzar error para detener el proceso si un item es inválido
             throw new Error(`Hay una comida en el plan sin fecha válida (${item.meal_name || 'Desconocida'}). Por favor, revisa.`);
        }
        return {
            meal_id: item.meal_id,
            plan_date: item.plan_date, // Enviar fecha YYYY-MM-DD
            meal_type: item.meal_type,
            quantity: item.quantity,
            unit: item.unit || 'g',
            // Opcional: Enviar ID del item si estamos editando y ya existe en BD
            // id: item.meal_plan_item_id || undefined
        };
    });

    const planData = {
      plan_name: planName,
      description: description,
      is_active: isActive,
      // Enviar targets como números o null
      target_calories: targetCalories ? parseFloat(targetCalories) : null,
      target_protein_g: targetProtein ? parseFloat(targetProtein) : null,
      target_carbs_g: targetCarbs ? parseFloat(targetCarbs) : null,
      target_fat_g: targetFat ? parseFloat(targetFat) : null,
      items: itemsToSubmit
    };

    console.log('MealPlanForm - Enviando payload:', JSON.stringify(planData, null, 2));

    try {
      if (isEditing) {
        await MealPlanService.update(id, planData);
        setSuccess('Plan actualizado con éxito.');
      } else {
        await MealPlanService.create(planData);
        setSuccess('Plan creado con éxito.');
      }

      if (onSaveSuccess) {
        setTimeout(() => onSaveSuccess(), 1500);
      } else {
        setTimeout(() => navigate('/nutrition/meal-plans'), 1500); // Redirigir a la lista
      }
    } catch (err) {
      console.error("Error saving meal plan:", err);
      const errorDetail = err.response?.data?.detail;
      let errorMessage = err.message || 'Error al guardar el plan.'; // Default a err.message si existe
       if (typeof errorDetail === 'string') {
          errorMessage = errorDetail;
       } else if (Array.isArray(errorDetail) && errorDetail[0]?.msg) {
         errorMessage = `Error: ${errorDetail[0].msg} (campo: ${errorDetail[0].loc.slice(1).join('.')})`;
       }
       // Usar el error lanzado desde la validación de items si existe
       if (err instanceof Error && !err.response) {
           errorMessage = err.message;
       }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [planName, description, isActive, items, targetCalories, targetProtein, targetCarbs, targetFat, isEditing, id, navigate, onSaveSuccess]); // Dependencias del useCallback

  // Filtrar items para la fecha del día activo
  const getActiveTabItems = useCallback(() => {
    const targetDateString = getActiveDateString();
    return items.filter(item => item.plan_date === targetDateString);
  }, [items, getActiveDateString]); // Depende de items y la función de fecha

  // --- Renderizado ---
  if (loading && isEditing && !items.length) { // Mostrar carga solo si está cargando para editar
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        {error && <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      </Box>

      <PlanBasicInfo
        name={planName}
        description={description}
        isActive={isActive}
        onChange={handleBasicInfoChange}
      />

      <NutritionTargets
        calories={targetCalories}
        protein={targetProtein}
        carbs={targetCarbs}
        fat={targetFat}
        profile={userNutritionProfile}
        onChange={handleTargetsChange}
      />

      <DaySelectorTabs
        days={daysOfWeek}
        activeTab={activeTab}
        onChange={(newTab) => setActiveTab(newTab)} // Actualiza la pestaña activa
      />

      {/* Revisa si ProgressSection y PlanSummary necesitan adaptarse a filtrar por fecha */}
       {/* <ProgressSection ... /> */}
       {/* <PlanSummary ... /> */}

      <MealSelector
        meals={availableMeals}
        onAddMeal={handleAddMeal}
      />

      <DayMealsList
        items={getActiveTabItems()} // Pasa items filtrados por fecha
        onRemove={handleRemoveMeal}
      />

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          variant="outlined"
          startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
          onClick={() => navigate('/nutrition/meal-plans')} // Navegar a la lista
          disabled={loading}
        >
          Cancelar
        </Button>

        <Button
          type="button"
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={loading || !planName.trim()}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
        >
          {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
        </Button>
      </Box>
    </Box>
  );
};

export default MealPlanForm;