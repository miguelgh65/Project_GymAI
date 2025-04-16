// src/components/nutrition/meal-plans/MealPlanCalendar.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, CircularProgress, Alert, Grid, Paper, 
  List, ListItem, ListItemText, IconButton, Button, Chip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChevronLeft, faChevronRight, faSync, 
  faInfoCircle, faPlus, faUtensils
} from '@fortawesome/free-solid-svg-icons';
import { format, startOfWeek, endOfWeek, addDays, subDays, isSameDay, eachDayOfInterval } from 'date-fns';
import { es } from 'date-fns/locale';
import { MealPlanService } from '../../../services/nutrition';
import { useNavigate } from 'react-router-dom';

const MealPlanCalendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [weekPlans, setWeekPlans] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activePlans, setActivePlans] = useState([]);
  const [usingLocalData, setUsingLocalData] = useState(false);
  const navigate = useNavigate();

  // Inicio y fin de la semana actual (lunes a domingo)
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 });
  const daysInWeek = eachDayOfInterval({ start: weekStart, end: weekEnd });
  
  // Días de la semana en español
  const dayNames = {
    'Lunes': 0,
    'Martes': 1, 
    'Miércoles': 2, 
    'Jueves': 3, 
    'Viernes': 4, 
    'Sábado': 5, 
    'Domingo': 6
  };

  // Cargar planes activos al inicio
  useEffect(() => {
    const fetchActivePlans = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Limpiar caché primero
        MealPlanService.clearCache();
        
        // Obtener planes activos
        const response = await MealPlanService.getAll(true);
        console.log("Planes activos:", response);
        
        const plans = response.meal_plans || [];
        setActivePlans(plans);
        setUsingLocalData(response.fromCache || response.fromLocalOnly || false);
        
        // Si no hay planes de la API, intentar obtener directamente de localStorage
        if (plans.length === 0) {
          try {
            const localStorageKey = 'local_meal_plans';
            const localData = localStorage.getItem(localStorageKey);
            
            if (localData) {
              const localPlans = JSON.parse(localData);
              const activeLocalPlans = localPlans.filter(p => p.is_active);
              
              console.log("Planes locales activos:", activeLocalPlans);
              if (activeLocalPlans.length > 0) {
                setActivePlans(activeLocalPlans);
                setUsingLocalData(true);
              }
            }
          } catch (localErr) {
            console.error("Error obteniendo planes locales:", localErr);
          }
        }
      } catch (err) {
        console.error("Error obteniendo planes activos:", err);
        setError("Error al cargar los planes activos");
        
        // Intentar cargar desde localStorage como último recurso
        try {
          const localStorageKey = 'local_meal_plans';
          const localData = localStorage.getItem(localStorageKey);
          
          if (localData) {
            const localPlans = JSON.parse(localData);
            const activeLocalPlans = localPlans.filter(p => p.is_active);
            
            if (activeLocalPlans.length > 0) {
              setActivePlans(activeLocalPlans);
              setUsingLocalData(true);
            }
          }
        } catch (localErr) {
          console.error("Error obteniendo planes locales:", localErr);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchActivePlans();
  }, []);

  // Procesar datos de la semana cuando cambien planes activos o la semana
  useEffect(() => {
    if (activePlans.length === 0) return;

    const startDateStr = format(weekStart, 'yyyy-MM-dd');
    const endDateStr = format(weekEnd, 'yyyy-MM-dd');
    console.log(`Procesando planes para semana: ${startDateStr} a ${endDateStr}`);

    // Inicializar objeto para agrupar comidas por día
    const grouped = {};
    
    // Inicializar arrays vacíos para cada día
    daysInWeek.forEach(day => {
      const dateKey = format(day, 'yyyy-MM-dd');
      grouped[dateKey] = [];
    });
    
    // Mapeo de nombre de día a fecha de la semana actual
    const dayToDateMap = {};
    Object.keys(dayNames).forEach((dayName, index) => {
      dayToDateMap[dayName] = format(daysInWeek[index], 'yyyy-MM-dd');
    });
    
    // Procesar todos los planes activos
    let totalItems = 0;
    
    activePlans.forEach(plan => {
      console.log(`Procesando plan: ${plan.name || plan.plan_name}`, plan);
      
      // Verificar si el plan tiene items
      if (!plan.items || !Array.isArray(plan.items) || plan.items.length === 0) {
        console.log(`El plan ${plan.id} no tiene comidas asignadas`);
        return;
      }
      
      // Recorrer items del plan y asignarlos a los días correctos
      plan.items.forEach(item => {
        if (item.day_of_week && dayToDateMap[item.day_of_week]) {
          const dateKey = dayToDateMap[item.day_of_week];
          
          if (!grouped[dateKey]) {
            grouped[dateKey] = [];
          }
          
          // Añadir información del plan e item
          const formattedItem = {
            ...item,
            plan_id: plan.id,
            plan_name: plan.name || plan.plan_name,
            meal_name: item.meal_name || `Comida ${item.meal_id}`
          };
          
          // Añadir al grupo de este día
          grouped[dateKey].push(formattedItem);
          totalItems++;
        }
      });
    });
    
    // Ordenar por tipo de comida en cada día
    Object.keys(grouped).forEach(dateKey => {
      const mealTypes = ['Desayuno', 'Almuerzo', 'Comida', 'Merienda', 'Cena'];
      grouped[dateKey].sort((a, b) => {
        const indexA = mealTypes.indexOf(a.meal_type);
        const indexB = mealTypes.indexOf(b.meal_type);
        return indexA - indexB;
      });
    });
    
    console.log(`Procesadas ${totalItems} comidas para la semana`);
    setWeekPlans(grouped);
  }, [activePlans, weekStart, weekEnd]);

  // Navegación entre semanas
  const handlePrevWeek = () => setCurrentDate(subDays(currentDate, 7));
  const handleNextWeek = () => setCurrentDate(addDays(currentDate, 7));
  const handleToday = () => setCurrentDate(new Date());
  
  // Refrescar datos
  const handleRefresh = () => {
    // Limpiar caché y recargar
    MealPlanService.clearCache();
    setLoading(true);
    setActivePlans([]);
    
    // Recargar planes activos
    MealPlanService.getAll(true)
      .then(response => {
        setActivePlans(response.meal_plans || []);
        setUsingLocalData(response.fromCache || response.fromLocalOnly || false);
      })
      .catch(err => {
        console.error("Error al refrescar planes:", err);
        setError("Error al refrescar los planes");
      })
      .finally(() => setLoading(false));
  };
  
  // Navegar a crear un plan
  const handleCreatePlan = () => {
    navigate('/nutrition');
    localStorage.setItem('nutrition_tab', '1'); // "Crear Plan" tab
    window.location.reload();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton onClick={handlePrevWeek} aria-label="Semana anterior">
            <FontAwesomeIcon icon={faChevronLeft} />
          </IconButton>
          <Box textAlign="center" sx={{ mx: 2 }}>
            <Typography variant="h6">
              Semana del {format(weekStart, 'd LLLL', { locale: es })} al {format(weekEnd, 'd LLLL yyyy', { locale: es })}
            </Typography>
            <Button size="small" onClick={handleToday}>Hoy</Button>
          </Box>
          <IconButton onClick={handleNextWeek} aria-label="Semana siguiente">
            <FontAwesomeIcon icon={faChevronRight} />
          </IconButton>
        </Box>
        
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<FontAwesomeIcon icon={faSync} />}
            onClick={handleRefresh}
            sx={{ mr: 1 }}
          >
            Actualizar
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<FontAwesomeIcon icon={faPlus} />}
            onClick={handleCreatePlan}
          >
            Crear Plan
          </Button>
        </Box>
      </Box>

      {usingLocalData && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <FontAwesomeIcon icon={faInfoCircle} style={{ marginRight: '8px' }} />
          Mostrando planes guardados localmente. Algunos cambios pueden no estar sincronizados con el servidor.
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
          <CircularProgress size={30} sx={{ mr: 2 }} />
          <Typography>Cargando calendario de planes...</Typography>
        </Box>
      ) : error ? (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          action={
            <Button size="small" onClick={handleRefresh}>
              Reintentar
            </Button>
          }
        >
          {error}
        </Alert>
      ) : activePlans.length === 0 ? (
        <Alert severity="info" sx={{ mb: 3, py: 2 }}>
          <Box>
            <Typography variant="body1" paragraph>
              No hay planes de comida activos para mostrar en el calendario.
            </Typography>
            <Button
              variant="outlined"
              startIcon={<FontAwesomeIcon icon={faPlus} />}
              onClick={handleCreatePlan}
              size="small"
            >
              Crear Primer Plan
            </Button>
          </Box>
        </Alert>
      ) : (
        <Grid container spacing={1}>
          {daysInWeek.map((day, index) => {
            const dateKey = format(day, 'yyyy-MM-dd');
            const dayItems = weekPlans[dateKey] || [];
            const isToday = isSameDay(day, new Date());
            const dayName = Object.keys(dayNames)[index];

            return (
              <Grid item xs={12} sm={6} md={3} lg={12 / 7} key={dateKey}>
                <Paper 
                  elevation={isToday ? 4 : 1} 
                  sx={{ 
                    p: 1, 
                    height: '100%', 
                    border: isToday ? '2px solid' : 'none', 
                    borderColor: 'primary.main',
                    minHeight: '200px'
                  }}
                >
                  <Typography 
                    variant="subtitle2" 
                    align="center" 
                    gutterBottom 
                    sx={{ 
                      fontWeight: 'bold',
                      pb: 1,
                      borderBottom: '1px solid #eee'
                    }}
                  >
                    {format(day, 'EEEE d', { locale: es })}
                  </Typography>
                  <List dense disablePadding>
                    {dayItems.length === 0 ? (
                      <ListItem>
                        <ListItemText 
                          primary="No hay comidas" 
                          primaryTypographyProps={{ 
                            variant: 'body2', 
                            color: 'text.secondary',
                            align: 'center'
                          }} 
                        />
                      </ListItem>
                    ) : (
                      dayItems.map((item, index) => (
                        <ListItem 
                          key={`${item.meal_id}-${index}`} 
                          disableGutters
                          sx={{ 
                            py: 0.5,
                            borderLeft: '3px solid',
                            borderColor: 
                              item.meal_type === 'Desayuno' ? 'success.light' :
                              item.meal_type === 'Almuerzo' ? 'primary.light' :
                              item.meal_type === 'Comida' ? 'secondary.light' :
                              item.meal_type === 'Merienda' ? 'warning.light' : 
                              'info.light',
                            pl: 1,
                            mb: 0.5,
                            borderRadius: '4px',
                            '&:hover': {
                              bgcolor: 'action.hover'
                            }
                          }}
                        >
                          <ListItemText
                            primary={item.meal_name}
                            secondary={item.meal_type}
                            primaryTypographyProps={{ 
                              variant: 'body2', 
                              noWrap: true,
                              title: item.meal_name
                            }}
                            secondaryTypographyProps={{ 
                              variant: 'caption',
                              sx: {
                                display: 'inline-block',
                                bgcolor: 'background.paper',
                                px: 0.5,
                                borderRadius: '4px'
                              }
                            }}
                          />
                        </ListItem>
                      ))
                    )}
                  </List>
                  {/* Añadir botón de acceso directo para añadir comida a este día */}
                  {activePlans.length > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                      <Button 
                        size="small" 
                        startIcon={<FontAwesomeIcon icon={faUtensils} />}
                        onClick={() => {
                          // Navegar a editar el primer plan activo
                          navigate('/nutrition');
                          localStorage.setItem('nutrition_edit_plan_id', activePlans[0].id);
                          localStorage.setItem('nutrition_edit_day', dayName);
                          localStorage.setItem('nutrition_tab', '1');
                          window.location.reload();
                        }}
                        sx={{ fontSize: '0.7rem' }}
                      >
                        Añadir comida
                      </Button>
                    </Box>
                  )}
                </Paper>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
};

export default MealPlanCalendar;