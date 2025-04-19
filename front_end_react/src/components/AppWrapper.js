// src/components/AppWrapper.js
// ****** ARCHIVO CORREGIDO (Versión Guardián de Rutas) ******

import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom'; // Necesitamos Navigate y useLocation
import AuthService from '../services/AuthService';
import axios from 'axios'; // Mantenemos axios por si se usa para validar token

// Importar un componente de carga (opcional, pero bueno tenerlo)
import { Box, CircularProgress } from '@mui/material';

// Componente Guardián: recibe la ruta hija como 'children'
const AppWrapper = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(AuthService.isAuthenticated());
  const [loading, setLoading] = useState(true); // Empezar cargando
  const location = useLocation(); // Para redirigir de vuelta después del login

  useEffect(() => {
    let isMounted = true; // Para evitar actualizaciones en componente desmontado

    const checkAuth = async () => {
      setLoading(true);
      const token = AuthService.getToken();
      let authStatus = false;

      if (token) {
        // Opcional: Validar token con el backend aquí si quieres más seguridad
        // Si la validación falla, AuthService.logout() y authStatus = false
        // Por ahora, asumimos que si hay token, está autenticado inicialmente
         authStatus = true;
         // Ejemplo de validación (descomentar y adaptar si es necesario):
         /*
         try {
           await axios.get('/api/current-user'); // O la ruta de validación que tengas
           authStatus = true;
         } catch (error) {
           console.error("AppWrapper: Falló validación de token", error);
           AuthService.logout();
           authStatus = false;
         }
         */
      } else {
        authStatus = false;
      }

      if (isMounted) {
        setIsAuthenticated(authStatus);
        setLoading(false);
      }
    };

    checkAuth();

    // Listener para cambios de autenticación (si AuthService lo implementa)
    const handleAuthChange = () => {
        if (isMounted) {
            setIsAuthenticated(AuthService.isAuthenticated());
        }
    }
    window.addEventListener('authChange', handleAuthChange);

    return () => {
      isMounted = false; // Cleanup
      window.removeEventListener('authChange', handleAuthChange);
    };
  }, [location]); // Volver a comprobar si cambia la ruta (puede ser redundante)

  // Mientras se comprueba la autenticación, mostrar un loader
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="calc(100vh - 64px)">
        <CircularProgress />
      </Box>
    );
  }

  // Si está autenticado, renderiza el componente hijo (la ruta protegida)
  if (isAuthenticated) {
    return children;
  }

  // Si no está autenticado, redirige a la página de login
  // state={{ from: location }} permite redirigir de vuelta después del login
  return <Navigate to="/login" state={{ from: location }} replace />;
};

export default AppWrapper;