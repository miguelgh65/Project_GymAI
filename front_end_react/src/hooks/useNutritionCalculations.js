import { useState, useEffect, useCallback, useMemo } from 'react';
// Asume que calculateDailyMacros y calculateTotalMacros existen en nutrition-utils
import { calculateDailyMacros, calculateTotalMacros } from '../utils/nutrition-utils';

/**
 * Hook para calcular y actualizar los totales nutricionales de un plan de comidas.
 * @param {object} dailyMeals - Objeto donde las claves son fechas 'YYYY-MM-DD' y los valores son arrays de mealItems.
 * Ej: { '2024-01-01': [{meal_id: 1, name: 'Chicken Salad', quantity: 1, unit: 'serving', calories: 350, ...macros}, ...], ... }
 * Asume que cada mealItem tiene 'calories', 'protein_g', 'carbohydrates_g', 'fat_g'.
 */
function useNutritionCalculations(dailyMeals) {
  const [dailyTotals, setDailyTotals] = useState({});
  const [planTotal, setPlanTotal] = useState({ calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 });

  // Usamos useMemo para evitar recalcular si dailyMeals no cambia referencialmente
  const safeDailyMeals = useMemo(() => dailyMeals || {}, [dailyMeals]);

  const recalculateTotals = useCallback(() => {
    // Llama a las funciones de utilidad para obtener los totales
    const newDailyTotals = calculateDailyMacros(safeDailyMeals);
    const newPlanTotal = calculateTotalMacros(newDailyTotals);

    setDailyTotals(newDailyTotals);
    setPlanTotal(newPlanTotal);
  }, [safeDailyMeals]); // Recalcula solo si safeDailyMeals cambia

  useEffect(() => {
    recalculateTotals();
  }, [recalculateTotals]); // Ejecuta el cálculo cuando la función memoizada cambia (o al montar)

  return { dailyTotals, planTotal, recalculateTotals };
}

export default useNutritionCalculations;