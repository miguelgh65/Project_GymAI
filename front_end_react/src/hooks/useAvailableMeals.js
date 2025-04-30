// src/hooks/useAvailableMeals.js
import { useState, useEffect } from 'react';
// Asegúrate que la ruta a MealService es correcta desde la carpeta hooks
import { MealService } from '../services/nutrition';

export const useAvailableMeals = () => {
    const [availableMeals, setAvailableMeals] = useState([]);
    const [loadingMeals, setLoadingMeals] = useState(true); // Estado interno de carga
    const [errorLoadingMeals, setErrorLoadingMeals] = useState(null); // Estado interno de error

    useEffect(() => {
        let isMounted = true;
        const fetchMeals = async () => {
            setLoadingMeals(true);
            setErrorLoadingMeals(null);
            try {
                const response = await MealService.getAll();

                // response.meals debería ser un array de objetos como:
                // [{ id: 1, meal_name: "Pollo...", calories: 300, proteins: 30, ... }, ...]
                const mealsArray = response?.meals && Array.isArray(response.meals) ? response.meals : [];

                if (isMounted) {
                    console.log(`useAvailableMeals: Recibidos ${mealsArray.length} objetos de comida. Iniciando transformación...`);

                    // *** CORRECCIÓN AQUÍ: Procesar cada 'meal' como un objeto ***
                    const transformedMeals = mealsArray.map((meal, index) => {
                        // --- Log para ver cada objeto original ---
                        console.log(`Mapping meal object ${index}:`, meal);

                        // Validar que 'meal' sea un objeto y tenga las propiedades esperadas
                        if (typeof meal !== 'object' || meal === null) {
                            console.warn(`Item ${index} no es un objeto válido:`, meal);
                            return null; // Saltar este item si no es un objeto
                        }

                        // Intentar extraer y convertir valores usando las claves del objeto
                        const id = meal?.id;
                        const name = meal?.meal_name || meal?.name; // Aceptar ambos nombres por si acaso
                        const caloriesStr = meal?.calories;
                        const proteinStr = meal?.proteins;
                        const carbsStr = meal?.carbohydrates;
                        const fatStr = meal?.fats;
                        const imageUrl = meal?.image_url;

                        // Convertir a números, usando 0 como default si falla o es null/undefined
                        const calories = parseFloat(caloriesStr) || 0;
                        const protein_g = parseFloat(proteinStr) || 0;
                        const carbohydrates_g = parseFloat(carbsStr) || 0;
                        const fat_g = parseFloat(fatStr) || 0;

                        const resultingObject = {
                            id: id,
                            name: name || 'Nombre Desconocido', // Fallback por si el nombre falta
                            // Propiedades que espera el formulario/componentes
                            calories: calories,
                            protein_g: protein_g,
                            carbohydrates_g: carbohydrates_g,
                            fat_g: fat_g,
                            // Otros campos originales que puedan ser útiles
                            recipe: meal?.recipe,
                            ingredients_str: meal?.ingredients, // Si existe el campo de ingredientes como string
                            image_url: imageUrl || null
                        };

                        // --- Log para ver el objeto resultante ---
                        console.log(`Resulting object ${index}:`, resultingObject);
                        // --- Log para ver si parseFloat falló (NaN) ---
                        if (isNaN(calories) || isNaN(protein_g) || isNaN(carbohydrates_g) || isNaN(fat_g)) {
                            console.warn(`   >> NaN detected in object ${index}! Check parseFloat inputs:`, {caloriesStr, proteinStr, carbsStr, fatStr});
                        }

                        // Solo devolver si tiene id y nombre válidos
                        if (resultingObject.id && resultingObject.name) {
                            return resultingObject;
                        } else {
                            console.warn(`   >> Objeto inválido o incompleto descartado:`, resultingObject);
                            return null;
                        }

                    }).filter(m => m !== null); // Filtrar los que resultaron null

                    console.log("useAvailableMeals: Comidas transformadas y filtradas:", transformedMeals);

                    setAvailableMeals(transformedMeals);

                    // --- Lógica de error/warning ---
                    if (transformedMeals.length === 0 && mealsArray.length > 0) {
                         console.error("useAvailableMeals: ERROR - Se recibieron objetos de comida pero la transformación/filtro falló para TODOS.");
                         // Mantenemos el error original porque indica un problema de formato inesperado
                         setErrorLoadingMeals("Formato de datos de comidas inesperado recibido del backend o fallo en la transformación.");
                    } else if (transformedMeals.length === 0) {
                        console.warn("useAvailableMeals: Carga finalizada pero no se encontraron comidas válidas en la respuesta.");
                        // Podrías considerar no poner un error aquí si es válido no tener comidas
                        // setErrorLoadingMeals("No se encontraron comidas disponibles.");
                    } else {
                         console.log(`useAvailableMeals: Carga finalizada, ${transformedMeals.length} comidas transformadas válidas encontradas.`);
                    }
                }
            } catch (err) {
                console.error("useAvailableMeals - Error fetching meals:", err);
                if (isMounted) {
                    // Asegúrate de que el mensaje de error sea útil
                    const errorMessage = err.response?.data?.detail || err.message || "No se pudieron cargar las comidas disponibles. Intenta de nuevo más tarde.";
                    setErrorLoadingMeals(errorMessage);
                    setAvailableMeals([]); // Limpiar comidas en caso de error
                }
            } finally {
                if (isMounted) {
                    setLoadingMeals(false);
                }
            }
        };

        fetchMeals();

        return () => {
            isMounted = false; // Cleanup
        };
    }, []); // Ejecutar solo al montar

    // Devolver isLoading y error
    return { availableMeals, isLoading: loadingMeals, error: errorLoadingMeals };
};