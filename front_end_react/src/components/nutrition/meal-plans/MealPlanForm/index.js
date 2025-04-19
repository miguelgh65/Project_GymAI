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
// Viendo tu 'tree', estos imports deberían funcionar si estás en 'src/components/nutrition/meal-plans/MealPlanForm/'
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
  // Esta función asume que el formulario siempre opera sobre la semana en curso.
  const getActiveDateString = useCallback(() => {
      const today = new Date();
      // Obtiene el Lunes de la semana actual (weekStartsOn: 1 para Lunes)
      const startOfCurrentWeek = startOfWeek(today, { weekStartsOn: 1 });
      // Añade los días correspondientes a la pestaña activa (0=Lunes, 1=Martes...)
      const targetDate = addDays(startOfCurrentWeek, activeTab);
      return format(targetDate, 'yyyy-MM-dd');
  }, [activeTab]); // Depende solo de la pestaña activa

  // --- Efectos (Carga de datos) ---

  // Cargar perfil nutricional
  useEffect(() => {
    const loadNutritionProfile = async () => {
        try {
          const profile = await NutritionCalculator.getProfile();
          if (profile) {
            console.log("Perfil nutricional cargado:", profile);
            setUserNutritionProfile(profile);
            // Pre-rellenar targets si no están definidos y vienen del perfil
            if (!targetCalories && profile.goal_calories) setTargetCalories(profile.goal_calories.toString());
            if (!targetProtein && profile.target_protein_g) setTargetProtein(profile.target_protein_g.toString());
            if (!targetCarbs && profile.target_carbs_g) setTargetCarbs(profile.target_carbs_g.toString());
            if (!targetFat && profile.target_fat_g) setTargetFat(profile.target_fat_g.toString());
          }
          // ... manejo de targets temporales (si aplica)...
        } catch (error) {
          console.error("Error al cargar perfil nutricional:", error);
        }
      };
      loadNutritionProfile();
      // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Cargar perfil solo una vez al montar

  // Cargar datos del plan si estamos editando
  useEffect(() => {
    if (isEditing && id) {
      setLoading(true);
      setError(null); // Limpiar error anterior
      MealPlanService.getById(id)
        .then(data => {
          console.log("Datos del plan cargados para editar:", data);
          setPlanName(data.plan_name || data.name || '');
          setDescription(data.description || '');
          setIsActive(data.is_active !== undefined ? data.is_active : true);
          // Rellenar targets desde el plan cargado
          setTargetCalories(data.target_calories?.toString() ?? '');
          setTargetProtein(data.target_protein_g?.toString() ?? '');
          setTargetCarbs(data.target_carbs_g?.toString() ?? '');
          setTargetFat(data.target_fat_g?.toString() ?? '');

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
             setItems([]); // Asegurar array vacío si no vienen items
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("Error fetching meal plan:", err);
          setError(err.message || 'Error al cargar el plan.');
          setLoading(false);
        });
    } else {
       // Resetear estado al crear o si se quita el ID de edición
       setPlanName('');
       setDescription('');
       setIsActive(true);
       setItems([]);
       // Usar targets del perfil si existe, si no, vacíos
       setTargetCalories(userNutritionProfile?.goal_calories?.toString() || '');
       setTargetProtein(userNutritionProfile?.target_protein_g?.toString() || '');
       setTargetCarbs(userNutritionProfile?.target_carbs_g?.toString() || '');
       setTargetFat(userNutritionProfile?.target_fat_g?.toString() || '');
       setError(null);
       setSuccess(null);
       setActiveTab(0); // Resetear a Lunes
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, isEditing]); // Depender de id y isEditing para recargar/resetear

  // Cargar comidas disponibles
  useEffect(() => {
    setLoading(true); // Indicar carga de comidas
    MealService.getAll()
      .then(response => {
        const meals = response.meals || [];
        console.log(`Cargadas ${meals.length} comidas disponibles`);
        setAvailableMeals(meals);
      })
      .catch(err => {
        console.error("Error fetching available meals:", err);
        setError("Error al cargar el listado de comidas disponibles.");
      })
      .finally(() => {
         // Asegurarse de quitar el estado de carga general si solo cargaba comidas
         // Esto es un poco tricky si la carga del plan también estaba ocurriendo.
         // Podría necesitarse un estado de carga separado para las comidas.
         // Por ahora, quitamos el estado de carga principal aquí.
         // setLoading(false); // Quitar setLoading aquí puede ser problemático si el plan aún carga.
      });
  }, []); // Cargar comidas solo una vez

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
    const numQuantity = parseFloat(quantity);
    if (isNaN(numQuantity) || numQuantity <= 0) {
        setError("La cantidad debe ser un número positivo.");
        return;
    }
    setError(null);

    const factor = numQuantity / 100;
    const targetDateString = getActiveDateString();
    const tempId = `temp_${Date.now()}_${Math.random()}`;

    const newItem = {
      id: tempId,
      meal_plan_item_id: null,
      meal_id: meal.id,
      meal_name: meal.name || meal.meal_name || 'Comida Desconocida',
      plan_date: targetDateString,
      meal_type: mealType,
      quantity: numQuantity,
      unit: unit || 'g',
      calories: meal.calories ? Math.round(meal.calories * factor) : 0,
      protein_g: meal.protein_g || meal.proteins ? Math.round((meal.protein_g || meal.proteins) * factor * 10) / 10 : 0,
      carbohydrates_g: meal.carbohydrates_g || meal.carbohydrates ? Math.round((meal.carbohydrates_g || meal.carbohydrates) * factor * 10) / 10 : 0,
      fat_g: meal.fat_g || meal.fats ? Math.round((meal.fat_g || meal.fats) * factor * 10) / 10 : 0
    };

    console.log("MealPlanForm - Añadiendo item al estado:", newItem);
    setItems(prevItems => [...prevItems, newItem]);
  }, [activeTab, getActiveDateString]);

  const handleRemoveMeal = useCallback((itemToRemoveId) => {
    setItems(prevItems => prevItems.filter(item => item.id !== itemToRemoveId));
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!planName.trim()) {
      setError("El nombre del plan es obligatorio.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    let itemsToSubmit;
    try {
        // Validar y mapear items dentro del try/catch
        itemsToSubmit = items.map(item => {
            if (!item.plan_date || !isValid(parseISO(item.plan_date))) {
                console.error("Item inválido encontrado durante el guardado (falta fecha válida):", item);
                throw new Error(`Hay una comida en el plan sin fecha válida (${item.meal_name || 'Desconocida'}). Por favor, revisa.`);
            }
            // Solo incluir campos que espera el backend para CUD
            return {
                meal_id: item.meal_id,
                plan_date: item.plan_date,
                meal_type: item.meal_type,
                quantity: item.quantity,
                unit: item.unit || 'g',
                // Incluir 'id' (meal_plan_item_id) solo si estamos editando y el item lo tiene
                ...(isEditing && item.meal_plan_item_id && { id: item.meal_plan_item_id }),
            };
        });
    } catch (validationError) {
        // Si la validación de items falla, mostrar error y detener
        setError(validationError.message);
        setLoading(false);
        return;
    }


    const planData = {
      plan_name: planName,
      description: description,
      is_active: isActive,
      target_calories: targetCalories ? parseFloat(targetCalories) : null,
      target_protein_g: targetProtein ? parseFloat(targetProtein) : null,
      target_carbs_g: targetCarbs ? parseFloat(targetCarbs) : null,
      target_fat_g: targetFat ? parseFloat(targetFat) : null,
      items: itemsToSubmit
    };

    console.log('MealPlanForm - Enviando payload:', JSON.stringify(planData, null, 2));

    try {
      let response; // Para potencialmente usar la respuesta
      if (isEditing) {
        response = await MealPlanService.update(id, planData);
        setSuccess('Plan actualizado con éxito.');
      } else {
        response = await MealPlanService.create(planData);
        setSuccess('Plan creado con éxito.');
         // Opcional: podrías querer actualizar el estado 'items' con los IDs reales devueltos
         // if (response && response.items) { setItems(transformarItemsRecibidos(response.items)); }
      }

      // Limpiar caché del servicio para forzar recarga en la lista
      MealPlanService.clearCache();

      if (onSaveSuccess) {
        setTimeout(() => onSaveSuccess(response), 1500); // Pasar respuesta al callback
      } else {
        setTimeout(() => navigate('/nutrition/meal-plans'), 1500); // Redirigir a la lista
      }
    } catch (err) {
      console.error("Error saving meal plan:", err);
      const errorDetail = err.response?.data?.detail;
      let errorMessage = err.message || 'Error al guardar el plan.';
       if (typeof errorDetail === 'string') {
          errorMessage = errorDetail;
       } else if (Array.isArray(errorDetail) && errorDetail[0]?.msg) {
         errorMessage = `Error: ${errorDetail[0].msg} (campo: ${errorDetail[0].loc.slice(1).join('.')})`;
       }
       // Asegurar que no mostramos el error de validación que ya manejamos
       if (!(err instanceof Error && !err.response && errorMessage.includes('fecha válida'))) {
           setError(errorMessage);
       }
    } finally {
      setLoading(false);
    }
  }, [planName, description, isActive, items, targetCalories, targetProtein, targetCarbs, targetFat, isEditing, id, navigate, onSaveSuccess]);

  // Filtrar items para la fecha del día activo
  const getActiveTabItems = useCallback(() => {
    const targetDateString = getActiveDateString();
    return items.filter(item => item.plan_date === targetDateString);
  }, [items, getActiveDateString]);

  // --- Renderizado ---
  // Evitar renderizar si está cargando para editar y aún no hay datos básicos
  if (loading && isEditing && !planName) {
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
        onChange={(newTab) => setActiveTab(newTab)}
      />

      {/* <ProgressSection items={items} activeDate={getActiveDateString()} ... /> */}
       {/* <PlanSummary items={items} ... /> */}

      <MealSelector
        meals={availableMeals}
        onAddMeal={handleAddMeal}
      />

      <DayMealsList
        items={getActiveTabItems()}
        onRemove={handleRemoveMeal}
      />

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          variant="outlined"
          startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
          onClick={() => navigate('/nutrition/meal-plans')}
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