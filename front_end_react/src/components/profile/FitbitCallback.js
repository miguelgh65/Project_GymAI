// src/components/profile/FitbitCallback.js
import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert, Paper } from '@mui/material';
import axios from 'axios';
import AuthService from '../../services/AuthService';

function FitbitCallback() {
  const [status, setStatus] = useState('processing');
  const [message, setMessage] = useState('Procesando la autorización de Fitbit...');
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Get the code and state from URL query parameters
        const params = new URLSearchParams(location.search);
        const code = params.get('code');
        const state = params.get('state');

        if (!code) {
          setStatus('error');
          setMessage('No se recibió código de autorización de Fitbit.');
          return;
        }

        console.log('Recibido código de Fitbit, enviando al backend...');

        // Get JWT token
        const token = AuthService.getToken();
        if (!token) {
          setStatus('error');
          setMessage('No hay sesión activa. Por favor, inicia sesión nuevamente.');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Forward the code to your backend
        const response = await axios.post('/api/fitbit/callback', 
          { code, state },
          { headers: { 'Authorization': `Bearer ${token}` } }
        );

        if (response.data.success) {
          setStatus('success');
          setMessage('¡Cuenta de Fitbit conectada exitosamente!');
          // Redirect back to profile after 2 seconds
          setTimeout(() => navigate('/profile'), 2000);
        } else {
          setStatus('error');
          setMessage(response.data.message || 'Error al procesar la autorización de Fitbit.');
        }
      } catch (error) {
        console.error('Error procesando callback de Fitbit:', error);
        setStatus('error');
        setMessage(
          error.response?.data?.message || 
          error.response?.data?.detail || 
          'Error al conectar con Fitbit. Por favor, intenta nuevamente.'
        );
      }
    };

    processCallback();
  }, [location, navigate]);

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column',
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '80vh' 
    }}>
      <Paper elevation={3} sx={{ p: 4, maxWidth: 500, width: '100%', textAlign: 'center' }}>
        {status === 'processing' && (
          <>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6">{message}</Typography>
          </>
        )}

        {status === 'success' && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}

        {status === 'error' && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}

        <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
          Serás redirigido automáticamente...
        </Typography>
      </Paper>
    </Box>
  );
}

export default FitbitCallback;