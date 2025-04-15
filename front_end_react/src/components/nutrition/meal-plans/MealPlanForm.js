// src/components/nutrition/meal-plans/MealPlanForm.js
import React, { useState, useEffect } from 'react';
import { MealPlanService, MealService } from '../../../services/NutritionService';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box, Typography, TextField, Button, Checkbox, FormControlLabel,
    CircularProgress, Alert, Grid, Autocomplete, IconButton, List, ListItem, ListItemText
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faMinus, faSave } from '@fortawesome/free-solid-svg-icons';

const MealPlanForm = () => {
    const { planId } = useParams();
    const navigate = useNavigate();
    const isEditing = Boolean(planId);

    const [planName, setPlanName] = useState('');
    const [isActive, setIsActive] = useState(true);
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const [availableMeals, setAvailableMeals] = useState([]);
    const [selectedMeal, setSelectedMeal] = useState(null);
    const [selectedDay, setSelectedDay] = useState('Lunes');
    const [selectedMealType, setSelectedMealType] = useState('Desayuno');

    const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    const mealTypes = ['Desayuno', 'Almuerzo', 'Comida', 'Merienda', 'Cena', 'Otro'];

    useEffect(() => {
        if (isEditing) {
            setLoading(true);
            MealPlanService.getById(planId)
                .then(data => {
                    // Verificar la estructura de los datos y adaptarse a ella
                    setPlanName(data.plan_name || data.name || '');
                    setIsActive(data.is_active);
                    setItems(data.items || []);
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Error fetching meal plan:", err);
                    setError(err.message || 'Error al cargar el plan.');
                    setLoading(false);
                });
        }
    }, [planId, isEditing]);

    useEffect(() => {
        MealService.getAll()
            .then(response => {
                // Asegurarse de acceder a la propiedad correcta
                const meals = response.meals || response || [];
                
                // Transformar los datos si es necesario
                const processedMeals = meals.map(meal => ({
                    id: meal.id,
                    name: meal.meal_name || meal.name || `Comida ${meal.id}`,
                    calories: meal.calories
                }));
                
                setAvailableMeals(processedMeals);
                console.log("Comidas cargadas:", processedMeals);
            })
            .catch(err => {
                console.error("Error fetching available meals:", err);
                setError("Error al cargar el listado de comidas disponibles.");
            });
    }, []);

    const handleAddItem = () => {
        if (!selectedMeal) {
            setError('Por favor, selecciona una comida.');
            return;
        }

        setItems([...items, {
            meal_id: selectedMeal.id,
            meal_name: selectedMeal.name,
            day_of_week: selectedDay,
            meal_type: selectedMealType
        }]);
        setError(null);
    };

    const handleRemoveItem = (indexToRemove) => {
        setItems(items.filter((_, index) => index !== indexToRemove));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        
        if (!planName.trim()) {
            setError("El nombre del plan es obligatorio");
            return;
        }
        
        setLoading(true);
        setError(null);
        setSuccess(null);

        const planData = {
            plan_name: planName,  // Asegurarse de usar el nombre correcto de campo
            is_active: isActive,
            items: items.map(item => ({
                 meal_id: item.meal_id,
                 day_of_week: item.day_of_week,
                 meal_type: item.meal_type
            }))
        };

        try {
            if (isEditing) {
                await MealPlanService.update(planId, planData);
                setSuccess('Plan actualizado con éxito.');
            } else {
                await MealPlanService.create(planData);
                setSuccess('Plan creado con éxito.');
            }
            
            // Opcional: redirigir después de un éxito
            setTimeout(() => navigate('/nutrition/meal-plans'), 1500);
        } catch (err) {
            console.error("Error saving meal plan:", err);
            setError(err.message || 'Error al guardar el plan.');
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
                {isEditing ? 'Editar Plan de Comida' : 'Crear Nuevo Plan de Comida'}
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

            <TextField
                margin="normal"
                required
                fullWidth
                id="planName"
                label="Nombre del Plan"
                name="planName"
                value={planName}
                onChange={(e) => setPlanName(e.target.value)}
                autoFocus={!isEditing}
                error={!planName.trim()}
                helperText={!planName.trim() ? "El nombre es obligatorio" : ""}
            />
             <FormControlLabel
                control={
                    <Checkbox
                        checked={isActive}
                        onChange={(e) => setIsActive(e.target.checked)}
                        name="isActive"
                        color="primary"
                     />
                 }
                label="Plan Activo"
             />

            <Typography variant="subtitle1" sx={{ mt: 3, mb: 1 }}>Añadir Comida al Plan</Typography>
             <Grid container spacing={2} alignItems="center">
                 <Grid item xs={12} sm={4}>
                    <Autocomplete
                        options={availableMeals}
                        getOptionLabel={(option) => option.name || ''}
                        value={selectedMeal}
                        onChange={(event, newValue) => {
                            setSelectedMeal(newValue);
                        }}
                        isOptionEqualToValue={(option, value) => option.id === value?.id}
                        renderInput={(params) => <TextField {...params} label="Seleccionar Comida" />}
                    />
                 </Grid>
                 <Grid item xs={12} sm={3}>
                     <TextField
                        select
                        label="Día de la Semana"
                        value={selectedDay}
                        onChange={(e) => setSelectedDay(e.target.value)}
                        fullWidth
                        SelectProps={{ native: true }}
                     >
                         {daysOfWeek.map(day => <option key={day} value={day}>{day}</option>)}
                    </TextField>
                 </Grid>
                 <Grid item xs={12} sm={3}>
                    <TextField
                        select
                        label="Tipo de Comida"
                        value={selectedMealType}
                        onChange={(e) => setSelectedMealType(e.target.value)}
                        fullWidth
                        SelectProps={{ native: true }}
                     >
                         {mealTypes.map(type => <option key={type} value={type}>{type}</option>)}
                    </TextField>
                 </Grid>
                 <Grid item xs={12} sm={2}>
                     <Button
                        variant="outlined"
                        onClick={handleAddItem}
                        startIcon={<FontAwesomeIcon icon={faPlus} />}
                        fullWidth
                        sx={{ height: '56px' }}
                        disabled={!selectedMeal}
                    >
                        Añadir
                    </Button>
                 </Grid>
             </Grid>

            <Typography variant="subtitle1" sx={{ mt: 3 }}>Comidas en el Plan</Typography>
            <List dense>
                {items.length === 0 ? (
                    <ListItem><ListItemText primary="Aún no hay comidas en este plan." /></ListItem>
                ) : (
                    items.map((item, index) => (
                        <ListItem
                            key={`${item.meal_id}-${item.day_of_week}-${item.meal_type}-${index}`}
                            secondaryAction={
                                <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveItem(index)}>
                                    <FontAwesomeIcon icon={faMinus} />
                                </IconButton>
                            }
                        >
                            <ListItemText
                                primary={item.meal_name || `Comida ID: ${item.meal_id}`}
                                secondary={`${item.day_of_week} - ${item.meal_type}`}
                            />
                        </ListItem>
                    ))
                 )}
             </List>

            <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading || !planName.trim()}
                startIcon={loading ? <CircularProgress size={20} /> : <FontAwesomeIcon icon={faSave} />}
            >
                {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
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

export default MealPlanForm;