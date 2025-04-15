import { useState, useEffect, useCallback } from 'react';
import { MealPlanService } from '../services/NutritionService';

// Función auxiliar para normalizar un plan de comida
const normalizePlan = (plan) => {
  if (!plan) return null;
  
  return {
    id: plan.id,
    plan_name: plan.plan_name || plan.name || '',
    name: plan.name || plan.plan_name || '',
    description: plan.description || '',
    is_active: typeof plan.is_active === 'boolean' ? plan.is_active : true,
    start_date: plan.start_date || null,
    end_date: plan.end_date || null,
    items: Array.isArray(plan.items) ? plan.items : []
  };
};

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
      
      // Extraer los planes de comida de la respuesta y normalizarlos
      const plans = result.meal_plans || [];
      const normalizedPlans = plans.map(normalizePlan);
      
      console.log('MealPlans loaded and normalized:', normalizedPlans);
      setMealPlans(normalizedPlans);
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