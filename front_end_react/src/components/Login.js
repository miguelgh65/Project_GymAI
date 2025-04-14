// src/components/Login.js - mejorado con diagnóstico
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, CardContent, Button, Typography, Box, 
  TextField, Divider, Avatar, CircularProgress, Fade,
  Alert, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner, faLink, faDumbbell, faBug, faChevronDown } from '@fortawesome/free-solid-svg-icons';
import { faTelegram, faGoogle } from '@fortawesome/free-brands-svg-icons';
import AuthService from '../services/AuthService';

// Estilos personalizados sin necesidad de imagen externa
const LoginContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  // Usa un degradado en lugar de una imagen
  background: 'linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%)',
}));

const StyledCard = styled(Card)(({ theme }) => ({
  maxWidth: 500,
  width: '100%',
  borderRadius: theme.spacing(2),
  boxShadow: '0 8px 40px rgba(0, 0, 0, 0.12)',
  overflow: 'visible',
  position: 'relative',
  padding: theme.spacing(3),
  background: 'rgba(255, 255, 255, 0.95)',
  backdropFilter: 'blur(10px)',
}));

const LogoAvatar = styled(Avatar)(({ theme }) => ({
  width: 80,
  height: 80,
  backgroundColor: theme.palette.primary.main,
  boxShadow: '0 8px 20px rgba(0, 0, 0, 0.2)',
  position: 'absolute',
  top: -40,
  left: '50%',
  transform: 'translateX(-50%)',
  fontSize: '2rem',
}));

function Login({ onLoginSuccess }) {
  const [googleClientId, setGoogleClientId] = useState('809764193714-h551ast9v2n4c7snp5e8sidja1bm995g.apps.googleusercontent.com');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [debugMode, setDebugMode] = useState(false);
  const [logMessages, setLogMessages] = useState([]);
  const [localStorageStatus, setLocalStorageStatus] = useState({});
  const [cookiesStatus, setCookiesStatus] = useState({});
  const navigate = useNavigate();

  // Función de log mejorada
  const logDebug = useCallback((message, type = 'info') => {
    const timestamp = new Date().toISOString().substr(11, 8);
    const logEntry = { timestamp, message, type };
    console.log(`[${timestamp}] [${type}] ${message}`);
    setLogMessages(prev => [...prev, logEntry]);
  }, []);

  // Comprobar estado de localStorage
  const checkLocalStorage = useCallback(() => {
    try {
      localStorage.setItem('test_key', 'test_value');
      const testValue = localStorage.getItem('test_key');
      localStorage.removeItem('test_key');
      
      // Comprobar token actual
      const currentToken = localStorage.getItem('access_token');
      const currentUser = localStorage.getItem('user');
      
      setLocalStorageStatus({
        available: testValue === 'test_value',
        currentToken: currentToken ? `${currentToken.substring(0, 15)}...` : 'No hay token',
        currentUser: currentUser ? 'Presente' : 'No hay datos de usuario',
        error: null
      });
      logDebug('Estado de localStorage comprobado: ' + (testValue === 'test_value' ? 'Disponible' : 'No disponible'));
    } catch (e) {
      setLocalStorageStatus({
        available: false,
        error: e.message
      });
      logDebug('Error al acceder a localStorage: ' + e.message, 'error');
    }
  }, [logDebug]);

  // Comprobar estado de cookies
  const checkCookies = useCallback(() => {
    try {
      document.cookie = "test_cookie=test_value; path=/";
      const hasCookies = document.cookie.indexOf("test_cookie=") !== -1;
      
      setCookiesStatus({
        available: hasCookies,
        allCookies: document.cookie,
        error: null
      });
      logDebug('Estado de cookies comprobado: ' + (hasCookies ? 'Disponible' : 'No disponible'));
    } catch (e) {
      setCookiesStatus({
        available: false,
        error: e.message
      });
      logDebug('Error al acceder a cookies: ' + e.message, 'error');
    }
  }, [logDebug]);

  // Iniciar diagnóstico
  useEffect(() => {
    if (debugMode) {
      logDebug('Modo diagnóstico activado');
      checkLocalStorage();
      checkCookies();
    }
  }, [debugMode, checkLocalStorage, checkCookies, logDebug]);

  // Manejo de credenciales de Google mejorado con feedback visual y logging
  const handleGoogleCredentialResponse = useCallback(async (response) => {
    setIsLoading(true);
    setError(null);
    logDebug('Google auth response recibida');
    
    if (!response || !response.credential) {
      logDebug('ERROR: No se recibió credential en la respuesta de Google', 'error');
      setError('No se recibió información de autenticación de Google');
      setIsLoading(false);
      return;
    }
    
    logDebug(`Token recibido: ${response.credential.substring(0, 10)}...`);
    
    try {
      logDebug('Enviando token a backend para verificación');
      // Usar AuthService para manejar la autenticación
      const result = await AuthService.loginWithGoogle(response.credential);
      
      logDebug(`Respuesta del backend: ${JSON.stringify(result)}`);
      
      if (result.success && result.user) {
        logDebug('Login exitoso, usuario recibido');
        
        // Comprobar localStorage después del login
        checkLocalStorage();
        
        // Llamar al callback del componente padre si existe
        if (onLoginSuccess) {
          logDebug('Llamando a onLoginSuccess con datos de usuario');
          onLoginSuccess(result.user);
        }
        
        logDebug('Redirigiendo a página principal');
        navigate('/');
      } else {
        logDebug('Login fallido: respuesta success=true pero sin datos de usuario', 'error');
        setError('La autenticación fue exitosa pero no se recibieron datos de usuario');
      }
    } catch (error) {
      logDebug(`Error durante Google Sign-In: ${error.message}`, 'error');
      console.error('Error detallado:', error);
      
      // Mostrar información más detallada del error
      let errorDetail = '';
      if (error.response) {
        errorDetail = `Status: ${error.response.status}, Mensaje: ${JSON.stringify(error.response.data)}`;
        logDebug(`Detalles de error HTTP: ${errorDetail}`, 'error');
      }
      
      setError(errorDetail || error.message || 'Error desconocido durante la autenticación');
    } finally {
      setIsLoading(false);
    }
  }, [navigate, onLoginSuccess, checkLocalStorage, logDebug]);

  // Inicialización de Google Sign-In con logging mejorado
  const initializeGoogleSignIn = useCallback(() => {
    if (window.google && googleClientId) {
      try {
        logDebug('Inicializando Google Sign-In');
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true
        });
        
        const buttonElement = document.getElementById('google-login-btn');
        if (!buttonElement) {
          logDebug('Error: No se encontró el elemento con ID "google-login-btn"', 'error');
          return;
        }
        
        logDebug('Renderizando botón de Google');
        window.google.accounts.id.renderButton(
          buttonElement,
          { 
            theme: 'filled_blue', 
            size: 'large', 
            width: '100%',
            text: 'continue_with',
            shape: 'pill',
            logo_alignment: 'center'
          }
        );
        
        logDebug('Inicialización de Google Sign-In completada');
      } catch (error) {
        logDebug(`Error al inicializar Google Sign-In: ${error.message}`, 'error');
        console.error('Error detallado:', error);
        setError('No se pudo inicializar el inicio de sesión con Google');
      }
    } else {
      logDebug('Google API no disponible o clientId no configurado', 'warning');
    }
  }, [googleClientId, handleGoogleCredentialResponse, logDebug]);

  // Cargar el script de Google con logging mejorado
  useEffect(() => {
    const loadGoogleScript = () => {
      if (document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
        logDebug('Script de Google ya cargado en el DOM');
        if (window.google) {
          logDebug('Objeto global google disponible, inicializando Sign-In');
          initializeGoogleSignIn();
        } else {
          logDebug('Objeto global google NO disponible a pesar de que el script está cargado', 'warning');
        }
        return;
      }
      
      logDebug('Cargando script de Google Sign-In...');
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        logDebug('Script de Google cargado correctamente');
        initializeGoogleSignIn();
      };
      script.onerror = (e) => {
        logDebug(`Error al cargar el script de Google Sign-In: ${e}`, 'error');
        setError('Error al cargar el script de Google Sign-In');
      };
      document.body.appendChild(script);
      logDebug('Script de Google añadido al DOM');
    };
    
    loadGoogleScript();
  }, [initializeGoogleSignIn, logDebug]);

  // Forzar reintento (limpia localStorage y recarga la página)
  const handleForceRetry = () => {
    logDebug('Limpiando localStorage y forzando recarga');
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      logDebug('localStorage limpiado');
    } catch (e) {
      logDebug(`Error al limpiar localStorage: ${e.message}`, 'error');
    }
    window.location.reload();
  };

  return (
    <LoginContainer>
      <StyledCard>
        <LogoAvatar>
          <FontAwesomeIcon icon={faDumbbell} />
        </LogoAvatar>
        
        <Box sx={{ mt: 5, mb: 3, textAlign: 'center' }}>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            GymAI
          </Typography>
          <Typography variant="subtitle1" color="textSecondary" gutterBottom>
            Tu entrenador personal con inteligencia artificial
          </Typography>
        </Box>
        
        {error && (
          <Fade in={!!error}>
            <Alert 
              severity="error"
              sx={{ mb: 3 }}
              action={
                <Button color="inherit" size="small" onClick={handleForceRetry}>
                  Reintentar
                </Button>
              }
            >
              <Typography variant="body2">
                {error}
              </Typography>
            </Alert>
          </Fade>
        )}
        
        <Box sx={{ mb: 4 }}>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
              <CircularProgress size={36} />
            </Box>
          ) : (
            <Box id="google-login-btn" sx={{ my: 2 }}></Box>
          )}
        </Box>
        
        <Divider sx={{ my: 3 }}>
          <Typography variant="body2" color="textSecondary">
            O CONÉCTATE CON
          </Typography>
        </Divider>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <Button
            variant="outlined"
            startIcon={<FontAwesomeIcon icon={faTelegram} />}
            sx={{ borderRadius: '20px', textTransform: 'none' }}
            component="a"
            href="https://t.me/RoonieColemAi_dev_bot"
            target="_blank"
            rel="noopener noreferrer"
          >
            Telegram Bot
          </Button>
        </Box>
        
        <Box sx={{ mt: 4 }}>
          <Button 
            variant="text" 
            color="primary" 
            startIcon={<FontAwesomeIcon icon={faBug} />}
            onClick={() => setDebugMode(!debugMode)}
            fullWidth
            size="small"
          >
            {debugMode ? "Ocultar diagnóstico" : "Mostrar diagnóstico"}
          </Button>
          
          {debugMode && (
            <><Accordion sx={{ mt: 2, mb: 2 }}>
              <AccordionSummary expandIcon={<FontAwesomeIcon icon={faChevronDown} />}>
                <Typography variant="subtitle2">Estado del sistema</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="subtitle2" gutterBottom>LocalStorage:</Typography>
                <Box sx={{ mb: 2, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    Disponible: {localStorageStatus.available ? '✓' : '✗'}<br />
                    Token: {localStorageStatus.currentToken}<br />
                    Usuario: {localStorageStatus.currentUser}<br />
                    {localStorageStatus.error && `Error: ${localStorageStatus.error}`}
                  </Typography>
                </Box>

                <Typography variant="subtitle2" gutterBottom>Cookies:</Typography>
                <Box sx={{ mb: 2, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    Disponibles: {cookiesStatus.available ? '✓' : '✗'}<br />
                    {cookiesStatus.error && `Error: ${cookiesStatus.error}`}<br />
                    {cookiesStatus.allCookies && `Cookies: ${cookiesStatus.allCookies}`}
                  </Typography>
                </Box>

                <Button variant="outlined" size="small" onClick={handleForceRetry} sx={{ mr: 1, mb: 1 }}>
                  Limpiar y reintentar
                </Button>

                <Button variant="outlined" size="small" onClick={() => {
                  checkLocalStorage();
                  checkCookies();
                } } sx={{ mb: 1 }}>
                  Actualizar estado
                </Button>
              </AccordionDetails>
            </Accordion><Accordion sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<FontAwesomeIcon icon={faChevronDown} />}>
                  <Typography variant="subtitle2">Logs ({logMessages.length})</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ maxHeight: '200px', overflow: 'auto', bgcolor: '#f5f5f5', p: 1, borderRadius: 1 }}>
                    {logMessages.map((log, index) => (
                      <Typography
                        key={index}
                        variant="body2"
                        component="div"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          color: log.type === 'error' ? 'error.main' :
                            log.type === 'warning' ? 'warning.main' : 'text.primary',
                          mb: 0.5
                        }}
                      >
                        [{log.timestamp}] {log.message}
                      </Typography>
                    ))}
                    {logMessages.length === 0 && (
                      <Typography variant="body2" color="text.secondary">No hay logs disponibles</Typography>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion></>
          )}
        </Box>
        
        <Typography variant="body2" align="center" color="textSecondary" sx={{ mt: 2 }}>
          Al iniciar sesión aceptas los términos de servicio y nuestra política de privacidad.
        </Typography>
      </StyledCard>
    </LoginContainer>
  );
}

export default Login;