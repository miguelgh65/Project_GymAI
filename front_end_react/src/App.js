// src/App.js
import React, { useState, useEffect, useCallback } from 'react';
// <<< ELIMINAR BrowserRouter de aquí >>>
// import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Routes, Route, Navigate } from 'react-router-dom'; // Mantener estos
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

  // Configurar axios (sin cambios)
  useEffect(() => {
    axios.defaults.withCredentials = true;
  }, []);

  // Función loadUser (sin cambios respecto a la versión anterior)
  const loadUser = useCallback(async () => {
    console.log("Intentando obtener datos del usuario...");
    try {
      const userData = await AuthService.getCurrentUser();
      console.log("Datos de usuario obtenidos en App.js:", userData);
      setUser(userData);
    } catch (error) {
      // console.error('Error cargando usuario en App.js:', error); // Puedes comentar si el log de AuthService es suficiente
      setUser(null);
    } finally {
      if (loading) setLoading(false);
    }
  }, [loading]);

  // useEffect para cargar usuario al inicio (sin cambios)
  useEffect(() => {
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // handleLogout (sin cambios)
  const handleLogout = () => {
    AuthService.logout().then(() => { setUser(null); });
  };

  // handleLoginSuccess (sin cambios)
  const handleLoginSuccess = useCallback(() => {
    console.log("Login exitoso reportado a App.js, recargando usuario...");
    loadUser();
  }, [loadUser]);


  if (loading && !user) {
    return <div className="loading">Cargando...</div>;
  }

  return (
    // <<< ELIMINAR el <Router> de aquí >>>
    // <Router>
      <div className="app-container">
        <Header user={user} onLogout={handleLogout} />
        <Routes> {/* Routes ahora funciona porque BrowserRouter está en index.js */}
          <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />
          <Route path="/profile" element={user ? <Profile /> : <Navigate to="/login" />} />
          <Route path="/" element={user ? <ExerciseForm user={user} /> : <Navigate to="/login" />} />
          <Route path="/chatbot" element={user ? <Chatbot user={user} /> : <Navigate to="/login" />} />
          <Route path="/rutina_hoy" element={user ? <TodayRoutine user={user} /> : <Navigate to="/login" />} />
          <Route path="/rutina" element={user ? <WeeklyRoutine user={user} /> : <Navigate to="/login" />} />
          <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/login" />} />
          <Route path="*" element={<Navigate to={user ? "/" : "/login"} replace />} />
        </Routes>
      </div>
    // </Router>
    // <<< FIN ELIMINAR el <Router> de aquí >>>
  );
}

export default App;