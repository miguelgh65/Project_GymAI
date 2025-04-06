import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import Header from './components/Header';
import Login from './components/Login';
import ExerciseForm from './components/ExerciseForm';
import Chatbot from './components/Chatbot';
import Profile from './components/Profile';
import TodayRoutine from './components/TodayRoutine';
import WeeklyRoutine from './components/WeeklyRoutine';
import AuthService from './services/AuthService';
import Dashboard from './components/Dashboard/Dashboard';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Configurar axios para incluir credenciales
  useEffect(() => {
    axios.defaults.withCredentials = true;
  }, []);

  // Cargar datos del usuario actual
  const loadUser = useCallback(async () => {
    try {
      const response = await AuthService.getCurrentUser();
      console.log("Datos de usuario obtenidos:", response);
      
      // Asegúrate de que response tenga la estructura esperada
      if (response && response.user) {
        setUser(response.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Error cargando usuario:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Cargar usuario al inicio
  useEffect(() => {
    loadUser();
  }, [loadUser]);

  // Manejar cierre de sesión
  const handleLogout = async () => {
    try {
      await AuthService.logout();
      setUser(null);
    } catch (error) {
      console.error('Error en logout:', error);
    }
  };

  // Manejar inicio de sesión exitoso
  const handleLoginSuccess = useCallback((userData) => {
    console.log("Login exitoso, usuario recibido:", userData);
    setUser(userData);
  }, []);

  // Mostrar pantalla de carga inicial
  if (loading) {
    return <div className="loading">Cargando...</div>;
  }

  return (
    <div className="app-container">
      <Header user={user} onLogout={handleLogout} />
      <Routes>
        <Route 
          path="/login" 
          element={user ? <Navigate to="/" /> : <Login onLoginSuccess={handleLoginSuccess} />} 
        />
        <Route path="/profile" element={user ? <Profile user={user} /> : <Navigate to="/login" />} />
        <Route path="/" element={user ? <ExerciseForm user={user} /> : <Navigate to="/login" />} />
        <Route path="/chatbot" element={user ? <Chatbot user={user} /> : <Navigate to="/login" />} />
        <Route path="/rutina_hoy" element={user ? <TodayRoutine user={user} /> : <Navigate to="/login" />} />
        <Route path="/rutina" element={user ? <WeeklyRoutine user={user} /> : <Navigate to="/login" />} />
        <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to={user ? "/" : "/login"} replace />} />
      </Routes>
    </div>
  );
}

export default App;