// src/components/Login.js - Fixed version
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, CardContent, Button, Typography, Box, 
  TextField, Divider, Avatar, CircularProgress, Fade,
  Alert
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner, faDumbbell } from '@fortawesome/free-solid-svg-icons';
import { faTelegram, faGoogle } from '@fortawesome/free-brands-svg-icons';
import AuthService from '../services/AuthService';

// Styles (unchanged)
const LoginContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
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
  const [googleClientId] = useState('809764193714-h551ast9v2n4c7snp5e8sidja1bm995g.apps.googleusercontent.com');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [debugMode, setDebugMode] = useState(false);
  const [logMessages, setLogMessages] = useState([]);
  const navigate = useNavigate();

  const logDebug = useCallback((message, type = 'info') => {
    const timestamp = new Date().toISOString().substr(11, 8);
    console.log(`[${timestamp}] ${message}`);
    setLogMessages(prev => [...prev, { timestamp, message, type }]);
  }, []);

  // Directly handle Google credentials
  const handleGoogleCredentialResponse = useCallback(async (response) => {
    logDebug('Google auth response received');
    setIsLoading(true);
    setError(null);
    
    if (!response || !response.credential) {
      logDebug('ERROR: No credential in Google response', 'error');
      setError('Authentication failed: No credentials received from Google');
      setIsLoading(false);
      return;
    }
    
    try {
      logDebug(`Token received: ${response.credential.substring(0, 10)}...`);
      logDebug('Sending token to backend...');
      
      // IMPORTANT: Use the standard AuthService
      const result = await AuthService.loginWithGoogle(response.credential);
      
      logDebug(`Backend response: success=${result.success}`);
      
      if (result.success && result.user) {
        logDebug('Login successful, user data received');
        
        // IMPORTANT: Call the callback to update parent state
        if (typeof onLoginSuccess === 'function') {
          logDebug('Calling onLoginSuccess with user data');
          onLoginSuccess(result.user);
        }
        
        logDebug('Redirecting to home page');
        navigate('/');
      } else {
        logDebug('Login failed: success=true but no user data', 'error');
        setError('Authentication failed: No user data received');
      }
    } catch (error) {
      logDebug(`Error during Google login: ${error.message}`, 'error');
      console.error('Detailed error:', error);
      
      // Display appropriate error message
      setError(
        error.response?.data?.detail || 
        error.message || 
        'Authentication failed. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [navigate, onLoginSuccess, logDebug]);

  // Initialize Google Sign-In
  const initializeGoogleSignIn = useCallback(() => {
    if (!window.google || !googleClientId) {
      logDebug('Google API not available', 'warning');
      return;
    }

    try {
      logDebug('Initializing Google Sign-In');
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
      });
      
      const buttonElement = document.getElementById('google-login-btn');
      if (!buttonElement) {
        logDebug('Error: Cannot find "google-login-btn" element', 'error');
        return;
      }
      
      logDebug('Rendering Google button');
      window.google.accounts.id.renderButton(
        buttonElement,
        { 
          theme: 'filled_blue', 
          size: 'large', 
          width: '100%',
          text: 'continue_with',
          shape: 'pill'
        }
      );
      
      logDebug('Google Sign-In initialization completed');
    } catch (error) {
      logDebug(`Error initializing Google Sign-In: ${error.message}`, 'error');
      setError('Could not initialize Google login. Please try again later.');
    }
  }, [googleClientId, handleGoogleCredentialResponse, logDebug]);

  // Load Google script
  useEffect(() => {
    const loadGoogleScript = () => {
      if (document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
        logDebug('Google script already loaded in DOM');
        if (window.google) {
          logDebug('Google global object available, initializing Sign-In');
          initializeGoogleSignIn();
        } else {
          logDebug('Google global object NOT available despite script being loaded', 'warning');
          setTimeout(initializeGoogleSignIn, 1000); // Try again after a delay
        }
        return;
      }
      
      logDebug('Loading Google Sign-In script...');
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        logDebug('Google script loaded successfully');
        setTimeout(initializeGoogleSignIn, 500); // Slight delay to ensure everything is ready
      };
      script.onerror = (e) => {
        logDebug(`Error loading Google script: ${e}`, 'error');
        setError('Failed to load Google authentication service');
      };
      document.body.appendChild(script);
    };
    
    loadGoogleScript();
  }, [initializeGoogleSignIn, logDebug]);

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
            <Alert severity="error" sx={{ mb: 3 }}>
              <Typography variant="body2">{error}</Typography>
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
        
        <Typography variant="body2" align="center" color="textSecondary" sx={{ mt: 2 }}>
          Al iniciar sesión aceptas los términos de servicio y nuestra política de privacidad.
        </Typography>
        
        {/* Simple debug toggle button */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Button 
            variant="text" 
            color="primary" 
            size="small"
            onClick={() => setDebugMode(!debugMode)}
          >
            {debugMode ? "Ocultar diagnóstico" : "Mostrar diagnóstico"}
          </Button>
          
          {debugMode && (
            <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1, maxHeight: '150px', overflow: 'auto' }}>
              {logMessages.map((log, idx) => (
                <Typography 
                  key={idx} 
                  variant="caption" 
                  component="div" 
                  sx={{ 
                    fontFamily: 'monospace', 
                    color: log.type === 'error' ? 'error.main' : 'text.primary',
                    mb: 0.5 
                  }}
                >
                  [{log.timestamp}] {log.message}
                </Typography>
              ))}
              {logMessages.length === 0 && <Typography variant="caption">No hay logs disponibles</Typography>}
            </Box>
          )}
        </Box>
      </StyledCard>
    </LoginContainer>
  );
}

export default Login;