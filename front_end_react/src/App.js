// src/AppWrapper.js o src/App.js (dependiendo de tu estructura)
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Login from './components/Login';
import Profile from './components/Profile';
import ExerciseForm from './components/ExerciseForm';
import Chatbot from './components/Chatbot';
import TodayRoutine from './components/TodayRoutine';
import WeeklyRoutine from './components/WeeklyRoutine';
import AuthService from './services/AuthService';
import Dashboard from './components/Dashboard/Dashboard';
import { Box, CircularProgress, Typography } from '@mui/material';

function AppWrapper() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);

  // Función para cargar datos de usuario
  const loadUser = async () => {
    setLoading(true);
    try {
      // Verificar si hay un token en localStorage
      const token = localStorage.getItem('access_token');
      if (token) {
        // Intentar cargar el usuario de localStorage primero
        const savedUser = AuthService.getCurrentUser();
        if (savedUser) {
          setUser(savedUser);
          console.log("Usuario cargado desde localStorage:", savedUser);
        }
      } else {
        setUser(null);
        console.log("No hay token almacenado, usuario no autenticado");
      }
    } catch (error) {
      console.error('Error cargando usuario:', error);
      setUser(null);
    } finally {
      setLoading(false);
      setAuthChecked(true);
    }
  };

  // Cargar usuario al iniciar
  useEffect(() => {
    loadUser();
  }, []);

  // Manejador de login para actualizar el estado
  const handleLoginSuccess = (userData) => {
    console.log("Login exitoso, actualizando estado de usuario:", userData);
    setUser(userData);
  };

  // Manejador de logout para actualizar el estado
  const handleLogout = () => {
    console.log("Logout ejecutado, limpiando estado de usuario");
    AuthService.logout();
    setUser(null);
  };

  // Pantalla de carga mientras verifica el estado de autenticación
  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          bgcolor: '#f5f5f5'
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 3 }}>
          Cargando GymAI...
        </Typography>
      </Box>
    );
  }

  return (
    <Router>
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        minHeight: '100vh',
        bgcolor: '#f5f5f5'
      }}>
        {/* Header siempre visible */}
        <Header user={user} onLogout={handleLogout} />
        
        {/* Contenido principal */}
        <Box 
          component="main" 
          sx={{ 
            flexGrow: 1, 
            p: { xs: 1, sm: 2, md: 3 },
            width: '100%',
            maxWidth: '1200px',
            mx: 'auto'
          }}
        >
          <Routes>
            {/* Ruta protegida por defecto */}
            <Route path="/" element={
              <ExerciseForm user={user} />
            } />
            
            {/* Ruta de login pública */}
            <Route path="/login" element={
              user ? <Navigate to="/" /> : <Login onLoginSuccess={handleLoginSuccess} />
            } />
            
            {/* Otras rutas protegidas */}
            <Route path="/profile" element={<Profile user={user} />} />
            <Route path="/chatbot" element={<Chatbot user={user} />} />
            <Route path="/rutina_hoy" element={<TodayRoutine user={user} />} />
            <Route path="/rutina" element={<WeeklyRoutine user={user} />} />
            <Route path="/dashboard" element={<Dashboard user={user} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
}

export default AppWrapper;