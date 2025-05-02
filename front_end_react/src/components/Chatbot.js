import React, { useState, useEffect, useRef } from 'react';
import {
  Card, CardContent, CardHeader, CardActions, TextField, Button, Box,
  Typography, CircularProgress, Stack, Paper, Alert, FormControlLabel, Switch
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRobot, faPaperPlane, faSpinner, faLightbulb, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';
import { styled } from '@mui/material/styles';
import AuthService from '../services/AuthService'; // Importar AuthService directamente

// --- Estilos (sin cambios) ---
const ChatMessagesContainer = styled(CardContent)(({ theme }) => ({
  height: '400px',
  overflowY: 'auto',
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius + 'px',
  padding: theme.spacing(2),
  backgroundColor: theme.palette.grey[100],
  display: 'flex',
  flexDirection: 'column',
}));

const MessageBubble = styled(Paper)(({ theme, ownerState }) => ({
  padding: theme.spacing(1.25, 1.875),
  borderRadius: '18px',
  marginBottom: theme.spacing(1.25),
  maxWidth: '80%',
  wordBreak: 'break-word',
  alignSelf: ownerState.role === 'user' ? 'flex-end' : 'flex-start',
  backgroundColor: ownerState.role === 'user'
    ? '#007bff'
    : (ownerState.role === 'system'
        ? '#ffc107' // Amarillo para mensajes del sistema
        : '#e9ecef'), // Gris para mensajes del bot/asistente
  color: ownerState.role === 'user'
    ? theme.palette.common.white
    : theme.palette.text.primary,
  elevation: 1, // Sombra ligera
}));

const TypingIndicator = styled('span')({
  '& span': { animation: 'blink 1.4s infinite both', display: 'inline-block' },
  '& span:nth-of-type(2)': { animationDelay: '0.2s' },
  '& span:nth-of-type(3)': { animationDelay: '0.4s' },
  '@keyframes blink': { '0%': { opacity: 0.2 }, '20%': { opacity: 1 }, '100%': { opacity: 0.2 } },
});
// --- Fin Estilos ---

function Chatbot({ user }) {
  const [messages, setMessages] = useState([
    {
      role: 'system', // Usar 'system' para mensajes iniciales o informativos
      content: '¡Hola! Soy tu entrenador personal AI. ¿En qué puedo ayudarte hoy?'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true); // Por defecto activado
  const chatContainerRef = useRef(null);
  const abortControllerRef = useRef(null);

  const suggestions = [
    '¿Cuál es mi entrenamiento para hoy?',
    'Muestra mis últimos ejercicios',
    'Necesito ayuda con mi rutina',
    'Dame consejos de nutrición'
  ];

  // DIAGNÓSTICO DE AUTENTICACIÓN movido dentro del componente
  useEffect(() => {
    // Verificar token disponible en diferentes ubicaciones
    const localStorageToken = localStorage.getItem('access_token');
    console.log('Token en localStorage:', localStorageToken ? `${localStorageToken.substring(0, 15)}...` : 'NO DISPONIBLE');
    
    // Verificar cookies
    const cookies = document.cookie.split('; ');
    const tokenCookie = cookies.find(cookie => cookie.startsWith('access_token='));
    console.log('Token en cookies:', tokenCookie ? `${tokenCookie.substring(12, 27)}...` : 'NO DISPONIBLE');
    
    // Verificar objeto de usuario
    console.log('Objeto user recibido como prop:', user);
    
    // Verificar si podemos obtener el token mediante AuthService
    try {
      const token = AuthService.getToken();
      console.log('Token obtenido desde AuthService:', token ? `${token.substring(0, 15)}...` : 'NO DISPONIBLE');
    } catch (e) {
      console.error('Error al obtener token desde AuthService:', e);
    }
    
    // Verificar login usando AuthService
    console.log('¿Autenticado según AuthService?', AuthService.isAuthenticated());
    console.log('Usuario según AuthService:', AuthService.getCurrentUser());
    
    // Hacer una llamada de prueba usando axios (debería usar el interceptor)
    axios.get('/api')
      .then(response => {
        console.log('Prueba de axios exitosa:', response.data);
        // Verificar si podemos ver los headers en la petición
        console.log('Config de la petición:', response.config);
      })
      .catch(error => {
        console.error('Error en prueba de axios:', error);
      });
  }, [user]); // Añadir user como dependencia

  // Limpiar controlador al desmontar
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Scroll automático al final del chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Método sin streaming (corrección final usando axios estándar)
  const sendMessageNormal = async (messageText) => {
    const trimmedMessage = messageText.trim();
    if (!trimmedMessage || !user) return;

    const userMessage = { role: 'user', content: trimmedMessage };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // No necesitas incluir el token manualmente aquí, el interceptor de axios lo hace automáticamente
      // axios.interceptors.request.use ya añade el token a todas las solicitudes axios
      const response = await axios.post('/api/chatbot/send', {
        message: trimmedMessage,
        stream: false
      });

      console.log("Respuesta del servidor:", response.data);

      let responsesToAdd = [];
      if (response.data.success && response.data.responses) {
         responsesToAdd = Array.isArray(response.data.responses)
             ? response.data.responses.map(msg => ({
                 role: msg.role === 'tool' ? 'system' : (msg.role || 'assistant'),
                 content: msg.content
             }))
             : [{ role: 'assistant', content: response.data.responses }];
      } else {
        responsesToAdd = [{ role: 'assistant', content: response.data.message || 'Lo siento, ocurrió un error al procesar tu mensaje.' }];
      }
       setMessages(prevMessages => [...prevMessages, ...responsesToAdd]);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || 'Lo siento, no pude conectarme con el servidor.';
      setMessages(prevMessages => [
        ...prevMessages,
        { role: 'assistant', content: errorMsg }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  // Método con streaming mejorado (corrección final usando la misma lógica de autenticación)
  const sendMessageStreaming = async (messageText) => {
    const trimmedMessage = messageText.trim();
    if (!trimmedMessage || !user) return;

    // Agregar mensaje del usuario
    const userMessage = { role: 'user', content: trimmedMessage };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Crear mensaje temporal del asistente
    const tempMessageId = Date.now();
    setMessages(prevMessages => [
      ...prevMessages,
      { role: 'assistant', content: '', id: tempMessageId, isStreaming: true }
    ]);

    try {
      // Cancelar cualquier stream anterior
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Crear nuevo controlador
      const controller = new AbortController();
      abortControllerRef.current = controller;

      // Obtener el token usando AuthService
      // Esta es la misma lógica que usa el interceptor de axios en tu aplicación
      const token = AuthService.getToken();
      console.log("Token para streaming:", token ? "Presente" : "No encontrado");

      // Llamada para obtener el stream con los headers correctos
      const response = await fetch('/api/chatbot/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Authorization': `Bearer ${token}` // Usa token del AuthService
        },
        body: JSON.stringify({ 
          message: trimmedMessage,
          stream: true 
        }),
        credentials: 'include',
        signal: controller.signal
      });

      if (!response.ok) {
        console.error(`Error HTTP: ${response.status}`);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Procesar el stream utilizando ReadableStream
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedContent = '';

      // Loop para leer el stream
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log("Stream completado");
          break;
        }

        // Decodificar y añadir al buffer
        buffer += decoder.decode(value, { stream: true });
        
        // Procesar eventos SSE (data: {...}\n\n)
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Guardar la última línea incompleta

        // Procesar cada evento SSE completo
        for (const line of lines) {
          if (line.startsWith('data:')) {
            try {
              // Limpiar y parsear el JSON
              const jsonStr = line.substring(5).trim();
              if (!jsonStr) continue;
              
              const data = JSON.parse(jsonStr);
              
              // Actualizar el contenido acumulado
              if (data.content !== undefined) {
                accumulatedContent = data.content;
                
                // Actualizar el mensaje en tiempo real
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === tempMessageId 
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  )
                );
              }
              
              // Verificar si hay errores
              if (data.error) {
                throw new Error(data.error);
              }
              
              // Verificar si está completo
              if (data.done) {
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === tempMessageId 
                      ? { ...msg, isStreaming: false }
                      : msg
                  )
                );
              }
            } catch (e) {
              console.error('Error processing SSE:', e, line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      
      // No mostrar error si fue cancelación intencional
      if (error.name !== 'AbortError') {
        setMessages(prev => 
          prev.map(msg => 
            msg.id === tempMessageId 
              ? { ...msg, content: 'Error de conexión. Por favor, inténtalo de nuevo.', isStreaming: false }
              : msg
          )
        );
      }
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  };

  // Método unificado para enviar mensaje
  const sendMessage = async (messageText) => {
    if (useStreaming) {
      await sendMessageStreaming(messageText);
    } else {
      await sendMessageNormal(messageText);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  // Formateador de contenido (sin cambios)
  const formatMessageContent = (content) => {
    if (typeof content !== 'string') return <Typography variant="body1" component="span">{JSON.stringify(content)}</Typography>;
    if (content.trim().startsWith('{') && content.trim().endsWith('}')) {
        try {
            const jsonData = JSON.parse(content);
            return <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.875rem' }}>{JSON.stringify(jsonData, null, 2)}</pre>;
        } catch (e) { /* fallback to text */ }
    }
    let formattedText = content.replace(/\*(.*?)\*/g, '<strong>$1</strong>');
    formattedText = formattedText.replace(/- (.*?)(?=\n|$)/g, '• $1<br>');
    return <Typography variant="body1" component="span" dangerouslySetInnerHTML={{ __html: formattedText }} />;
  };

  // Renderizado del componente
  if (!user) {
      return (
         <Box sx={{ m: 2 }}>
            <Alert severity="warning">Debes iniciar sesión para usar el chatbot.</Alert>
         </Box>
      );
  }

  return (
    <Box sx={{ m: 2 }}>
      {/* Card principal del Chat */}
      <Card elevation={3} sx={{ mb: 3 }}>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
              <Typography variant="h5" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
                <FontAwesomeIcon icon={faRobot} style={{ marginRight: 8 }} /> Entrenador Personal AI
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={useStreaming}
                    onChange={(e) => setUseStreaming(e.target.checked)}
                    color="default"
                    size="small"
                  />
                }
                label={<Typography variant="caption" sx={{ color: 'white' }}>Streaming</Typography>}
              />
            </Box>
          }
          sx={{ backgroundColor: '#007bff', color: 'white' }}
        />
        <ChatMessagesContainer ref={chatContainerRef}>
            {messages.map((message, index) => (
              <MessageBubble key={index} ownerState={{ role: message.role }}>
                {message.isStreaming && message.content === '' ? (
                  <TypingIndicator>
                    Escribiendo<span>.</span><span>.</span><span>.</span>
                  </TypingIndicator>
                ) : (
                  formatMessageContent(message.content)
                )}
              </MessageBubble>
            ))}
            {isTyping && !messages.some(m => m.isStreaming) && (
               <MessageBubble ownerState={{ role: 'assistant' }}>
                  <TypingIndicator>
                    Escribiendo<span>.</span><span>.</span><span>.</span>
                  </TypingIndicator>
               </MessageBubble>
            )}
        </ChatMessagesContainer>
        <CardActions sx={{ p: 2, backgroundColor: 'background.paper' }}>
           <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                placeholder="Escribe tu mensaje aquí..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={isTyping}
                variant="outlined"
                size="small"
                aria-label="Entrada de mensaje del chat"
              />
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={isTyping || !inputMessage.trim()}
                sx={{ minWidth: 'auto', px: 1.5 }}
                aria-label="Enviar mensaje"
              >
                {isTyping
                   ? <CircularProgress size={20} color="inherit" />
                   : <FontAwesomeIcon icon={faPaperPlane} />}
              </Button>
           </Box>
        </CardActions>
      </Card>

      {/* Card de Sugerencias */}
      <Card elevation={3}>
        <CardHeader
          title={
            <Typography variant="h5" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
               <FontAwesomeIcon icon={faLightbulb} style={{ marginRight: 8 }} /> Sugerencias
            </Typography>
          }
          sx={{ backgroundColor: '#17a2b8', color: 'white' }}
        />
        <CardContent>
           <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outlined"
                  color="primary"
                  onClick={() => handleSuggestionClick(suggestion)}
                  size="small"
                  sx={{ borderRadius: '20px', textTransform: 'none' }} // Sin mayúsculas
                >
                  {suggestion}
                </Button>
              ))}
           </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Chatbot;