// src/components/nutrition/dashboard/dashboard-components/ProfileMissing.js
import React from 'react';
import { Alert, Button } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalculator } from '@fortawesome/free-solid-svg-icons';

const ProfileMissing = ({ onGoToCalculator }) => (
  <Alert severity="info" sx={{ mb: 3 }}>
    No tienes un perfil nutricional configurado. 
    Usa la calculadora de macros para establecer tus objetivos.
    
    <Button 
      variant="contained"
      color="primary"
      startIcon={<FontAwesomeIcon icon={faCalculator} />}
      onClick={onGoToCalculator}
      sx={{ mt: 2 }}
    >
      Ir a Calculadora de Macros
    </Button>
  </Alert>
);

export default ProfileMissing;