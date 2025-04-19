// src/components/nutrition/dashboard/dashboard-components/DailyTracking.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, 
  Paper, TextField
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheckCircle } from '@fortawesome/free-solid-svg-icons';

const DailyTracking = () => {
  const [completedMeals, setCompletedMeals] = useState({});
  const [calorieNote, setCalorieNote] = useState('');
  
  useEffect(() => {
    // Cargar datos de localStorage al montar
    try {
      const today = new Date().toISOString().split('T')[0];
      const savedMeals = localStorage.getItem(`completed_meals_${today}`);
      const savedNote = localStorage.getItem(`calorie_note_${today}`);
      
      if (savedMeals) setCompletedMeals(JSON.parse(savedMeals));
      if (savedNote) setCalorieNote(savedNote);
    } catch (err) {
      console.error("Error al cargar seguimiento:", err);
    }
  }, []);
  
  const toggleMealCompleted = (mealType) => {
    const today = new Date().toISOString().split('T')[0];
    const newCompletedMeals = { ...completedMeals };
    
    newCompletedMeals[mealType] = !newCompletedMeals[mealType];
    
    setCompletedMeals(newCompletedMeals);
    localStorage.setItem(`completed_meals_${today}`, JSON.stringify(newCompletedMeals));
  };
  
  const handleCalorieNoteChange = (event) => {
    const today = new Date().toISOString().split('T')[0];
    const newNote = event.target.value;
    
    setCalorieNote(newNote);
    localStorage.setItem(`calorie_note_${today}`, newNote);
  };
  
  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '10px' }} />
          Seguimiento Diario
        </Typography>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Comidas completadas hoy:
          </Typography>
          
          <Grid container spacing={1} sx={{ mb: 3 }}>
            {['Desayuno', 'Almuerzo', 'Comida', 'Merienda', 'Cena'].map((meal) => (
              <Grid item xs={6} sm={4} key={meal}>
                <Paper 
                  elevation={1} 
                  onClick={() => toggleMealCompleted(meal)}
                  sx={{ 
                    p: 1.5, 
                    textAlign: 'center',
                    cursor: 'pointer',
                    border: '1px solid',
                    borderColor: completedMeals[meal] ? 'success.main' : 'divider',
                    bgcolor: completedMeals[meal] ? 'success.light' : 'background.paper',
                    '&:hover': { bgcolor: completedMeals[meal] ? 'success.light' : 'action.hover' }
                  }}
                >
                  <Typography variant="body2">
                    {completedMeals[meal] && <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '5px', color: '#2e7d32' }} />}
                    {meal}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
          
          <Typography variant="subtitle1" gutterBottom>
            Exceso/Déficit calórico:
          </Typography>
          
          <TextField 
            fullWidth
            multiline
            rows={2}
            placeholder="Registra aquí excesos o déficits calóricos del día..."
            value={calorieNote}
            onChange={handleCalorieNoteChange}
            variant="outlined"
            size="small"
            sx={{ mb: 1 }}
          />
          
          <Typography variant="caption" color="text.secondary">
            * Los datos de seguimiento se guardan localmente en tu navegador
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default DailyTracking;