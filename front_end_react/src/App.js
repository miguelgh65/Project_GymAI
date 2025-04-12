// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// --- Imports de Componentes (Rutas relativas desde src/) ---
import Header from './components/Header';
import Login from './components/Login';
import Profile from './components/Profile';
import ExerciseForm from './components/ExerciseForm';
import Chatbot from './components/Chatbot';
import TodayRoutine from './components/TodayRoutine';
import WeeklyRoutine from './components/WeeklyRoutine';
import Dashboard from './components/Dashboard/Dashboard';
// --- Import de la "Página" de Nutrición (Ubicada ahora en components/nutrition) ---
import NutritionPage from './components/nutrition/NutritionPage'; // <-- RUTA CORREGIDA

// --- Import del Servicio de Autenticación ---
import AuthService from './services/AuthService'; // <-- RUTA CORREGIDA

// --- Imports de Material UI ---
import { Box, CircularProgress, Typography } from '@mui/material';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const savedUser = AuthService.getCurrentUser();
        if (savedUser) {
          setUser(savedUser);
        } else {
          setUser(null);
          AuthService.logout();
        }
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Error cargando usuario:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    AuthService.logout();
    setUser(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100vh', bgcolor: 'background.default' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 3 }}>Cargando GymAI...</Typography>
      </Box>
    );
  }

  return (
    <Router>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
        <Header user={user} onLogout={handleLogout} />
        <Box component="main" sx={{ flexGrow: 1, p: { xs: 1, sm: 2, md: 3 }, width: '100%', maxWidth: '1200px', mx: 'auto' }}>
          <Routes>
            {/* Login público */}
            <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login onLoginSuccess={handleLoginSuccess} />} />

            {/* Rutas protegidas */}
            <Route path="/" element={user ? <ExerciseForm user={user} /> : <Navigate to="/login" replace />} />
            <Route path="/profile" element={user ? <Profile user={user} /> : <Navigate to="/login" replace />} />
            <Route path="/chatbot" element={user ? <Chatbot user={user} /> : <Navigate to="/login" replace />} />
            <Route path="/rutina_hoy" element={user ? <TodayRoutine user={user} /> : <Navigate to="/login" replace />} />
            <Route path="/rutina" element={user ? <WeeklyRoutine user={user} /> : <Navigate to="/login" replace />} />
            <Route path="/dashboard" element={user ? <Dashboard user={user} /> : <Navigate to="/login" replace />} />

            {/* --- RUTA PARA NUTRICIÓN (con import corregido a components/nutrition) --- */}
            <Route path="/nutrition" element={user ? <NutritionPage user={user} /> : <Navigate to="/login" replace />} />
            {/* --------------------------------------------------------------------- */}

            {/* Catch-all */}
            <Route path="*" element={<Navigate to={user ? "/" : "/login"} replace />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
}

export default App;