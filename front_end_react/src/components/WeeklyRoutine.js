import React, { useState, useEffect } from 'react';
    import {
      Box, Typography, Button, Card, CardContent, CardHeader,
      Grid, TextField, CircularProgress, Alert, Divider
    } from '@mui/material';
    import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
    import {
      faCalendarAlt,
      faSpinner,
      faSave,
      faCheckCircle,
      faExclamationTriangle,
      faDumbbell
    } from '@fortawesome/free-solid-svg-icons';
    import axios from 'axios'; // Asegúrate que axios está importado

    function WeeklyRoutine({ user }) {
      const [loading, setLoading] = useState(true);
      const [routineData, setRoutineData] = useState({});
      const [isSubmitting, setIsSubmitting] = useState(false);
      const [response, setResponse] = useState(null);
      const [error, setError] = useState(null); // Estado para errores de carga

      const weekdays = [
        { id: 1, name: 'Lunes' },
        { id: 2, name: 'Martes' },
        { id: 3, name: 'Miércoles' },
        { id: 4, name: 'Jueves' },
        { id: 5, name: 'Viernes' },
        { id: 6, name: 'Sábado' },
        { id: 7, name: 'Domingo' }
      ];

      useEffect(() => {
         if(user) {
             loadRoutine();
         } else {
             setLoading(false);
             setError("Debes iniciar sesión para ver o editar tu rutina.");
         }
      }, [user]);

      const loadRoutine = async () => {
        try {
          setLoading(true);
          setError(null);
          // *** CAMBIO AQUÍ: Añadir /api/ ***
          const result = await axios.get('/api/rutina?format=json');
          if (result.data.success && result.data.rutina) {
            setRoutineData(result.data.rutina);
          } else {
             // Manejar el caso donde la rutina podría estar vacía pero la llamada fue exitosa
             setRoutineData({});
          }
        } catch (err) {
          console.error('Error al cargar la rutina:', err);
          setError(`Error al cargar la rutina: ${err.response?.data?.message || err.message}`);
          setRoutineData({}); // Establecer vacío en caso de error
        } finally {
          setLoading(false);
        }
      };

      const handleSubmit = async () => {
        const routine = {};
        let hasChanges = false; // Para detectar si realmente hay cambios
        weekdays.forEach(day => {
          const textarea = document.getElementById(`day-${day.id}`);
          if (textarea) {
            const exercises = textarea.value
              .split('\n')
              .map(line => line.trim())
              .filter(line => line.length > 0);
            routine[day.id] = exercises;
            // Comprobar si el valor ha cambiado respecto al inicial
            const initialValue = (routineData[day.id] || []).join('\n');
            if (textarea.value.trim() !== initialValue.trim()) {
                 hasChanges = true;
            }
          }
        });

        // Opcional: No enviar si no hay cambios
        // if (!hasChanges) {
        //      setResponse({ success: true, message: "No se detectaron cambios en la rutina." });
        //      setTimeout(() => setResponse(null), 3000);
        //      return;
        // }

        setIsSubmitting(true);
        setResponse(null);

        try {
          // *** CAMBIO AQUÍ: Añadir /api/ ***
          const result = await axios.post('/api/rutina', { rutina: routine });
          setResponse({
            success: result.data.success,
            message: result.data.message
          });
          if(result.data.success) {
              // Actualizar el estado local para reflejar los datos guardados
              setRoutineData(routine);
          }
        } catch (error) {
          console.error('Error al guardar la rutina:', error);
          setResponse({
            success: false,
            message: error.response?.data?.detail || error.response?.data?.message || 'Error al guardar la rutina.'
          });
        } finally {
          setIsSubmitting(false);
          setTimeout(() => setResponse(null), 5000);
        }
      };

      if (!user && !loading) {
          return (
             <Box sx={{ m: 2 }}>
                 <Alert severity="warning">{error || "Debes iniciar sesión para gestionar tu rutina."}</Alert>
             </Box>
          );
      }

      if (loading) {
        return (
          <Box sx={{ m: 2 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <CircularProgress size={40} sx={{ mb: 3 }} />
                <Typography variant="h6">Cargando tu rutina...</Typography>
              </CardContent>
            </Card>
          </Box>
        );
      }

      if (error && !loading) {
         return (
             <Box sx={{ m: 2 }}>
                 <Card>
                     <CardContent>
                         <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                           <FontAwesomeIcon icon={faCalendarAlt} style={{ marginRight: 12 }} /> Mi Rutina Semanal
                         </Typography>
                         <Alert severity="error" icon={<FontAwesomeIcon icon={faExclamationTriangle}/>}>
                           {error}
                         </Alert>
                     </CardContent>
                 </Card>
             </Box>
         );
      }


      return (
        <Box sx={{ m: 2 }}>
          <Card elevation={3}>
            <CardHeader
              title={
                <Typography variant="h5" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={faCalendarAlt} style={{ marginRight: 12 }} />
                  Mi Rutina Semanal
                </Typography>
              }
              sx={{
                backgroundColor: '#f5f5f5',
                borderBottom: '1px solid #e0e0e0',
                pb: 2
              }}
            />

            <CardContent>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Configura los ejercicios para cada día de la semana. Los cambios se guardarán al hacer clic en el botón.
              </Typography>

              <Grid container spacing={3}>
                {weekdays.map(day => (
                  <Grid item xs={12} md={6} key={day.id}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardHeader
                        title={
                          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                            <FontAwesomeIcon icon={faDumbbell} style={{ marginRight: 8, color: '#6366F1' }} />
                            {day.name}
                          </Typography>
                        }
                        sx={{
                          py: 1.5,
                          backgroundColor: '#fafafa',
                          borderBottom: '1px solid #f0f0f0'
                        }}
                      />
                      <CardContent sx={{ pt: 2 }}>
                        <TextField
                          id={`day-${day.id}`}
                          multiline
                          placeholder="Introduce los ejercicios (uno por línea)"
                          // Usa defaultValue para inputs no controlados O usa useState para controlar cada uno
                          defaultValue={routineData[day.id] ? routineData[day.id].join('\n') : ''}
                          fullWidth
                          rows={4}
                          variant="outlined"
                          size="small"
                          aria-label={`Ejercicios para ${day.name}`}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>

              {response && (
                <Box sx={{ mt: 3 }}>
                  <Alert
                    severity={response.success ? 'success' : 'error'}
                    icon={response.success ? <FontAwesomeIcon icon={faCheckCircle} /> : <FontAwesomeIcon icon={faExclamationTriangle} />}
                    onClose={() => setResponse(null)} // Permitir cerrar la alerta
                  >
                    {response.message}
                  </Alert>
                </Box>
              )}

              <Box sx={{ mt: 4, textAlign: 'right' }}>
                <Button
                  variant="contained"
                  color="primary"
                  disabled={isSubmitting}
                  onClick={handleSubmit}
                  startIcon={isSubmitting ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
                  sx={{ py: 1, px: 3 }}
                >
                  {isSubmitting ? 'Guardando...' : 'Guardar Rutina'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>
      );
    }

    export default WeeklyRoutine;