import { useState, useEffect, useCallback } from 'react';
import { MealPlanService } from '../services/NutritionService';

export function useMealPlans(initialActive = null) {
  const [mealPlans, setMealPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState(initialActive);
  
  const loadMealPlans = useCallback(async (isActive = activeFilter) => {
    setLoading(true);
    setError(null);
    try {
      const result = await MealPlanService.getAll(isActive);
      setMealPlans(result.meal_plans || []);
    } catch (err) {
      console.error('Error loading meal plans:', err);
      setError('Error al cargar planes de comida');
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);
  
  useEffect(() => {
    loadMealPlans();
  }, [loadMealPlans]);
  
  const handleFilterChange = (newActiveFilter) => {
    setActiveFilter(newActiveFilter);
    loadMealPlans(newActiveFilter);
  };
  
  return {
    mealPlans,
    loading,
    error,
    activeFilter,
    handleFilterChange,
    refreshMealPlans: loadMealPlans
  };
}