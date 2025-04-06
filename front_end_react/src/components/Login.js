// Archivo: src/components/Login.js (con setTimeout)

import React, { useState, useEffect, useCallback } from 'react';
// Importar useNavigate
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardActions, Button, Typography, Box } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner, faLink, faCopy } from '@fortawesome/free-solid-svg-icons';
import { faTelegram } from '@fortawesome/free-brands-svg-icons';
import axios from 'axios';

// Recibir onLoginSuccess como prop
function Login({ onLoginSuccess }) {
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [linkCode, setLinkCode] = useState(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [googleClientId, setGoogleClientId] = useState('809764193714-h551ast9v2n4c7snp5e8sidja1bm995g.apps.googleusercontent.com'); // Reemplaza si es diferente
  const [isLoading, setIsLoading] = useState(false);

  // Obtener la función navigate
  const navigate = useNavigate();

  const handleGoogleCredentialResponse = useCallback(async (response) => {
    setIsLoading(true);
    console.log('Google auth response received:', response);
    try {
      const verifyResponse = await axios.post('/api/auth/google/verify', { // Ruta corregida
        id_token: response.credential,
        // telegram_id: linkCode // Pasa si es necesario
      });

      console.log('Verify response:', verifyResponse.data);

      if (verifyResponse.data.success) {
        console.log("Login verificado con éxito en backend.");

        // <<< INICIO: AÑADIR RETRASO >>>
        console.log("Esperando 150ms antes de proceder...");
        setTimeout(() => {
            console.log("Procediendo después de la espera...");
            // LLAMAR A LA FUNCIÓN DEL PADRE
            if (onLoginSuccess) {
                onLoginSuccess(); // Avisa a App.js para que recargue el usuario
            }
            // NAVEGAR SIN RECARGAR PÁGINA
            navigate('/'); // Redirige a la página principal usando React Router
            // Ya no necesitamos setIsLoading(false) aquí
        }, 150); // Esperar 150 milisegundos
        // <<< FIN: AÑADIR RETRASO >>>

      } else {
        alert(verifyResponse.data.message || 'Error al verificar con el servidor');
        setIsLoading(false); // Detener carga si hay error de verificación del backend
      }
    } catch (error) {
      console.error('Error durante Google Sign-In:', error);
      alert('Error al conectar con el servidor: ' + (error.response?.data?.detail || error.response?.data?.message || error.message));
      setIsLoading(false); // Detener carga si hay error de red/servidor
    }
    // No poner setIsLoading(false) aquí fuera del catch/else si el setTimeout se inicia
  }, [linkCode, navigate, onLoginSuccess]); // Dependencias correctas

  // initializeGoogleSignIn (sin cambios respecto a la versión anterior)
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
      const response = await axios.post('/api/generate-link-code');
      if (response.data.success) {
        setLinkCode(response.data.code);
        setShowInstructions(true);
      } else {
        alert(response.data.message || 'No se pudo generar el código (¿Estás logueado?)');
      }
    } catch (error) {
      console.error('Error generando código:', error);
      if (error.response?.status === 401) { alert('Debes iniciar sesión primero para generar un código de vinculación.'); }
      else { alert('Error al generar código de vinculación'); }
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


  // Renderizado JSX (sin cambios)
  return (
     <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' }}>
       <Card sx={{ maxWidth: 450, p: 3, borderRadius: 2, boxShadow: 3 }}>
         <CardContent>
           <Typography variant="h5" align="center" gutterBottom> Accede a tu cuenta </Typography>
           <Typography variant="body2" align="center" gutterBottom> Inicia sesión para acceder a todas las funciones </Typography>
           {isLoading ? ( <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}> <FontAwesomeIcon icon={faSpinner} spin size="2x" /> </Box> ) : ( <Box id="google-login-btn" sx={{ my: 2 }}></Box> )}
           <Box sx={{ mt: 3 }}>
             <Typography variant="h6" gutterBottom> Vincular cuenta de Telegram </Typography>
             {!showInstructions ? ( <Button variant="contained" color="primary" onClick={generateLinkCode} disabled={isGeneratingCode} fullWidth startIcon={isGeneratingCode ? <FontAwesomeIcon icon={faSpinner} spin /> : <FontAwesomeIcon icon={faLink} />}> {isGeneratingCode ? 'Generando código...' : 'Generar código de vinculación'} </Button> ) : ( <Box sx={{ mt: 2 }}> <Typography variant="body2"> Sigue estos pasos: </Typography> <ol style={{ textAlign: 'left', paddingLeft: '1rem' }}> <li>Abre nuestro <a href="https://t.me/RoonieColemAi_dev_bot" target="_blank" rel="noopener noreferrer">bot de Telegram</a></li> <li>Envía el comando <code>/vincular</code> al bot</li> <li>Cuando el bot lo solicite, envía este código:</li> </ol> <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', my: 1 }}> <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{linkCode}</Typography> <Button onClick={copyCodeToClipboard} sx={{ ml: 1 }} variant="outlined"> <FontAwesomeIcon icon={faCopy} /> </Button> </Box> <Typography variant="caption" color="textSecondary"> El código expira en 10 minutos </Typography> </Box> )}
           </Box>
         </CardContent>
         <CardActions> <Typography variant="body2" align="center" sx={{ width: '100%' }}> <FontAwesomeIcon icon={faTelegram} /> También puedes interactuar con GymAI a través de nuestro <a href="https://t.me/RoonieColemAi_dev_bot" target="_blank" rel="noopener noreferrer">bot de Telegram</a> </Typography> </CardActions>
       </Card>
     </Box>
   );
}

export default Login;