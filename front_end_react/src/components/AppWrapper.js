import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './Header';
import Login from './Login';
import Profile from './Profile';
import ExerciseForm from './ExerciseForm';
import Chatbot from './Chatbot';
import TodayRoutine from './TodayRoutine';
import WeeklyRoutine from './WeeklyRoutine';
import AuthService from '../services/AuthService';

function AppWrapper() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Función para cargar datos de usuario
  // En AppWrapper.js - modificar la carga del usuario

// Función para cargar datos de usuario
const loadUser = async () => {
  setLoading(true);
  try {
    // Usar el servicio de autenticación para obtener el usuario desde localStorage
    const userData = AuthService.getCurrentUser();
    setUser(userData);
    
    // Si no hay usuario en localStorage pero hay token, intentar obtener el usuario
    if (!userData && AuthService.getToken()) {
      try {
        // Opcional: Hacer una solicitud para validar el token y obtener datos actualizados
        const response = await axios.get('/api/current-user');
        if (response.data.success && response.data.user) {
          setUser(response.data.user);
          localStorage.setItem('user', JSON.stringify(response.data.user));
        }
      } catch (err) {
        // Si hay un error, probablemente el token es inválido
        AuthService.logout();
      }
    }
  } catch (error) {
    console.error('Error cargando usuario:', error);
    setUser(null);
  } finally {
    setLoading(false);
  }
};

// Manejador de logout para actualizar el estado
const handleLogout = () => {
  AuthService.logout();
  setUser(null);
};

  return (
    <Router>
      <div className="app-container">
        {/* Pasa el usuario y la función de logout */}
        <Header user={user} onLogout={handleLogout} />
        
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Cargando...</p>
          </div>
        ) : (
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/profile" element={<Profile user={user} />} />
            <Route path="/" element={<ExerciseForm user={user} />} />
            <Route path="/chatbot" element={<Chatbot user={user} />} />
            <Route path="/rutina_hoy" element={<TodayRoutine user={user} />} />
            <Route path="/rutina" element={<WeeklyRoutine user={user} />} />
            {/* Agregar aquí las demás rutas */}
          </Routes>
        )}
      </div>
    </Router>
  );
}

export default AppWrapper;
