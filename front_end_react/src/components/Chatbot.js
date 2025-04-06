import React, { useState, useEffect, useRef } from 'react';
import {
  Card, CardContent, CardHeader, CardActions, TextField, Button, Box,
  Typography, CircularProgress, Stack, Paper, Alert // Añadido Alert
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRobot, faPaperPlane, faSpinner, faLightbulb, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons'; // Añadido faExclamationTriangle
import axios from 'axios'; // Asegúrate que axios está importado
import { styled } from '@mui/material/styles';

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
  const chatContainerRef = useRef(null);

  const suggestions = [
    '¿Cuál es mi entrenamiento para hoy?',
    'Muestra mis últimos ejercicios',
    'Necesito ayuda con mi rutina',
    'Dame consejos de nutrición'
  ];

  // Scroll automático al final del chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]); // Ejecutar cuando cambian los mensajes o el estado de escritura

  const sendMessage = async (messageText) => {
    const trimmedMessage = messageText.trim();
    if (!trimmedMessage || !user) return; // No enviar si está vacío o no hay usuario

    const userMessage = { role: 'user', content: trimmedMessage };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // *** CAMBIO AQUÍ: Añadir /api/ ***
      const response = await axios.post('/api/chatbot/send', {
        // user_id ya se obtiene del lado del servidor a través de la cookie/dependencia
        message: trimmedMessage
      });
      // *** FIN CAMBIO ***

      let responsesToAdd = [];
      if (response.data.success && response.data.responses) {
         responsesToAdd = Array.isArray(response.data.responses)
             ? response.data.responses.map(msg => ({
                 role: msg.role === 'tool' ? 'system' : (msg.role || 'assistant'),
                 content: msg.content
             }))
             : [{ role: 'assistant', content: response.data.responses }]; // Caso de respuesta simple
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
            <Typography variant="h5" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
               <FontAwesomeIcon icon={faRobot} style={{ marginRight: 8 }} /> Entrenador Personal AI
            </Typography>
          }
          sx={{ backgroundColor: '#007bff', color: 'white' }}
        />
        <ChatMessagesContainer ref={chatContainerRef}>
            {messages.map((message, index) => (
              <MessageBubble key={index} ownerState={{ role: message.role }}>
                 {formatMessageContent(message.content)}
              </MessageBubble>
            ))}
            {isTyping && (
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