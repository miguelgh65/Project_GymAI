// src/components/nutrition/meal-plans/MealPlanList.js
import React, { useState, useEffect } from 'react';
import { MealPlanService } from '../../../services/NutritionService';
import {
    Box, Typography, IconButton,
    CircularProgress, Alert, Button, Card, CardContent, Chip,
    Grid, Paper, Divider, Switch, FormControlLabel
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faPlus, faClipboardList, faCalendarWeek } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { getNutritionSummary } from '../../../utils/nutrition-utils';

const MealPlanList = () => {
    const [mealPlans, setMealPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showActive, setShowActive] = useState(true);
    const navigate = useNavigate();

    const fetchMealPlans = async () => {
        setLoading(true);
        setError(null);
        try {
            console.log("Fetching meal plans...");
            const response = await MealPlanService.getAll(showActive ? true : null);
            console.log("Meal plans response:", response);
            
            // Extraer los planes correctamente de la respuesta
            const plans = response?.meal_plans || [];
            
            console.log("Processed meal plans:", plans);
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
    }, [showActive]); // Se ejecuta cuando cambia el filtro de activos

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

    // CORREGIDO: Cambiamos la navegación para ir a la pestaña de creación de plan
    const handleCreateNew = () => {
        // Navegamos al índice 1 que corresponde a "Crear Plan"
        navigate("/nutrition");
        // Necesitamos una forma de indicar al componente padre que seleccione la pestaña 1
        // Una solución sería usar URL params o state, pero como alternativa podemos usar localStorage
        localStorage.setItem('nutrition_tab', '1'); // Esta es una solución temporal
        window.location.reload(); // Recargamos para asegurar que se aplica la selección
    };

    // Función para obtener un resumen de macros para un plan
    const getPlanMacroSummary = (plan) => {
        if (!plan.items || plan.items.length === 0) {
            return null;
        }

        // En un caso real, necesitarías acceder a las comidas completas
        // Este es un placeholder para la demostración
        const mockMacros = {
            calories: Math.round(1800 + Math.random() * 800),
            proteins: Math.round(120 + Math.random() * 80),
            carbohydrates: Math.round(180 + Math.random() * 120),
            fats: Math.round(60 + Math.random() * 40)
        };

        return getNutritionSummary(mockMacros);
    };

    return (
        <Box sx={{ m: 2 }}>
            <Card elevation={3}>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                        <Typography variant="h5" component="h1">
                            <FontAwesomeIcon icon={faClipboardList} style={{ marginRight: '10px' }} />
                            Planes de Comida
                        </Typography>
                        <Box>
                            <FormControlLabel 
                                control={
                                    <Switch 
                                        checked={showActive} 
                                        onChange={() => setShowActive(!showActive)}
                                        color="primary"
                                    />
                                } 
                                label="Solo planes activos" 
                                sx={{ mr: 2 }}
                            />
                            <Button 
                                variant="contained" 
                                color="primary"
                                startIcon={<FontAwesomeIcon icon={faPlus} />}
                                onClick={handleCreateNew}
                            >
                                Nuevo Plan
                            </Button>
                        </Box>
                    </Box>
                    
                    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                    
                    {loading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
                            <CircularProgress />
                        </Box>
                    ) : (
                        <>
                            {mealPlans.length === 0 ? (
                                <Alert severity="info" sx={{ mb: 2 }}>
                                    No se encontraron planes de comida. ¡Crea tu primer plan usando el botón "Nuevo Plan"!
                                </Alert>
                            ) : (
                                <Grid container spacing={3}>
                                    {mealPlans.map((plan) => {
                                        const macroSummary = getPlanMacroSummary(plan);
                                        
                                        return (
                                            <Grid item xs={12} md={6} lg={4} key={plan.id}>
                                                <Paper elevation={2} sx={{ p: 2, height: '100%', position: 'relative' }}>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                        <Typography variant="h6">
                                                            {plan.plan_name || plan.name || `Plan ${plan.id}`}
                                                        </Typography>
                                                        <Chip 
                                                            label={plan.is_active ? "Activo" : "Inactivo"} 
                                                            color={plan.is_active ? "success" : "default"}
                                                            size="small"
                                                        />
                                                    </Box>
                                                    
                                                    <Divider sx={{ mb: 2 }} />
                                                    
                                                    {/* Resumen de días */}
                                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                                        <FontAwesomeIcon icon={faCalendarWeek} style={{ marginRight: '5px' }} />
                                                        {plan.items && plan.items.length > 0 
                                                            ? `${plan.items.length} comidas programadas` 
                                                            : "Sin comidas programadas"}
                                                    </Typography>
                                                    
                                                    {/* Macros si están disponibles */}
                                                    {macroSummary && (
                                                        <Box sx={{ mb: 2 }}>
                                                            <Typography variant="subtitle2" gutterBottom>
                                                                Promedio diario:
                                                            </Typography>
                                                            <Grid container spacing={1}>
                                                                <Grid item xs={12}>
                                                                    <Typography variant="body2" fontWeight="bold">
                                                                        {macroSummary.calories} kcal
                                                                    </Typography>
                                                                </Grid>
                                                                <Grid item xs={4}>
                                                                    <Typography variant="caption">
                                                                        P: {macroSummary.macros.proteins.grams}g
                                                                    </Typography>
                                                                </Grid>
                                                                <Grid item xs={4}>
                                                                    <Typography variant="caption">
                                                                        C: {macroSummary.macros.carbs.grams}g
                                                                    </Typography>
                                                                </Grid>
                                                                <Grid item xs={4}>
                                                                    <Typography variant="caption">
                                                                        G: {macroSummary.macros.fats.grams}g
                                                                    </Typography>
                                                                </Grid>
                                                            </Grid>
                                                        </Box>
                                                    )}
                                                    
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                                                        <Button 
                                                            variant="outlined" 
                                                            size="small"
                                                            onClick={() => {
                                                                // Navegar a la vista de detalles
                                                                navigate(`/nutrition`);
                                                                localStorage.setItem('nutrition_detail_plan_id', plan.id);
                                                                setTimeout(() => window.location.reload(), 100);
                                                            }}
                                                        >
                                                            Ver Detalles
                                                        </Button>
                                                        <Box>
                                                            <IconButton
                                                                size="small"
                                                                color="primary"
                                                                onClick={() => {
                                                                    // Navegar a la edición
                                                                    navigate(`/nutrition`);
                                                                    localStorage.setItem('nutrition_tab', '1');
                                                                    localStorage.setItem('nutrition_edit_plan_id', plan.id);
                                                                    setTimeout(() => window.location.reload(), 100);
                                                                }}
                                                            >
                                                                <FontAwesomeIcon icon={faEdit} />
                                                            </IconButton>
                                                            <IconButton
                                                                size="small"
                                                                color="error"
                                                                onClick={() => handleDelete(plan.id)}
                                                                sx={{ ml: 1 }}
                                                            >
                                                                <FontAwesomeIcon icon={faTrash} />
                                                            </IconButton>
                                                        </Box>
                                                    </Box>
                                                </Paper>
                                            </Grid>
                                        );
                                    })}
                                </Grid>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>
        </Box>
    );
};

export default MealPlanList;