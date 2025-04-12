// src/components/nutrition/meal-plans/MealPlanCalendar.js
import React, { useState, useEffect } from 'react';
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

    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 }); // Lunes
    const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 });
    const daysInWeek = eachDayOfInterval({ start: weekStart, end: weekEnd });

    useEffect(() => {
        const fetchWeekData = async () => {
            setLoading(true);
            setError(null);
            const startDateStr = format(weekStart, 'yyyy-MM-dd');
            const endDateStr = format(weekEnd, 'yyyy-MM-dd');

            try {
                // Necesitas un endpoint en tu backend que devuelva los items de planes ACTIVOS
                console.warn("Endpoint getMealPlansByDateRange asumido. Verifica tu backend y su respuesta.");
                const plansData = await MealPlanService.getMealPlansByDateRange(startDateStr, endDateStr);

                // Agrupar los items por fecha
                const grouped = {};
                plansData?.forEach(item => {
                    const dateKey = format(new Date(item.date), 'yyyy-MM-dd');
                    if (!grouped[dateKey]) {
                        grouped[dateKey] = [];
                    }
                    // Ordenar por tipo de comida (opcional)
                    const order = ['Desayuno', 'Almuerzo', 'Comida', 'Merienda', 'Cena', 'Otro'];
                    grouped[dateKey].push(item);
                    grouped[dateKey].sort((a, b) => order.indexOf(a.meal_type) - order.indexOf(b.meal_type));
                });
                setWeekPlans(grouped);

            } catch (err) {
                console.error("Error fetching weekly meal plans:", err);
                setError(err.message || 'Error al cargar el calendario del plan.');
            } finally {
                setLoading(false);
            }
        };

        fetchWeekData();
    }, [weekStart, weekEnd]);

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
                                        <ListItem><ListItemText secondary="-" sx={{ textAlign: 'center' }} /></ListItem>
                                     ) : (
                                        dayItems.map((item, index) => (
                                            <ListItem key={`${item.meal_id}-${index}`} disableGutters>
                                                <ListItemText
                                                     primary={item.meal_name || `Comida ID: ${item.meal_id}`}
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