import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardActions, Button, Typography, Box } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner, faLink, faCopy } from '@fortawesome/free-solid-svg-icons';
import { faTelegram } from '@fortawesome/free-brands-svg-icons';
import axios from 'axios';

// Recibir onLoginSuccess como prop para actualizar estado en App.js
function Login({ onLoginSuccess }) {
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [linkCode, setLinkCode] = useState(null);
  const [showInstructions, setShowInstructions] = useState(false);
  // Asegúrate que este Client ID sea correcto o cárgalo desde variables de entorno
  const [googleClientId, setGoogleClientId] = useState('809764193714-h551ast9v2n4c7snp5e8sidja1bm995g.apps.googleusercontent.com');
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();

  const handleGoogleCredentialResponse = useCallback(async (response) => {
    setIsLoading(true);
    console.log('Google auth response received:', response);
    try {
        const verifyResponse = await axios.post('/api/auth/google/verify', {
            id_token: response.credential,
        });

        console.log('Verify response:', verifyResponse.data);

        // --- CAMBIO PRINCIPAL AQUÍ ---
        // Verificar que la respuesta sea exitosa Y que contenga el objeto 'user'
        if (verifyResponse.data.success && verifyResponse.data.user) {
            console.log("Login verificado, usuario recibido:", verifyResponse.data.user);

            // Llamar a onLoginSuccess INMEDIATAMENTE con los datos del usuario recibidos
            if (onLoginSuccess) {
                onLoginSuccess(verifyResponse.data.user); // <<< PASAR DATOS DEL USUARIO AL PADRE (App.js)
            }

            // Navegar a la página principal (ya no se necesita setTimeout)
            navigate('/');

        } else {
            // Error en la respuesta del backend
            alert(verifyResponse.data.message || 'Error al verificar con el servidor');
            setIsLoading(false);
        }
    } catch (error) {
        console.error('Error durante Google Sign-In:', error);
        alert('Error al conectar con el servidor: ' + (error.response?.data?.detail || error.response?.data?.message || error.message));
        setIsLoading(false);
    }
    // No poner setIsLoading(false) aquí si el setTimeout se inicia
  }, [navigate, onLoginSuccess]); // Actualizar dependencias

  // initializeGoogleSignIn (sin cambios)
  const initializeGoogleSignIn = useCallback(() => {
    if (window.google && googleClientId) {
      try {
        console.log('Inicializando Google Sign-In con ID:', googleClientId);
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleCredentialResponse
        });
        window.google.accounts.id.renderButton(
          document.getElementById('google-login-btn'),
          { theme: 'outline', size: 'large', width: '100%', text: 'signin_with', shape: 'rectangular' }
        );
      } catch (error) {
        console.error('Error al inicializar Google Sign-In:', error);
      }
    }
  }, [googleClientId, handleGoogleCredentialResponse]);

  // useEffect para cargar script de Google (sin cambios)
  useEffect(() => {
    const loadGoogleScript = () => {
      if (document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
        if (window.google) initializeGoogleSignIn();
        return;
      }
      console.log('Cargando script de Google Sign-In...');
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true; script.defer = true;
      script.onload = initializeGoogleSignIn;
      document.body.appendChild(script);
    };
    loadGoogleScript();
  }, [initializeGoogleSignIn]);

  // generateLinkCode (sin cambios)
  const generateLinkCode = useCallback(async () => {
    setIsGeneratingCode(true);
    try {
      // Importante: Esta llamada requiere que el usuario YA esté logueado
      // Debería hacerse desde una página de perfil, no desde Login.
      // Si la lógica es vincular ANTES de loguear, el flujo debe cambiar.
      // Asumiendo que es para usuarios ya logueados:
      const response = await axios.post('/api/generate-link-code');
      if (response.data.success) {
        setLinkCode(response.data.code);
        setShowInstructions(true);
      } else {
        alert(response.data.message || 'No se pudo generar el código (¿Estás logueado?)');
      }
    } catch (error) {
      console.error('Error generando código:', error);
      if (error.response?.status === 401) {
         alert('Debes iniciar sesión primero para generar un código de vinculación.');
       } else {
         alert('Error al generar código de vinculación: ' + (error.response?.data?.detail || error.message));
       }
    } finally {
      setIsGeneratingCode(false);
    }
  }, []);


  // copyCodeToClipboard (sin cambios)
  const copyCodeToClipboard = useCallback(() => {
    if (!linkCode) return;
    navigator.clipboard.writeText(linkCode)
      .then(() => alert('Código copiado al portapapeles'))
      .catch(err => { console.error('Error al copiar:', err); alert('No se pudo copiar el código.'); });
  }, [linkCode]);


  // Renderizado JSX (sin cambios visibles, pero nota sobre generateLinkCode)
  return (
     <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' }}>
       <Card sx={{ maxWidth: 450, p: 3, borderRadius: 2, boxShadow: 3 }}>
         <CardContent>
           <Typography variant="h5" align="center" gutterBottom> Accede a tu cuenta </Typography>
           <Typography variant="body2" align="center" gutterBottom> Inicia sesión para acceder a todas las funciones </Typography>
           {isLoading ? ( <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}> <FontAwesomeIcon icon={faSpinner} spin size="2x" /> </Box> ) : ( <Box id="google-login-btn" sx={{ my: 2 }}></Box> )}

           {/* --- Sección Vincular Telegram ---
               NOTA: La lógica de `generateLinkCode` usualmente requiere estar logueado.
               Mostrar esto en la página de Login puede ser confuso.
               Considera mover la funcionalidad de vincular Telegram a una página de perfil
               una vez que el usuario haya iniciado sesión.
           */}
           <Box sx={{ mt: 3, borderTop: '1px solid #eee', pt: 2 }}>
             <Typography variant="subtitle1" gutterBottom> Vincular cuenta de Telegram </Typography>
             <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
               (Opcional: Puedes generar un código de vinculación desde tu perfil una vez hayas iniciado sesión)
             </Typography>
             {/* Comentado botón aquí porque requiere login previo */}
             {/*
             {!showInstructions ? (
               <Button
                 variant="contained"
                 color="primary"
                 onClick={generateLinkCode}
                 disabled={isGeneratingCode}
                 fullWidth
                 startIcon={isGeneratingCode ? <FontAwesomeIcon icon={faSpinner} spin /> : <FontAwesomeIcon icon={faLink} />}
               >
                 {isGeneratingCode ? 'Generando código...' : 'Generar código de vinculación'}
               </Button>
             ) : (
               <Box sx={{ mt: 2 }}>
                 // ... (instrucciones y código si se generó) ...
               </Box>
             )}
             */}
           </Box>
         </CardContent>
         <CardActions>
           <Typography variant="body2" align="center" sx={{ width: '100%' }}>
             <FontAwesomeIcon icon={faTelegram} /> También puedes interactuar con GymAI a través de nuestro <a href="https://t.me/RoonieColemAi_dev_bot" target="_blank" rel="noopener noreferrer">bot de Telegram</a>
           </Typography>
         </CardActions>
       </Card>
     </Box>
   );
}

export default Login;