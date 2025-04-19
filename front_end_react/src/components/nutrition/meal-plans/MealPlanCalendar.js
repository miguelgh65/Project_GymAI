// src/components/nutrition/meal-plans/MealPlanCalendar.js
import React, { useState, useEffect } from 'react';
import { MealPlanService } from '../../../services/NutritionService';
import { 
    Box, Typography, CircularProgress, Alert, Grid, Paper, 
    List, ListItem, ListItemText, IconButton, Button, Tooltip,
    Divider, Chip, Card, CardContent
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
    faChevronLeft, faChevronRight, faCoffee, faSun, 
    faUtensils, faCookie, faMoon, faEllipsisH, faCalendarDay,
    faFire, faDrumstickBite, faAppleAlt, faOilCan, faSyncAlt
} from '@fortawesome/free-solid-svg-icons';
import { 
    format, startOfWeek, endOfWeek, addDays, subDays, 
    isSameDay, eachDayOfInterval, parseISO, isValid 
} from 'date-fns';
import { es } from 'date-fns/locale';

const MealPlanCalendar = () => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [weekPlans, setWeekPlans] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activePlans, setActivePlans] = useState([]);

    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 }); // Lunes
    const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 });
    const daysInWeek = eachDayOfInterval({ start: weekStart, end: weekEnd });

    // Iconos para tipos de comida
    const mealTypeIcons = {
        'Desayuno': faCoffee,
        'Almuerzo': faSun,
        'Comida': faUtensils,
        'Merienda': faCookie,
        'Cena': faMoon,
        'Otro': faEllipsisH
    };

    // Cargar planes activos
    const fetchActivePlans = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await MealPlanService.getAll(true);
            
            console.log("Planes activos recibidos:", response);
            
            const plans = response.meal_plans || [];
            
            // Cargar planes completos con sus items
            const plansWithItems = await Promise.all(
                plans.map(async plan => {
                    try {
                        const fullPlan = await MealPlanService.getById(plan.id);
                        console.log(`Plan ${plan.id} cargado con sus items:`, fullPlan);
                        return fullPlan;
                    } catch (err) {
                        console.error(`Error al cargar el plan ${plan.id}:`, err);
                        return plan; // Devolver el plan sin items en caso de error
                    }
                })
            );
            
            setActivePlans(plansWithItems);
        } catch (err) {
            console.error("Error fetching active meal plans:", err);
            setError(err.message || 'Error al cargar los planes activos.');
        } finally {
            setLoading(false);
        }
    };

    // Cargar planes al inicio y cuando cambie la semana
    useEffect(() => {
        fetchActivePlans();
    }, []);

    // Process week data when active plans change or week changes
    useEffect(() => {
        if (activePlans.length === 0) return;

        const startDateStr = format(weekStart, 'yyyy-MM-dd');
        const endDateStr = format(weekEnd, 'yyyy-MM-dd');
        console.log(`Procesando planes de comida para la semana: ${startDateStr} a ${endDateStr}`);

        // Process the plans to organize by days
        const grouped = {};
        
        // Initialize empty arrays for each day
        daysInWeek.forEach(day => {
            const dateKey = format(day, 'yyyy-MM-dd');
            grouped[dateKey] = [];
        });
        
        // Función para obtener el día de la semana desde plan_date o day_of_week
        const getDayOfWeek = (item) => {
            // Si tiene day_of_week, lo usamos directamente
            if (item.day_of_week) {
                const dayMap = {
                    'Lunes': 0,
                    'Martes': 1,
                    'Miércoles': 2,
                    'Jueves': 3, 
                    'Viernes': 4,
                    'Sábado': 5,
                    'Domingo': 6
                };
                return dayMap[item.day_of_week] !== undefined ? dayMap[item.day_of_week] : null;
            }
            
            // Si tiene plan_date, obtenemos el día de la semana
            if (item.plan_date && isValid(parseISO(item.plan_date))) {
                const date = parseISO(item.plan_date);
                // getDay() devuelve 0 para domingo, 1 para lunes, etc.
                // Ajustamos para que 0 sea lunes y 6 sea domingo
                const day = date.getDay();
                return day === 0 ? 6 : day - 1;
            }
            
            return null;
        };
        
        // Determinar el tipo de comida desde meal_type
        const getMealType = (meal_type) => {
            if (!meal_type) return 'Comida';
            
            // Si viene como "MealTime.X", extraer solo la X
            if (meal_type.includes('.')) {
                return meal_type.split('.')[1];
            }
            
            return meal_type;
        };
        
        // Procesar cada plan activo
        activePlans.forEach(plan => {
            console.log(`Procesando plan ${plan.id || plan.plan_name}:`, plan);
            
            // Verificar si el plan tiene items
            if (!plan.items || !Array.isArray(plan.items)) {
                console.warn(`Plan ${plan.id || plan.plan_name} no tiene items o no es un array`);
                return;
            }
            
            console.log(`Plan tiene ${plan.items.length} items`);
            
            // Procesar cada item del plan
            plan.items.forEach(item => {
                console.log(`Procesando item:`, item);
                
                const dayIndex = getDayOfWeek(item);
                console.log(`Item día calculado: ${dayIndex}`);
                
                if (dayIndex !== null && dayIndex >= 0 && dayIndex < 7) {
                    const dateKey = format(daysInWeek[dayIndex], 'yyyy-MM-dd');
                    console.log(`Item asignado a fecha: ${dateKey}`);
                    
                    if (!grouped[dateKey]) {
                        grouped[dateKey] = [];
                    }
                    
                    // Procesar el tipo de comida
                    const cleanedMealType = getMealType(item.meal_type);
                    
                    // Añadir info del plan
                    grouped[dateKey].push({
                        ...item,
                        plan_name: plan.plan_name || plan.name,
                        meal_name: item.meal_name || `Comida ${item.meal_id}`,
                        meal_type: cleanedMealType,
                        // Añadir macros si existen
                        calories: item.calories,
                        protein_g: item.protein_g,
                        carbohydrates_g: item.carbohydrates_g,
                        fat_g: item.fat_g
                    });
                }
            });
        });
        
        // Ordenar items por tipo de comida
        Object.keys(grouped).forEach(date => {
            const mealTypeOrder = ['Desayuno', 'Almuerzo', 'Comida', 'Merienda', 'Cena', 'Otro'];
            grouped[date].sort((a, b) => {
                const typeA = a.meal_type || '';
                const typeB = b.meal_type || '';
                return mealTypeOrder.indexOf(typeA) - mealTypeOrder.indexOf(typeB);
            });
        });
        
        console.log("Resultado final organizado por días:", grouped);
        setWeekPlans(grouped);
    }, [activePlans, weekStart, weekEnd, daysInWeek]);

    const handlePrevWeek = () => {
        setCurrentDate(subDays(currentDate, 7));
    };

    const handleNextWeek = () => {
        setCurrentDate(addDays(currentDate, 7));
    };

    const handleToday = () => {
        setCurrentDate(new Date());
    };

    // Función para obtener el icono del tipo de comida
    const getMealTypeIcon = (type) => {
        const cleanType = type?.replace('MealTime.', '') || 'Otro';
        return mealTypeIcons[cleanType] || faUtensils;
    };

    // Función para agrupar comidas por tipo
    const groupMealsByType = (meals) => {
        const grouped = {};
        
        meals.forEach(meal => {
            const type = meal.meal_type || 'Otro';
            if (!grouped[type]) {
                grouped[type] = [];
            }
            grouped[type].push(meal);
        });
        
        return grouped;
    };

    return (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <IconButton onClick={handlePrevWeek} aria-label="Semana anterior">
                    <FontAwesomeIcon icon={faChevronLeft} />
                </IconButton>
                
                <Box textAlign="center">
                    <Typography variant="h6">
                        Semana del {format(weekStart, 'd LLLL', { locale: es })} - {format(weekEnd, 'd LLLL yyyy', { locale: es })}
                    </Typography>
                    <Button onClick={handleToday} size="small">Hoy</Button>
                </Box>

                <IconButton onClick={handleNextWeek} aria-label="Semana siguiente">
                    <FontAwesomeIcon icon={faChevronRight} />
                </IconButton>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                <Button 
                    startIcon={<FontAwesomeIcon icon={faSyncAlt} />}
                    onClick={fetchActivePlans}
                    size="small"
                    variant="outlined"
                >
                    Actualizar Planes
                </Button>
            </Box>

            {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
                    <CircularProgress />
                </Box>
            )}
            
            {error && <Alert severity="error">{error}</Alert>}

            {!loading && activePlans.length === 0 && (
                <Alert severity="info">
                    No hay planes de comida activos. Activa un plan o crea uno nuevo.
                </Alert>
            )}

            <Grid container spacing={1}>
                {daysInWeek.map(day => {
                    const dateKey = format(day, 'yyyy-MM-dd');
                    const dayItems = weekPlans[dateKey] || [];
                    const isToday = isSameDay(day, new Date());
                    const mealsByType = groupMealsByType(dayItems);

                    return (
                        <Grid item xs={12} sm={6} md={4} lg={12/7} key={dateKey}>
                            <Paper 
                                elevation={isToday ? 4 : 1} 
                                sx={{ 
                                    p: 2, 
                                    height: '100%', 
                                    border: isToday ? '2px solid' : 'none', 
                                    borderColor: 'primary.main',
                                    display: 'flex',
                                    flexDirection: 'column'
                                }}
                            >
                                <Typography 
                                    variant="subtitle1" 
                                    align="center" 
                                    gutterBottom 
                                    sx={{ 
                                        fontWeight: 'bold',
                                        bgcolor: isToday ? 'primary.light' : 'grey.100',
                                        color: isToday ? 'white' : 'inherit',
                                        borderRadius: 1,
                                        p: 0.5
                                    }}
                                >
                                    <FontAwesomeIcon icon={faCalendarDay} style={{ marginRight: '8px' }} />
                                    {format(day, 'EEEE d', { locale: es })}
                                </Typography>
                                
                                {dayItems.length === 0 ? (
                                    <Box sx={{ 
                                        display: 'flex', 
                                        justifyContent: 'center', 
                                        alignItems: 'center',
                                        flexGrow: 1,
                                        color: 'text.secondary',
                                        fontStyle: 'italic'
                                    }}>
                                        <Typography variant="body2">No hay comidas</Typography>
                                    </Box>
                                ) : (
                                    <Box sx={{ mt: 1, overflow: 'auto', flexGrow: 1 }}>
                                        {Object.entries(mealsByType).map(([type, meals]) => (
                                            <Box key={type} sx={{ mb: 1.5 }}>
                                                <Typography 
                                                    variant="subtitle2" 
                                                    sx={{ 
                                                        display: 'flex', 
                                                        alignItems: 'center',
                                                        color: 'primary.main'
                                                    }}
                                                >
                                                    <FontAwesomeIcon 
                                                        icon={getMealTypeIcon(type)} 
                                                        style={{ marginRight: '8px' }} 
                                                    />
                                                    {type}
                                                </Typography>
                                                
                                                <List dense disablePadding>
                                                    {meals.map((meal, idx) => (
                                                        <ListItem 
                                                            key={`${meal.meal_id}-${idx}`} 
                                                            disableGutters
                                                            sx={{ pl: 2 }}
                                                        >
                                                            <ListItemText
                                                                primary={
                                                                    <Typography 
                                                                        variant="body2" 
                                                                        noWrap 
                                                                        sx={{ fontWeight: 500 }}
                                                                    >
                                                                        {meal.meal_name}
                                                                    </Typography>
                                                                }
                                                                secondary={
                                                                    <>
                                                                        <Typography 
                                                                            variant="caption" 
                                                                            noWrap
                                                                            color="text.secondary"
                                                                            display="block"
                                                                        >
                                                                            {meal.plan_name} • {meal.quantity} {meal.unit || 'g'}
                                                                        </Typography>
                                                                        {meal.calories && (
                                                                            <Typography 
                                                                                variant="caption" 
                                                                                noWrap
                                                                                color="text.secondary"
                                                                                display="block"
                                                                                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                                                                            >
                                                                                <FontAwesomeIcon icon={faFire} size="xs" /> {meal.calories} kcal
                                                                                {meal.protein_g && <> • <FontAwesomeIcon icon={faDrumstickBite} size="xs" /> {meal.protein_g}g</>}
                                                                                {meal.carbohydrates_g && <> • <FontAwesomeIcon icon={faAppleAlt} size="xs" /> {meal.carbohydrates_g}g</>}
                                                                                {meal.fat_g && <> • <FontAwesomeIcon icon={faOilCan} size="xs" /> {meal.fat_g}g</>}
                                                                            </Typography>
                                                                        )}
                                                                    </>
                                                                }
                                                            />
                                                        </ListItem>
                                                    ))}
                                                </List>
                                            </Box>
                                        ))}
                                    </Box>
                                )}
                            </Paper>
                        </Grid>
                    );
                })}
            </Grid>
        </Box>
    );
};

export default MealPlanCalendar;