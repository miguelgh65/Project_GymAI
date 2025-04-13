// src/components/profile/FitbitConnection.js
import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, Typography, Button, Card, CardContent,
  Divider, CircularProgress, Alert, Grid, Chip, Link
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLink, faUnlink, faCheckCircle } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';
import AuthService from '../../services/AuthService';
import ApiService from '../../services/ApiService';

function FitbitConnection({ user, onUpdate }) {
  const [isFitbitConnected, setIsFitbitConnected] = useState(false);
  const [fitbitProfile, setFitbitProfile] = useState(null);
  const [isFitbitLoading, setIsFitbitLoading] = useState(false);
  const [fitbitError, setFitbitError] = useState(null);
  const [uiMessage, setUiMessage] = useState(null);
  
  // Ref para el formulario
  const formRef = useRef(null);
  
  // Obtener la URL base de la API
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';

  useEffect(() => {
    if (user) {
      checkAndLoadFitbitData();
    }
  }, [user]);

  const checkAndLoadFitbitData = async () => {
    if (!user) return;

    console.log("Verificando estado de Fitbit...");
    setIsFitbitLoading(true);
    setFitbitError(null);
    try {
      const profileResponse = await ApiService.getFitbitData('profile');
      console.log("Respuesta de getFitbitData:", profileResponse);

      if (profileResponse.success) {
         if (profileResponse.is_connected && profileResponse.data) {
             setIsFitbitConnected(true);
             setFitbitProfile(profileResponse.data);
             console.log("Fitbit conectado y perfil cargado.");
         } else {
             setIsFitbitConnected(profileResponse.is_connected || false);
             setFitbitProfile(null);
             if (!profileResponse.is_connected) {
                 console.log("Fitbit no está conectado según el backend.");
             } else {
                 console.warn("Fitbit conectado pero no se pudo cargar el perfil:", profileResponse.message);
                 setFitbitError('Fitbit conectado, pero no se pudo cargar el perfil.');
             }
         }
      } else {
         console.error("Error en la respuesta del backend al verificar Fitbit:", profileResponse.message);
         setIsFitbitConnected(false);
         setFitbitProfile(null);
         setFitbitError(profileResponse.message || 'Error al verificar estado de Fitbit.');
      }
    } catch (error) {
      console.error('Error en llamada a getFitbitData:', error);
      setIsFitbitConnected(false);
      setFitbitProfile(null);
      
      if (error.response && error.response.status === 403) {
        console.log("Fitbit no conectado (403 Forbidden)");
        // No mostrar error en este caso, simplemente no está conectado
      } else {
        setFitbitError(error.response?.data?.detail || 'No se pudo verificar el estado de Fitbit.');
      }
    } finally {
      setIsFitbitLoading(false);
    }
  };

  // Método para iniciar conexión a Fitbit con Axios
  const connectFitbit = async () => {
    console.log("Iniciando conexión Fitbit via Axios con token JWT...");
    setIsFitbitLoading(true);
    setFitbitError(null);
    
    try {
      // Obtener el token
      const token = AuthService.getToken();
      if (!token) {
        setFitbitError("No hay token de autenticación disponible.");
        setIsFitbitLoading(false);
        return;
      }
      
      // Configurar la solicitud con el token en los headers
      const config = {
        headers: { 
          'Authorization': `Bearer ${token}`
        },
        // Importante: permitir redirecciones y seguirlas automáticamente
        maxRedirects: 5,
        // Permitir que el navegador maneje las redirecciones
        validateStatus: function(status) {
          return status < 400; // Aceptar respuestas 3xx como válidas
        }
      };
      
      // Hacer la llamada GET a Fitbit connect
      console.log("Solicitando conexión a Fitbit con config:", config);
      
      // En lugar de hacer una solicitud normal, creamos un iframe temporal
      // para cargar la URL con el token en un header, y luego dejar que el
      // navegador maneje la redirección
      
      // Primero obtenemos la URL de redirección
      const response = await axios.get(`${API_URL}/api/fitbit/connect-url`, config);
      
      if (response.data && response.data.redirect_url) {
        // Redirigir a la URL obtenida
        window.location.href = response.data.redirect_url;
      } else {
        throw new Error("No se obtuvo una URL de redirección válida");
      }
    } catch (error) {
      console.error("Error conectando a Fitbit:", error);
      setFitbitError("Error al iniciar la conexión con Fitbit. Inténtalo de nuevo más tarde.");
      setIsFitbitLoading(false);
    }
    // No detenemos el loading si la redirección es exitosa
  };

  // Función alternativa: enviar formulario que abre en nueva ventana
  const handleConnectFitbitClick = () => {
    setIsFitbitLoading(true);
    
    // Verificar si hay token
    const token = AuthService.getToken();
    if (!token) {
      setFitbitError("No hay token de autenticación disponible.");
      setIsFitbitLoading(false);
      return;
    }
    
    // Utilizar una solución simple y directa que funciona en todos los navegadores
    // Creamos una solicitud GET directa con el token en la URL
    window.location.href = `${API_URL}/api/fitbit/connect?token=${token}`;
  };

  const disconnectFitbit = async () => {
    console.log("Desconectando Fitbit...");
    setUiMessage(null);
    setIsFitbitLoading(true);
    try {
      const response = await ApiService.disconnectFitbit();
      if (response.success) {
        setIsFitbitConnected(false);
        setFitbitProfile(null);
        setFitbitError(null);
        setUiMessage({
          type: 'success',
          text: response.message || 'Cuenta de Fitbit desconectada'
        });
        console.log("Fitbit desconectado exitosamente.");
        if (onUpdate) onUpdate();
      } else {
        console.error("Error en API al desconectar Fitbit:", response.message);
        setUiMessage({ type: 'error', text: response.message || 'Error al desconectar.' });
      }
    } catch (error) {
      console.error('Error de red/servidor al desconectar Fitbit:', error);
      setUiMessage({ type: 'error', text: `Error: ${error.response?.data?.detail || 'No se pudo desconectar.'}` });
    } finally {
      setIsFitbitLoading(false);
      setTimeout(() => setUiMessage(null), 5000);
    }
  };

  return (
    <Card elevation={3} sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>Conexión Fitbit</Typography>
        {fitbitError && <Alert severity="error" sx={{ mb: 2 }}>{fitbitError}</Alert>}
        {uiMessage && (
          <Alert severity={uiMessage.type} sx={{ mb: 2 }} onClose={() => setUiMessage(null)}>
            {uiMessage.text}
          </Alert>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Chip
            icon={<FontAwesomeIcon icon={faLink} />}
            label="Fitbit"
            variant="outlined"
            size="small"
            sx={{ minWidth: '100px' }}
          />
          {isFitbitConnected ? (
            <>
              <Typography component="span" sx={{ color: 'success.main', fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
                <FontAwesomeIcon icon={faCheckCircle} style={{marginRight: 4}}/> Conectado
              </Typography>
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={disconnectFitbit}
                disabled={isFitbitLoading}
                startIcon={<FontAwesomeIcon icon={faUnlink} />}
                sx={{ ml: 'auto' }}
              >
                {isFitbitLoading ? <CircularProgress size={16} sx={{ mr: 1 }}/> : null}
                Desconectar
              </Button>
            </>
          ) : (
            <>
              <Typography component="span" sx={{ color: 'text.secondary', mr: 2 }}>
                No conectado
              </Typography>
              
              {/* NUEVA SOLUCIÓN: Botón normal que redirige al endpoint con token en URL */}
              <Button
                variant="contained"
                onClick={handleConnectFitbitClick}
                disabled={isFitbitLoading}
                startIcon={<FontAwesomeIcon icon={faLink} />}
                size="small"
                sx={{ backgroundColor: '#00B0B9', '&:hover': { backgroundColor: '#008a91'} }}
              >
                {isFitbitLoading ? <CircularProgress size={16} sx={{ mr: 1 }} color="inherit"/> : null}
                Conectar con Fitbit
              </Button>
            </>
          )}
          {isFitbitLoading && <CircularProgress size={20} sx={{ ml: 2 }} />}
        </Box>

        {isFitbitConnected && fitbitProfile?.user && (
          <Box sx={{ mt: 3, p: 2, backgroundColor: '#f9f9f9', borderRadius: 1 }}>
            <Typography variant="subtitle1" gutterBottom>
              Perfil Fitbit ({fitbitProfile.user.displayName || 'Usuario'})
            </Typography>
            <Grid container spacing={2}>
              {fitbitProfile.user.age && (
                <Grid item xs={6} sm={4} md={3}>
                  <Card variant="outlined" sx={{ p: 1, textAlign: 'center', height: '100%' }}>
                    <Typography variant="h5" color="primary">{fitbitProfile.user.age}</Typography>
                    <Typography variant="caption" color="textSecondary">Edad</Typography>
                  </Card>
                </Grid>
              )}
              {fitbitProfile.user.height && (
                <Grid item xs={6} sm={4} md={3}>
                  <Card variant="outlined" sx={{ p: 1, textAlign: 'center', height: '100%' }}>
                    <Typography variant="h5" color="primary">{fitbitProfile.user.height}</Typography>
                    <Typography variant="caption" color="textSecondary">Altura (cm)</Typography>
                  </Card>
                </Grid>
              )}
              {fitbitProfile.user.weight && (
                <Grid item xs={6} sm={4} md={3}>
                  <Card variant="outlined" sx={{ p: 1, textAlign: 'center', height: '100%' }}>
                    <Typography variant="h5" color="primary">{fitbitProfile.user.weight}</Typography>
                    <Typography variant="caption" color="textSecondary">Peso (kg)</Typography>
                  </Card>
                </Grid>
              )}
              {fitbitProfile.user.averageDailySteps && (
                <Grid item xs={6} sm={4} md={3}>
                  <Card variant="outlined" sx={{ p: 1, textAlign: 'center', height: '100%' }}>
                    <Typography variant="h5" color="primary">{fitbitProfile.user.averageDailySteps}</Typography>
                    <Typography variant="caption" color="textSecondary">Pasos diarios (prom)</Typography>
                  </Card>
                </Grid>
              )}
            </Grid>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default FitbitConnection;