// src/components/nutrition/meal-plans/MealPlanList.js
import React, { useState, useEffect } from 'react';
import { MealPlanService } from '../../../services/NutritionService';import {
    Box, Typography, List, ListItem, ListItemText, IconButton,
    CircularProgress, Alert, Button
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
            const data = await MealPlanService.getAll();
            setMealPlans(data);
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

    if (loading) {
        return <CircularProgress />;
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    return (
        <Box>
            <Typography variant="h6" gutterBottom>Lista de Planes de Comida</Typography>
            <Button
                variant="contained"
                startIcon={<FontAwesomeIcon icon={faPlus} />}
                component={Link}
                to="/nutrition/meal-plans/new"
                sx={{ mb: 2 }}
            >
                Crear Nuevo Plan
            </Button>
            <List>
                {mealPlans.length === 0 && !loading ? (
                     <ListItem><ListItemText primary="No se encontraron planes de comida." /></ListItem>
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
                            primary={plan.name}
                            secondary={`ID: ${plan.id} - Activo: ${plan.is_active ? 'Sí' : 'No'}`}
                        />
                         <Button component={Link} to={`/nutrition/meal-plans/detail/${plan.id}`} size="small">
                              Ver Detalles
                         </Button>
                    </ListItem>
                    ))
                 )}
            </List>
        </Box>
    );
};

export default MealPlanList;