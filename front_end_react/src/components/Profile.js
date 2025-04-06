// Archivo: front_end_react/src/components/Profile.js
import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Box, Typography, Button, Card, CardContent,
  Divider, CircularProgress, Alert, Grid, Avatar, Chip, Link
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
// --- IMPORTACIONES FONT AWESOME MODIFICADAS ---
// Se importa faGoogle y faTelegram de brands
import { faGoogle, faTelegram } from '@fortawesome/free-brands-svg-icons';
// NO SE IMPORTA faFitbit desde ningún sitio
// Se importan los iconos sólidos necesarios
import { faUser, faCheckCircle, faTimesCircle, faLink, faUnlink, faSpinner, faExclamationTriangle, faSignOutAlt, faCopy } from '@fortawesome/free-solid-svg-icons';
// --- FIN IMPORTACIONES MODIFICADAS ---
import AuthService from '../services/AuthService';

function Profile() {
  // Estados para usuario, carga y mensajes
  const [user, setUser] = useState(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [uiMessage, setUiMessage] = useState(null);

  // Estados para Fitbit
  const [isFitbitConnected, setIsFitbitConnected] = useState(false);
  const [fitbitProfile, setFitbitProfile] = useState(null);
  const [isFitbitLoading, setIsFitbitLoading] = useState(false);
  const [fitbitError, setFitbitError] = useState(null);

  // Estados para vinculación Telegram
  const [linkCode, setLinkCode] = useState(null);
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [showTelegramInstructions, setShowTelegramInstructions] = useState(false);


  const location = useLocation();
  const navigate = useNavigate();

  // --- Funciones de Carga de Datos (con prefijo /api/) ---

  const fetchUserData = useCallback(async () => {
    console.log("Intentando obtener datos del usuario...");
    setIsLoadingUser(true);
    setUiMessage(null);
    try {
      const response = await axios.get('/api/current-user'); // URL con /api
      console.log("Respuesta de /api/current-user:", response.data);

      if (response.data.success && response.data.user) {
        setUser(response.data.user);
      } else {
        setUser(null);
        console.log("Usuario no autenticado según /api/current-user");
        // navigate('/login'); // Opcional: redirigir
      }
    } catch (error) {
      console.error('Error al cargar datos del usuario:', error.response?.data || error.message);
      setUser(null);
      if (error.response?.status === 401) {
          navigate('/login');
      } else {
          setUiMessage({ type: 'error', text: 'Error al cargar la información del perfil.' });
      }
    } finally {
      setIsLoadingUser(false);
    }
  }, [navigate]);

  const checkAndLoadFitbitData = useCallback(async () => {
    if (!user) return;

    console.log("Verificando estado de Fitbit...");
    setIsFitbitLoading(true);
    setFitbitError(null);
    try {
       const profileResponse = await axios.get('/api/fitbit/data?data_type=profile'); // URL con /api
       console.log("Respuesta de /api/fitbit/data?data_type=profile:", profileResponse.data);

       if (profileResponse.data.success && profileResponse.data.data) {
           setIsFitbitConnected(true);
           setFitbitProfile(profileResponse.data.data);
           console.log("Fitbit conectado y perfil cargado.");
       } else {
           console.warn("Llamada a Fitbit exitosa pero sin datos de perfil:", profileResponse.data.message);
           setIsFitbitConnected(true);
           setFitbitProfile(null);
           setFitbitError('Fitbit conectado, pero no se pudo cargar el perfil.');
       }

    } catch (error) {
      console.error('Error al verificar/cargar datos de Fitbit:', error.response?.data || error.message);
      setIsFitbitConnected(false);
      setFitbitProfile(null);
      if (error.response?.status !== 401 && error.response?.status !== 403) {
         setFitbitError('No se pudo verificar el estado de Fitbit.');
      }
    } finally {
       setIsFitbitLoading(false);
    }
  }, [user]);

  // --- Hooks useEffect (sin cambios) ---

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  useEffect(() => {
    if (user) {
      checkAndLoadFitbitData();
    }
  }, [user, checkAndLoadFitbitData]);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const status = searchParams.get('fitbit_status');
    const message = searchParams.get('message');

    if (status) {
      console.log(`Callback de Fitbit detectado: status=${status}, message=${message}`);
      setUiMessage({
        type: status === 'success' ? 'success' : 'error',
        text: message || (status === 'success' ? 'Operación con Fitbit completada.' : 'Ocurrió un error con Fitbit.')
      });

      if (status === 'success') {
        if(user) checkAndLoadFitbitData();
      }
      navigate('/profile', { replace: true });
    }
  }, [location, navigate, checkAndLoadFitbitData, user]);

  // --- Manejadores de Eventos (con prefijo /api/) ---

  const connectFitbit = () => {
    console.log("Iniciando conexión Fitbit via backend...");
    const backendConnectUrl = `/api/fitbit/connect`; // URL con /api
    window.location.href = backendConnectUrl;
  };

  const disconnectFitbit = async () => {
    console.log("Desconectando Fitbit...");
    setUiMessage(null);
    setIsFitbitLoading(true);
    try {
      const response = await axios.post('/api/fitbit/disconnect'); // URL con /api
      if (response.data.success) {
        setIsFitbitConnected(false);
        setFitbitProfile(null);
        setFitbitError(null);
        setUiMessage({
          type: 'success',
          text: response.data.message || 'Cuenta de Fitbit desconectada'
        });
        console.log("Fitbit desconectado exitosamente.");
      } else {
         console.error("Error en API al desconectar Fitbit:", response.data.message);
         setUiMessage({ type: 'error', text: response.data.message || 'Error al desconectar.' });
      }
    } catch (error) {
      console.error('Error de red/servidor al desconectar Fitbit:', error.response?.data || error.message);
      setUiMessage({ type: 'error', text: `Error: ${error.response?.data?.detail || 'No se pudo desconectar.'}` });
    } finally {
        setIsFitbitLoading(false);
        setTimeout(() => setUiMessage(null), 5000);
    }
  };

  const generateLinkCode = async () => {
    setIsGeneratingCode(true);
    setLinkCode(null);
    setShowTelegramInstructions(false);
    setUiMessage(null);
    try {
      const response = await axios.post('/api/generate-link-code'); // URL con /api
      if (response.data.success) {
        setLinkCode(response.data.code);
        setShowTelegramInstructions(true);
      } else {
        setUiMessage({ type: 'error', text: response.data.message || 'No se pudo generar el código.' });
      }
    } catch (error) {
      console.error('Error generando código:', error);
      setUiMessage({ type: 'error', text: 'Error al generar código de vinculación.' });
    } finally {
      setIsGeneratingCode(false);
       setTimeout(() => setUiMessage(null), 5000);
    }
  };

   const copyCodeToClipboard = () => {
     if (!linkCode) return;
     navigator.clipboard.writeText(linkCode).then(() => {
       setUiMessage({ type: 'success', text: 'Código copiado!' });
       setTimeout(() => setUiMessage(null), 3000);
     }).catch(err => {
       console.error('Error al copiar:', err);
       setUiMessage({ type: 'error', text: 'No se pudo copiar el código.' });
        setTimeout(() => setUiMessage(null), 3000);
     });
   };

  const handleLogout = async () => {
    setUiMessage({ type: 'info', text: 'Cerrando sesión...' });
    try {
      await AuthService.logout(); // Usa AuthService
    } catch (error) {
      console.error('Error durante el logout:', error);
      setUiMessage({ type: 'error', text: 'Error al cerrar sesión.' });
      setTimeout(() => setUiMessage(null), 5000);
    }
  };

  // --- Renderizado ---

  if (isLoadingUser) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
         <Alert severity="warning" sx={{ mb: 2 }}>
           Debes iniciar sesión para ver tu perfil.
         </Alert>
         <Button variant="contained" onClick={() => navigate('/login')}>
            Ir a Login
         </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
         <Typography variant="h4">Mi Perfil</Typography>
         <Button
            variant="outlined"
            onClick={handleLogout}
            startIcon={<FontAwesomeIcon icon={faSignOutAlt} />}
            color="error"
            size="small"
         >
           Cerrar Sesión
         </Button>
      </Box>

      {uiMessage && (
        <Alert
          severity={uiMessage.type}
          sx={{ mb: 3 }}
          onClose={() => setUiMessage(null)}
        >
          {uiMessage.text}
        </Alert>
      )}

      <Card elevation={3}>
        <CardContent>
          {/* Información del Usuario */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, flexWrap: 'wrap' }}>
             <Avatar
                src={user.profile_picture || undefined}
                alt={user.display_name || 'Avatar'}
                sx={{ width: 80, height: 80, mr: 2, bgcolor: 'primary.main' }}
             >
               {!user.profile_picture && <FontAwesomeIcon icon={faUser} size="2x" />}
             </Avatar>
             <Box>
              <Typography variant="h5" component="div">{user.display_name || 'Usuario'}</Typography>
              <Typography variant="body2" color="text.secondary">{user.email}</Typography>
             </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Cuentas Conectadas */}
          <Typography variant="h6" gutterBottom> Cuentas conectadas </Typography>

          {/* Google */}
          <Box sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
            <Chip
              icon={<FontAwesomeIcon icon={faGoogle} />}
              label="Google"
              variant="outlined"
              size="small"
              sx={{ mr: 1, minWidth: '100px' }}
            />
            {user.has_google ? (
               <Typography component="span" sx={{ color: 'success.main', fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
                 <FontAwesomeIcon icon={faCheckCircle} style={{marginRight: 4}} /> Conectado
               </Typography>
             ) : (
               <Typography component="span" sx={{ color: 'text.secondary' }}>
                 No conectado
               </Typography>
             )}
          </Box>

          {/* Telegram */}
           <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
             <Chip
                icon={<FontAwesomeIcon icon={faTelegram} />}
                label="Telegram"
                variant="outlined"
                size="small"
                sx={{ mr: 1, minWidth: '100px' }}
              />
             {user.has_telegram ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                   <Typography component="span" sx={{ color: 'success.main', fontWeight: 'bold', mr: 2, display: 'flex', alignItems: 'center' }}>
                     <FontAwesomeIcon icon={faCheckCircle} style={{marginRight: 4}}/> Conectado
                   </Typography>
                   <Link href="https://t.me/RoonieColemAi_dev_bot" target="_blank" rel="noopener noreferrer" sx={{ fontSize: '0.875rem' }}>
                     Abrir Bot
                   </Link>
                </Box>
              ) : (
               <Box sx={{ mt: {xs: 1, sm: 0} }}>
                <Button
                    variant="contained"
                    color="info"
                    size="small"
                    onClick={generateLinkCode}
                    disabled={isGeneratingCode}
                    startIcon={isGeneratingCode ? <CircularProgress size={16} color="inherit"/> : <FontAwesomeIcon icon={faLink} />}
                  >
                    {isGeneratingCode ? 'Generando...' : 'Vincular Telegram'}
                  </Button>
               </Box>
              )}
           </Box>

          {/* Instrucciones Telegram (si se generó código) */}
          {showTelegramInstructions && linkCode && (
               <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    1. Abre nuestro <Link href="https://t.me/RoonieColemAi_dev_bot" target="_blank" rel="noopener noreferrer">bot de Telegram</Link>.<br/>
                    2. Envía el comando <code>/vincular</code>.<br/>
                    3. Envía este código cuando te lo pida:<br/>
                    <Box sx={{ my: 1, display: 'flex', alignItems: 'center' }}>
                       <Typography variant="h6" component="span" sx={{ fontWeight: 'bold', mr: 1 }}>{linkCode}</Typography>
                       <Button onClick={copyCodeToClipboard} size="small" variant="outlined" startIcon={<FontAwesomeIcon icon={faCopy}/>}>
                          Copiar
                       </Button>
                    </Box>
                    (Expira en 10 minutos)
                  </Typography>
               </Alert>
          )}

          <Divider sx={{ my: 3 }} />

          {/* Fitbit */}
          <Typography variant="h6" gutterBottom>Conexión Fitbit</Typography>
          {fitbitError && <Alert severity="error" sx={{ mb: 2 }}>{fitbitError}</Alert>}

          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
             {/* *** CAMBIO AQUÍ: Se usa faLink como icono sustituto *** */}
             <Chip
                icon={<FontAwesomeIcon icon={faLink} />}
                label="Fitbit"
                variant="outlined"
                size="small"
                sx={{ minWidth: '100px' }}
             />
             {/* *** FIN CAMBIO *** */}
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
                 <Button
                   variant="contained"
                   onClick={connectFitbit}
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
            {isFitbitLoading && !isLoadingUser && <CircularProgress size={20} sx={{ ml: 2 }} />}
         </Box>

         {/* Mostrar datos de perfil Fitbit si están disponibles */}
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
    </Box>
  );
}

export default Profile;