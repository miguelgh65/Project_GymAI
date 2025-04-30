// src/App.js - CORREGIDO para errores de build
import React, { useEffect, useState, useCallback } from 'react'; // Añadido useCallback
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom'; // Añadido useNavigate
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material'; // Importar Box si se usa
import theme from './theme';

// --- Components ---
import Header from './components/Header';
import Login from './components/Login';
import Dashboard from './components/Dashboard/Dashboard';
import Profile from './components/Profile';
import WeeklyRoutine from './components/WeeklyRoutine';
import TodayRoutine from './components/TodayRoutine';
import Chatbot from './components/Chatbot';
import ExerciseForm from './components/ExerciseForm';
import FitbitCallback from './components/profile/FitbitCallback'; // Callback Fitbit
// *** AÑADIDO: Importar NutritionPage ***
import NutritionPage from './components/nutrition/NutritionPage'; 
// *** AÑADIDO: Importar HomePage (si la creaste antes) ***
import HomePage from './components/HomePage'; // Asegúrate que la ruta sea correcta
// Importar MealPlanDetail si se usa
// import MealPlanDetail from './components/nutrition/meal-plans/MealPlanDetail'; 

// --- Services ---
import AuthService from './services/AuthService';

function App() {
  // Usar estado para saber si está autenticado en lugar de user directamente
  // Esto simplifica la lógica de protección de rutas
  const [isAuthenticated, setIsAuthenticated] = useState(AuthService.isAuthenticated());
  const [currentUser, setCurrentUser] = useState(null); // Guardar detalles del usuario si es necesario
  const [loading, setLoading] = useState(true);

  // Cargar usuario y verificar token al inicio
  useEffect(() => {
    let isMounted = true;
    const checkAuthAndLoadUser = async () => {
      setLoading(true);
      const token = AuthService.getToken();
      const userData = AuthService.getCurrentUser(); // Datos de localStorage

      if (token) {
        if (userData) {
           // Si hay token y datos locales, asumimos autenticado inicialmente
           // Podrías añadir una validación de token aquí si quieres más seguridad
           if(isMounted) {
             setIsAuthenticated(true);
             setCurrentUser(userData);
           }
        } else {
           // Si hay token pero no datos locales (raro), intentar validar token
           // (Podrías poner aquí la lógica de llamada a /api/current-user si la necesitas)
           // Si falla la validación -> logout
           // AuthService.logout();
           if (isMounted) setIsAuthenticated(false);
        }
      } else {
        // No hay token
        if (isMounted) setIsAuthenticated(false);
      }
      if (isMounted) setLoading(false);
    };

    checkAuthAndLoadUser();
    
    // Listener para cambios (si AuthService lo implementa)
    const handleAuthChange = () => {
      if(isMounted){
        setIsAuthenticated(AuthService.isAuthenticated());
        setCurrentUser(AuthService.getCurrentUser());
      }
    }
    window.addEventListener('authChange', handleAuthChange);

    return () => { 
      isMounted = false; 
      window.removeEventListener('authChange', handleAuthChange);
    };
  }, []);

  // --- Funciones de Autenticación ---
  const handleLoginSuccess = useCallback((userData) => {
    console.log("App: Login successful, updating state");
    setIsAuthenticated(true);
    setCurrentUser(userData); // Guardar detalles del usuario
    // No es necesario redirigir aquí, Navigate en la ruta /login lo hará
  }, []); // No depende de nada externo que cambie

  // *** AÑADIDO: Definición de handleLogout ***
  const handleLogout = useCallback(() => { // useCallback para pasarlo como prop estable
    console.log("App: Logging out user");
    AuthService.logout(); // Llama al servicio para limpiar token/localStorage
    setIsAuthenticated(false); // Actualiza el estado de autenticación
    setCurrentUser(null); // Limpiar datos de usuario
    // La redirección ocurrirá automáticamente por el cambio de estado y Navigate
  }, []); // No depende de nada externo que cambie

  // --- Renderizado ---

  if (loading) {
    // Puedes usar un componente CircularProgress de MUI aquí
    return <div className="loading">Cargando...</div>; 
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        {/* Renderizar Header solo si está autenticado */}
        {isAuthenticated && <Header user={currentUser} onLogout={handleLogout} />} 
        
        <Box 
           component="main" 
           sx={{ 
             flexGrow: 1, 
             // Aplicar padding solo si está autenticado y el Header está presente
             p: isAuthenticated ? 3 : 0, 
             // Aplicar margen superior solo si está autenticado y el Header está presente
             mt: isAuthenticated ? '64px' : 0 // Ajusta '64px' a la altura real de tu Header
            }}
          >
          <Routes>
            {/* Ruta de Login: solo accesible si NO está autenticado */}
            <Route 
              path="/login" 
              element={!isAuthenticated ? <Login onLoginSuccess={handleLoginSuccess} /> : <Navigate to="/" replace />} 
            />

            {/* Callback Fitbit: ruta pública */}
            <Route path="/fitbit-callback" element={<FitbitCallback />} />
            
            {/* --- Rutas Protegidas --- */}
            {/* Usamos un elemento ternario para proteger CADA ruta */}

            {/* Ruta Principal '/' (Nueva HomePage) */}
            <Route 
              path="/" 
              element={isAuthenticated ? <HomePage /> : <Navigate to="/login" replace />} 
            />

            {/* Ruta Registro Ejercicio */}
            <Route 
              path="/registrar" 
              element={isAuthenticated ? <ExerciseForm user={currentUser} /> : <Navigate to="/login" replace />} 
            />

            <Route 
              path="/dashboard" 
              element={isAuthenticated ? <Dashboard user={currentUser} /> : <Navigate to="/login" replace />} 
            />

            <Route 
              path="/profile" 
              element={isAuthenticated ? <Profile user={currentUser} /> : <Navigate to="/login" replace />} 
            />
             
            <Route 
              path="/rutina" // Cambiado de rutina-semanal a rutina si es la principal
              element={isAuthenticated ? <WeeklyRoutine user={currentUser} /> : <Navigate to="/login" replace />} 
            />
              
            <Route 
              path="/rutina-hoy" 
              element={isAuthenticated ? <TodayRoutine user={currentUser} /> : <Navigate to="/login" replace />} 
            />

            <Route 
              path="/chatbot" 
              element={isAuthenticated ? <Chatbot user={currentUser} /> : <Navigate to="/login" replace />} 
            />
            
            {/* Ruta de Nutrición (usa NutritionPage importado) */}
            <Route 
              path="/nutrition/*" // Permite sub-rutas dentro de NutritionPage
              element={isAuthenticated ? <NutritionPage user={currentUser} /> : <Navigate to="/login" replace />} 
            />
            
            {/* Ruta para el detalle del plan (si NutritionPage no la maneja internamente) */}
            {/* <Route 
              path="/nutrition/meal-plans/:planId" 
              element={isAuthenticated ? <MealPlanDetail /> : <Navigate to="/login" replace />} 
            /> 
            */}

            {/* Ruta Catch-all: redirige a home si está logueado, a login si no */}
            <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />

          </Routes>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;