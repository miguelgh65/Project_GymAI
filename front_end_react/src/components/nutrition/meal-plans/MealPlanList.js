// src/components/nutrition/meal-plans/MealPlanList.js
import React, { useState, useEffect } from 'react';
import { MealPlanService } from '../../../services/NutritionService';
import {
    Box, Typography, List, ListItem, ListItemText, IconButton,
    CircularProgress, Alert, Button, Card, CardContent
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faPlus } from '@fortawesome/free-solid-svg-icons';
import { Link } from 'react-router-dom';

const MealPlanList = () => {
    const [mealPlans, setMealPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchMealPlans = async () => {
        setLoading(true);
        setError(null);
        try {
            // Modificamos para capturar y procesar la respuesta correctamente
            const response = await MealPlanService.getAll();
            // Asegurarnos de que estamos accediendo a la estructura correcta de datos
            const plans = response?.meal_plans || [];
            
            console.log("Respuesta de planes:", response); // Ayuda para debugging
            setMealPlans(plans);
            
            if (plans.length === 0) {
                console.log("No se encontraron planes de comida");
            }
        } catch (err) {
            console.error("Error fetching meal plans:", err);
            setError(err.message || 'Error al cargar los planes de comida.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMealPlans();
    }, []); // Se ejecuta al montar el componente

    const handleDelete = async (id) => {
        if (window.confirm('¿Estás seguro de que quieres eliminar este plan de comida?')) {
            try {
                await MealPlanService.delete(id);
                fetchMealPlans();
            } catch (err) {
                console.error("Error deleting meal plan:", err);
                setError(err.message || 'Error al eliminar el plan.');
            }
        }
    };

    return (
        <Box sx={{ m: 2 }}>
            <Card elevation={3}>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                        <Typography variant="h5" component="h1">
                            Planes de Comida
                        </Typography>
                        <Button 
                            variant="contained" 
                            color="primary"
                            startIcon={<FontAwesomeIcon icon={faPlus} />}
                            component={Link}
                            to="/nutrition/meal-plans/new"
                        >
                            Nuevo Plan
                        </Button>
                    </Box>
                    
                    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                    
                    {loading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
                            <CircularProgress />
                        </Box>
                    ) : (
                        <List>
                            {mealPlans.length === 0 ? (
                                <Alert severity="info" sx={{ mb: 2 }}>
                                    No se encontraron planes de comida. ¡Crea tu primer plan usando el botón "Nuevo Plan"!
                                </Alert>
                            ) : (
                                mealPlans.map((plan) => (
                                    <ListItem
                                        key={plan.id}
                                        secondaryAction={
                                            <>
                                                <IconButton
                                                    edge="end"
                                                    aria-label="edit"
                                                    component={Link}
                                                    to={`/nutrition/meal-plans/edit/${plan.id}`}
                                                >
                                                    <FontAwesomeIcon icon={faEdit} />
                                                </IconButton>
                                                <IconButton
                                                    edge="end"
                                                    aria-label="delete"
                                                    onClick={() => handleDelete(plan.id)}
                                                    sx={{ ml: 1 }}
                                                >
                                                    <FontAwesomeIcon icon={faTrash} />
                                                </IconButton>
                                            </>
                                        }
                                        divider
                                    >
                                        <ListItemText
                                            primary={plan.plan_name || plan.name || `Plan ${plan.id}`}
                                            secondary={`ID: ${plan.id} - Activo: ${plan.is_active ? 'Sí' : 'No'}`}
                                        />
                                        <Button component={Link} to={`/nutrition/meal-plans/detail/${plan.id}`} size="small">
                                            Ver Detalles
                                        </Button>
                                    </ListItem>
                                ))
                            )}
                        </List>
                    )}
                </CardContent>
            </Card>
        </Box>
    );
};

export default MealPlanList;