// src/components/nutrition/meal-plans/MealPlanForm.js
import React, { useState, useEffect } from 'react';
import { MealService, MealPlanService, NutritionCalculator } from '../../../services/NutritionService';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box, Typography, TextField, Button, Checkbox, FormControlLabel,
    CircularProgress, Alert, Grid, Autocomplete, IconButton, List, ListItem, 
    ListItemText, Divider, Card, CardContent, Tabs, Tab, Chip, Paper,
    LinearProgress, Tooltip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
    faPlus, faMinus, faSave, faArrowLeft, faSun, faCoffee, 
    faUtensils, faCookie, faMoon, faEllipsisH, faFire, 
    faDrumstickBite, faAppleAlt, faOilCan
} from '@fortawesome/free-solid-svg-icons';

const MealPlanForm = () => {
    const { planId } = useParams();
    const navigate = useNavigate();
    const isEditing = Boolean(planId);

    // Estado principal del formulario
    const [planName, setPlanName] = useState('');
    const [description, setDescription] = useState('');
    const [isActive, setIsActive] = useState(true);
    const [items, setItems] = useState([]);
    
    // Estado para objetivos nutricionales
    const [targetCalories, setTargetCalories] = useState('');
    const [targetProtein, setTargetProtein] = useState('');
    const [targetCarbs, setTargetCarbs] = useState('');
    const [targetFat, setTargetFat] = useState('');
    const [userNutritionProfile, setUserNutritionProfile] = useState(null);
    
    // Estado de control del formulario
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    // Estado para selector de comidas
    const [availableMeals, setAvailableMeals] = useState([]);
    const [selectedMeal, setSelectedMeal] = useState(null);
    const [quantity, setQuantity] = useState('100');
    const [unit, setUnit] = useState('g');

    // Estado para la navegación de pestañas de días
    const [activeTab, setActiveTab] = useState(0);

    const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    const mealTypes = [
        { value: 'Desayuno', label: 'Desayuno', icon: faCoffee },
        { value: 'Almuerzo', label: 'Almuerzo', icon: faSun },
        { value: 'Comida', label: 'Comida', icon: faUtensils },
        { value: 'Merienda', label: 'Merienda', icon: faCookie },
        { value: 'Cena', label: 'Cena', icon: faMoon },
        { value: 'Otro', label: 'Otro', icon: faEllipsisH }
    ];
    const [selectedMealType, setSelectedMealType] = useState(mealTypes[0].value);

    // Cargar perfil nutricional del usuario
    useEffect(() => {
        const loadNutritionProfile = async () => {
            try {
                const profile = await NutritionCalculator.getProfile();
                if (profile) {
                    console.log("Perfil nutricional cargado:", profile);
                    setUserNutritionProfile(profile);
                    
                    // Si no hay objetivos en el plan, usar los del perfil como valores predeterminados
                    if (!targetCalories && profile.goal_calories) {
                        setTargetCalories(profile.goal_calories.toString());
                    }
                    if (!targetProtein && profile.target_protein_g) {
                        setTargetProtein(profile.target_protein_g.toString());
                    }
                    if (!targetCarbs && profile.target_carbs_g) {
                        setTargetCarbs(profile.target_carbs_g.toString());
                    }
                    if (!targetFat && profile.target_fat_g) {
                        setTargetFat(profile.target_fat_g.toString());
                    }
                }
            } catch (error) {
                console.error("Error al cargar perfil nutricional:", error);
            }
        };
        
        loadNutritionProfile();
    }, [targetCalories, targetProtein, targetCarbs, targetFat]);

    // Cargar datos si estamos editando
    useEffect(() => {
        if (isEditing) {
            setLoading(true);
            MealPlanService.getById(planId)
                .then(data => {
                    console.log("Datos del plan cargados:", data);
                    setPlanName(data.plan_name || data.name || '');
                    setDescription(data.description || '');
                    setIsActive(data.is_active !== undefined ? data.is_active : true);
                    
                    // Cargar objetivos nutricionales
                    if (data.target_calories) setTargetCalories(data.target_calories.toString());
                    if (data.target_protein_g) setTargetProtein(data.target_protein_g.toString());
                    if (data.target_carbs_g) setTargetCarbs(data.target_carbs_g.toString());
                    if (data.target_fat_g) setTargetFat(data.target_fat_g.toString());
                    
                    // Transformar items si existen
                    if (data.items && Array.isArray(data.items)) {
                        setItems(data.items.map(item => ({
                            ...item,
                            day_of_week: item.day_of_week || getDayFromDate(item.plan_date) || 'Lunes',
                            meal_type: item.meal_type?.replace('MealTime.', '') || 'Comida'
                        })));
                    }
                    
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Error fetching meal plan:", err);
                    setError(err.message || 'Error al cargar el plan.');
                    setLoading(false);
                });
        }
    }, [planId, isEditing]);

    // Cargar comidas disponibles
    useEffect(() => {
        MealService.getAll()
            .then(response => {
                const meals = response.meals || [];
                console.log(`Cargadas ${meals.length} comidas disponibles`);
                setAvailableMeals(meals);
            })
            .catch(err => {
                console.error("Error fetching available meals:", err);
                setError("Error al cargar el listado de comidas disponibles.");
            });
    }, []);

    // Función para obtener el día de la semana de una fecha
    const getDayFromDate = (dateString) => {
        if (!dateString) return null;
        
        try {
            const date = new Date(dateString);
            const dayIndex = date.getDay(); // 0 = Domingo, 1 = Lunes, ...
            // Ajustar para que 0 = Lunes, 6 = Domingo
            const adjustedIndex = dayIndex === 0 ? 6 : dayIndex - 1;
            return daysOfWeek[adjustedIndex];
        } catch (error) {
            console.error("Error parsing date:", error);
            return null;
        }
    };

    // Manejador para cambio de pestaña
    const handleTabChange = (event, newValue) => {
        setActiveTab(newValue);
    };

    // Añadir una comida al plan
    const handleAddItem = () => {
        if (!selectedMeal) {
            setError('Por favor, selecciona una comida.');
            return;
        }

        if (!quantity || parseFloat(quantity) <= 0) {
            setError('Por favor, introduce una cantidad válida.');
            return;
        }

        // Calcular factor para los macros
        const factor = parseFloat(quantity) / 100; // Asumiendo que los macros son por 100g/ml

        const newItem = {
            meal_id: selectedMeal.id,
            meal_name: selectedMeal.name || selectedMeal.meal_name,
            day_of_week: daysOfWeek[activeTab],
            meal_type: selectedMealType,
            quantity: parseFloat(quantity),
            unit: unit || 'g',
            // Incluir propiedades nutricionales si existen
            calories: selectedMeal.calories ? Math.round(selectedMeal.calories * factor) : null,
            protein_g: selectedMeal.protein_g || selectedMeal.proteins ? 
                       Math.round((selectedMeal.protein_g || selectedMeal.proteins) * factor * 10) / 10 : null,
            carbohydrates_g: selectedMeal.carbohydrates_g || selectedMeal.carbohydrates ? 
                             Math.round((selectedMeal.carbohydrates_g || selectedMeal.carbohydrates) * factor * 10) / 10 : null,
            fat_g: selectedMeal.fat_g || selectedMeal.fats ? 
                   Math.round((selectedMeal.fat_g || selectedMeal.fats) * factor * 10) / 10 : null
        };

        setItems([...items, newItem]);
        // Limpiar selección después de añadir
        setSelectedMeal(null);
        setQuantity('100');
        setError(null);
    };

    // Eliminar una comida del plan
    const handleRemoveItem = (indexToRemove) => {
        setItems(items.filter((_, index) => index !== indexToRemove));
    };

    // Agrupar items por día y tipo de comida para mostrarlos
    const groupItemsByDay = () => {
        const grouped = {};
        
        // Inicializar estructura para cada día
        daysOfWeek.forEach(day => {
            grouped[day] = {};
            mealTypes.forEach(type => {
                grouped[day][type.value] = [];
            });
        });
        
        // Agrupar items por día y tipo
        items.forEach(item => {
            const day = item.day_of_week || daysOfWeek[0];
            const type = item.meal_type || 'Comida';
            
            if (!grouped[day]) {
                grouped[day] = {};
            }
            
            if (!grouped[day][type]) {
                grouped[day][type] = [];
            }
            
            grouped[day][type].push(item);
        });
        
        return grouped;
    };
    
    // Obtener icono para tipo de comida
    const getMealTypeIcon = (type) => {
        const mealType = mealTypes.find(t => t.value === type);
        return mealType ? mealType.icon : faUtensils;
    };

    // Calcular totales de macros para un día
    const calculateDayTotals = (day) => {
        const dayItems = items.filter(item => item.day_of_week === day);
        
        const totals = {
            calories: 0,
            protein_g: 0,
            carbs_g: 0,
            fat_g: 0
        };
        
        dayItems.forEach(item => {
            if (item.calories) totals.calories += item.calories;
            if (item.protein_g) totals.protein_g += item.protein_g;
            if (item.carbohydrates_g) totals.carbs_g += item.carbohydrates_g;
            if (item.fat_g) totals.fat_g += item.fat_g;
        });
        
        return totals;
    };

    // Calcular totales de macros para un tipo de comida
    const calculateMealTypeTotals = (day, type) => {
        const typeItems = items.filter(item => 
            item.day_of_week === day && item.meal_type === type);
        
        const totals = {
            calories: 0,
            protein_g: 0,
            carbs_g: 0,
            fat_g: 0
        };
        
        typeItems.forEach(item => {
            if (item.calories) totals.calories += item.calories;
            if (item.protein_g) totals.protein_g += item.protein_g;
            if (item.carbohydrates_g) totals.carbs_g += item.carbohydrates_g;
            if (item.fat_g) totals.fat_g += item.fat_g;
        });
        
        return totals;
    };

    // Calcular totales de macros para todo el plan
    const calculatePlanTotals = () => {
        const totals = {
            calories: 0,
            protein_g: 0,
            carbs_g: 0,
            fat_g: 0
        };
        
        items.forEach(item => {
            if (item.calories) totals.calories += item.calories;
            if (item.protein_g) totals.protein_g += item.protein_g;
            if (item.carbohydrates_g) totals.carbs_g += item.carbohydrates_g;
            if (item.fat_g) totals.fat_g += item.fat_g;
        });
        
        return totals;
    };

    // Calcular porcentaje de progreso para los objetivos
    const calculateProgress = (totals) => {
        const progress = {
            calories: 0,
            protein: 0,
            carbs: 0,
            fat: 0
        };
        
        if (targetCalories && totals.calories) {
            progress.calories = Math.min(100, Math.round((totals.calories / parseFloat(targetCalories)) * 100));
        }
        
        if (targetProtein && totals.protein_g) {
            progress.protein = Math.min(100, Math.round((totals.protein_g / parseFloat(targetProtein)) * 100));
        }
        
        if (targetCarbs && totals.carbs_g) {
            progress.carbs = Math.min(100, Math.round((totals.carbs_g / parseFloat(targetCarbs)) * 100));
        }
        
        if (targetFat && totals.fat_g) {
            progress.fat = Math.min(100, Math.round((totals.fat_g / parseFloat(targetFat)) * 100));
        }
        
        return progress;
    };

    // Enviar el formulario
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
            plan_name: planName,
            description: description,
            is_active: isActive,
            target_calories: targetCalories ? parseFloat(targetCalories) : null,
            target_protein_g: targetProtein ? parseFloat(targetProtein) : null,
            target_carbs_g: targetCarbs ? parseFloat(targetCarbs) : null,
            target_fat_g: targetFat ? parseFloat(targetFat) : null,
            items: items.map(item => ({
                 meal_id: item.meal_id,
                 day_of_week: item.day_of_week,
                 meal_type: item.meal_type,
                 quantity: item.quantity,
                 unit: item.unit || 'g'
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
            
            // Redirigir después de un éxito
            setTimeout(() => navigate('/nutrition'), 1500);
        } catch (err) {
            console.error("Error saving meal plan:", err);
            setError(err.message || 'Error al guardar el plan.');
        } finally {
            setLoading(false);
        }
    };

    // Obtener las comidas agrupadas
    const groupedItems = groupItemsByDay();
    const planTotals = calculatePlanTotals();
    const progress = calculateProgress(planTotals);
    const dayTotals = calculateDayTotals(daysOfWeek[activeTab]);
    const dayProgress = calculateProgress(dayTotals);
    
    if (loading && isEditing) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                {isEditing ? 'Editar Plan de Comida' : 'Crear Nuevo Plan de Comida'}
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>Información General</Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                        <TextField
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
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            id="description"
                            label="Descripción (Opcional)"
                            name="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            multiline
                            rows={1}
                        />
                    </Grid>
                    <Grid item xs={12}>
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
                    </Grid>
                </Grid>
            </Paper>

            {/* Objetivos nutricionales */}
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>Objetivos Nutricionales</Typography>
                
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                        <TextField
                            fullWidth
                            label="Calorías objetivo (kcal)"
                            type="number"
                            value={targetCalories}
                            onChange={(e) => setTargetCalories(e.target.value)}
                            InputProps={{ inputProps: { min: 0 } }}
                            helperText={userNutritionProfile?.goal_calories ? 
                                       `Tu perfil: ${userNutritionProfile.goal_calories} kcal` : ''}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <TextField
                            fullWidth
                            label="Proteínas objetivo (g)"
                            type="number"
                            value={targetProtein}
                            onChange={(e) => setTargetProtein(e.target.value)}
                            InputProps={{ inputProps: { min: 0 } }}
                            helperText={userNutritionProfile?.target_protein_g ? 
                                       `Tu perfil: ${userNutritionProfile.target_protein_g}g` : ''}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <TextField
                            fullWidth
                            label="Carbohidratos objetivo (g)"
                            type="number"
                            value={targetCarbs}
                            onChange={(e) => setTargetCarbs(e.target.value)}
                            InputProps={{ inputProps: { min: 0 } }}
                            helperText={userNutritionProfile?.target_carbs_g ? 
                                       `Tu perfil: ${userNutritionProfile.target_carbs_g}g` : ''}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <TextField
                            fullWidth
                            label="Grasas objetivo (g)"
                            type="number"
                            value={targetFat}
                            onChange={(e) => setTargetFat(e.target.value)}
                            InputProps={{ inputProps: { min: 0 } }}
                            helperText={userNutritionProfile?.target_fat_g ? 
                                       `Tu perfil: ${userNutritionProfile.target_fat_g}g` : ''}
                        />
                    </Grid>
                </Grid>
                
                {(targetCalories || targetProtein || targetCarbs || targetFat) && (
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Progreso del Plan Completo:
                        </Typography>
                        
                        <Grid container spacing={2}>
                            {targetCalories && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faFire} /> Calorías
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {planTotals.calories} / {targetCalories} kcal
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={progress.calories} 
                                            color={progress.calories > 100 ? "error" : "primary"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                            
                            {targetProtein && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faDrumstickBite} /> Proteínas
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {planTotals.protein_g} / {targetProtein}g
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={progress.protein} 
                                            color={progress.protein > 100 ? "error" : "success"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                            
                            {targetCarbs && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faAppleAlt} /> Carbohidratos
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {planTotals.carbs_g} / {targetCarbs}g
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={progress.carbs} 
                                            color={progress.carbs > 100 ? "error" : "info"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                            
                            {targetFat && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faOilCan} /> Grasas
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {planTotals.fat_g} / {targetFat}g
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={progress.fat} 
                                            color={progress.fat > 100 ? "error" : "warning"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                        </Grid>
                    </Box>
                )}
            </Paper>

            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>Añadir Comidas al Plan</Typography>
                
                {/* Selector de días */}
                <Tabs
                    value={activeTab}
                    onChange={handleTabChange}
                    variant="scrollable"
                    scrollButtons="auto"
                    sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
                >
                    {daysOfWeek.map((day, index) => (
                        <Tab key={index} label={day} />
                    ))}
                </Tabs>
                
                {/* Macros del día actual */}
                {(targetCalories || targetProtein || targetCarbs || targetFat) && (
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Progreso para {daysOfWeek[activeTab]}:
                        </Typography>
                        
                        <Grid container spacing={2}>
                            {targetCalories && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faFire} /> Calorías
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {dayTotals.calories} / {Math.round(parseInt(targetCalories) / 7)} kcal
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={Math.min(100, (dayTotals.calories / (parseInt(targetCalories) / 7)) * 100)} 
                                            color={dayTotals.calories > (parseInt(targetCalories) / 7) ? "error" : "primary"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                            
                            {targetProtein && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faDrumstickBite} /> Proteínas
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {dayTotals.protein_g} / {Math.round(parseInt(targetProtein) / 7)}g
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={Math.min(100, (dayTotals.protein_g / (parseInt(targetProtein) / 7)) * 100)} 
                                            color={dayTotals.protein_g > (parseInt(targetProtein) / 7) ? "error" : "success"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                            
                            {targetCarbs && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faAppleAlt} /> Carbohidratos
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {dayTotals.carbs_g} / {Math.round(parseInt(targetCarbs) / 7)}g
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={Math.min(100, (dayTotals.carbs_g / (parseInt(targetCarbs) / 7)) * 100)} 
                                            color={dayTotals.carbs_g > (parseInt(targetCarbs) / 7) ? "error" : "info"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                            
                            {targetFat && (
                                <Grid item xs={12} sm={6} md={3}>
                                    <Box sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="caption" display="block">
                                                <FontAwesomeIcon icon={faOilCan} /> Grasas
                                            </Typography>
                                            <Typography variant="caption" display="block">
                                                {dayTotals.fat_g} / {Math.round(parseInt(targetFat) / 7)}g
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={Math.min(100, (dayTotals.fat_g / (parseInt(targetFat) / 7)) * 100)} 
                                            color={dayTotals.fat_g > (parseInt(targetFat) / 7) ? "error" : "warning"}
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                </Grid>
                            )}
                        </Grid>
                        
                        <Divider sx={{ my: 2 }} />
                    </Box>
                )}
                
                {/* Formulario para añadir comida */}
                <Grid container spacing={2} alignItems="center" sx={{ mb: 3 }}>
                    <Grid item xs={12} md={4}>
                        <Autocomplete
                            options={availableMeals}
                            getOptionLabel={(option) => option?.name || option?.meal_name || ''}
                            value={selectedMeal}
                            onChange={(event, newValue) => setSelectedMeal(newValue)}
                            isOptionEqualToValue={(option, value) => option?.id === value?.id}
                            renderInput={(params) => (
                                <TextField {...params} label="Seleccionar Comida" required fullWidth />
                            )}
                            renderOption={(props, option) => (
                                <li {...props}>
                                    <Box>
                                        <Typography variant="body2">
                                            {option.name || option.meal_name}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            {option.calories || '?'} kcal | P: {option.protein_g || option.proteins || '?'}g | 
                                            C: {option.carbohydrates_g || option.carbohydrates || '?'}g | 
                                            G: {option.fat_g || option.fats || '?'}g
                                        </Typography>
                                    </Box>
                                </li>
                            )}
                        />
                    </Grid>
                    <Grid item xs={6} md={2}>
                        <TextField
                            select
                            label="Tipo de Comida"
                            value={selectedMealType}
                            onChange={(e) => setSelectedMealType(e.target.value)}
                            fullWidth
                            SelectProps={{ native: true }}
                        >
                            {mealTypes.map(type => (
                                <option key={type.value} value={type.value}>
                                    {type.label}
                                </option>
                            ))}
                        </TextField>
                    </Grid>
                    <Grid item xs={3} md={2}>
                        <TextField
                            label="Cantidad"
                            type="number"
                            value={quantity}
                            onChange={(e) => setQuantity(e.target.value)}
                            fullWidth
                            inputProps={{ min: 0, step: "any" }}
                        />
                    </Grid>
                    <Grid item xs={3} md={2}>
                        <TextField
                            label="Unidad"
                            value={unit}
                            onChange={(e) => setUnit(e.target.value)}
                            fullWidth
                            placeholder="g"
                        />
                    </Grid>
                    <Grid item xs={12} md={2}>
                        <Button
                            variant="contained"
                            onClick={handleAddItem}
                            startIcon={<FontAwesomeIcon icon={faPlus} />}
                            fullWidth
                            disabled={!selectedMeal}
                            sx={{ height: '56px' }}
                        >
                            Añadir
                        </Button>
                    </Grid>
                </Grid>
                
                {/* Muestra las comidas del día seleccionado */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                        Comidas para {daysOfWeek[activeTab]}:
                    </Typography>
                    
                    {mealTypes.map((type) => {
                        const dayItems = groupedItems[daysOfWeek[activeTab]][type.value] || [];
                        const typeTotals = calculateMealTypeTotals(daysOfWeek[activeTab], type.value);
                        
                        return (
                            <Card 
                                key={type.value} 
                                variant="outlined" 
                                sx={{ mb: 2, borderColor: dayItems.length ? 'primary.main' : 'grey.300' }}
                            >
                                <CardContent sx={{ py: 1 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center' }}>
                                            <FontAwesomeIcon icon={type.icon} style={{ marginRight: '8px' }} />
                                            {type.label}
                                        </Typography>
                                        
                                        {dayItems.length > 0 && (
                                            <Typography variant="caption" color="text.secondary">
                                                <Tooltip title="Calorías | Proteínas | Carbohidratos | Grasas">
                                                    <span>
                                                        <FontAwesomeIcon icon={faFire} /> {typeTotals.calories} kcal | 
                                                        P: {typeTotals.protein_g}g | 
                                                        C: {typeTotals.carbs_g}g | 
                                                        G: {typeTotals.fat_g}g
                                                    </span>
                                                </Tooltip>
                                            </Typography>
                                        )}
                                    </Box>
                                    
                                    {dayItems.length === 0 ? (
                                        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mt: 1 }}>
                                            No hay comidas asignadas
                                        </Typography>
                                    ) : (
                                        <List dense>
                                            {dayItems.map((item, idx) => {
                                                const itemIndex = items.findIndex(i => 
                                                    i.meal_id === item.meal_id && 
                                                    i.day_of_week === item.day_of_week && 
                                                    i.meal_type === item.meal_type
                                                );
                                                
                                                return (
                                                    <ListItem 
                                                        key={idx}
                                                        secondaryAction={
                                                            <IconButton 
                                                                edge="end" 
                                                                aria-label="delete" 
                                                                onClick={() => handleRemoveItem(itemIndex)}
                                                                size="small"
                                                                color="error"
                                                            >
                                                                <FontAwesomeIcon icon={faMinus} />
                                                            </IconButton>
                                                        }
                                                    >
                                                        <ListItemText
                                                            primary={
                                                                <Typography variant="body2" noWrap>
                                                                    {item.meal_name || `Comida ID: ${item.meal_id}`}
                                                                </Typography>
                                                            }
                                                            secondary={
                                                                <Typography variant="caption" color="text.secondary">
                                                                    {item.quantity} {item.unit || 'g'} | 
                                                                    {item.calories ? ` ${item.calories} kcal |` : ''} 
                                                                    {item.protein_g ? ` P: ${item.protein_g}g |` : ''} 
                                                                    {item.carbohydrates_g ? ` C: ${item.carbohydrates_g}g |` : ''} 
                                                                    {item.fat_g ? ` G: ${item.fat_g}g` : ''}
                                                                </Typography>
                                                            }
                                                        />
                                                    </ListItem>
                                                );
                                            })}
                                        </List>
                                    )}
                                </CardContent>
                            </Card>
                        );
                    })}
                </Box>
                
                {/* Resumen general */}
                <Divider sx={{ my: 3 }} />
                
                <Typography variant="subtitle1" gutterBottom>
                    Resumen del Plan:
                </Typography>
                
                <Grid container spacing={2} sx={{ mb: 2 }}>
                    {daysOfWeek.map((day) => {
                        const dayItemsCount = Object.values(groupedItems[day] || {})
                            .flat()
                            .length;
                        
                        const dayTotals = calculateDayTotals(day);
                            
                        return (
                            <Grid item key={day} xs={6} sm={4} md={3} lg={12/7}>
                                <Paper 
                                    elevation={0} 
                                    variant="outlined"
                                    sx={{ 
                                        p: 1.5, 
                                        textAlign: 'center',
                                        borderColor: dayItemsCount ? 'primary.main' : 'grey.300',
                                        borderWidth: dayItemsCount ? 2 : 1
                                    }}
                                >
                                    <Typography variant="subtitle2">{day}</Typography>
                                    <Chip 
                                        label={`${dayItemsCount} comidas`} 
                                        color={dayItemsCount ? "primary" : "default"}
                                        size="small"
                                        sx={{ mt: 1, mb: 1 }}
                                    />
                                    {dayItemsCount > 0 && (
                                        <Typography variant="caption" display="block" color="text.secondary">
                                            {dayTotals.calories} kcal | P: {dayTotals.protein_g}g | 
                                            C: {dayTotals.carbs_g}g | G: {dayTotals.fat_g}g
                                        </Typography>
                                    )}
                                </Paper>
                            </Grid>
                        );
                    })}
                </Grid>
            </Paper>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                <Button
                    variant="outlined"
                    startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
                    onClick={() => navigate('/nutrition')}
                >
                    Cancelar
                </Button>
                
                <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    onClick={handleSubmit}
                    disabled={loading || !planName.trim()}
                    startIcon={loading ? <CircularProgress size={20} /> : <FontAwesomeIcon icon={faSave} />}
                >
                    {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
                </Button>
            </Box>
        </Box>
    );
};

export default MealPlanForm;