// src/components/Profile.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import UserInfo from './profile/UserInfo';
import ConnectedAccounts from './profile/ConnectedAccounts';
import FitbitConnection from './profile/FitbitConnection';
import ApiService from '../services/ApiService';

const Profile = ({ user, onUserUpdated }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Función para refrescar los datos del usuario
  const refreshUserData = async () => {
    if (!user) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await ApiService.getCurrentUser();
      if (response && response.success && response.user) {
        if (onUserUpdated) {
          onUserUpdated(response.user);
        }
        setSuccess("Información de usuario actualizada");
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (error) {
      console.error("Error actualizando información de usuario:", error);
      setError("No se pudo actualizar la información. Por favor recarga la página.");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Alert severity="warning">
          Debes iniciar sesión para ver tu perfil.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Mi Perfil</Typography>
        {loading && <CircularProgress size={24} />}
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      
      <UserInfo user={user} />
      <ConnectedAccounts user={user} onUpdate={refreshUserData} />
      <FitbitConnection user={user} onUpdate={refreshUserData} />
    </Box>
  );
};

export default Profile;