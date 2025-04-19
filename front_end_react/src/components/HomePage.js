// src/components/HomePage.js
import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Paper, Grid, Button } from '@mui/material';
import { keyframes } from '@mui/system';
import { Link as RouterLink } from 'react-router-dom'; // Para enlaces internos

// Importar los assets (asegúrate que las rutas sean correctas)
import cb1 from '../assets/cb1.png';
import cb2 from '../assets/cb2.png';
import cb3 from '../assets/cb3.png';
import r1 from '../assets/r1.png';
import r2 from '../assets/r2.png';
import r3 from '../assets/r3.png';

// Arrays de imágenes
const cbImages = [cb1, cb2, cb3];
const rImages = [r1, r2, r3];

// Función para obtener un elemento aleatorio de un array
const getRandomItem = (arr) => arr[Math.floor(Math.random() * arr.length)];

// Animación simple para las imágenes (opcional)
const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

const HomePage = () => {
  const [selectedCbImage, setSelectedCbImage] = useState(null);
  const [selectedRImage, setSelectedRImage] = useState(null);

  useEffect(() => {
    // Seleccionar imágenes aleatorias al montar el componente
    setSelectedCbImage(getRandomItem(cbImages));
    setSelectedRImage(getRandomItem(rImages));
  }, []); // El array vacío asegura que se ejecute solo una vez

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper 
        elevation={4} 
        sx={{ 
          p: { xs: 3, md: 5 }, 
          borderRadius: 3, 
          // background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' // Un fondo suave
          // O un fondo más oscuro si tu tema es oscuro:
           background: (theme) => theme.palette.mode === 'dark' 
             ? 'linear-gradient(135deg, #2d3748 0%, #1a202c 100%)' 
             : 'linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%)', // Gradiente azul claro
           color: (theme) => theme.palette.mode === 'dark' ? '#fff' : '#004d40', // Texto oscuro sobre fondo claro
        }}
      >
        <Grid container spacing={4} alignItems="center">
          
          {/* Columna de Texto */}
          <Grid item xs={12} md={7}>
            <Typography 
              variant="h2" 
              component="h1" 
              gutterBottom 
              sx={{ 
                fontWeight: 'bold', 
                // color: '#1976d2', // Color primario del tema
                color: 'inherit', // Heredar color del Paper
                textShadow: '1px 1px 3px rgba(0,0,0,0.1)',
                mb: 3,
              }}
            >
              Bienvenido a GymAI
            </Typography>
            <Typography 
              variant="h5" 
              component="p" 
              paragraph 
              sx={{ 
                // color: '#555',
                color: 'inherit',
                opacity: 0.9,
                lineHeight: 1.7,
                 mb: 4,
              }}
            >
              Tu compañero inteligente para el gimnasio. Registra tus entrenamientos,
              planifica tu nutrición y sigue tu progreso, todo con la ayuda de la IA.
              ¡Empieza a transformar tu físico hoy!
            </Typography>
            <Box>
               <Button 
                  variant="contained" 
                  color="primary" 
                  size="large" 
                  component={RouterLink} 
                  to="/registrar" // Enlace a la nueva ruta de registro
                  sx={{ mr: 2, mb: { xs: 2, md: 0 } }}
               >
                  Registrar Entrenamiento
               </Button>
               <Button 
                  variant="outlined" 
                  color="secondary" 
                  size="large"
                  component={RouterLink} 
                  to="/dashboard" // O a donde quieras dirigir
               >
                  Ver Mi Progreso
               </Button>
            </Box>
          </Grid>

          {/* Columna de Imágenes */}
          <Grid item xs={12} md={5} sx={{ textAlign: 'center' }}>
            {selectedRImage && (
              <Box
                component="img"
                src={selectedRImage}
                alt="Imagen aleatoria rutina"
                sx={{
                  maxWidth: '80%',
                  height: 'auto',
                  borderRadius: '12px',
                  boxShadow: 6,
                  mb: 3,
                  animation: `${fadeIn} 0.8s ease-out`,
                }}
              />
            )}
            {selectedCbImage && (
              <Box
                component="img"
                src={selectedCbImage}
                alt="Imagen aleatoria chatbot"
                sx={{
                  maxWidth: '60%',
                  height: 'auto',
                  borderRadius: '12px',
                  boxShadow: 3,
                  opacity: 0.9,
                  animation: `${fadeIn} 1s ease-out 0.2s`, // Delay ligero
                  animationFillMode: 'backwards', // Para que empiece invisible antes del delay
                }}
              />
            )}
          </Grid>

        </Grid>
      </Paper>
    </Container>
  );
};

export default HomePage;