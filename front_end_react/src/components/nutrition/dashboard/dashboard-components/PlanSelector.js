// src/components/nutrition/dashboard/dashboard-components/PlanSelector.js
import React, { useState } from 'react';
import { 
  Box, Typography, Card, CardContent, Button, Grid, 
  CircularProgress, Alert, Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faUtensils, faEdit, faSyncAlt
} from '@fortawesome/free-solid-svg-icons';

const PlanSelector = ({ 
  profile, 
  activePlans = [], 
  hasTargets, 
  onRefreshPlans 
}) => {
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [applyingToPlans, setApplyingToPlans] = useState(false);
  const [error, setError] = useState(null);

  // Aplicar los objetivos del perfil a un plan seleccionado
  const applyProfileToPlan = async () => {
    if (!selectedPlanId || !profile) {
      console.error("No hay plan seleccionado o perfil para aplicar");
      return;
    }
    
    setApplyingToPlans(true);
    try {
      // Implementation...
      // This would call your service to update the plan
      alert("¡Objetivos aplicados correctamente al plan!");
      onRefreshPlans();
    } catch (err) {
      console.error("Error al aplicar objetivos:", err);
      setError("No se pudieron aplicar los objetivos al plan seleccionado");
    } finally {
      setApplyingToPlans(false);
      setSelectedPlanId(null);
    }
  };

  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <FontAwesomeIcon icon={faUtensils} style={{ marginRight: '10px' }} />
          Aplicar a Planes de Comida
        </Typography>
        
        {!hasTargets ? (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Tu perfil nutricional no tiene objetivos completos. Usa la calculadora de macros para establecerlos.
          </Alert>
        ) : activePlans.length === 0 ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            No tienes planes de comida activos. Crea un plan primero para aplicarle tus objetivos nutricionales.
          </Alert>
        ) : (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" gutterBottom>
              Selecciona un plan de comida activo para aplicarle tus objetivos nutricionales:
            </Typography>
            
            <Grid container spacing={2} sx={{ mt: 1 }}>
              {activePlans.map(plan => (
                <Grid item xs={12} sm={6} key={plan.id}>
                  <Paper 
                    elevation={1} 
                    onClick={() => setSelectedPlanId(plan.id)}
                    sx={{ 
                      p: 2, 
                      cursor: 'pointer',
                      border: selectedPlanId === plan.id ? '2px solid' : '1px solid',
                      borderColor: selectedPlanId === plan.id ? 'primary.main' : 'divider',
                      transition: 'all 0.2s',
                      '&:hover': {
                        borderColor: 'primary.main',
                        boxShadow: 2
                      }
                    }}
                  >
                    <Typography variant="subtitle1" noWrap>
                      {plan.plan_name || plan.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {plan.target_calories 
                        ? `Objetivo: ${plan.target_calories} kcal` 
                        : "Sin objetivos nutricionales"}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
            
            <Button
              variant="contained"
              color="primary"
              disabled={!selectedPlanId || applyingToPlans || !hasTargets}
              startIcon={applyingToPlans ? <CircularProgress size={20} /> : <FontAwesomeIcon icon={faEdit} />}
              onClick={applyProfileToPlan}
              sx={{ mt: 3 }}
              fullWidth
            >
              Aplicar Objetivos al Plan Seleccionado
            </Button>
          </Box>
        )}
        
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </CardContent>
    </Card>
  );
};

export default PlanSelector;