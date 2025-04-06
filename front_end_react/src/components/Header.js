import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faDumbbell, 
  faSignInAlt, 
  faSignOutAlt, 
  faUserCircle,
  faRobot,
  faPlusCircle,
  faCalendarDay,
  faCalendarAlt,
  faChartLine,
  faUser
} from '@fortawesome/free-solid-svg-icons';
import AuthService from '../services/AuthService';

function Header({ user, onLogout }) {
  // En Header.js - función handleLogout
const handleLogout = async (e) => {
  e.preventDefault();
  
  console.log("Iniciando proceso de logout...");
  
  try {
    // Usar el servicio de autenticación
    AuthService.logout();
    
    // Notifica al componente padre
    if (typeof onLogout === 'function') {
      onLogout();
    }
    
    // Redirigir a la página de login
    window.location.href = '/login';
  } catch (error) {
    console.error('Error en proceso de logout:', error);
  }
};

  return (
    <header>
      <div className="header-container">
        <div className="site-branding">
          <h1>
            <FontAwesomeIcon icon={faDumbbell} /> RoonieColemAI
          </h1>
          <p className="subtitle">Sistema Inteligente de Entrenamiento Personalizado</p>
        </div>
        
        <div className="user-menu">
          {user ? (
            <div className="user-profile">
              {user.profile_picture ? (
                <img src={user.profile_picture} alt={user.display_name} className="user-avatar" />
              ) : (
                <FontAwesomeIcon icon={faUserCircle} className="user-avatar" />
              )}
              <span>{user.display_name}</span>
              {/* Botón de logout prominente y más visible */}
              <button 
                className="logout-btn" 
                title="Cerrar sesión" 
                onClick={handleLogout}
                style={{ 
                  marginLeft: '10px',
                  background: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '6px 12px',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
              >
                <FontAwesomeIcon icon={faSignOutAlt} style={{ marginRight: '6px' }} />
                <span>Cerrar Sesión</span>
              </button>
            </div>
          ) : (
            <Link to="/login" className="login-btn">
              <FontAwesomeIcon icon={faSignInAlt} /> Iniciar sesión
            </Link>
          )}
        </div>
      </div>
      
      <nav className="tabs">
        <NavLink to="/chatbot" className={({ isActive }) => isActive ? 'tab-btn active' : 'tab-btn'}>
          <FontAwesomeIcon icon={faRobot} /> Entrenador AI
        </NavLink>
        <NavLink to="/" className={({ isActive }) => isActive ? 'tab-btn active' : 'tab-btn'}>
          <FontAwesomeIcon icon={faPlusCircle} /> Registrar
        </NavLink>
        <NavLink to="/rutina_hoy" className={({ isActive }) => isActive ? 'tab-btn active' : 'tab-btn'}>
          <FontAwesomeIcon icon={faCalendarDay} /> Hoy
        </NavLink>
        <NavLink to="/rutina" className={({ isActive }) => isActive ? 'tab-btn active' : 'tab-btn'}>
          <FontAwesomeIcon icon={faCalendarAlt} /> Mi Rutina
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'tab-btn active' : 'tab-btn'}>
          <FontAwesomeIcon icon={faChartLine} /> Dashboard
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => isActive ? 'tab-btn active' : 'tab-btn'}>
          <FontAwesomeIcon icon={faUser} /> Perfil
        </NavLink>
      </nav>
    </header>
  );
}

export default Header;
