// src/components/profile/FitbitConnection.js
import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Card, CardContent,
  CircularProgress, Alert, Collapse, IconButton
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faLink, faUnlink, faCheckCircle, 
  faChevronDown, faChevronUp 
} from '@fortawesome/free-solid-svg-icons';
import ApiService from '../../services/ApiService';
import AuthService from '../../services/AuthService';
// Importamos nuestro nuevo componente
import FitbitDashboard from './FitbitDashboard';

function FitbitConnection({ user, onUpdate }) {
  const [isFitbitConnected, setIsFitbitConnected] = useState(false);
  const [fitbitProfile, setFitbitProfile] = useState(null);
  const [isFitbitLoading, setIsFitbitLoading] = useState(false);
  const [fitbitError, setFitbitError] = useState(null);
  const [uiMessage, setUiMessage] = useState(null);
  const [showDashboard, setShowDashboard] = useState(false);

  useEffect(() => {
    if (user) {
      checkAndLoadFitbitData();
    }
    // Check URL params for status messages from the backend callback redirect
    const params = new URLSearchParams(window.location.search);
    const fitbitStatus = params.get('fitbit_status');
    const fitbitMessage = params.get('message');
    
    if (fitbitStatus === 'success' && fitbitMessage) {
        setUiMessage({ type: 'success', text: fitbitMessage });
        setShowDashboard(true); // Automáticamente mostrar el dashboard al conectar exitosamente
        window.history.replaceState({}, document.title, "/profile");
    } else if (fitbitStatus === 'error' && fitbitMessage) {
        setUiMessage({ type: 'error', text: fitbitMessage });
        window.history.replaceState({}, document.title, "/profile");
    }
    
    // Configurar un temporizador para ocultar el mensaje después de 7 segundos
    const messageTimer = setTimeout(() => setUiMessage(null), 7000);
    
    // Limpiar el temporizador al desmontar el componente
    return () => clearTimeout(messageTimer);
  }, [user]);

  const checkAndLoadFitbitData = async () => {
    console.group('💡 Fitbit Connection Diagnostic');
    console.log("User details:", user);
    
    setIsFitbitLoading(true);
    setFitbitError(null);
    
    try {
      console.log("🔍 Attempting to fetch Fitbit profile data...");
      const profileResponse = await ApiService.getFitbitData('profile');
      
      console.log("🌐 Raw Fitbit Response:", profileResponse);
      
      if (profileResponse.success) {
        console.log("✅ Successfully retrieved Fitbit data");
        
        if (profileResponse.is_connected && profileResponse.data?.user) {
          console.log("🔗 Fitbit Connected. User Details:", profileResponse.data.user);
          setIsFitbitConnected(true);
          setFitbitProfile(profileResponse.data);
        } else {
          console.warn("⚠️ Fitbit Connection Status:", {
            is_connected: profileResponse.is_connected,
            message: profileResponse.message
          });
          setIsFitbitConnected(false);
          setFitbitProfile(null);
        }
      } else {
        console.error("❌ Fitbit Data Retrieval Failed:", profileResponse.message);
        setIsFitbitConnected(false);
        setFitbitProfile(null);
        setFitbitError(profileResponse.message || 'Unable to fetch Fitbit data');
      }
    } catch (error) {
      console.error('❌ Comprehensive Fitbit Error:', {
        name: error.name,
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        headers: error.response?.headers
      });
      
      setIsFitbitConnected(false);
      setFitbitProfile(null);
      
      // Manejo detallado de diferentes tipos de errores
      if (error.response) {
        switch (error.response.status) {
          case 401:
          case 403:
            setFitbitError('No autorizado o conexión de Fitbit expirada. Por favor, reconecte.');
            break;
          case 404:
            setFitbitError('Datos de Fitbit no encontrados.');
            break;
          case 500:
            setFitbitError('Error interno del servidor al recuperar datos de Fitbit.');
            break;
          default:
            setFitbitError(
              error.response.data?.message || 
              'Error desconocido al conectar con Fitbit'
            );
        }
      } else {
        setFitbitError(
          error.message || 
          'Error de red o conexión al recuperar datos de Fitbit'
        );
      }
    } finally {
      setIsFitbitLoading(false);
      console.groupEnd();
    }
  };

  const handleConnectFitbit = async () => {
    console.log("🔒 Iniciando conexión con Fitbit...");
    setIsFitbitLoading(true);
    setFitbitError(null);
  
    try {
      // Ensure user is logged in
      const token = AuthService.getToken();
      if (!token) {
        console.error("No authentication token available");
        setFitbitError("Por favor, inicia sesión primero");
        return;
      }
  
      const connectUrlResponse = await ApiService.getFitbitConnectUrl();
      
      if (connectUrlResponse && connectUrlResponse.redirect_url) {
        console.log("🚀 Redirigiendo a URL de autorización de Fitbit");
        window.location.href = connectUrlResponse.redirect_url;
      } else {
        console.error("No se pudo obtener URL de conexión Fitbit");
        setFitbitError("Error al iniciar conexión con Fitbit");
      }
    } catch (error) {
      console.error("❌ Error en conexión Fitbit:", error);
      setFitbitError(
        error.response?.data?.message || 
        "Error al conectar con Fitbit. Inténtalo de nuevo."
      );
    } finally {
      setIsFitbitLoading(false);
    }
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
        setShowDashboard(false);
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

  const toggleDashboard = () => {
    setShowDashboard(!showDashboard);
  };

  return (
    <Card elevation={3} sx={{ mb: 3, overflow: 'visible' }}>
      <CardContent>
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          <Typography variant="h6">Conexión Fitbit</Typography>
          
          {isFitbitConnected && (
            <Button
              variant="text"
              size="small"
              onClick={toggleDashboard}
              startIcon={<FontAwesomeIcon icon={showDashboard ? faChevronUp : faChevronDown} />}
              color="primary"
            >
              {showDashboard ? 'Ocultar Dashboard' : 'Ver Dashboard'}
            </Button>
          )}
        </Box>
        
        {/* Display fitbitError */}
        {fitbitError && !uiMessage && (
          <Alert severity="error" sx={{ mt: 2, mb: 2 }} onClose={() => setFitbitError(null)}>
            {fitbitError}
          </Alert>
        )}
        
        {/* Display uiMessage (for connect/disconnect success/error) */}
        {uiMessage && (
          <Alert severity={uiMessage.type} sx={{ mt: 2, mb: 2 }} onClose={() => setUiMessage(null)}>
            {uiMessage.text}
          </Alert>
        )}

        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          flexWrap: 'wrap', 
          gap: 2,
          mt: 2,
          p: 2,
          bgcolor: 'background.paper',
          borderRadius: 1,
          border: '1px solid',
          borderColor: 'divider'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <FontAwesomeIcon 
              icon={faLink} 
              style={{ marginRight: '8px', color: '#00B0B9' }} 
            />
            <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
              Fitbit
            </Typography>
          </Box>
          
          {isFitbitConnected ? (
            <>
              <Typography 
                component="span" 
                sx={{ 
                  color: 'success.main', 
                  fontWeight: 'bold', 
                  display: 'flex', 
                  alignItems: 'center',
                  ml: 2
                }}
              >
                <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: 4 }}/> 
                Conectado
              </Typography>
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={disconnectFitbit}
                disabled={isFitbitLoading}
                startIcon={<FontAwesomeIcon icon={faUnlink} />}
                sx={{ ml: 'auto' }} // Push to the right
              >
                {isFitbitLoading ? <CircularProgress size={16} sx={{ mr: 1 }}/> : null}
                Desconectar
              </Button>
            </>
          ) : (
            <>
              <Typography 
                component="span" 
                sx={{ 
                  color: 'text.secondary', 
                  ml: 2 
                }}
              >
                No conectado
              </Typography>
              <Button
                variant="contained"
                onClick={handleConnectFitbit}
                disabled={isFitbitLoading}
                startIcon={<FontAwesomeIcon icon={faLink} />}
                size="small"
                sx={{ 
                  ml: 'auto',
                  backgroundColor: '#00B0B9', 
                  '&:hover': { backgroundColor: '#008a91'} 
                }}
              >
                {isFitbitLoading ? <CircularProgress size={16} sx={{ mr: 1 }} color="inherit"/> : null}
                Conectar con Fitbit
              </Button>
            </>
          )}
        </Box>

        {/* Fitbit Dashboard */}
        <Collapse in={isFitbitConnected && showDashboard}>
          <Box sx={{ mt: 3 }}>
            <FitbitDashboard user={user} />
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
}

export default FitbitConnection;