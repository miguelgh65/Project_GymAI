// src/components/nutrition/meals/MealForm.js
import React, { useState, useEffect } from 'react';
import { MealService, IngredientService } from '../../../services/NutritionService';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box, Typography, TextField, Button, CircularProgress, Alert, Grid,
    Autocomplete, IconButton, List, ListItem, ListItemText, InputAdornment
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faMinus, faSave } from '@fortawesome/free-solid-svg-icons';

const MealForm = () => {
    const { mealId } = useParams();
    const navigate = useNavigate();
    const isEditing = Boolean(mealId);

    const [mealName, setMealName] = useState('');
    const [description, setDescription] = useState('');
    const [ingredients, setIngredients] = useState([]); // [{ ingredient_id, name, quantity, unit }]
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    // Estado para selector de ingredientes
    const [availableIngredients, setAvailableIngredients] = useState([]);
    const [selectedIngredient, setSelectedIngredient] = useState(null);
    const [quantity, setQuantity] = useState('');

    // Cargar datos de la comida si estamos editando
    useEffect(() => {
        if (isEditing) {
            setLoading(true);
            MealService.getById(mealId, true) // Pide ingredientes con true
                .then(data => {
                    setMealName(data.name);
                    setDescription(data.description || '');
                    setIngredients(data.ingredients || []);
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Error fetching meal:", err);
                    setError(err.message || 'Error al cargar la comida.');
                    setLoading(false);
                });
        }
    }, [mealId, isEditing]);

    // Cargar ingredientes disponibles
    useEffect(() => {
        IngredientService.getAll()
            .then(data => setAvailableIngredients(data))
            .catch(err => console.error("Error fetching available ingredients:", err));
    }, []);

    const handleAddIngredient = () => {
        if (!selectedIngredient || !quantity || parseFloat(quantity) <= 0) {
            setError('Selecciona un ingrediente e introduce una cantidad válida.');
            return;
        }
        const exists = ingredients.some(ing => ing.ingredient_id === selectedIngredient.id);
        if (exists) {
             setError('Este ingrediente ya está en la comida. Edita la cantidad si es necesario.');
             return;
        }

        setIngredients([...ingredients, {
            ingredient_id: selectedIngredient.id,
            name: selectedIngredient.name,
            quantity: parseFloat(quantity),
            unit: selectedIngredient.unit || 'g'
        }]);
        // Limpiar campos
        setSelectedIngredient(null);
        setQuantity('');
        setError(null);
    };

    const handleRemoveIngredient = (ingredientIdToRemove) => {
        setIngredients(ingredients.filter(ing => ing.ingredient_id !== ingredientIdToRemove));
    };

     const handleQuantityChange = (ingredientId, newQuantity) => {
        const numQuantity = parseFloat(newQuantity);
        if (isNaN(numQuantity) || numQuantity < 0) return;
        setIngredients(ingredients.map(ing =>
            ing.ingredient_id === ingredientId ? { ...ing, quantity: numQuantity } : ing
        ));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (ingredients.length === 0) {
             setError('La comida debe tener al menos un ingrediente.');
             return;
        }
        setLoading(true);
        setError(null);
        setSuccess(null);

        const mealData = {
            name: mealName,
            description: description,
            ingredients: ingredients.map(ing => ({
                ingredient_id: ing.ingredient_id,
                quantity: ing.quantity
            }))
        };

        try {
            let savedMeal;
            if (isEditing) {
                savedMeal = await MealService.update(mealId, mealData);
                setSuccess('Comida actualizada con éxito.');
            } else {
                savedMeal = await MealService.create(mealData);
                setSuccess('Comida creada con éxito.');
            }
        } catch (err) {
            console.error("Error saving meal:", err);
            setError(err.message || 'Error al guardar la comida.');
        } finally {
            setLoading(false);
        }
    };

     if (loading && isEditing) {
        return <CircularProgress />;
    }

    return (
         <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
            <Typography variant="h6" gutterBottom>
                {isEditing ? 'Editar Comida' : 'Crear Nueva Comida'}
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

            <TextField
                margin="normal" required fullWidth id="mealName"
                label="Nombre de la Comida" name="mealName" value={mealName}
                onChange={(e) => setMealName(e.target.value)} autoFocus={!isEditing}
            />
            <TextField
                margin="normal" fullWidth id="description" label="Descripción (Opcional)"
                name="description" value={description} multiline rows={2}
                onChange={(e) => setDescription(e.target.value)}
            />

            <Typography variant="subtitle1" sx={{ mt: 3, mb: 1 }}>Añadir Ingrediente</Typography>
            <Grid container spacing={2} alignItems="center">
                 <Grid item xs={12} sm={6}>
                    <Autocomplete
                        options={availableIngredients}
                        getOptionLabel={(option) => option.name || ''}
                        value={selectedIngredient}
                        onChange={(event, newValue) => setSelectedIngredient(newValue)}
                        isOptionEqualToValue={(option, value) => option.id === value?.id}
                        renderInput={(params) => <TextField {...params} label="Seleccionar Ingrediente" />}
                    />
                 </Grid>
                 <Grid item xs={6} sm={3}>
                     <TextField
                        label="Cantidad" type="number" value={quantity}
                        onChange={(e) => setQuantity(e.target.value)} fullWidth
                        InputProps={{ inputProps: { min: 0, step: "any" },
                         endAdornment: <InputAdornment position="end">{selectedIngredient?.unit || 'g'}</InputAdornment>
                        }}
                     />
                 </Grid>
                 <Grid item xs={6} sm={3}>
                     <Button 
                        variant="outlined" 
                        onClick={handleAddIngredient} 
                        startIcon={<FontAwesomeIcon icon={faPlus} />} 
                        fullWidth 
                        sx={{ height: '56px' }}
                     >
                        Añadir
                     </Button>
                 </Grid>
             </Grid>

            <Typography variant="subtitle1" sx={{ mt: 3 }}>Ingredientes en la Comida</Typography>
             <List dense>
                 {ingredients.length === 0 ? (
                     <ListItem><ListItemText primary="Aún no hay ingredientes en esta comida." /></ListItem>
                 ) : (
                    ingredients.map((ing) => (
                        <ListItem
                            key={ing.ingredient_id}
                            secondaryAction={
                                <IconButton 
                                    edge="end" 
                                    aria-label="delete" 
                                    onClick={() => handleRemoveIngredient(ing.ingredient_id)}
                                >
                                    <FontAwesomeIcon icon={faMinus} />
                                </IconButton>
                            }
                        >
                             <Grid container spacing={1} alignItems="center">
                                <Grid item xs={6} sm={7}>
                                    <ListItemText primary={ing.name} secondary={`ID: ${ing.ingredient_id}`} />
                                </Grid>
                                <Grid item xs={4} sm={3}>
                                     <TextField
                                        size="small" type="number" value={ing.quantity} label="Cantidad"
                                        onChange={(e) => handleQuantityChange(ing.ingredient_id, e.target.value)}
                                        InputProps={{ inputProps: { min: 0, step: "any" },
                                            endAdornment: <InputAdornment position="end">{ing.unit || 'g'}</InputAdornment>
                                        }}
                                     />
                                </Grid>
                             </Grid>
                        </ListItem>
                    ))
                )}
             </List>

            <Button 
                type="submit" 
                fullWidth 
                variant="contained" 
                sx={{ mt: 3, mb: 2 }} 
                disabled={loading} 
                startIcon={loading ? <CircularProgress size={20} /> : <FontAwesomeIcon icon={faSave} />}
            >
                {isEditing ? 'Guardar Cambios' : 'Crear Comida'}
            </Button>
             <Button 
                fullWidth 
                variant="outlined" 
                onClick={() => navigate('/nutrition')} 
                sx={{ mb: 2 }}
             >
                Cancelar
             </Button>
        </Box>
    );
};

export default MealForm;