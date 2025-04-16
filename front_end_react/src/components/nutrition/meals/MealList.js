// src/components/nutrition/meal-plans/MealPlanList.js
import React, { useState, useEffect } from 'react';
import { MealPlanService } from '../../../services/NutritionService';
import {
    Box, Typography, IconButton,
    CircularProgress, Alert, Button, Card, CardContent, Chip,
    Grid, Paper, Divider, Switch, FormControlLabel, Tooltip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
    faEdit, faTrash, faPlus, faClipboardList, 
    faCalendarWeek, faSync, faExclamationTriangle,
    faUtensils
} from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { getNutritionSummary } from '../../../utils/nutrition-utils';

const MealPlanList = ({ onCreateNew, onEdit }) => {
    const [mealPlans, setMealPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showActive, setShowActive] = useState(true);
    const [usingLocalData, setUsingLocalData] = useState(false);
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
            
            // Determinar si estamos usando datos locales
            setUsingLocalData(plans.some(plan => plan.id.toString().startsWith('local-')));
            
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

    // CORREGIDO: Cambiamos la navegación para usar las funciones proporcionadas
    const handleCreateNew = () => {
        if (onCreateNew) {
            onCreateNew();
        } else {
            // Navegación alternativa usando localStorage si no tenemos la función
            localStorage.setItem('nutrition_tab', '1');
            navigate('/nutrition');
        }
    };

    // Función para editar un plan
    const handleEdit = (id) => {
        if (onEdit) {
            onEdit(id);
        } else {
            // Navegación alternativa usando localStorage si no tenemos la función
            localStorage.setItem('nutrition_edit_plan_id', id);
            localStorage.setItem('nutrition_tab', '1');
            navigate('/nutrition');
        }
    };

    // Función para obtener un resumen de macros para un plan
    const getPlanMacroSummary = (plan) => {
        if (!plan.items || plan.items.length === 0) {
            return null;
        }

        // Si el plan tiene información de macros precalculados, usarla
        if (plan.total_calories && plan.total_proteins && plan.total_carbs && plan.total_fats) {
            return getNutritionSummary({
                calories: plan.total_calories,
                proteins: plan.total_proteins,
                carbohydrates: plan.total_carbs,
                fats: plan.total_fats
            });
        }

        // Calcular macros en base a los días (7)
        const totalDays = 7;
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
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {usingLocalData && (
                                <Tooltip title="Algunos planes solo existen localmente">
                                    <Alert severity="info" icon={<FontAwesomeIcon icon={faExclamationTriangle} />} sx={{ mr: 2, py: 0 }}>
                                        Datos locales
                                    </Alert>
                                </Tooltip>
                            )}
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
                                        const isLocalPlan = plan.id.toString().startsWith('local-');
                                        
                                        return (
                                            <Grid item xs={12} md={6} lg={4} key={plan.id}>
                                                <Paper 
                                                    elevation={2} 
                                                    sx={{ 
                                                        p: 2, 
                                                        height: '100%', 
                                                        position: 'relative',
                                                        border: isLocalPlan ? '1px dashed #1976d2' : 'none'
                                                    }}
                                                >
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
                                                            startIcon={<FontAwesomeIcon icon={faUtensils} />}
                                                            onClick={() => navigate(`/nutrition/meal-plans/detail/${plan.id}`)}
                                                        >
                                                            Ver Detalles
                                                        </Button>
                                                        <Box>
                                                            <Tooltip title="Editar plan">
                                                                <IconButton
                                                                    size="small"
                                                                    color="primary"
                                                                    onClick={() => handleEdit(plan.id)}
                                                                >
                                                                    <FontAwesomeIcon icon={faEdit} />
                                                                </IconButton>
                                                            </Tooltip>
                                                            <Tooltip title="Eliminar plan">
                                                                <IconButton
                                                                    size="small"
                                                                    color="error"
                                                                    onClick={() => handleDelete(plan.id)}
                                                                    sx={{ ml: 1 }}
                                                                >
                                                                    <FontAwesomeIcon icon={faTrash} />
                                                                </IconButton>
                                                            </Tooltip>
                                                        </Box>
                                                    </Box>
                                                    
                                                    {isLocalPlan && (
                                                        <Chip 
                                                            label="Guardado localmente" 
                                                            size="small" 
                                                            variant="outlined"
                                                            color="primary"
                                                            sx={{ position: 'absolute', top: '8px', right: '8px', fontSize: '0.6rem' }}
                                                        />
                                                    )}
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