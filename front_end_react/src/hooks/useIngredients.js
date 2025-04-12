import { useState, useEffect, useCallback } from 'react';
import { IngredientService } from '../services/NutritionService';

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
      setIngredients(result.ingredients || []);
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