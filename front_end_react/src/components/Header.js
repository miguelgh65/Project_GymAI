// src/components/Header.js - Versión CORREGIDA para enlaces

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Button, Avatar, Menu, MenuItem,
  IconButton, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, // Usar ListItemButton
  Box, Divider, useMediaQuery, useTheme
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faDumbbell,
  faSignInAlt,
  faSignOutAlt,
  faUserCircle,
  faRobot,
  faPlusCircle, // Icono para Registrar
  faCalendarDay,
  faCalendarAlt,
  faChartLine,
  faAppleAlt,
  faUser,
  faBars,
  faTimes, // Podrías usarlo para cerrar el drawer
  faHome // Icono para Home/Main
} from '@fortawesome/free-solid-svg-icons';
// AuthService ya no se necesita aquí si onLogout viene de App.js
// import AuthService from '../services/AuthService';

function Header({ user, onLogout }) { // Recibe user y onLogout de App.js
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  const navigate = useNavigate(); // Usar navigate para logout si es necesario

  const handleLogout = () => {
    setAnchorEl(null); // Cerrar menú desplegable si está abierto
    if (typeof onLogout === 'function') {
      onLogout(); // Llama a la función handleLogout definida en App.js
    }
    // La redirección a /login debería ocurrir automáticamente en App.js
    // debido al cambio de estado de autenticación, no es necesario navigate aquí.
    // navigate('/login');
  };

  const handleUserMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleDrawer = (open) => (event) => {
    if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
      return;
    }
    setDrawerOpen(open);
  };

  // Renderizador de enlaces de navegación para la barra principal (Desktop)
  const renderNavLink = (to, icon, label) => {
    const isActive = location.pathname === to;

    return (
      <Button
        component={Link}
        to={to}
        key={label} // Añadir key para listas
        color="inherit" // Usar inherit para que el tema controle el color base
        sx={{
          mx: 1,
          textTransform: 'none',
          fontWeight: isActive ? 'bold' : 'normal', // Más claro activo/inactivo
          color: isActive ? theme.palette.secondary.main : 'inherit', // Resaltar activo con color secundario o primario
          position: 'relative', // Para el pseudo-elemento
          '&:after': { // Subrayado sutil para el activo
              content: '""',
              display: isActive ? 'block' : 'none',
              position: 'absolute',
              bottom: 0,
              left: '10%',
              width: '80%',
              height: '2px',
              backgroundColor: theme.palette.secondary.main, // Usar color secundario o primario
          },
          '&:hover': {
            backgroundColor: alpha(theme.palette.common.white, 0.1), // Efecto hover más sutil
          }
        }}
        startIcon={<FontAwesomeIcon icon={icon} size="sm" />} // Ajustar tamaño icono
      >
        {label}
      </Button>
    );
  };

  // Definir elementos del menú (para Desktop y Mobile)
   const menuItems = [
      // *** CORREGIDO: Enlace 'Registrar' va a '/registrar' ***
      { text: 'Registrar', icon: faPlusCircle, path: '/registrar' },
      { text: 'Hoy', icon: faCalendarDay, path: '/rutina-hoy' },
      { text: 'Mi Rutina', icon: faCalendarAlt, path: '/rutina' },
      { text: 'Dashboard', icon: faChartLine, path: '/dashboard' },
      { text: 'Nutrición', icon: faAppleAlt, path: '/nutrition' },
      { text: 'Entrenador AI', icon: faRobot, path: '/chatbot' }, // Movido Chatbot aquí
      { text: 'Perfil', icon: faUser, path: '/profile' }
    ];


  // Contenido del Drawer (Menú lateral móvil)
  const drawerContent = (
    <Box
      sx={{ width: 250 }}
      role="presentation"
      onClick={toggleDrawer(false)} // Cerrar al hacer clic fuera o en un item
      onKeyDown={toggleDrawer(false)}
    >
      {/* Opcional: Un título o logo pequeño en el drawer */}
       <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
         <FontAwesomeIcon icon={faDumbbell} size="lg" style={{ marginRight: '10px' }} />
         <Typography variant="h6">GymAI Menu</Typography>
       </Box>
       <Divider />
      <List>
         {/* Enlace a Home/Main explícito */}
          <ListItem disablePadding>
             <ListItemButton
               component={Link}
               to="/" // Enlace a la página principal
               selected={location.pathname === '/'}
             >
               <ListItemIcon>
                 <FontAwesomeIcon icon={faHome} />
               </ListItemIcon>
               <ListItemText primary="Inicio" />
             </ListItemButton>
          </ListItem>

        {/* Mapear los items definidos arriba */}
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path} // Usar la ruta definida
              selected={location.pathname.startsWith(item.path) && item.path !== '/'} // Marcar como activo
            >
              <ListItemIcon>
                <FontAwesomeIcon icon={item.icon} />
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider sx={{ my: 1 }}/>
      {user && ( // Mostrar botón logout solo si está logueado
         <Box sx={{ px: 2, py: 1}}>
             <Button
               fullWidth
               color="error" // O un color que indique logout
               variant="outlined" // Un estilo menos prominente que "contained"
               onClick={handleLogout}
               startIcon={<FontAwesomeIcon icon={faSignOutAlt} />}
             >
               Cerrar Sesión
             </Button>
          </Box>
      )}
    </Box>
  );

  // --- Renderizado del Header ---
  return (
    <AppBar position="fixed" elevation={1}> {/* Usar position="fixed" y elevation */}
      <Toolbar>
        {isMobile ? (
          <>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              onClick={toggleDrawer(true)} // Abre el drawer
              edge="start"
              sx={{ mr: 1 }} // Reducir margen si es necesario
            >
              <FontAwesomeIcon icon={faBars} />
            </IconButton>
            {/* Logo también enlaza a Home en móvil */}
            <Typography variant="h6" component={Link} to="/" sx={{ color: 'inherit', textDecoration: 'none', flexGrow: 1 }}>
               <FontAwesomeIcon icon={faDumbbell} style={{ marginRight: '8px'}} /> GymAI
            </Typography>
          </>
        ) : (
          <>
             {/* Logo/Título principal enlaza a Home */}
            <Typography variant="h6" component={Link} to="/" sx={{ color: 'inherit', textDecoration: 'none', mr: 3 }}>
               <FontAwesomeIcon icon={faDumbbell} style={{ marginRight: '8px'}}/> GymAI
            </Typography>
            {/* Navegación principal para Desktop */}
            <Box sx={{ display: 'flex', flexGrow: 1 }}>
              {menuItems.map((item) => renderNavLink(item.path, item.icon, item.text))}
            </Box>
          </>
        )}

        {/* Sección del usuario (Avatar/Botón Login) */}
        <Box sx={{ flexShrink: 0 }}> {/* Evitar que se encoja */}
          {user ? (
            <>
              <IconButton onClick={handleUserMenuOpen} size="small">
                 <Avatar
                   alt={user.display_name || 'Usuario'}
                   src={user.profile_picture || undefined} // Usar undefined si no hay imagen para fallback a icono
                   sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }} // Tamaño y color de fondo
                 >
                   {/* Fallback a inicial si no hay foto */}
                   {!user.profile_picture && user.display_name ? user.display_name[0].toUpperCase() : <FontAwesomeIcon icon={faUserCircle} />}
                 </Avatar>
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleUserMenuClose}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              >
                <MenuItem component={Link} to="/profile" onClick={handleUserMenuClose}>
                  <ListItemIcon>
                    <FontAwesomeIcon icon={faUser} size="sm"/>
                  </ListItemIcon>
                  Mi Perfil
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout}>
                   <ListItemIcon>
                    <FontAwesomeIcon icon={faSignOutAlt} size="sm"/>
                  </ListItemIcon>
                  Cerrar Sesión
                </MenuItem>
              </Menu>
            </>
          ) : (
             // Botón Login solo visible si no hay usuario
            <Button
              color="inherit"
              component={Link}
              to="/login"
              startIcon={<FontAwesomeIcon icon={faSignInAlt} />}
            >
              {!isMobile && "Login"} {/* Ocultar texto en móvil si se prefiere */}
            </Button>
          )}
        </Box>

        {/* Drawer para móvil */}
        <Drawer
          anchor="left"
          open={drawerOpen}
          onClose={toggleDrawer(false)} // Cierra el drawer
        >
          {drawerContent}
        </Drawer>
      </Toolbar>
    </AppBar>
  );
}

// Función alpha para transparencias (si no la tienes importada de MUI)
function alpha(color, opacity) {
    if (!color) return '';
    const R = parseInt(color.substring(1, 3), 16);
    const G = parseInt(color.substring(3, 5), 16);
    const B = parseInt(color.substring(5, 7), 16);
    return `rgba(${R}, ${G}, ${B}, ${opacity})`;
}


export default Header;