// src/components/nutrition/meal-plans/MealPlanDetail.js
import React, { useState, useEffect } from 'react';
import { MealPlanService } from '../../../services/NutritionService';
import { useParams, Link } from 'react-router-dom';
import {
    Box, Typography, CircularProgress, Alert, Paper, List, ListItem, ListItemText, Divider, Button, Grid
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit } from '@fortawesome/free-solid-svg-icons';

// Componente simple para mostrar los items agrupados
const DayMeals = ({ day, items }) => (
    <Box mb={2}>
        <Typography variant="subtitle1" gutterBottom>{day}</Typography>
        <List dense disablePadding>
            {items.length > 0 ? items.map((item, index) => (
                 <ListItem key={`${item.meal_id}-${item.meal_type}-${index}`} sx={{ pl: 2 }}>
                     <ListItemText
                         primary={item.meal_type}
                         secondary={`Comida ID: ${item.meal_id}`}
                     />
                 </ListItem>
            )) : <ListItemText secondary="No hay comidas asignadas." sx={{ pl: 2 }}/>}
        </List>
    </Box>
);

const MealPlanDetail = () => {
    const { planId } = useParams();
    const [plan, setPlan] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        setLoading(true);
        setError(null);
        MealPlanService.getById(planId)
            .then(data => {
                setPlan(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching meal plan details:", err);
                setError(err.message || 'Error al cargar los detalles del plan.');
                setLoading(false);
            });
    }, [planId]);

    if (loading) {
        return <CircularProgress />;
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    if (!plan) {
         return <Alert severity="warning">No se encontró el plan de comida.</Alert>;
    }

    // Agrupar items por día para visualización
    const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    const groupedItems = daysOfWeek.reduce((acc, day) => {
        acc[day] = plan.items?.filter(item => item.day_of_week === day) || [];
        // Opcional: Ordenar por tipo de comida (Desayuno, Comida, Cena...)
        acc[day].sort((a, b) => {
             const order = ['Desayuno', 'Almuerzo', 'Comida', 'Merienda', 'Cena', 'Otro'];
             return order.indexOf(a.meal_type) - order.indexOf(b.meal_type);
        });
        return acc;
    }, {});

    return (
        <Paper elevation={3} sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                 <Typography variant="h5" component="h1">{plan.name}</Typography>
                 <Button
                    variant="outlined"
                    startIcon={<FontAwesomeIcon icon={faEdit} />}
                    component={Link}
                    to={`/nutrition/meal-plans/edit/${plan.id}`}
                 >
                     Editar Plan
                </Button>
             </Box>
             <Typography variant="subtitle1" color={plan.is_active ? 'green' : 'red'} gutterBottom>
                 {plan.is_active ? 'Activo' : 'Inactivo'}
             </Typography>
             <Divider sx={{ my: 2 }}/>

            <Typography variant="h6" gutterBottom>Comidas por Día</Typography>
             <Grid container spacing={2}>
                {daysOfWeek.map(day => (
                    <Grid item xs={12} sm={6} md={4} key={day}>
                        <DayMeals day={day} items={groupedItems[day]} />
                    </Grid>
                ))}
            </Grid>
        </Paper>
    );
};

export default MealPlanDetail;