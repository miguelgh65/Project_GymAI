// src/components/nutrition/meal-plans/MealPlanCalendar.js
import React, { useState, useEffect, useCallback } from 'react';
import { MealPlanService } from '../../../services/NutritionService';
import { Box, Typography, CircularProgress, Alert, Grid, Paper, List, ListItem, ListItemText, IconButton, Button } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronLeft, faChevronRight } from '@fortawesome/free-solid-svg-icons';
import { format, startOfWeek, endOfWeek, addDays, subDays, isSameDay, eachDayOfInterval } from 'date-fns';
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

    // First fetch active plans once
    useEffect(() => {
        const fetchActivePlans = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await MealPlanService.getAll(true);
                setActivePlans(response.meal_plans || []);
            } catch (err) {
                console.error("Error fetching active meal plans:", err);
                setError(err.message || 'Error al cargar los planes activos.');
            } finally {
                setLoading(false);
            }
        };

        fetchActivePlans();
    }, []);

    // Process week data when active plans change or week changes
    useEffect(() => {
        if (activePlans.length === 0) return;

        const startDateStr = format(weekStart, 'yyyy-MM-dd');
        const endDateStr = format(weekEnd, 'yyyy-MM-dd');
        console.log(`Processing meal plans for week: ${startDateStr} to ${endDateStr}`);

        // Process the plans to organize by days
        const grouped = {};
        
        // Initialize empty arrays for each day
        daysInWeek.forEach(day => {
            const dateKey = format(day, 'yyyy-MM-dd');
            grouped[dateKey] = [];
        });
        
        // Sort active plans to relevant days 
        activePlans.forEach(plan => {
            if (!plan.items || !Array.isArray(plan.items)) return;
            
            // Map days of week to dates in current week
            const dayMap = {
                'Lunes': format(daysInWeek[0], 'yyyy-MM-dd'),
                'Martes': format(daysInWeek[1], 'yyyy-MM-dd'),
                'Miércoles': format(daysInWeek[2], 'yyyy-MM-dd'),
                'Jueves': format(daysInWeek[3], 'yyyy-MM-dd'),
                'Viernes': format(daysInWeek[4], 'yyyy-MM-dd'),
                'Sábado': format(daysInWeek[5], 'yyyy-MM-dd'),
                'Domingo': format(daysInWeek[6], 'yyyy-MM-dd')
            };
            
            plan.items.forEach(item => {
                if (item.day_of_week && dayMap[item.day_of_week]) {
                    const dateKey = dayMap[item.day_of_week];
                    if (!grouped[dateKey]) {
                        grouped[dateKey] = [];
                    }
                    
                    // Add plan info
                    grouped[dateKey].push({
                        ...item,
                        plan_name: plan.plan_name || plan.name,
                        meal_name: item.meal_name || `Comida ${item.meal_id}`
                    });
                }
            });
        });
        
        // Sort items by meal type
        Object.keys(grouped).forEach(date => {
            const order = ['Desayuno', 'Almuerzo', 'Comida', 'Merienda', 'Cena'];
            grouped[date].sort((a, b) => order.indexOf(a.meal_type) - order.indexOf(b.meal_type));
        });
        
        setWeekPlans(grouped);
    }, [activePlans, weekStart, weekEnd]);

    const handlePrevWeek = () => {
        setCurrentDate(subDays(currentDate, 7));
    };

    const handleNextWeek = () => {
        setCurrentDate(addDays(currentDate, 7));
    };

    const handleToday = () => {
        setCurrentDate(new Date());
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

             {loading && <CircularProgress />}
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

                    return (
                         <Grid item xs={12} sm={6} md={3} lg={12 / 7} key={dateKey}>
                             <Paper elevation={isToday ? 4 : 1} sx={{ p: 1, height: '100%', border: isToday ? '2px solid' : 'none', borderColor: 'primary.main' }}>
                                 <Typography variant="subtitle2" align="center" gutterBottom sx={{ fontWeight: 'bold' }}>
                                     {format(day, 'EEEE d', { locale: es })}
                                 </Typography>
                                 <List dense disablePadding>
                                     {dayItems.length === 0 ? (
                                        <ListItem><ListItemText secondary="No hay comidas" sx={{ textAlign: 'center' }} /></ListItem>
                                     ) : (
                                        dayItems.map((item, index) => (
                                            <ListItem key={`${item.meal_id}-${index}`} disableGutters>
                                                <ListItemText
                                                     primary={item.meal_name}
                                                     secondary={item.meal_type}
                                                     primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                                                     secondaryTypographyProps={{ variant: 'caption' }}
                                                 />
                                             </ListItem>
                                         ))
                                     )}
                                 </List>
                             </Paper>
                         </Grid>
                     );
                 })}
             </Grid>
        </Box>
    );
};

export default MealPlanCalendar;