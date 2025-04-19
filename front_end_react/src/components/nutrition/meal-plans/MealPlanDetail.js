// src/components/nutrition/meal-plans/MealPlanDetail.js
import React, { useState, useEffect } from 'react';
import { MealPlanService } from '../../../services/NutritionService';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
    Box, Typography, CircularProgress, Alert, Paper, List, ListItem, ListItemText, 
    Divider, Button, Grid, Chip, Card, CardContent
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faArrowLeft, faUtensils, faCalendarWeek } from '@fortawesome/free-solid-svg-icons';

// Componente mejorado para mostrar los items agrupados por día
const DayMeals = ({ day, items }) => (
    <Card variant="outlined" sx={{ mb: 2, height: '100%' }}>
        <CardContent>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>{day}</Typography>
            
            {items.length > 0 ? (
                <List dense disablePadding>
                    {items.map((item, index) => (
                        <ListItem key={`${item.meal_id}-${item.meal_type}-${index}`} sx={{ pl: 1 }}>
                            <ListItemText
                                primary={item.meal_name || `Comida ID: ${item.meal_id}`}
                                secondary={
                                    <Box>
                                        <Typography variant="caption" component="span" color="text.secondary">
                                            {item.meal_type?.replace('MealTime.', '')} • {item.quantity} {item.unit}
                                        </Typography>
                                        {item.calories && (
                                            <Typography variant="caption" component="span" sx={{ ml: 1 }}>
                                                • {item.calories} kcal
                                            </Typography>
                                        )}
                                    </Box>
                                }
                            />
                        </ListItem>
                    ))}
                </List>
            ) : (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', pl: 1 }}>
                    No hay comidas asignadas.
                </Typography>
            )}
        </CardContent>
    </Card>
);

const MealPlanDetail = () => {
    const { planId } = useParams();
    const navigate = useNavigate();
    const [plan, setPlan] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadPlan = async () => {
            setLoading(true);
            setError(null);
            try {
                console.log(`Cargando detalles del plan ${planId}...`);
                const data = await MealPlanService.getById(planId);
                console.log("Datos del plan recibidos:", data);
                setPlan(data);
            } catch (err) {
                console.error("Error fetching meal plan details:", err);
                setError(err.message || 'Error al cargar los detalles del plan.');
            } finally {
                setLoading(false);
            }
        };
        
        loadPlan();
    }, [planId]);

    const handleGoBack = () => {
        navigate('/nutrition');
        localStorage.setItem('nutrition_tab', '0'); // Volver a la pestaña de planes
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ m: 2 }}>
                <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
                <Button
                    variant="outlined"
                    startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
                    onClick={handleGoBack}
                >
                    Volver a Planes
                </Button>
            </Box>
        );
    }

    if (!plan) {
        return (
            <Box sx={{ m: 2 }}>
                <Alert severity="warning" sx={{ mb: 2 }}>No se encontró el plan de comida.</Alert>
                <Button
                    variant="outlined"
                    startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
                    onClick={handleGoBack}
                >
                    Volver a Planes
                </Button>
            </Box>
        );
    }

    // Mostrar los días de la semana en español
    const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    
    // Agrupar items por día - comprobamos si tenemos day_of_week o plan_date
    let groupedItems = {};
    
    // Primero verificamos si hay items
    const hasItems = plan.items && Array.isArray(plan.items) && plan.items.length > 0;
    
    if (hasItems) {
        // Inicializar objeto con días vacíos
        daysOfWeek.forEach(day => {
            groupedItems[day] = [];
        });
        
        // Procesar los items para agruparlos por día
        plan.items.forEach(item => {
            // Determinar el día correcto para este item
            let dayKey = null;
            
            // Caso 1: Si tiene day_of_week y es uno de nuestros días en español
            if (item.day_of_week && daysOfWeek.includes(item.day_of_week)) {
                dayKey = item.day_of_week;
            } 
            // Caso 2: Si tiene plan_date, intentar extraer el día de la semana
            else if (item.plan_date) {
                // Convertir fecha ISO a objeto Date
                try {
                    const itemDate = new Date(item.plan_date);
                    // Obtener día de semana (0 = domingo, 1 = lunes, ..., 6 = sábado)
                    let dayIndex = itemDate.getDay();
                    // Ajustar para que lunes sea 0, domingo sea 6
                    dayIndex = dayIndex === 0 ? 6 : dayIndex - 1;
                    dayKey = daysOfWeek[dayIndex];
                } catch (e) {
                    console.warn(`Error al procesar fecha ${item.plan_date}:`, e);
                }
            }
            
            // Si no pudimos determinar el día, usar el primero (Lunes)
            if (!dayKey) {
                dayKey = daysOfWeek[0];
            }
            
            // Agregar el item al día correspondiente
            groupedItems[dayKey].push(item);
        });
        
        // Ordenar items por tipo de comida dentro de cada día
        Object.keys(groupedItems).forEach(day => {
            const mealTypeOrder = ["Desayuno", "Almuerzo", "Comida", "Merienda", "Cena", "Otro"];
            groupedItems[day].sort((a, b) => {
                const typeA = a.meal_type?.replace('MealTime.', '') || '';
                const typeB = b.meal_type?.replace('MealTime.', '') || '';
                return mealTypeOrder.indexOf(typeA) - mealTypeOrder.indexOf(typeB);
            });
        });
    }

    return (
        <Paper elevation={3} sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Box>
                    <Typography variant="h5" component="h1">{plan.plan_name}</Typography>
                    <Chip 
                        label={plan.is_active ? "Plan Activo" : "Plan Inactivo"} 
                        color={plan.is_active ? "success" : "default"} 
                        size="small"
                        sx={{ mt: 1 }}
                    />
                </Box>
                <Box>
                    <Button
                        variant="outlined"
                        startIcon={<FontAwesomeIcon icon={faEdit} />}
                        onClick={() => {
                            navigate('/nutrition');
                            localStorage.setItem('nutrition_edit_plan_id', planId);
                            localStorage.setItem('nutrition_tab', '1'); // Tab de edición
                        }}
                        sx={{ mr: 1 }}
                    >
                        Editar Plan
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
                        onClick={handleGoBack}
                    >
                        Volver
                    </Button>
                </Box>
            </Box>
            
            {plan.description && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {plan.description}
                </Typography>
            )}
            
            <Divider sx={{ my: 2 }}/>

            {/* Mostrar información nutricional si está disponible */}
            {(plan.target_calories || plan.target_protein_g || plan.target_carbs_g || plan.target_fat_g) && (
                <Box mb={3}>
                    <Typography variant="h6" gutterBottom>
                        <FontAwesomeIcon icon={faUtensils} style={{ marginRight: '8px' }} />
                        Objetivos Nutricionales
                    </Typography>
                    <Grid container spacing={2}>
                        {plan.target_calories && (
                            <Grid item xs={6} sm={3}>
                                <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Calorías</Typography>
                                    <Typography variant="h6">{plan.target_calories}</Typography>
                                </Card>
                            </Grid>
                        )}
                        {plan.target_protein_g && (
                            <Grid item xs={6} sm={3}>
                                <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Proteínas</Typography>
                                    <Typography variant="h6">{plan.target_protein_g}g</Typography>
                                </Card>
                            </Grid>
                        )}
                        {plan.target_carbs_g && (
                            <Grid item xs={6} sm={3}>
                                <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Carbohidratos</Typography>
                                    <Typography variant="h6">{plan.target_carbs_g}g</Typography>
                                </Card>
                            </Grid>
                        )}
                        {plan.target_fat_g && (
                            <Grid item xs={6} sm={3}>
                                <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Grasas</Typography>
                                    <Typography variant="h6">{plan.target_fat_g}g</Typography>
                                </Card>
                            </Grid>
                        )}
                    </Grid>
                </Box>
            )}

            <Typography variant="h6" gutterBottom>
                <FontAwesomeIcon icon={faCalendarWeek} style={{ marginRight: '8px' }} />
                Comidas por Día
            </Typography>
            
            {!hasItems ? (
                <Alert severity="info" sx={{ mb: 2 }}>
                    Este plan no tiene comidas asignadas todavía. Edita el plan para añadir comidas.
                </Alert>
            ) : (
                <Grid container spacing={2}>
                    {daysOfWeek.map(day => (
                        <Grid item xs={12} sm={6} md={4} key={day}>
                            <DayMeals day={day} items={groupedItems[day] || []} />
                        </Grid>
                    ))}
                </Grid>
            )}
        </Paper>
    );
};

export default MealPlanDetail;