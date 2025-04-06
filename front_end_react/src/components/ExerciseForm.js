import React, { useState, useRef } from 'react';
import axios from 'axios';
import {
  Card, CardContent, CardActions, TextField, Button, Typography,
  Alert, Box, Stack, CircularProgress, Divider
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faPlusCircle,
  faSave,
  faInfoCircle,
  faCheckCircle,
  faExclamationTriangle
} from '@fortawesome/free-solid-svg-icons';

function ExerciseForm({ user }) {
  const [exerciseData, setExerciseData] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState(null);
  const timerRef = useRef(null);

  const handleSubmit = async (e) => {
    e?.preventDefault();

    if (!exerciseData.trim()) {
      setResponse({
        success: false,
        message: 'Introduce los detalles de tu entrenamiento.'
      });
      
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setResponse(null), 5000);
      return;
    }

    setIsSubmitting(true);
    setResponse(null);

    try {
      const result = await axios.post('/api/log-exercise', {
        exercise_data: exerciseData
      });

      setResponse({
        success: result.data.success,
        message: result.data.message
      });

      if (result.data.success) {
        setExerciseData('');
      }
    } catch (error) {
      console.error("Error al registrar ejercicio:", error);
      setResponse({
        success: false,
        message: error.response?.data?.detail || error.response?.data?.message || 'Error de comunicación con el servidor.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Limpiar timers al desmontar el componente
  React.useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  if (!user) {
    return (
      <Box sx={{ my: 3, mx: 2 }}>
        <Alert severity="info">Por favor, inicia sesión para registrar tu entrenamiento.</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ my: 3, mx: 2 }}>
      <Card variant="outlined" elevation={3} sx={{ overflow: 'visible' }}>
        <CardContent>
          <Typography variant="h5" component="div" sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            mb: 2,
            color: '#1976d2',
            fontWeight: 500
          }}>
            <FontAwesomeIcon icon={faPlusCircle} style={{ marginRight: 12 }} />
            Registro de Entrenamiento
          </Typography>

          <Divider sx={{ mb: 3 }} />

          <Box component="form" onSubmit={handleSubmit} noValidate>
            <TextField
              fullWidth
              multiline
              rows={5}
              variant="outlined"
              label="Describe tu entrenamiento (IA Procesará)"
              placeholder={`Ejemplos:\nPress Banca: 5x75kg, 7x70kg, 8x60kg\nCorrer: 5km en 30 minutos\nDominadas: 12, 10, 8 (peso corporal)`}
              value={exerciseData}
              onChange={(e) => setExerciseData(e.target.value)}
              disabled={isSubmitting}
              required
              aria-label="Descripción del entrenamiento"
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&:hover fieldset': {
                    borderColor: '#1976d2',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#1976d2',
                    borderWidth: 2,
                  },
                },
                mb: 1
              }}
            />
            <Typography
              variant="caption"
              display="block"
              sx={{ mt: 1, color: 'text.secondary' }}
            >
              <FontAwesomeIcon icon={faInfoCircle} style={{ marginRight: 4 }} />
              Usa un formato libre o estructurado. La IA interpretará tu registro.
            </Typography>
          </Box>
        </CardContent>

        <CardActions sx={{ p: 2, justifyContent: 'flex-end', borderTop: '1px solid rgba(0, 0, 0, 0.08)' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSubmit}
            disabled={isSubmitting || !exerciseData.trim()}
            startIcon={
              isSubmitting
                ? <CircularProgress size={20} color="inherit" />
                : <FontAwesomeIcon icon={faSave} />
            }
            type="button"
            sx={{ 
              py: 1, 
              px: 3,
              boxShadow: 2,
              '&:hover': {
                boxShadow: 4,
              },
              '&:disabled': {
                boxShadow: 0,
              }
            }}
          >
            {isSubmitting ? 'Registrando...' : 'Registrar Entrenamiento'}
          </Button>
        </CardActions>

        {response && (
          <Box sx={{ px: 2, pb: 2 }}>
            <Alert
              severity={response.success ? 'success' : 'error'}
              iconMapping={{
                success: <FontAwesomeIcon icon={faCheckCircle} fontSize="inherit" />,
                error: <FontAwesomeIcon icon={faExclamationTriangle} fontSize="inherit" />,
              }}
              onClose={() => setResponse(null)}
              sx={{ boxShadow: 1 }}
            >
              {response.message}
            </Alert>
          </Box>
        )}
      </Card>
    </Box>
  );
}

export default ExerciseForm;