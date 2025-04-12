// src/components/Header.js
import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  AppBar, Toolbar, Typography, Button, Avatar, Menu, MenuItem, 
  IconButton, Drawer, List, ListItem, ListItemIcon, ListItemText,
  Box, Divider, useMediaQuery, useTheme
} from '@mui/material';
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
  faAppleAlt,
  faUser,
  faBars,
  faTimes
} from '@fortawesome/free-solid-svg-icons';
import AuthService from '../services/AuthService';

function Header({ user, onLogout }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async (e) => {
    // Prevenir comportamiento predeterminado
    e.preventDefault();
    
    console.log("Iniciando proceso de logout...");
    
    try {
      // Usa el servicio de autenticación
      AuthService.logout();
      
      // Notifica al componente padre (si proporcionó un callback)
      if (typeof onLogout === 'function') {
        onLogout();
      }
      
      // Navegar a la página de login usando navigate en lugar de manipular window.location
      navigate('/login');
    } catch (error) {
      console.error('Error en proceso de logout:', error);
    }
  };

  const handleUserMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  // Usamos el componente Link para navegación
  const renderNavLink = (to, icon, label) => {
    const isActive = location.pathname === to;
    
    return (
      <Button
        component={Link}
        to={to}
        color={isActive ? "primary" : "inherit"}
        sx={{
          mx: 1,
          textTransform: 'none',
          fontWeight: isActive ? 600 : 400,
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
          }
        }}
        startIcon={<FontAwesomeIcon icon={icon} />}
      >
        {label}
      </Button>
    );
  };

  return (
    <AppBar position="static">
      <Toolbar>
        {isMobile ? (
          <>
            <IconButton
              color="inherit"
              aria-label="menu"
              onClick={toggleDrawer}
              edge="start"
              sx={{ mr: 2 }}
            >
              <FontAwesomeIcon icon={faBars} />
            </IconButton>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              <FontAwesomeIcon icon={faDumbbell} /> GymAI
            </Typography>
          </>
        ) : (
          <>
            <Typography variant="h6" component={Link} to="/" sx={{ color: 'white', textDecoration: 'none', flexGrow: 0 }}>
              <FontAwesomeIcon icon={faDumbbell} /> GymAI
            </Typography>
            <Box sx={{ display: 'flex', mx: 2, flexGrow: 1 }}>
              {renderNavLink("/chatbot", faRobot, "Entrenador AI")}
              {renderNavLink("/", faPlusCircle, "Registrar")}
              {renderNavLink("/rutina_hoy", faCalendarDay, "Hoy")}
              {renderNavLink("/rutina", faCalendarAlt, "Mi Rutina")}
              {renderNavLink("/dashboard", faChartLine, "Dashboard")}
              {renderNavLink("/nutrition", faAppleAlt, "Nutrición")}
              {renderNavLink("/profile", faUser, "Perfil")}
            </Box>
          </>
        )}
        
        <Box>
          {user ? (
            <Button 
              color="inherit"
              onClick={handleUserMenuOpen}
              startIcon={
                user.profile_picture ? (
                  <Avatar src={user.profile_picture} alt={user.display_name} sx={{ width: 24, height: 24 }} />
                ) : (
                  <FontAwesomeIcon icon={faUserCircle} />
                )
              }
            >
              {!isMobile && user.display_name}
            </Button>
          ) : (
            <Button 
              color="inherit" 
              component={Link} 
              to="/login"
              startIcon={<FontAwesomeIcon icon={faSignInAlt} />}
            >
              {!isMobile && "Iniciar sesión"}
            </Button>
          )}
        </Box>
        
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleUserMenuClose}
        >
          <MenuItem component={Link} to="/profile" onClick={handleUserMenuClose}>
            <ListItemIcon>
              <FontAwesomeIcon icon={faUser} />
            </ListItemIcon>
            <ListItemText primary="Mi Perfil" />
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout}>
            <ListItemIcon>
              <FontAwesomeIcon icon={faSignOutAlt} />
            </ListItemIcon>
            <ListItemText primary="Cerrar Sesión" />
          </MenuItem>
        </Menu>
        
        <Drawer
          anchor="left"
          open={drawerOpen}
          onClose={toggleDrawer}
        >
          <Box
            sx={{ width: 250 }}
            role="presentation"
          >
            <List>
              {[
                { text: 'Entrenador AI', icon: faRobot, path: '/chatbot' },
                { text: 'Registrar', icon: faPlusCircle, path: '/' },
                { text: 'Hoy', icon: faCalendarDay, path: '/rutina_hoy' },
                { text: 'Mi Rutina', icon: faCalendarAlt, path: '/rutina' },
                { text: 'Dashboard', icon: faChartLine, path: '/dashboard' },
                { text: 'Nutrición', icon: faAppleAlt, path: '/nutrition' },
                { text: 'Perfil', icon: faUser, path: '/profile' }
              ].map((item) => (
                <ListItem 
                  button 
                  key={item.text} 
                  component={Link}
                  to={item.path}
                  onClick={toggleDrawer}
                  selected={location.pathname === item.path}
                >
                  <ListItemIcon>
                    <FontAwesomeIcon icon={item.icon} />
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItem>
              ))}
            </List>
            <Divider />
            {user && (
              <Button
                fullWidth
                color="error"
                variant="contained"
                onClick={handleLogout}
                sx={{ m: 2 }}
                startIcon={<FontAwesomeIcon icon={faSignOutAlt} />}
              >
                Cerrar Sesión
              </Button>
            )}
          </Box>
        </Drawer>
      </Toolbar>
    </AppBar>
  );
}

export default Header;