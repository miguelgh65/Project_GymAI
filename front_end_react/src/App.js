import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';

// Components
import Header from './components/Header';
import Login from './components/Login';
import Dashboard from './components/Dashboard/Dashboard';
import Profile from './components/Profile';
import WeeklyRoutine from './components/WeeklyRoutine';
import TodayRoutine from './components/TodayRoutine';
import Chatbot from './components/Chatbot';
import ExerciseForm from './components/ExerciseForm';
import NutritionPage from './components/nutrition/NutritionPage';

// Services
import AuthService from './services/AuthService';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      try {
        const userData = await AuthService.getCurrentUser();
        if (userData) {
          setUser(userData);
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Auth-related functions
  const login = (userData) => {
    setUser(userData);
  };

  const logout = async () => {
    try {
      await AuthService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (loading) {
    return <div className="loading">Cargando...</div>;
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="app">
          {user && <Header user={user} onLogout={logout} />}
          <main className="main-content">
            <Routes>
              <Route path="/login" element={!user ? <Login onLogin={login} /> : <Navigate to="/" />} />
              
              <Route path="/" element={user ? <ExerciseForm /> : <Navigate to="/login" />} />
              
              <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/login" />} />
              
              <Route path="/profile" element={user ? <Profile user={user} /> : <Navigate to="/login" />} />
              
              <Route path="/rutina" element={user ? <WeeklyRoutine /> : <Navigate to="/login" />} />
              
              <Route path="/rutina_hoy" element={user ? <TodayRoutine /> : <Navigate to="/login" />} />
              
              <Route path="/chatbot" element={user ? <Chatbot /> : <Navigate to="/login" />} />
              
              {/* Add the Nutrition route */}
              <Route path="/nutrition" element={user ? <NutritionPage /> : <Navigate to="/login" />} />
              
              {/* Redirect to home if no route matches */}
              <Route path="*" element={<Navigate to={user ? "/" : "/login"} />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;