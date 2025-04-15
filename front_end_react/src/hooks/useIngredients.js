import { useState, useEffect, useCallback } from 'react';
import { IngredientService } from '../services/NutritionService';

// Función auxiliar para normalizar un ingrediente
const normalizeIngredient = (ingredient) => {
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
};

export function useIngredients(initialSearch = '') {
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState(initialSearch);
  
  const loadIngredients = useCallback(async (search = searchTerm) => {
    setLoading(true);
    setError(null);
    try {
      const result = await IngredientService.getAll(search);
      
      // Normalizar los ingredientes antes de guardarlos en el estado
      const normalizedIngredients = (result.ingredients || []).map(normalizeIngredient);
      
      console.log('Ingredients loaded and normalized:', normalizedIngredients);
      setIngredients(normalizedIngredients);
    } catch (err) {
      console.error('Error loading ingredients:', err);
      setError('Error al cargar ingredientes');
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);
  
  useEffect(() => {
    loadIngredients();
  }, [loadIngredients]);
  
  const handleSearch = (newSearchTerm) => {
    setSearchTerm(newSearchTerm);
    loadIngredients(newSearchTerm);
  };
  
  return {
    ingredients,
    loading,
    error,
    searchTerm,
    handleSearch,
    refreshIngredients: loadIngredients
  };
}