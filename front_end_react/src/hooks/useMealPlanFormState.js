// src/hooks/useMealPlanFormState.js

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MealPlanService } from '../services/nutrition'; // Asegúrate que la ruta es correcta
import { format, parseISO, isValid, getDay } from 'date-fns'; // Importar date-fns
import { es } from 'date-fns/locale/es'; // Importar locale español si se usa format

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
    is_active: true, // Añadido is_active, importante para el backend
    // Añadir cualquier otro campo necesario del plan
};

// Helper para obtener el nombre del día correcto basado en date-fns (0=Domingo, 1=Lunes...)
const getDayName = (date) => {
    const dayIndex = getDay(date); // 0 for Sunday, 1 for Monday etc.
    const days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    return days[dayIndex];
}


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
                    // *** CORREGIDO: Usar getById del servicio ***
                    const data = await MealPlanService.getById(planId, true); // Pedir con items
                    if (isMounted && data) {
                        // Transformar items a la estructura 'days' requerida por el frontend
                        const formattedDays = {};
                        if (data.items && Array.isArray(data.items)) {
                            data.items.forEach(item => {
                                // Necesitamos una forma de obtener la fecha 'YYYY-MM-DD' del item
                                // Si el item tiene 'plan_date', la usamos. Si no, intentamos derivarla si es posible.
                                // ¡¡ESTO ES CRÍTICO Y DEPENDE DE TU API!!
                                // Asumiendo que 'plan_date' VIENE del backend en formato ISO o similar.
                                let dateString = null;
                                if (item.plan_date && isValid(parseISO(item.plan_date))) {
                                     dateString = format(parseISO(item.plan_date), 'yyyy-MM-dd');
                                } else if (item.day_of_week && plan.start_date) {
                                    // Lógica más compleja si solo viene day_of_week (no recomendado para carga)
                                    console.warn("Item solo tiene day_of_week, la carga puede ser imprecisa si no hay plan_date");
                                    // Se necesitaría mapear day_of_week a una fecha específica de la semana del plan
                                    // Esta parte es compleja y propensa a errores, idealmente el backend debe devolver plan_date
                                }

                                if (dateString) {
                                    if (!formattedDays[dateString]) {
                                        formattedDays[dateString] = [];
                                    }
                                    // Crear el mealItem para el estado frontend.
                                    // Asume que 'item' del backend ya trae suficiente info de la comida.
                                    // Si solo trae meal_id, necesitarías obtener detalles de la comida de otra fuente (ej: useAvailableMeals)
                                    formattedDays[dateString].push({
                                        // Usar el ID del *meal_plan_item* como ID único en el frontend
                                        id: item.id, // Este debería ser el ID de la tabla meal_plan_items
                                        meal_plan_item_id: item.id, // Guardarlo explícitamente
                                        meal_id: item.meal_id, // El ID de la comida en sí
                                        // Asumir que estos campos vienen del backend (JOIN en la consulta de getById)
                                        // Si no vienen, tendrás que buscarlos en availableMeals usando item.meal_id
                                        meal: { // Anidar el objeto meal si EnhancedMealPlanForm lo espera así
                                            id: item.meal_id,
                                            name: item.meal_name || 'Unknown Meal',
                                            calories: item.calories || 0,
                                            protein_g: item.protein_g || 0,
                                            carbohydrates_g: item.carbohydrates_g || 0,
                                            fat_g: item.fat_g || 0,
                                            image_url: item.image_url || null
                                            // ...otros detalles de la comida...
                                        },
                                        quantity: item.quantity || 1,
                                        unit: item.unit || 'serving', // O el default que uses
                                        meal_type: item.meal_type || 'Comida', // Añadir meal_type si existe
                                        meal_time: item.meal_time || item.meal_type || 'Comida', // Compatibilidad
                                        // ... otros campos necesarios ...
                                    });
                                } else {
                                    console.warn("No se pudo determinar la fecha para el item:", item);
                                }
                            });
                        }

                        setPlan({
                            id: data.id,
                            name: data.plan_name || data.name || '', // Ser flexible con el nombre
                            description: data.description || '',
                            start_date: data.start_date ? format(parseISO(data.start_date), 'yyyy-MM-dd') : null, // Asegurar formato
                            end_date: data.end_date ? format(parseISO(data.end_date), 'yyyy-MM-dd') : null, // Asegurar formato
                            target_calories: data.target_calories ?? '', // Usar ?? para manejar null/undefined
                            target_protein_g: data.target_protein_g ?? '',
                            target_carbs_g: data.target_carbs_g ?? '',
                            target_fat_g: data.target_fat_g ?? '',
                            goal: data.goal || '',
                            is_active: data.is_active !== undefined ? data.is_active : true, // Manejar is_active
                            days: formattedDays,
                        });
                    } else if (isMounted) {
                        setError(`Plan ID: ${planId} no encontrado o respuesta inválida.`);
                        setPlan(initialPlanState); // Resetear a estado inicial si falla la carga
                    }
                } catch (err) {
                    console.error("useMealPlanFormState - Error loading plan:", err);
                    if (isMounted) {
                        setError(err.message || 'Error cargando el plan.');
                        setPlan(initialPlanState); // Resetear a estado inicial si falla la carga
                    }
                } finally {
                    if (isMounted) setIsLoading(false);
                }
            };
            loadPlan();
        } else {
             // Resetear si pasamos de editar a crear o si no hay planId
             setPlan(initialPlanState);
             setIsLoading(false);
             setError(null);
             setSuccess(null);
        }

        return () => { isMounted = false; };
    }, [isEditing, planId]); // Dependencia clave


    // --- Manejador genérico para campos simples del plan ---
    const handleChange = useCallback((event) => {
        const { name, value, type, checked } = event.target;
        setPlan(prevPlan => ({
            ...prevPlan,
            // Usar 'checked' para checkboxes, 'value' para otros
            [name]: type === 'checkbox' ? checked : value
        }));
    }, []);

    // --- Manejador para cambios de fecha (si usas DatePickers externos) ---
    const handleDateChange = useCallback((name, date) => {
        setPlan(prevPlan => ({
            ...prevPlan,
            // Formatear a YYYY-MM-DD o null si la fecha no es válida
            [name]: date && isValid(date) ? format(date, 'yyyy-MM-dd') : null
        }));
    }, []);


    // --- Modificadores para la estructura 'days' ---
    const addMealToDay = useCallback((dateString, meal) => {
        // Generar un ID temporal ÚNICO para este item en el frontend
        const tempId = `temp_${Date.now()}_${Math.random()}`;

        setPlan(prevPlan => {
            const currentDayMeals = prevPlan.days[dateString] ? [...prevPlan.days[dateString]] : [];
            // Crear el nuevo item con la estructura esperada por el frontend
            const newMealItem = {
                id: tempId, // Asignar ID temporal
                meal_plan_item_id: null, // ID real vendrá del backend
                meal_id: meal.id, // ID de la comida base
                meal: { ...meal }, // Guardar el objeto comida completo para mostrar detalles
                quantity: meal.quantity || 100, // Default quantity (e.g., 100g)
                unit: meal.unit || 'g', // Default unit (e.g., grams)
                // Puedes añadir meal_type aquí si lo gestionas en el MealSearchInput
                // meal_type: meal.meal_type || 'Comida',
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
            // Filtrar por el ID único del item (puede ser temporal o el ID de meal_plan_item)
            const updatedDayMeals = currentDayMeals.filter(item => item.id !== mealItemId);

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
                // Validar y asegurar que quantity sea un número >= 0
                const numQuantity = Number(quantity);
                const validQuantity = !isNaN(numQuantity) && numQuantity >= 0 ? numQuantity : currentDayMeals[mealIndex].quantity; // Mantener anterior si inválido

                const updatedMeal = { ...currentDayMeals[mealIndex], quantity: validQuantity };
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
            // Validar la fecha antes de usarla
             if (!isValid(parseISO(dateString))) {
                console.error(`Fecha inválida encontrada en el estado 'days': ${dateString}`);
                setError(`Se encontró una fecha inválida (${dateString}) en el plan.`);
                // Podríamos decidir parar aquí o continuar sin los items de esta fecha
                // Por seguridad, paramos:
                 throw new Error("Fecha inválida en el plan."); // Lanzar error para detener el guardado
             }

             mealItems.forEach(item => {
                 // El backend espera una lista de items con meal_id, quantity, y una forma de saber el día/tipo
                 const backendItem = {
                    meal_id: item.meal_id || item.meal?.id, // Asegurar que tenemos meal_id
                    quantity: item.quantity,
                    unit: item.unit || 'g', // Enviar unidad si el backend la usa
                    // Elegir CÓMO representar el día: plan_date o day_of_week
                    // Opción 1: Enviar fecha exacta (preferido si el backend lo soporta)
                    plan_date: dateString, // 'YYYY-MM-DD'
                    // Opción 2: Enviar día de la semana (si el backend lo prefiere así)
                    // day_of_week: getDayName(parseISO(dateString)), // Ej: 'Lunes', 'Martes'...
                    // Enviar tipo de comida si existe
                    meal_type: item.meal_type || item.meal_time || 'Comida', // Usar meal_type si está definido
                    // Enviar el ID del meal_plan_item si estamos editando y el item ya existe en DB
                    ...(isEditing && item.meal_plan_item_id && { id: item.meal_plan_item_id }),
                 };
                 // Validar que tenemos meal_id antes de añadir
                 if (!backendItem.meal_id) {
                     console.error("Item sin meal_id encontrado, no se puede guardar:", item);
                     setError(`Falta ID de comida para un item en ${dateString}.`);
                     throw new Error("Item inválido en el plan."); // Lanzar error
                 }
                 itemsToSave.push(backendItem);
             });
         });

        /* // Validación opcional: ¿Hay items? (Descomentar si es necesario)
        if (itemsToSave.length === 0 && !isEditing) { // Solo requerir items al crear
            setError("El plan debe contener al menos una comida para ser creado.");
            return false;
        }
        */

        setIsLoading(true);
        // Crear el objeto a enviar, asegurando que los targets sean números o null
        const planDataToSend = {
            // Quitar 'id' al crear, incluirlo al actualizar
            ...(isEditing && { id: plan.id }),
            plan_name: plan.name, // Asegurar que el backend espera plan_name
            description: plan.description,
            goal: plan.goal,
            is_active: plan.is_active, // Enviar estado activo
            start_date: plan.start_date, // Enviar fechas si existen y son válidas
            end_date: plan.end_date,
            target_calories: plan.target_calories === '' || plan.target_calories === null ? null : Number(plan.target_calories),
            target_protein_g: plan.target_protein_g === '' || plan.target_protein_g === null ? null : Number(plan.target_protein_g),
            target_carbs_g: plan.target_carbs_g === '' || plan.target_carbs_g === null ? null : Number(plan.target_carbs_g),
            target_fat_g: plan.target_fat_g === '' || plan.target_fat_g === null ? null : Number(plan.target_fat_g),
            items: itemsToSave, // La lista transformada de items
            user_id: '1' // O el ID del usuario actual si lo obtienes de alguna parte
        };

        console.log("Enviando datos al backend:", JSON.stringify(planDataToSend, null, 2));


        try {
            let response;
            if (isEditing) {
                 // *** CORREGIDO: Usar update del servicio ***
                console.log(`Intentando actualizar plan ID: ${planId}`);
                response = await MealPlanService.update(planId, planDataToSend);
                setSuccess('Plan de nutrición actualizado con éxito.');
            } else {
                // *** CORREGIDO: Usar create del servicio ***
                console.log("Intentando crear nuevo plan");
                response = await MealPlanService.create(planDataToSend);
                setSuccess('Plan de nutrición creado con éxito.');
                // Si la creación devuelve el plan con ID, podríamos actualizar el estado
                // if (response && response.id) {
                //     setPlan(prev => ({ ...prev, id: response.id })); // Actualizar ID local
                // }
            }
             console.log("Respuesta del backend:", response);
             // Opcional: Navegar después de un tiempo
             // setTimeout(() => navigate('/nutrition/meal-plans'), 1500);
             return true; // Indicar éxito

        } catch (err) {
            console.error("useMealPlanFormState - Error saving plan:", err);
            // Intentar obtener un mensaje de error más específico si la API lo envía
            const errorDetail = err.response?.data?.detail || err.message || 'Ocurrió un error al guardar.';
            setError(errorDetail);
            return false; // Indicar fallo
        } finally {
            setIsLoading(false);
        }
    }, [plan, isEditing, planId, navigate]); // Dependencias


    // --- Devolver Estado y Funciones ---
    return {
        plan, // El objeto completo del plan
        setPlan, // Función para modificar el plan (usada por handleTargetsChange en el form)
        isLoading,
        error,
        success, // Añadido estado de éxito
        handleChange, // El manejador genérico para name, description, is_active, etc.
        handleDateChange, // Para fechas
        addMealToDay, // Funciones específicas para manipular 'days'
        removeMealFromDay,
        updateMealQuantity,
        saveMealPlan // La función para guardar
    };
};