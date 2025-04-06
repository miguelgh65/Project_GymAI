// src/components/Login.js - corregido sin imagen externa
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, CardContent, CardHeader, Button, Typography, Box, 
  TextField, Divider, Avatar, CircularProgress, Fade
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner, faLink, faDumbbell } from '@fortawesome/free-solid-svg-icons';
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
  const navigate = useNavigate();

  // Manejo de credenciales de Google mejorado con feedback visual
  const handleGoogleCredentialResponse = useCallback(async (response) => {
    setIsLoading(true);
    setError(null);
    console.log('Google auth response received');
    
    try {
      // Usar AuthService para manejar la autenticación
      const result = await AuthService.loginWithGoogle(response.credential);
      
      if (result.success && result.user) {
        // Llamar al callback del componente padre si existe
        if (onLoginSuccess) {
          onLoginSuccess(result.user);
        }
        
        navigate('/');
      }
    } catch (error) {
      console.error('Error durante Google Sign-In:', error);
      setError(error.response?.data?.detail || error.message || 'Error durante la autenticación');
    } finally {
      setIsLoading(false);
    }
  }, [navigate, onLoginSuccess]);

  // Inicialización de Google Sign-In
  const initializeGoogleSignIn = useCallback(() => {
    if (window.google && googleClientId) {
      try {
        console.log('Inicializando Google Sign-In');
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true
        });
        
        window.google.accounts.id.renderButton(
          document.getElementById('google-login-btn'),
          { 
            theme: 'filled_blue', 
            size: 'large', 
            width: '100%',
            text: 'continue_with',
            shape: 'pill',
            logo_alignment: 'center'
          }
        );
        
        // Opcional: mostrar el One Tap UI
        // window.google.accounts.id.prompt();
      } catch (error) {
        console.error('Error al inicializar Google Sign-In:', error);
        setError('No se pudo inicializar el inicio de sesión con Google');
      }
    }
  }, [googleClientId, handleGoogleCredentialResponse]);

  // Cargar el script de Google
  useEffect(() => {
    const loadGoogleScript = () => {
      if (document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
        if (window.google) initializeGoogleSignIn();
        return;
      }
      
      console.log('Cargando script de Google Sign-In...');
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initializeGoogleSignIn;
      script.onerror = () => setError('Error al cargar el script de Google Sign-In');
      document.body.appendChild(script);
    };
    
    loadGoogleScript();
  }, [initializeGoogleSignIn]);

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
            <Box 
              sx={{ 
                p: 2, 
                mb: 3, 
                backgroundColor: 'error.light', 
                color: 'error.contrastText', 
                borderRadius: 1 
              }}
            >
              <Typography variant="body2">
                {error}
              </Typography>
            </Box>
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
        
        <Typography variant="body2" align="center" color="textSecondary" sx={{ mt: 2 }}>
          Al iniciar sesión aceptas los términos de servicio y nuestra política de privacidad.
        </Typography>
      </StyledCard>
    </LoginContainer>
  );
}

export default Login;