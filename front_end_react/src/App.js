// src/App.js - Add Fitbit callback route
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
import FitbitCallback from './components/profile/FitbitCallback'; // Import the new component

// Services
import AuthService from './services/AuthService';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      try {
        console.log("App: Checking authentication status...");
        const userData = AuthService.getCurrentUser();
        const token = AuthService.getToken();
        
        if (userData && token) {
          console.log("App: User is logged in", userData.display_name || userData.email);
          setUser(userData);
        } else {
          console.log("App: No user is logged in");
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
  const handleLogin = (userData) => {
    console.log("App: Login successful, updating user state", userData);
    setUser(userData);
  };

  const handleLogout = async () => {
    try {
      console.log("App: Logging out user");
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
          {user && <Header user={user} onLogout={handleLogout} />}
          <main className="main-content">
            <Routes>
              <Route path="/login" element={!user ? <Login onLoginSuccess={handleLogin} /> : <Navigate to="/" />} />
              
              <Route path="/" element={user ? <ExerciseForm user={user} /> : <Navigate to="/login" />} />
              
              <Route path="/dashboard" element={user ? <Dashboard user={user} /> : <Navigate to="/login" />} />
              
              <Route path="/profile" element={user ? <Profile user={user} /> : <Navigate to="/login" />} />
              
              <Route path="/rutina" element={user ? <WeeklyRoutine user={user} /> : <Navigate to="/login" />} />
              
              <Route path="/rutina_hoy" element={user ? <TodayRoutine user={user} /> : <Navigate to="/login" />} />
              
              <Route path="/chatbot" element={user ? <Chatbot user={user} /> : <Navigate to="/login" />} />
              
              <Route path="/nutrition" element={user ? <NutritionPage user={user} /> : <Navigate to="/login" />} />
              
              {/* Add the Fitbit callback route - this needs to be public */}
              <Route path="/fitbit-callback" element={<FitbitCallback />} />
              
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