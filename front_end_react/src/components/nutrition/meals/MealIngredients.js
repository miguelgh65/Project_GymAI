// src/components/nutrition/meals/MealIngredients.js
// **NOTA:** La lógica para mostrar/editar ingredientes de una comida
// ya está integrada en `MealDetail.js` (mostrar) y `MealForm.js` (editar).
// Este componente separado podría no ser necesario A MENOS que quieras
// una vista MUY específica solo para la lista de ingredientes de una comida,
// fuera del contexto del formulario o el detalle completo.

// Si AÚN ASÍ lo necesitas, sería algo así:

import React, { useState, useEffect } from 'react';
import { MealService } from '../../../services/NutritionService'; // Usa TU servicio
import { List, ListItem, ListItemText, Typography, CircularProgress, Alert } from '@mui/material';

const MealIngredients = ({ mealId }) => { // Recibe el ID de la comida como prop
    const [ingredients, setIngredients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!mealId) return; // No hacer nada si no hay ID

        setLoading(true);
        setError(null);
        // Llama al servicio para obtener solo los ingredientes de esta comida
        // Usa getIngredients si existe, o getById(mealId, true) y extrae la lista
        MealService.getIngredients(mealId) // O MealService.getById(mealId, true).then(d => d.ingredients)
            .then(data => {
                setIngredients(data || []); // Asegura que sea un array
                setLoading(false);
            })
            .catch(err => {
                console.error(`Error fetching ingredients for meal ${mealId}:`, err);
                setError(err.message || 'Error al cargar ingredientes.');
                setLoading(false);
            });

    }, [mealId]); // Recargar si cambia el ID de la comida

    if (loading) return <CircularProgress size={20} />;
    if (error) return <Alert severity="error" size="small">{error}</Alert>;

    return (
        <>
            <Typography variant="subtitle2" gutterBottom>Ingredientes:</Typography>
            <List dense disablePadding>
                {ingredients.length === 0 ? (
                    <ListItem><ListItemText secondary="No asignados." /></ListItem>
                ) : (
                    ingredients.map(ing => (
                        <ListItem key={ing.ingredient_id || ing.id}> {/* Usa la key correcta */}
                            <ListItemText
                                primary={ing.name} // Asume que el servicio devuelve el nombre
                                secondary={`${ing.quantity} ${ing.unit || 'g'}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                                secondaryTypographyProps={{ variant: 'caption' }}
                             />
                        </ListItem>
                    ))
                )}
            </List>
        </>
    );
};

export default MealIngredients;