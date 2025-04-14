// src/components/profile/FitbitConnection.js
import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Card, CardContent,
  CircularProgress, Alert, Grid, Chip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLink, faUnlink, faCheckCircle } from '@fortawesome/free-solid-svg-icons';
// Asegúrate de importar tu componente de detalles si lo vas a usar
// import FitbitProfileDetails from './FitbitProfileDetails';
import ApiService from '../../services/ApiService';

function FitbitConnection({ user, onUpdate }) {
  const [isFitbitConnected, setIsFitbitConnected] = useState(false);
  const [fitbitProfile, setFitbitProfile] = useState(null);
  const [isFitbitLoading, setIsFitbitLoading] = useState(false);
  const [fitbitError, setFitbitError] = useState(null);
  const [uiMessage, setUiMessage] = useState(null);

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
        // Optionally clear URL params
        window.history.replaceState({}, document.title, "/profile");
    } else if (fitbitStatus === 'error' && fitbitMessage) {
        setUiMessage({ type: 'error', text: fitbitMessage });
         // Optionally clear URL params
        window.history.replaceState({}, document.title, "/profile");
    }
    setTimeout(() => setUiMessage(null), 7000); // Auto-hide message

  }, [user]); // Dependency array remains

  const checkAndLoadFitbitData = async () => {
    if (!user) return;

    console.log("Verificando estado de Fitbit...");
    setIsFitbitLoading(true);
    setFitbitError(null);
    try {
      const profileResponse = await ApiService.getFitbitData('profile');
      console.log("Respuesta de getFitbitData:", profileResponse);

      if (profileResponse.success) {
         if (profileResponse.is_connected && profileResponse.data?.user) {
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
            }
         }
      } else {
         console.error("Error en la respuesta del backend al verificar Fitbit:", profileResponse.message);
         setIsFitbitConnected(false);
         setFitbitProfile(null);
         if (profileResponse.message !== 'Usuario no conectado a Fitbit.') {
            setFitbitError(profileResponse.message || 'Error al verificar estado de Fitbit.');
         }
      }
    } catch (error) {
      console.error('Error en llamada a getFitbitData:', error);
      setIsFitbitConnected(false);
      setFitbitProfile(null);

      if (error.response && (error.response.status === 403 || error.response.status === 401)) {
        console.log("Fitbit no conectado o requiere reconexión (API devolvió 401/403)");
      } else {
        setFitbitError(error.response?.data?.detail || 'No se pudo verificar el estado de Fitbit.');
      }
    } finally {
      setIsFitbitLoading(false);
    }
  };

  const handleConnectFitbit = () => {
    console.log("Navegando al endpoint de conexión del backend...");
    setIsFitbitLoading(true);
    setFitbitError(null);
    const backendBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5050';
    const connectUrl = `${backendBaseUrl}/api/fitbit/connect`;
    window.location.href = connectUrl;
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

  // --- Inicio del bloque Return JSX ---
  return (
    <Card elevation={3} sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>Conexión Fitbit</Typography>
        {/* Display fitbitError */}
        {fitbitError && !uiMessage && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setFitbitError(null)}>
            {fitbitError}
          </Alert>
        )}
        {/* Display uiMessage (for connect/disconnect success/error) */}
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
                <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: 4 }}/> Conectado
              </Typography>
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={disconnectFitbit}
                disabled={isFitbitLoading && isFitbitConnected} // Disable only when disconnecting
                startIcon={<FontAwesomeIcon icon={faUnlink} />}
                sx={{ ml: 'auto' }} // Push to the right
              >
                {isFitbitLoading && isFitbitConnected ? <CircularProgress size={16} sx={{ mr: 1 }}/> : null} {/* Show loading only when disconnecting */}
                Desconectar
              </Button>
            </>
          ) : (
            <>
              <Typography component="span" sx={{ color: 'text.secondary', mr: 2 }}>
                No conectado
              </Typography>
              {/* Button uses the corrected handleConnectFitbit */}
              <Button
                variant="contained"
                onClick={handleConnectFitbit} // Use the corrected function
                disabled={isFitbitLoading && !isFitbitConnected} // Disable only when connecting
                startIcon={<FontAwesomeIcon icon={faLink} />}
                size="small"
                sx={{ backgroundColor: '#00B0B9', '&:hover': { backgroundColor: '#008a91'} }}
              >
                {isFitbitLoading && !isFitbitConnected ? <CircularProgress size={16} sx={{ mr: 1 }} color="inherit"/> : null} {/* Show loading only when connecting */}
                Conectar con Fitbit
              </Button>
            </>
          )}
          {/* General loading indicator can be placed here if needed */}
          {/* {isFitbitLoading && <CircularProgress size={20} sx={{ ml: 2 }} />} */}
        </Box>

        {/* Display Fitbit Profile Details */}
        {/* *** CORRECCIÓN AQUÍ *** */}
        {isFitbitConnected && fitbitProfile?.user && (
          <> {/* <-- Envolver en Fragmento React */}
            {/* Puedes descomentar FitbitProfileDetails si ya lo tienes */}
            {/* <FitbitProfileDetails fitbitProfile={fitbitProfile} /> */}

            {/* O mostrar el Box directamente */}
            <Box sx={{ mt: 3, p: 2, backgroundColor: '#f9f9f9', borderRadius: 1 }}>
              <Typography variant="subtitle1">
                  Perfil Fitbit Cargado ({fitbitProfile.user.displayName || 'Usuario'})
              </Typography>
              {/* Aquí puedes añadir más detalles del perfil si quieres */}
              <Typography variant="body2" color="textSecondary">Edad: {fitbitProfile.user.age}</Typography>
              <Typography variant="body2" color="textSecondary">Altura: {fitbitProfile.user.height} cm</Typography>
              <Typography variant="body2" color="textSecondary">Peso: {fitbitProfile.user.weight} kg</Typography>
            </Box>
          </> // <-- Cerrar Fragmento React
        )}
        {/* *** FIN CORRECCIÓN *** */}

      </CardContent>
    </Card>
  );
  // --- Fin del bloque Return JSX ---
}

export default FitbitConnection;