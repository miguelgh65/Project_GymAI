import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MealPlanService } from '../services/nutrition'; // Asegúrate que la ruta es correcta
import { format, parseISO, isValid } from 'date-fns'; // Importar date-fns si es necesario aquí o pasar datos preformateados

// Estructura inicial del estado del plan
const initialPlanState = {
    id: null,
    name: '',
    description: '',
    start_date: null, // Podrías inicializar con fechas si lo deseas
    end_date: null,
    target_calories: '', // Inicializar como string vacío para inputs controlados
    target_protein_g: '',
    target_carbs_g: '',
    target_fat_g: '',
    goal: '', // Añadido goal si lo necesitas
    days: {}, // Objeto para { 'YYYY-MM-DD': [mealItem] }
    // Añadir cualquier otro campo necesario del plan
};

export const useMealPlanFormState = (planId) => {
    const navigate = useNavigate();
    const isEditing = Boolean(planId);

    const [plan, setPlan] = useState(initialPlanState);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null); // Para mensajes de éxito

    // --- Carga inicial en modo edición ---
    useEffect(() => {
        let isMounted = true;
        if (isEditing && planId) {
            const loadPlan = async () => {
                setIsLoading(true);
                setError(null);
                try {
                    // Asumiendo que getMealPlanById devuelve un objeto plan con la estructura deseada
                    // incluyendo name, description, targets, y 'items' que podemos transformar en 'days'
                    const data = await MealPlanService.getMealPlanById(planId);
                    if (isMounted && data) {
                        // Transformar items a la estructura 'days' requerida por el frontend
                        const formattedDays = {};
                        if (data.items && Array.isArray(data.items)) {
                             data.items.forEach(item => {
                                // Necesitamos una forma de obtener la fecha 'YYYY-MM-DD' del item
                                // Asumiré que 'plan_date' existe en el item. ¡¡AJUSTA ESTO!!
                                const dateString = item.plan_date ? format(parseISO(item.plan_date), 'yyyy-MM-dd') : null;

                                if (dateString) {
                                    if (!formattedDays[dateString]) {
                                        formattedDays[dateString] = [];
                                    }
                                    // Crear el mealItem. ¡¡NECESITAS ADAPTAR ESTO!!
                                    // Debes obtener los detalles de la comida (macros, etc.) si no vienen en 'item'
                                    // Y asegurar que tenga un ID único (item.id o meal_plan_item_id)
                                    formattedDays[dateString].push({
                                        id: item.id, // o item.meal_plan_item_id
                                        meal_id: item.meal_id,
                                        name: item.meal_name || 'Unknown Meal', // Obtener nombre real
                                        quantity: item.quantity,
                                        unit: item.unit,
                                        // Incluir macros aquí si es posible para el cálculo en frontend
                                        calories: item.calories || 0,
                                        protein_g: item.protein_g || 0,
                                        carbohydrates_g: item.carbohydrates_g || 0,
                                        fat_g: item.fat_g || 0,
                                        // ... otros campos necesarios ...
                                    });
                                }
                            });
                        }

                        setPlan({
                            id: data.id,
                            name: data.name || '',
                            description: data.description || '',
                            start_date: data.start_date,
                            end_date: data.end_date,
                            target_calories: data.target_calories ?? '', // Usar ?? para manejar null/undefined
                            target_protein_g: data.target_protein_g ?? '',
                            target_carbs_g: data.target_carbs_g ?? '',
                            target_fat_g: data.target_fat_g ?? '',
                            goal: data.goal || '',
                            days: formattedDays,
                        });
                    } else if (isMounted) {
                         setError(`Plan ID: ${planId} no encontrado.`);
                    }
                } catch (err) {
                    console.error("useMealPlanFormState - Error loading plan:", err);
                    if (isMounted) setError(err.message || 'Error cargando el plan.');
                } finally {
                    if (isMounted) setIsLoading(false);
                }
            };
            loadPlan();
        }
        // Resetear si pasamos de editar a crear
        if (!isEditing) {
            setPlan(initialPlanState);
        }

        return () => { isMounted = false; };
    }, [isEditing, planId]); // Dependencia clave

    // --- Manejador genérico para campos simples del plan ---
    const handleChange = useCallback((event) => {
        const { name, value } = event.target;
        setPlan(prevPlan => ({
            ...prevPlan,
            [name]: value
        }));
    }, []);

    // --- Manejador para cambios de fecha (si usas DatePickers externos) ---
    const handleDateChange = useCallback((name, date) => {
        setPlan(prevPlan => ({
            ...prevPlan,
            [name]: date ? format(date, 'yyyy-MM-dd') : null // Formatear fecha
        }));
    }, []);


    // --- Modificadores para la estructura 'days' ---
    const addMealToDay = useCallback((dateString, meal) => {
        // Generar un ID temporal ÚNICO para este item en el frontend
        // Puede ser basado en timestamp o un contador simple, hasta que se guarde y obtenga ID real
        const tempId = `temp_${Date.now()}_${Math.random()}`;

        setPlan(prevPlan => {
            const currentDayMeals = prevPlan.days[dateString] ? [...prevPlan.days[dateString]] : [];
            const newMealItem = {
                ...meal, // Asume que 'meal' tiene {meal_id, name, calories, macros...}
                id: tempId, // Asignar ID temporal
                meal_plan_item_id: null, // ID real vendrá del backend
                quantity: meal.quantity || 1, // Default quantity
                unit: meal.unit || 'serving' // Default unit
            };
            currentDayMeals.push(newMealItem);
            return {
                ...prevPlan,
                days: {
                    ...prevPlan.days,
                    [dateString]: currentDayMeals
                }
            };
        });
    }, []);

    const removeMealFromDay = useCallback((dateString, mealItemId) => {
        setPlan(prevPlan => {
            const currentDayMeals = prevPlan.days[dateString] ? prevPlan.days[dateString] : [];
            const updatedDayMeals = currentDayMeals.filter(item => item.id !== mealItemId); // Filtrar por ID único

            // Si el día queda vacío, podríamos eliminar la clave, o dejarla con array vacío
            const updatedDays = { ...prevPlan.days };
            if (updatedDayMeals.length > 0) {
                 updatedDays[dateString] = updatedDayMeals;
            } else {
                 delete updatedDays[dateString]; // Eliminar día si queda vacío
            }

            return {
                ...prevPlan,
                days: updatedDays
            };
        });
    }, []);

    const updateMealQuantity = useCallback((dateString, mealItemId, quantity) => {
        setPlan(prevPlan => {
             const currentDayMeals = prevPlan.days[dateString] ? [...prevPlan.days[dateString]] : [];
             const mealIndex = currentDayMeals.findIndex(item => item.id === mealItemId);

             if (mealIndex > -1) {
                 const updatedMeal = { ...currentDayMeals[mealIndex], quantity: Number(quantity) || 0 }; // Asegurar número
                 currentDayMeals[mealIndex] = updatedMeal;
                 return {
                     ...prevPlan,
                     days: {
                         ...prevPlan.days,
                         [dateString]: currentDayMeals
                     }
                 };
             }
             return prevPlan; // No hacer nada si no se encuentra el item
        });
    }, []);


    // --- Lógica de Guardado ---
    const saveMealPlan = useCallback(async () => {
        setError(null);
        setSuccess(null);

        if (!plan.name?.trim()) {
            setError("El nombre del plan es obligatorio.");
            return false;
        }

        // Transformar la estructura 'days' a la estructura 'items' que espera el backend
        const itemsToSave = [];
        Object.entries(plan.days).forEach(([dateString, mealItems]) => {
             mealItems.forEach(item => {
                 // Omitir IDs temporales al enviar al backend si es creación
                 // o asegurarse de enviar el ID correcto si es edición
                 const backendItem = {
                     meal_id: item.meal_id,
                     plan_date: dateString, // Asegurarse que el backend espera 'YYYY-MM-DD'
                     quantity: item.quantity,
                     unit: item.unit,
                     // Añadir meal_plan_item_id si existe y estamos editando
                     ...(isEditing && item.meal_plan_item_id && { id: item.meal_plan_item_id }), // Asume que el ID del item es 'id' en el backend
                     // Otros campos necesarios por el backend...
                 };
                 itemsToSave.push(backendItem);
             });
        });

        /* // Validación opcional: ¿Hay items?
        if (itemsToSave.length === 0) {
            setError("El plan debe contener al menos una comida.");
            return false;
        }
        */

        setIsLoading(true);
        // Crear el objeto a enviar, asegurando que los targets sean números o null
        const planDataToSend = {
            name: plan.name,
            description: plan.description,
            goal: plan.goal,
            start_date: plan.start_date,
            end_date: plan.end_date,
            target_calories: plan.target_calories === '' ? null : Number(plan.target_calories),
            target_protein_g: plan.target_protein_g === '' ? null : Number(plan.target_protein_g),
            target_carbs_g: plan.target_carbs_g === '' ? null : Number(plan.target_carbs_g),
            target_fat_g: plan.target_fat_g === '' ? null : Number(plan.target_fat_g),
            items: itemsToSave
        };

        try {
            let response;
            if (isEditing) {
                response = await MealPlanService.updateMealPlan(planId, planDataToSend);
                setSuccess('Plan de nutrición actualizado con éxito.');
            } else {
                response = await MealPlanService.createMealPlan(planDataToSend);
                setSuccess('Plan de nutrición creado con éxito.');
            }
             // Opcional: Navegar después de un tiempo o basado en la respuesta
             // setTimeout(() => navigate('/nutrition/meal-plans'), 1500);
             return true; // Indicar éxito
        } catch (err) {
            console.error("useMealPlanFormState - Error saving plan:", err);
            const errorDetail = err.response?.data?.detail || err.message || 'Ocurrió un error al guardar.';
            setError(errorDetail);
            return false; // Indicar fallo
        } finally {
            setIsLoading(false);
        }
    }, [plan, isEditing, planId, navigate]); // Dependencias

    // --- Devolver Estado y Funciones ---
    // Ahora devolvemos la estructura que espera EnhancedMealPlanForm
    return {
        plan, // El objeto completo del plan
        setPlan, // Función para modificar el plan (usada por handleTargetsChange)
        isLoading,
        error,
        success, // Añadido estado de éxito
        handleChange, // El manejador genérico para name, description, etc.
        handleDateChange, // Para fechas
        addMealToDay, // Funciones específicas para manipular 'days'
        removeMealFromDay,
        updateMealQuantity,
        saveMealPlan // La función para guardar
    };
};