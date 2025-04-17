/**
 * Formatea un objeto de macros a un string legible, redondeando decimales.
 * @param {object} macros - Objeto con { calories, protein_g, carbohydrates_g, fat_g }.
 * @returns {string} - String formateado.
 */
export const formatMacros = (macros) => {
  if (!macros) return 'C: 0, P: 0g, C: 0g, F: 0g';
  const cal = Math.round(macros.calories || 0);
  const p = Math.round(macros.protein_g || 0);
  const c = Math.round(macros.carbohydrates_g || 0);
  const f = Math.round(macros.fat_g || 0);
  return `Cals: ${cal}, P: ${p}g, C: ${c}g, F: ${f}g`;
};

/**
* Calcula los porcentajes de macronutrientes basados en las calorías totales.
* @param {object} macros - Objeto con { calories, protein_g, carbohydrates_g, fat_g }.
* @returns {object|null} - Objeto con { proteinPercent, carbPercent, fatPercent } o null si las calorías son 0.
*/
export const calculateMacroPercentages = (macros) => {
  if (!macros || !macros.calories || macros.calories === 0) {
      return { proteinPercent: 0, carbPercent: 0, fatPercent: 0 }; // Devuelve 0 si no hay calorías
  }

  const proteinCalories = (macros.protein_g || 0) * 4;
  const carbCalories = (macros.carbohydrates_g || 0) * 4;
  const fatCalories = (macros.fat_g || 0) * 9;
  const totalCalculatedCalories = proteinCalories + carbCalories + fatCalories; // Usar suma calculada para evitar división por cero si macros.calories es erróneo

  if (totalCalculatedCalories === 0) {
       return { proteinPercent: 0, carbPercent: 0, fatPercent: 0 };
  }

  const proteinPercent = Math.round((proteinCalories / totalCalculatedCalories) * 100);
  const carbPercent = Math.round((carbCalories / totalCalculatedCalories) * 100);
  const fatPercent = Math.round((fatCalories / totalCalculatedCalories) * 100);

  // Ajuste para que la suma sea 100% (opcional, puede llevar a ligeras imprecisiones)
  const sum = proteinPercent + carbPercent + fatPercent;
  if (sum !== 100 && sum !== 0) {
      const diff = 100 - sum;
      // Añadir la diferencia al macro mayoritario (o manejarlo como prefieras)
      // En este caso simple, lo añadimos a los carbohidratos por ejemplo
      return { proteinPercent, carbPercent: carbPercent + diff, fatPercent };
  }


  return { proteinPercent, carbPercent, fatPercent };
};


// --- FUNCIONES AÑADIDAS PARA EL CÁLCULO DE PLANES ---

/**
* Calcula las macros totales para un array de items de comida (mealItems).
* Asume que cada item tiene quantity, calories, protein_g, carbohydrates_g, fat_g.
* @param {Array} mealItems - Array de objetos de comida para un día o comida específica.
* @returns {object} - Objeto con las macros totales {calories, protein_g, carbohydrates_g, fat_g}.
*/
export const calculateMacrosForItems = (mealItems = []) => {
// Filtrar items que puedan ser null o undefined accidentalmente
const validItems = mealItems ? mealItems.filter(item => item != null) : [];

return validItems.reduce(
  (totals, item) => {
    // Validar que las propiedades existen y son números antes de sumar
    const quantity = Number(item.quantity);
    const factor = !isNaN(quantity) && quantity > 0 ? quantity : 1; // Usar 1 si la cantidad no es válida o es 0

    const calories = Number(item.calories);
    const protein = Number(item.protein_g);
    const carbs = Number(item.carbohydrates_g);
    const fat = Number(item.fat_g);

    if (!isNaN(calories)) totals.calories += calories * factor;
    if (!isNaN(protein)) totals.protein_g += protein * factor;
    if (!isNaN(carbs)) totals.carbohydrates_g += carbs * factor;
    if (!isNaN(fat)) totals.fat_g += fat * factor;

    return totals;
  },
  { calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 }
);
};

/**
* Calcula las macros totales para cada día.
* @param {object} dailyMealsData - Objeto { 'YYYY-MM-DD': [mealItem1, ...], ... }
* @returns {object} - Objeto { 'YYYY-MM-DD': {calories, protein_g, ...}, ... }
*/
export const calculateDailyMacros = (dailyMealsData = {}) => {
const dailyTotals = {};
// Asegurarse de que dailyMealsData es un objeto antes de iterar
if (typeof dailyMealsData !== 'object' || dailyMealsData === null) {
    return dailyTotals;
}
Object.entries(dailyMealsData).forEach(([date, mealItems]) => {
  // Asegurarse de que mealItems es un array
  if (Array.isArray(mealItems)) {
      dailyTotals[date] = calculateMacrosForItems(mealItems);
  } else {
      dailyTotals[date] = { calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 }; // Default si no es un array
  }
});
return dailyTotals;
};

/**
* Calcula las macros totales para todo el plan sumando los totales diarios.
* @param {object} dailyTotalsData - Objeto { 'YYYY-MM-DD': {calories, protein_g, ...}, ... }
* @returns {object} - Objeto con las macros totales {calories, protein_g, carbohydrates_g, fat_g}.
*/
export const calculateTotalMacros = (dailyTotalsData = {}) => {
 // Asegurarse de que dailyTotalsData es un objeto antes de iterar
 if (typeof dailyTotalsData !== 'object' || dailyTotalsData === null) {
    return { calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 };
}
return Object.values(dailyTotalsData).reduce(
  (totals, daily) => {
    // Validar que 'daily' es un objeto y tiene las propiedades esperadas
    if (typeof daily === 'object' && daily !== null) {
        totals.calories += Number(daily.calories) || 0;
        totals.protein_g += Number(daily.protein_g) || 0;
        totals.carbohydrates_g += Number(daily.carbohydrates_g) || 0;
        totals.fat_g += Number(daily.fat_g) || 0;
    }
    return totals;
  },
  { calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 }
);
};

// --- FIN DE FUNCIONES AÑADIDAS ---