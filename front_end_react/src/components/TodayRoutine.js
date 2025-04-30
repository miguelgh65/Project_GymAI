// Archivo: front_end_react/src/components/TodayRoutine.js
import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, Typography, TextField, Button, Box, Alert, List, ListItem, ListItemIcon, ListItemText, CircularProgress, Divider } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalendarDay, faSpinner, faCheckCircle, faCircle, faSave, faExclamationTriangle, faCalendarTimes, faRedo } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';

function TodayRoutine({ user }) {
  const [loading, setLoading] = useState(true);
  const [routineData, setRoutineData] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (user) {
      loadTodayRoutine();
    } else {
      setLoading(false);
      setRoutineData(null);
      setError('Debes iniciar sesión para ver tu rutina.');
    }

    // Limpiar timers al desmontar
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [user]);

  const loadTodayRoutine = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await axios.get('/api/rutina_hoy?format=json');
      setRoutineData(res.data);
    } catch (err) {
      console.error('Error al cargar la rutina:', err);
      setError(`Error al cargar la rutina: ${err.response?.data?.message || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const exerciseInputs = document.querySelectorAll('.reps-input');
    let exerciseData = [];
    let hasData = false;
    
    exerciseInputs.forEach(input => {
      if (input.value.trim() !== '') {
        hasData = true;
        const exerciseName = input.getAttribute('data-exercise');
        exerciseData.push(`${exerciseName}: ${input.value.trim()}`);
      }
    });

    if (!hasData) {
      setResponse({ success: false, message: 'Debes completar al menos un ejercicio.' });
      timerRef.current = setTimeout(() => setResponse(null), 5000);
      return;
    }

    setIsSubmitting(true);
    setResponse(null);

    try {
      const payload = { exercise_data: exerciseData.join('\n') };
      const result = await axios.post('/api/log-exercise', payload);

      setResponse({ success: result.data.success, message: result.data.message });

      if (result.data.success) {
        // Limpiar campos
        exerciseInputs.forEach(input => {
          if (input.value.trim() !== '') {
            input.value = '';
          }
        });
        
        // Recargar datos inmediatamente
        loadTodayRoutine();
      }
    } catch (err) {
      console.error('Error al enviar datos:', err);
      setResponse({ 
        success: false, 
        message: err.response?.data?.detail || err.response?.data?.message || 'Error en la comunicación con el servidor.' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Función modificada para reintentar ejercicios completados usando un endpoint existente
  const handleRetryExercises = async () => {
    try {
      setLoading(true);
      
      // En lugar de llamar a un endpoint específico para reiniciar los ejercicios,
      // usamos el endpoint de log-exercise con una marca especial
      const payload = {
        exercise_data: 'RESET_ROUTINE',
        day_name: routineData.dia_nombre  // Enviamos el nombre del día para identificar la rutina
      };
      
      // Intentamos enviar la solicitud al endpoint existente
      const result = await axios.post('/api/log-exercise', payload);
      
      if (result.data.success) {
        // Ahora recargamos la rutina
        await loadTodayRoutine();
        setResponse({ success: true, message: 'Ejercicios reiniciados para nuevo registro' });
      } else {
        // Si el endpoint responde con éxito=false
        setResponse({ 
          success: false, 
          message: result.data.message || "No se pudo reiniciar los ejercicios. Intenta de nuevo."
        });
      }
    } catch (error) {
      console.error("Error al reiniciar ejercicios:", error);
      
      // Si el error es 404, mostramos un mensaje más específico
      if (error.response && error.response.status === 404) {
        setResponse({ 
          success: false, 
          message: "La función de reinicio no está disponible actualmente. Contacta al administrador." 
        });
      } else {
        setResponse({ 
          success: false, 
          message: "Error al reiniciar ejercicios. Por favor, intenta de nuevo." 
        });
      }
    } finally {
      setLoading(false);
      timerRef.current = setTimeout(() => setResponse(null), 5000);
    }
  };

  // Renderizado
  if (!user && !loading) {
    return (
      <Box sx={{ m: 2 }}>
        <Alert severity="warning">Debes iniciar sesión para ver tu rutina.</Alert>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box sx={{ m: 2 }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress size={40} sx={{ mb: 2 }} />
            <Typography variant="body1">Cargando tu rutina de hoy...</Typography>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ m: 2 }}>
        <Card>
          <CardContent>
            <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <FontAwesomeIcon icon={faCalendarDay} style={{ marginRight: 8 }}/> Entrenamiento de Hoy
            </Typography>
            <Alert severity="error" icon={<FontAwesomeIcon icon={faExclamationTriangle} />}>
              {error}
            </Alert>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (!routineData || !routineData.success || !routineData.rutina || routineData.rutina.length === 0) {
    return (
      <Box sx={{ m: 2 }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', p: 4 }}>
            <FontAwesomeIcon icon={faCalendarTimes} size="3x" style={{ color: '#757575', marginBottom: 16 }} />
            <Typography variant="h6" sx={{ color: '#757575' }}>
              {routineData?.dia_nombre ? `Rutina de ${routineData.dia_nombre}` : ''}
            </Typography>
            <Typography variant="body1" sx={{ color: '#757575', mt: 1 }}>
              {routineData?.message || 'No hay rutina definida para hoy.'}
            </Typography>
            <Typography variant="body2" sx={{ color: '#757575', mt: 1 }}>
              Configura tu rutina en la pestaña "Mi Rutina".
            </Typography>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Verificar si todos los ejercicios están completados
  const allExercisesCompleted = routineData.rutina.every(item => item.realizado);

  return (
    <Box sx={{ m: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <FontAwesomeIcon icon={faCalendarDay} style={{ marginRight: 8 }}/> Entrenamiento de Hoy
          </Typography>
          <Typography variant="subtitle1" sx={{ color: 'text.secondary', mb: 2 }}>
            {routineData.dia_nombre}
          </Typography>
          
          {allExercisesCompleted ? (
            <Alert 
              severity="success" 
              icon={<FontAwesomeIcon icon={faCheckCircle} />}
              action={
                <Button 
                  color="inherit" 
                  size="small" 
                  onClick={handleRetryExercises}
                  startIcon={<FontAwesomeIcon icon={faRedo} />}
                >
                  Reintento
                </Button>
              }
              sx={{ mb: 2 }}
            >
              ¡Felicidades! Has completado todos los ejercicios de hoy.
            </Alert>
          ) : (
            <Typography variant="body2" sx={{ mb: 2 }}>
              Estos son los ejercicios que te tocan hoy. Registra tus series y pesos:
            </Typography>
          )}

          <Divider sx={{ my: 2 }} />

          <Box component="form" id="todayExerciseForm" onSubmit={handleSubmit}>
            <List disablePadding>
              {routineData.rutina.map((item, index) => (
                <ListItem 
                  key={index} 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: { xs: 'column', sm: 'row' }, 
                    alignItems: { xs: 'flex-start', sm: 'center' }, 
                    py: 1.5, 
                    borderBottom: index < routineData.rutina.length - 1 ? '1px solid #eee' : 'none',
                    backgroundColor: item.realizado ? 'rgba(76, 175, 80, 0.08)' : 'transparent' // Fondo verde suave si completado
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 1, sm: 0 }, flexGrow: 1, minWidth: '150px' }}>
                    <ListItemIcon sx={{ minWidth: 'auto', mr: 1.5, color: item.realizado ? 'success.main' : 'warning.main' }}>
                      <FontAwesomeIcon icon={item.realizado ? faCheckCircle : faCircle} />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.ejercicio}
                      sx={{ m: 0, color: item.realizado ? 'text.primary' : 'text.primary' }}
                    />
                  </Box>
                  <TextField
                    type="text"
                    placeholder="ej: 5x75, 7x70, 8x60"
                    disabled={allExercisesCompleted || isSubmitting} // Deshabilitar solo si todos están completados
                    inputProps={{
                      'data-exercise': item.ejercicio,
                      className: 'reps-input',
                      'aria-label': `Entrada para ${item.ejercicio}`
                    }}
                    variant="outlined"
                    size="small"
                    sx={{ 
                      width: { xs: '100%', sm: '50%', md: '40%' }, 
                      backgroundColor: item.realizado ? '#f0f7f0' : 'white' // Fondo más suave
                    }}
                  />
                </ListItem>
              ))}
            </List>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              {!allExercisesCompleted && (
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={isSubmitting}
                  startIcon={isSubmitting ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
                  sx={{ py: 1, px: 3 }}
                >
                  {isSubmitting ? 'Registrando...' : 'Registrar Entrenamiento'}
                </Button>
              )}
              
              {allExercisesCompleted && (
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={handleRetryExercises}
                  startIcon={<FontAwesomeIcon icon={faRedo} />}
                  sx={{ py: 1, px: 3 }}
                >
                  Registrar Nuevo Intento
                </Button>
              )}
            </Box>
          </Box>

          {response && (
            <Box sx={{ mt: 2 }}>
              <Alert
                severity={response.success ? 'success' : 'error'}
                icon={response.success ? <FontAwesomeIcon icon={faCheckCircle} /> : <FontAwesomeIcon icon={faExclamationTriangle} />}
                onClose={() => setResponse(null)}
              >
                {response.message}
              </Alert>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default TodayRoutine;