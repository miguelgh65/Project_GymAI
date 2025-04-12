import { useState, useEffect, useCallback } from 'react';
import { MealService } from '../services/NutritionService';

export function useMeals(initialSearch = '') {
  const [meals, setMeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState(initialSearch);
  
  const loadMeals = useCallback(async (search = searchTerm) => {
    setLoading(true);
    setError(null);
    try {
      const result = await MealService.getAll(search);
      setMeals(result.meals || []);
    } catch (err) {
      console.error('Error loading meals:', err);
      setError('Error al cargar comidas');
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);
  
  useEffect(() => {
    loadMeals();
  }, [loadMeals]);
  
  const handleSearch = (newSearchTerm) => {
    setSearchTerm(newSearchTerm);
    loadMeals(newSearchTerm);
  };
  
  return {
    meals,
    loading,
    error,
    searchTerm,
    handleSearch,
    refreshMeals: loadMeals
  };
}