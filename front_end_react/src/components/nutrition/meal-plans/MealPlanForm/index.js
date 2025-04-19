// src/components/nutrition/meal-plans/MealPlanForm/index.js
// ****** ARCHIVO CORREGIDO (Añadida importación de Typography) ******

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// *** CORRECCIÓN: Añadido Typography a la importación de @mui/material ***
import { Box, Alert, CircularProgress, Button, Typography } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faSave } from '@fortawesome/free-solid-svg-icons';
// Importar date-fns para manejo de fechas
import { format, parseISO, startOfWeek, addDays, isValid } from 'date-fns';
// Importar servicios (asegúrate que las rutas son correctas)
// Verifica que NutritionService exporte estos módulos o impórtalos directamente
import { MealService, MealPlanService, NutritionCalculator } from '../../../../services/NutritionService'; // Asumiendo que NutritionService agrupa estos

// Importar subcomponentes
import PlanBasicInfo from './PlanBasicInfo';
import NutritionTargets from './NutritionTargets';
import DaySelectorTabs from './DaySelectorTabs';
import MealSelector from './MealSelector';
import DayMealsList from './DayMealsList';
// import ProgressSection from './ProgressSection'; // Comentado si no se usa
// import PlanSummary from './PlanSummary'; // Comentado si no se usa
import axios from 'axios'; // Importar axios si necesitas verificar el tipo de error

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
  const [loading, setLoading] = useState(false); // Estado de carga general (podría separarse)
  const [formLoading, setFormLoading] = useState(false); // Estado de carga específico para el guardado
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Estado para la navegación de pestañas de días (0=Lunes, ..., 6=Domingo)
  const [activeTab, setActiveTab] = useState(0);

  const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

  // --- Funciones Auxiliares ---

  const getActiveDateString = useCallback(() => {
      const today = new Date();
      const startOfCurrentWeek = startOfWeek(today, { weekStartsOn: 1 });
      const targetDate = addDays(startOfCurrentWeek, activeTab);
      return format(targetDate, 'yyyy-MM-dd');
  }, [activeTab]);

  // --- Efectos (Carga de datos) ---

  // Cargar perfil nutricional y comidas disponibles al montar
   useEffect(() => {
        let isMounted = true; // Flag para evitar updates en componente desmontado
        setLoading(true); // Estado de carga inicial

        const loadInitialData = async () => {
            try {
                // Cargar perfil
                const profile = await NutritionCalculator.getProfile();
                if (isMounted && profile) {
                    console.log("Perfil nutricional cargado:", profile);
                    setUserNutritionProfile(profile);
                     // Pre-rellenar targets solo si no estamos editando o si el plan editado no los tiene
                    if (!isEditing) {
                        if (profile.goal_calories) setTargetCalories(profile.goal_calories.toString());
                        if (profile.target_protein_g) setTargetProtein(profile.target_protein_g.toString());
                        if (profile.target_carbs_g) setTargetCarbs(profile.target_carbs_g.toString());
                        if (profile.target_fat_g) setTargetFat(profile.target_fat_g.toString());
                    }
                }

                 // Cargar comidas disponibles
                 const mealsResponse = await MealService.getAll();
                 if (isMounted) {
                     const meals = mealsResponse.meals || [];
                     console.log(`Cargadas ${meals.length} comidas disponibles`);
                     setAvailableMeals(meals);
                 }

            } catch (err) {
                 console.error("Error al cargar datos iniciales (perfil/comidas):", err);
                 if (isMounted) {
                    setError("Error al cargar datos necesarios para el formulario.");
                 }
            } finally {
                // Quitar el loading general solo cuando todo ha cargado o fallado
                 if (isMounted && !isEditing) { // Si no estamos editando, quitamos loading aquí
                     setLoading(false);
                 }
                 // Si estamos editando, el loading se quitará en el useEffect de carga del plan
            }
        };

         loadInitialData();

         return () => { isMounted = false; }; // Cleanup al desmontar
         // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []); // Cargar solo una vez (cuidado con dependencias si 'isEditing' puede cambiar)

  // Cargar datos del plan si estamos editando
  useEffect(() => {
    let isMounted = true;
    if (isEditing && id) {
      setLoading(true); // Activar loading específico de la carga de edición
      setError(null);
      setSuccess(null);
      console.log(`[MealPlanForm] Editando plan ID: ${id}. Cargando datos...`);
      MealPlanService.getById(id)
        .then(data => {
            if (!isMounted) return; // Evitar update si se desmontó
          console.log("[MealPlanForm] Datos del plan cargados para editar:", data);
           if (!data) {
               throw new Error(`El plan con ID ${id} no se encontró o no se pudo cargar.`);
           }

          setPlanName(data.plan_name || data.name || ''); // Compatibilidad con 'name'
          setDescription(data.description || '');
          setIsActive(data.is_active !== undefined ? data.is_active : true);
          // Rellenar targets desde el plan cargado, si existen
          setTargetCalories(data.target_calories?.toString() ?? userNutritionProfile?.goal_calories?.toString() ?? '');
          setTargetProtein(data.target_protein_g?.toString() ?? userNutritionProfile?.target_protein_g?.toString() ?? '');
          setTargetCarbs(data.target_carbs_g?.toString() ?? userNutritionProfile?.target_carbs_g?.toString() ?? '');
          setTargetFat(data.target_fat_g?.toString() ?? userNutritionProfile?.target_fat_g?.toString() ?? '');

          // Mapear items asegurando que tengan plan_date y ID único para el estado
          if (data.items && Array.isArray(data.items)) {
            const loadedItems = data.items.map((item, index) => {
              let plan_date = null;
               // Intenta parsear la fecha, crucial que el backend devuelva YYYY-MM-DD o ISO
              if (item.plan_date) {
                  try {
                      const parsedDate = parseISO(item.plan_date);
                       if (isValid(parsedDate)) {
                            plan_date = format(parsedDate, 'yyyy-MM-dd');
                       } else {
                           console.warn(`Fecha inválida en item ${item.id || index}: ${item.plan_date}`);
                       }
                  } catch(e) {
                       console.warn(`Error parseando fecha en item ${item.id || index}: ${item.plan_date}`, e);
                  }
              }

              if (!plan_date) {
                   console.warn(`Item ${item.id || item.meal_id} sin fecha válida, será asociado a 'hoy' o descartado según lógica.`);
                  // DECISIÓN: ¿Qué hacer si no hay fecha? ¿Asignar una por defecto o descartar?
                  // Por ahora, lo descartamos para evitar datos inconsistentes.
                   return null;
              }

              return {
                // Usar un ID temporal si no viene uno de BD (importante para React keys y remove)
                id: item.id || `loaded_${item.meal_id}_${Date.now()}_${index}`,
                meal_plan_item_id: item.id || null, // ID real de la BD si existe
                meal_id: item.meal_id,
                meal_name: item.meal_name || item.meal?.name || 'Comida Desconocida', // Intentar obtener nombre del meal anidado si existe
                plan_date: plan_date,
                meal_type: item.meal_type?.replace('MealTime.', '') || 'Comida',
                quantity: item.quantity || 100,
                unit: item.unit || 'g',
                 // Usar macros del item si vienen, si no, calcular (si es posible y necesario)
                 // Es mejor si el backend ya devuelve los macros calculados para el item.
                calories: item.calories ?? (item.meal?.calories ? Math.round(item.meal.calories * (item.quantity/100)) : 0),
                protein_g: item.protein_g ?? (item.meal?.protein_g ? Math.round(item.meal.protein_g * (item.quantity/100) * 10) / 10 : 0),
                carbohydrates_g: item.carbohydrates_g ?? (item.meal?.carbohydrates_g ? Math.round(item.meal.carbohydrates_g * (item.quantity/100) * 10) / 10 : 0),
                fat_g: item.fat_g ?? (item.meal?.fat_g ? Math.round(item.meal.fat_g * (item.quantity/100) * 10) / 10 : 0)
              };
            }).filter(item => item !== null); // Filtrar los items descartados
            setItems(loadedItems);
          } else {
              setItems([]); // Asegurar array vacío si no vienen items
          }
        })
        .catch(err => {
           if (!isMounted) return;
          console.error("[MealPlanForm] Error fetching meal plan for edit:", err);
          setError(err.message || 'Error al cargar los datos del plan para editar.');
          // Quizás redirigir si el plan no se puede cargar?
          // navigate('/nutrition/meal-plans');
        })
        .finally(() => {
           if (isMounted) {
               setLoading(false); // Quitar loading específico de edición
           }
        });
    } else if (!isEditing) {
        // Resetear estado si cambiamos de editar a crear
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
        setLoading(false); // Asegurar que no hay loading si pasamos a modo 'crear'
    }

     return () => { isMounted = false; }; // Cleanup al desmontar o cambiar ID/isEditing
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, isEditing, userNutritionProfile]); // Depender también de userNutritionProfile para resetear targets

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
    // Permitir borrar el campo (value === '')
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
        // Limpiar error después de un tiempo
        setTimeout(() => setError(null), 3000);
        return;
    }
    setError(null); // Limpiar error si la cantidad es válida

    // Calcular factor basado en 100g o unidad base de la comida si está disponible
    const baseQuantity = meal.base_quantity || 100; // Asumir 100g si no hay base_quantity
    const baseUnit = meal.unit || 'g'; // Asumir 'g' si no hay unidad base
    // Por ahora, asumimos que el cálculo siempre es vs 100g si no se especifica lo contrario
    const factor = numQuantity / 100;

    const targetDateString = getActiveDateString();
    const tempId = `temp_${Date.now()}_${Math.random()}`; // ID temporal único para estado React

    const newItem = {
      id: tempId,
      meal_plan_item_id: null, // No tiene ID de BD aún
      meal_id: meal.id,
      meal_name: meal.name || meal.meal_name || 'Comida Desconocida', // Ser robustos con el nombre
      plan_date: targetDateString,
      meal_type: mealType || 'Comida', // Tipo de comida (Desayuno, Almuerzo...)
      quantity: numQuantity,
      unit: unit || baseUnit, // Usar unidad seleccionada o la base de la comida
      // Calcular macros basado en los macros por 100g (o baseQuantity) de la comida original
      calories: meal.calories ? Math.round(meal.calories * factor) : 0,
       // Ser robusto con nombres de campos (protein_g vs proteins, etc.)
      protein_g: (meal.protein_g ?? meal.proteins ?? 0) ? parseFloat(((meal.protein_g ?? meal.proteins ?? 0) * factor).toFixed(1)) : 0,
      carbohydrates_g: (meal.carbohydrates_g ?? meal.carbohydrates ?? 0) ? parseFloat(((meal.carbohydrates_g ?? meal.carbohydrates ?? 0) * factor).toFixed(1)) : 0,
      fat_g: (meal.fat_g ?? meal.fats ?? 0) ? parseFloat(((meal.fat_g ?? meal.fats ?? 0) * factor).toFixed(1)) : 0
    };

    console.log("[MealPlanForm] Añadiendo item al estado:", newItem);
    setItems(prevItems => [...prevItems, newItem]);
  }, [activeTab, getActiveDateString]); // Recalcular si cambia la pestaña activa

  const handleRemoveMeal = useCallback((itemToRemoveId) => {
      console.log("[MealPlanForm] Eliminando item con ID de estado:", itemToRemoveId);
    setItems(prevItems => prevItems.filter(item => item.id !== itemToRemoveId));
  }, []);


  // --- Función de Envío ---
  const handleSubmit = useCallback(async () => {
    if (!planName.trim()) {
      setError("El nombre del plan es obligatorio.");
      setTimeout(() => setError(null), 3000);
      return;
    }

    setFormLoading(true); // Usar estado de carga específico del formulario
    setError(null);
    setSuccess(null);

    let itemsToSubmit;
    try {
        // Validar y mapear items ANTES de construir el payload final
        itemsToSubmit = items.map(item => {
            // Asegurar que la fecha existe y es válida ANTES de enviar
            if (!item.plan_date || !isValid(parseISO(item.plan_date))) {
                console.error("Item inválido encontrado durante el guardado (fecha inválida):", item);
                // Lanzar un error específico que podamos identificar luego
                const validationError = new Error(`La comida '${item.meal_name || 'Desconocida'}' tiene una fecha inválida (${item.plan_date}). Por favor, revisa.`);
                validationError.isValidationError = true; // Marcar el error
                throw validationError;
            }
             // Mapear solo los campos que necesita el backend para crear/actualizar items
             // Es CRUCIAL que esto coincida con el schema Pydantic del backend
            return {
                // Enviar 'id' solo si es un item existente (tiene meal_plan_item_id)
                ...(isEditing && item.meal_plan_item_id && { id: item.meal_plan_item_id }),
                meal_id: item.meal_id,
                plan_date: item.plan_date, // Formato YYYY-MM-DD
                meal_type: item.meal_type || 'Comida',
                quantity: parseFloat(item.quantity) || 0,
                unit: item.unit || 'g',
            };
        });
    } catch (validationError) {
        // Si la validación de items falla, mostrar error y detener
         if (validationError.isValidationError) {
             setError(validationError.message);
         } else {
             // Otro error inesperado durante el mapeo
             console.error("Error inesperado mapeando items:", validationError);
             setError("Ocurrió un error preparando los datos del plan.");
         }
        setFormLoading(false); // Detener carga
        setTimeout(() => setError(null), 5000); // Limpiar error tras 5s
        return; // Detener ejecución de handleSubmit
    }


    const planData = {
      plan_name: planName.trim(), // Quitar espacios extra
      description: description,
      is_active: isActive,
      target_calories: targetCalories ? parseFloat(targetCalories) : null,
      target_protein_g: targetProtein ? parseFloat(targetProtein) : null,
      target_carbs_g: targetCarbs ? parseFloat(targetCarbs) : null,
      target_fat_g: targetFat ? parseFloat(targetFat) : null,
      items: itemsToSubmit // Los items ya validados y formateados
    };

    console.log('[MealPlanForm] Preparado para enviar payload:', JSON.stringify(planData, null, 2));

    try {
      let response;
      if (isEditing && id) { // Asegurarse de tener el ID para editar
        console.log(`[MealPlanForm] Llamando a MealPlanService.update con ID ${id}`);
        response = await MealPlanService.update(id, planData);
        setSuccess('Plan actualizado con éxito.');
      } else {
        console.log("[MealPlanForm] Llamando a MealPlanService.create");
        response = await MealPlanService.create(planData);
        setSuccess('Plan creado con éxito.');
        // Si creamos, podríamos querer actualizar el ID para futuras ediciones en la misma sesión
        // if (response && response.id) {
        //   navigate(`/nutrition/meal-plans/edit/${response.id}`, { replace: true }); // Ejemplo de redirección a editar
        // }
      }

      console.log("[MealPlanForm] Respuesta del servicio:", response);

      // Limpiar caché del servicio (si aplica y es necesario)
      // MealPlanService.clearCache(); // Ya se hace dentro del servicio

      // Ejecutar callback o navegar tras un breve delay para mostrar mensaje de éxito
      setTimeout(() => {
           if (onSaveSuccess) {
                onSaveSuccess(response); // Pasar respuesta (plan creado/actualizado) al callback
            } else {
                navigate('/nutrition/meal-plans'); // Navegar a la lista por defecto
            }
      }, 1500);

    } catch (err) {
      console.error("[MealPlanForm] Error al guardar el plan:", err);

      let errorMessage = `Error al ${isEditing ? 'actualizar' : 'crear'} el plan.`;

      // Intentar extraer mensaje más específico
      if (axios.isAxiosError(err)) { // Es un error de Axios (llamada API)
          if (err.response) {
              // Hubo respuesta del servidor (Error 4xx, 5xx)
              const status = err.response.status;
              const errorDetail = err.response.data?.detail;
              errorMessage += ` (Error ${status})`;
              if (typeof errorDetail === 'string') {
                  errorMessage = errorDetail; // Usar mensaje del backend directamente
              } else if (Array.isArray(errorDetail) && errorDetail[0]?.msg) {
                  // Formato de error de validación FastAPI
                  errorMessage = `Error de validación: ${errorDetail[0].msg} (Campo: ${errorDetail[0].loc.slice(1).join('.') || 'desconocido'})`;
              } else if (typeof err.response.data === 'string' && err.response.data.length < 200) {
                   // A veces el error viene como un string simple en la respuesta
                   errorMessage = err.response.data;
              }
          } else if (err.request) {
              // La petición se hizo pero no hubo respuesta (red, timeout)
              errorMessage = "No se pudo conectar con el servidor. Revisa tu conexión o inténtalo más tarde.";
          } else {
              // Error configurando la petición
              errorMessage = `Error de configuración: ${err.message}`;
          }
      } else if (err.isValidationError) {
           // Usar el mensaje del error de validación que lanzamos antes
           errorMessage = err.message;
      } else {
          // Otro tipo de error (JS, etc.)
          errorMessage = err.message || "Ocurrió un error inesperado.";
      }

      setError(errorMessage); // Mostrar el error procesado
       // No limpiar error automáticamente aquí, dejar que el usuario lo cierre o se limpie al intentar de nuevo/navegar

    } finally {
      setFormLoading(false); // <<<=== Asegurarse SIEMPRE de quitar el estado de carga del botón
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
      planName, description, isActive, items, // Dependencias del estado del formulario
      targetCalories, targetProtein, targetCarbs, targetFat, // Dependencias de targets
      isEditing, id, // Dependencias de modo edición
      navigate, onSaveSuccess // Dependencias de navegación/callback
  ]);

  // Filtrar items para la fecha del día activo
  const getActiveTabItems = useCallback(() => {
    const targetDateString = getActiveDateString();
    // console.log(`[MealPlanForm] Filtrando items para fecha: ${targetDateString}`);
    return items.filter(item => item.plan_date === targetDateString);
  }, [items, getActiveDateString]); // Depende de los items y de la fecha activa

  // --- Renderizado ---
  // Mostrar un loader principal si estamos cargando datos para editar
  if (loading && isEditing) { // Mostrar loader solo si está cargando *Y* en modo edición
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px', p: 5 }}>
        <CircularProgress />
        {/* *** CORRECCIÓN: Typography estaba indefinido aquí *** */}
        <Typography sx={{ ml: 2 }}>Cargando datos del plan...</Typography>
      </Box>
    );
  }

  return (
    <Box component="form" noValidate autoComplete="off" sx={{ mb: 4 }}>
      {/* Sección de Alertas */}
      <Box sx={{ mb: 2, minHeight: '60px' }}>
        {error && <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>{success}</Alert>}
      </Box>

      {/* Componentes del Formulario */}
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
        profile={userNutritionProfile} // Pasar perfil para posibles sugerencias
        onChange={handleTargetsChange}
      />

      <DaySelectorTabs
        days={daysOfWeek}
        activeTab={activeTab}
        onChange={(newTab) => setActiveTab(newTab)} // Cambiar la pestaña activa
      />

      {/* Sección de Selección y Lista de Comidas para el día activo */}
      <Box sx={{ mt: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
          {/* *** CORRECCIÓN: Typography estaba indefinido aquí *** */}
          <Typography variant="h6" gutterBottom>Comidas para {daysOfWeek[activeTab]} ({getActiveDateString()})</Typography>
          <MealSelector
            meals={availableMeals} // Lista de comidas disponibles para añadir
            onAddMeal={handleAddMeal}
            // Pasar estado de carga de comidas si fuera necesario
            // loadingMeals={loading} // Podría necesitar un estado de carga separado para meals
          />
          <DayMealsList
            items={getActiveTabItems()} // Mostrar solo las comidas del día activo
            onRemove={handleRemoveMeal}
          />
          {/* Podrías añadir un resumen de macros para el día activo aquí */}
          {/* <NutritionSummary items={getActiveTabItems()} /> */}
      </Box>


        {/* Componentes comentados si no están listos o no se usan */}
        {/* <ProgressSection items={items} activeDate={getActiveDateString()} ... /> */}
        {/* <PlanSummary items={items} ... /> */}


      {/* Botones de Acción */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Button
          variant="outlined"
          startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
          onClick={() => navigate('/nutrition/meal-plans')} // Botón para volver/cancelar
          disabled={formLoading} // Deshabilitar si se está guardando
        >
          {isEditing ? 'Volver sin Guardar' : 'Cancelar'}
        </Button>

        <Button
          type="button" // Importante que sea 'button' para no causar submit HTML nativo
          variant="contained"
          color="primary"
          onClick={handleSubmit} // Llama a nuestra función de guardado
          disabled={formLoading || !planName.trim() || loading} // Deshabilitar si carga, guarda, o no hay nombre
          startIcon={formLoading ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
        >
          {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
        </Button>
      </Box>
    </Box>
  );
};

export default MealPlanForm;