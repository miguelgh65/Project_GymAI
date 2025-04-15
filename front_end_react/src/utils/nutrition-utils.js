// utils/nutrition-utils.js
// Utilidades para normalizar datos y manejar cálculos nutricionales

/**
 * Normaliza un objeto de comida para garantizar la consistencia de campos
 * @param {Object} meal - Objeto comida a normalizar
 * @returns {Object} Objeto comida normalizado
 */
export function normalizeMeal(meal) {
    if (!meal) return null;
    
    return {
      id: meal.id,
      meal_name: meal.meal_name || meal.name || '',
      name: meal.name || meal.meal_name || '',
      recipe: meal.recipe || '',
      ingredients: meal.ingredients || '',
      description: meal.description || meal.recipe || meal.ingredients || '',
      calories: typeof meal.calories === 'number' ? Math.max(0, meal.calories) : 0,
      proteins: typeof meal.proteins === 'number' ? Math.max(0, meal.proteins) : 0,
      carbohydrates: typeof meal.carbohydrates === 'number' ? Math.max(0, meal.carbohydrates) : 0,
      fats: typeof meal.fats === 'number' ? Math.max(0, meal.fats) : 0,
      image_url: meal.image_url || ''
    };
  }
  
  /**
   * Normaliza un objeto de plan de comida para garantizar la consistencia de campos
   * @param {Object} plan - Objeto plan de comida a normalizar
   * @returns {Object} Objeto plan de comida normalizado
   */
  export function normalizeMealPlan(plan) {
    if (!plan) return null;
    
    return {
      id: plan.id,
      plan_name: plan.plan_name || plan.name || '',
      name: plan.name || plan.plan_name || '',
      description: plan.description || '',
      is_active: typeof plan.is_active === 'boolean' ? plan.is_active : true,
      start_date: plan.start_date || null,
      end_date: plan.end_date || null,
      items: Array.isArray(plan.items) ? plan.items.map(normalizeItem) : []
    };
  }
  
  /**
   * Normaliza un objeto de ingrediente para garantizar la consistencia de campos
   * @param {Object} ingredient - Objeto ingrediente a normalizar
   * @returns {Object} Objeto ingrediente normalizado
   */
  export function normalizeIngredient(ingredient) {
    if (!ingredient) return null;
    
    return {
      id: ingredient.id,
      ingredient_name: ingredient.ingredient_name || '',
      name: ingredient.name || ingredient.ingredient_name || '',
      calories: typeof ingredient.calories === 'number' ? Math.max(0, ingredient.calories) : 0,
      proteins: typeof ingredient.proteins === 'number' ? Math.max(0, ingredient.proteins) : 0,
      carbohydrates: typeof ingredient.carbohydrates === 'number' ? Math.max(0, ingredient.carbohydrates) : 0,
      fats: typeof ingredient.fats === 'number' ? Math.max(0, ingredient.fats) : 0
    };
  }
  
  /**
   * Normaliza un elemento del plan de comida (item)
   * @param {Object} item - Elemento del plan a normalizar
   * @returns {Object} Elemento del plan normalizado
   */
  function normalizeItem(item) {
    if (!item) return null;
    
    return {
      id: item.id,
      meal_id: item.meal_id,
      meal_name: item.meal_name || '',
      day_of_week: item.day_of_week || '',
      meal_type: item.meal_type || '',
      quantity: typeof item.quantity === 'number' ? Math.max(0, item.quantity) : 1
    };
  }
  
  /**
   * Formatea un valor de calorías para mostrar
   * @param {number|string} calories - Valor de calorías
   * @returns {string} Valor formateado
   */
  export function formatCalories(calories) {
    // Si es un número, formatearlo correctamente
    if (typeof calories === 'number') {
      return calories >= 0 ? `${Math.round(calories)} kcal` : '0 kcal';
    }
    
    // Si es un string que se puede convertir a número
    if (typeof calories === 'string' && !isNaN(parseFloat(calories))) {
      const numCal = parseFloat(calories);
      return numCal >= 0 ? `${Math.round(numCal)} kcal` : '0 kcal';
    }
    
    // Para cualquier otro caso
    return '0 kcal';
  }
  
  /**
   * Crea un informe nutricional resumido
   * @param {Object} item - Objeto con datos nutricionales (meal o ingredient)
   * @returns {Object} Reporte con calorías, macronutrientes y porcentajes
   */
  export function getNutritionSummary(item) {
    if (!item) return null;
    
    const nutrition = normalizeItemForNutrition(item);
    
    // Calcular calorías de cada macronutriente
    const proteinCalories = nutrition.proteins * 4;
    const carbCalories = nutrition.carbohydrates * 4;
    const fatCalories = nutrition.fats * 9;
    
    // Total de calorías calculado (podría diferir del valor almacenado)
    const calculatedCalories = proteinCalories + carbCalories + fatCalories;
    
    // Usar el valor calculado si difiere significativamente del almacenado
    const useCalculated = Math.abs(calculatedCalories - nutrition.calories) > 10;
    const totalCalories = useCalculated ? calculatedCalories : nutrition.calories;
    
    // Calcular porcentajes
    const proteinPercentage = totalCalories > 0 ? Math.round((proteinCalories / totalCalories) * 100) : 0;
    const carbPercentage = totalCalories > 0 ? Math.round((carbCalories / totalCalories) * 100) : 0;
    const fatPercentage = totalCalories > 0 ? Math.round((fatCalories / totalCalories) * 100) : 0;
    
    return {
      calories: totalCalories,
      macros: {
        proteins: {
          grams: nutrition.proteins,
          calories: proteinCalories,
          percentage: proteinPercentage
        },
        carbs: {
          grams: nutrition.carbohydrates,
          calories: carbCalories,
          percentage: carbPercentage
        },
        fats: {
          grams: nutrition.fats,
          calories: fatCalories,
          percentage: fatPercentage
        }
      },
      formattedCalories: formatCalories(totalCalories)
    };
  }
  
  /**
   * Normaliza cualquier tipo de item para extraer sus datos nutricionales
   * @param {Object} item - Objeto a normalizar (puede ser meal, ingredient u otro)
   * @returns {Object} Objeto con propiedades nutricionales normalizadas
   */
  function normalizeItemForNutrition(item) {
    return {
      calories: typeof item.calories === 'number' ? Math.max(0, item.calories) : 0,
      proteins: typeof item.proteins === 'number' ? Math.max(0, item.proteins) : 0,
      carbohydrates: typeof item.carbohydrates === 'number' ? Math.max(0, item.carbohydrates) : 0,
      fats: typeof item.fats === 'number' ? Math.max(0, item.fats) : 0
    };
  }