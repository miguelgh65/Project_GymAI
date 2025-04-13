// src/components/profile/UserInfo.js
import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Avatar,
  Divider,
  Button
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faSignOutAlt } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
// CORRECCIÓN: Importar desde src/services (ruta relativa correcta)
import AuthService from '../../services/AuthService';

const UserInfo = ({ user }) => {
  const navigate = useNavigate();
  
  const handleLogout = async () => {
    try {
      await AuthService.logout(); // Llama al método de logout del servicio
      // Redirigir a login después de que las tareas de logout se completen
      navigate('/login');
    } catch (error) {
      console.error('Error durante el logout:', error);
      // Si hay error, igualmente intentamos redirigir al login
      navigate('/login');
    }
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FontAwesomeIcon 
            icon={faUser} 
            style={{ color: '#00B0B9', marginRight: '10px', fontSize: '1.5rem' }} 
          />
          <Typography variant="h6">Información de Usuario</Typography>
        </Box>
        
        <Divider sx={{ mb: 3 }} />
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar
            src={user?.profile_picture || ''}
            alt={user?.display_name || 'Usuario'}
            sx={{ width: 80, height: 80, mr: 2 }}
          />
          
          <Box>
            <Typography variant="h6">{user?.display_name || 'Usuario'}</Typography>
            <Typography variant="body2" color="textSecondary">
              {user?.email || 'No hay email disponible'}
            </Typography>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<FontAwesomeIcon icon={faSignOutAlt} />}
            onClick={handleLogout}
          >
            Cerrar Sesión
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default UserInfo;