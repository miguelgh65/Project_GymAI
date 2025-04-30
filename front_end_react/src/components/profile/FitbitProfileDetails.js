import React from 'react';
import { 
  Typography, 
  Box, 
  Grid, 
  Card 
} from '@mui/material';

function FitbitProfileDetails({ fitbitProfile }) {
  // Función auxiliar para renderizar tarjetas de detalles
  const renderDetailCard = (value, label, icon) => {
    if (!value) return null;

    return (
      <Grid item xs={6} sm={4} md={3}>
        <Card 
          variant="outlined" 
          sx={{ 
            p: 2, 
            textAlign: 'center', 
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            transition: 'transform 0.2s',
            '&:hover': {
              transform: 'scale(1.05)',
              boxShadow: 2
            }
          }}
        >
          {icon && (
            <Box 
              sx={{ 
                fontSize: '2rem', 
                color: 'primary.main', 
                mb: 1 
              }}
            >
              {icon}
            </Box>
          )}
          <Typography 
            variant="h5" 
            color="primary" 
            sx={{ fontWeight: 600 }}
          >
            {value}
          </Typography>
          <Typography 
            variant="caption" 
            color="text.secondary"
          >
            {label}
          </Typography>
        </Card>
      </Grid>
    );
  };

  // Si no hay perfil, no renderizar nada
  if (!fitbitProfile?.user) return null;

  const { user } = fitbitProfile;

  return (
    <Box 
      sx={{ 
        mt: 3, 
        p: 2, 
        backgroundColor: 'background.paper', 
        borderRadius: 2 
      }}
    >
      <Typography 
        variant="h6" 
        gutterBottom 
        sx={{ 
          mb: 3, 
          borderBottom: '1px solid', 
          borderColor: 'divider', 
          pb: 1 
        }}
      >
        Perfil Fitbit
        <Typography 
          variant="subtitle2" 
          color="text.secondary" 
          component="span" 
          sx={{ ml: 2 }}
        >
          ({user.displayName || 'Usuario'})
        </Typography>
      </Typography>

      <Grid container spacing={2}>
        {renderDetailCard(
          user.age, 
          'Edad', 
          <span role="img" aria-label="Edad">🎂</span>
        )}

        {renderDetailCard(
          user.height, 
          'Altura (cm)', 
          <span role="img" aria-label="Altura">📏</span>
        )}

        {renderDetailCard(
          user.weight, 
          'Peso (kg)', 
          <span role="img" aria-label="Peso">⚖️</span>
        )}

        {renderDetailCard(
          user.averageDailySteps, 
          'Pasos diarios', 
          <span role="img" aria-label="Pasos">🚶</span>
        )}
      </Grid>
    </Box>
  );
}

export default FitbitProfileDetails;