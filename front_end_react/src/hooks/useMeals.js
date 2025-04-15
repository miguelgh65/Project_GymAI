import { useState, useEffect, useCallback } from 'react';
import { MealService } from '../services/NutritionService';

// Función auxiliar para normalizar una comida
const normalizeMeal = (meal) => {
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
};

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
      
      // Normalizar los datos antes de establecerlos
      const normalizedMeals = (result.meals || []).map(normalizeMeal);
      
      console.log('Meals loaded and normalized:', normalizedMeals);
      setMeals(normalizedMeals);
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