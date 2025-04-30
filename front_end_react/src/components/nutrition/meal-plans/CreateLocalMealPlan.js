// src/components/nutrition/meal-plans/CreateLocalMealPlan.js
import React, { useState } from 'react';
import { 
  Box, Typography, TextField, Button, Dialog, DialogTitle, 
  DialogContent, DialogActions, CircularProgress 
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSave, faTimes } from '@fortawesome/free-solid-svg-icons';
import { MealPlanService } from '../../../services/nutrition';

/**
 * Dialog component for quickly creating a local meal plan when none exist
 */
const CreateLocalMealPlan = ({ open, onClose, onSuccess }) => {
  const [planName, setPlanName] = useState('Mi primer plan de comidas');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleSubmit = async () => {
    if (!planName.trim()) {
      setError('Por favor, introduce un nombre para el plan');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Create basic meal plan skeleton
      const newPlan = {
        plan_name: planName,
        name: planName,
        is_active: true,
        items: [],
        description: 'Plan creado localmente'
      };
      
      // Save to local storage via service
      const result = await MealPlanService.create(newPlan);
      
      // Clear cache to ensure we load the new plan
      MealPlanService.clearCache();
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      // Close dialog
      onClose();
    } catch (err) {
      console.error('Error creating meal plan:', err);
      setError('Error al crear el plan. Por favor, intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open={open} onClose={!loading ? onClose : undefined} maxWidth="sm" fullWidth>
      <DialogTitle>Crear Plan de Comidas</DialogTitle>
      
      <DialogContent>
        <Box sx={{ py: 1 }}>
          <Typography variant="body2" color="text.secondary" paragraph>
            Crea tu primer plan de comidas para organizar tus comidas semanales.
            Después podrás añadir comidas para cada día de la semana.
          </Typography>
          
          {error && (
            <Typography variant="body2" color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          
          <TextField
            label="Nombre del plan"
            value={planName}
            onChange={(e) => setPlanName(e.target.value)}
            fullWidth
            margin="normal"
            variant="outlined"
            disabled={loading}
            autoFocus
          />
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button 
          startIcon={<FontAwesomeIcon icon={faTimes} />}
          onClick={onClose} 
          disabled={loading}
        >
          Cancelar
        </Button>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleSubmit}
          disabled={loading || !planName.trim()}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
        >
          {loading ? 'Creando...' : 'Crear Plan'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateLocalMealPlan;