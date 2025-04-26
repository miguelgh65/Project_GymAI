// src/components/nutrition/dashboard/dashboard-components/DailyTracking.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, 
  Paper, TextField, Button, CircularProgress, Alert,
  Chip, Divider, Tooltip, IconButton
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faCheckCircle, faSave, faSyncAlt,
  faEdit, faTimes, faInfoCircle, faCalculator
} from '@fortawesome/free-solid-svg-icons';
import { NutritionCalculator } from '../../../../services/NutritionService';
import TrackingService from '../../../../services/nutrition/TrackingService';

const DailyTracking = () => {
  // Valores predeterminados para cada tipo de comida
  const mealDefaults = {
    Desayuno: { calories: 350, protein: 20 },
    Almuerzo: { calories: 250, protein: 15 },
    Comida: { calories: 550, protein: 30 },
    Merienda: { calories: 150, protein: 10 },
    Cena: { calories: 400, protein: 25 }
  };
  
  const [completedMeals, setCompletedMeals] = useState({
    Desayuno: false,
    Almuerzo: false, 
    Comida: false,
    Merienda: false,
    Cena: false
  });
  
  // Estados para las calorías y proteínas
  const [actualCalories, setActualCalories] = useState('');
  const [actualProtein, setActualProtein] = useState('');
  const [isManualEntry, setIsManualEntry] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
  
  // Load data when component mounts
  useEffect(() => {
    loadData();
  }, []);
  
  // Load user profile and tracking data
  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load user nutrition profile to get target calories
      try {
        console.log("Loading nutrition profile...");
        const profileData = await NutritionCalculator.getProfile();
        console.log("Profile data:", profileData);
        
        if (profileData && profileData.profile) {
          setUserProfile(profileData.profile);
        } else if (profileData) {
          setUserProfile(profileData);
        }
      } catch (profileErr) {
        console.error("Error loading profile:", profileErr);
      }
      
      try {
        console.log(`Loading tracking data for ${today}...`);
        // Use TrackingService instead of direct API call
        const trackingData = await TrackingService.getTrackingForDay(today);
        console.log("Tracking data:", trackingData);
        
        if (trackingData) {
          setCompletedMeals(trackingData.completed_meals || {
            Desayuno: false,
            Almuerzo: false, 
            Comida: false,
            Merienda: false,
            Cena: false
          });
          
          if (trackingData.actual_calories) {
            setActualCalories(trackingData.actual_calories.toString());
            setIsManualEntry(true); // Si ya tiene valores, asumir entrada manual
          }
          
          if (trackingData.actual_protein) {
            setActualProtein(trackingData.actual_protein.toString());
          }
        } else {
          console.log("No tracking data found for today");
          // Load from localStorage as fallback
          loadFromLocalStorage();
        }
      } catch (trackingErr) {
        console.error("Error loading tracking data:", trackingErr);
        
        // Fall back to localStorage
        loadFromLocalStorage();
        setError("No se pudo cargar los datos de seguimiento. Intentando de nuevo...");
      }
    } catch (err) {
      console.error("General error in loadData:", err);
      setError("Error al cargar datos. Comprueba la conexión e inténtalo nuevamente.");
    } finally {
      setLoading(false);
    }
  };
  
  // Load data from localStorage as fallback only
  const loadFromLocalStorage = () => {
    try {
      console.log("Loading from localStorage fallback");
      const savedMeals = localStorage.getItem(`completed_meals_${today}`);
      const savedCalories = localStorage.getItem(`actual_calories_${today}`);
      const savedProtein = localStorage.getItem(`actual_protein_${today}`);
      const savedIsManual = localStorage.getItem(`is_manual_entry_${today}`);
      
      if (savedMeals) {
        setCompletedMeals(JSON.parse(savedMeals));
      }
      
      if (savedCalories) {
        setActualCalories(savedCalories);
      }
      
      if (savedProtein) {
        setActualProtein(savedProtein);
      }
      
      if (savedIsManual) {
        setIsManualEntry(JSON.parse(savedIsManual));
      }
    } catch (err) {
      console.error("Error loading from localStorage:", err);
    }
  };
  
  // Función para calcular automáticamente calorías y proteínas basado en comidas completadas
  const calculateNutrientsFromMeals = () => {
    let totalCalories = 0;
    let totalProtein = 0;
    
    Object.entries(completedMeals).forEach(([meal, isCompleted]) => {
      if (isCompleted && mealDefaults[meal]) {
        totalCalories += mealDefaults[meal].calories;
        totalProtein += mealDefaults[meal].protein;
      }
    });
    
    return { calories: totalCalories, protein: totalProtein };
  };
  
  // Toggle a meal's completion status
  const toggleMealCompleted = (mealType) => {
    const newCompletedMeals = { 
      ...completedMeals,
      [mealType]: !completedMeals[mealType]
    };
    
    setCompletedMeals(newCompletedMeals);
    
    // Recalcular nutrientes automáticamente si no está en modo manual
    if (!isManualEntry) {
      const { calories, protein } = calculateNutrientsFromMeals();
      setActualCalories(calories.toString());
      setActualProtein(protein.toString());
    }
    
    // Save to localStorage as backup
    localStorage.setItem(`completed_meals_${today}`, JSON.stringify(newCompletedMeals));
  };
  
  // Handle manual changes to the actual calories
  const handleCaloriesChange = (event) => {
    const newValue = event.target.value;
    setActualCalories(newValue);
    setIsManualEntry(true);
    
    // Save to localStorage as backup
    localStorage.setItem(`actual_calories_${today}`, newValue);
    localStorage.setItem(`is_manual_entry_${today}`, JSON.stringify(true));
  };
  
  // Handle manual changes to protein
  const handleProteinChange = (event) => {
    const newValue = event.target.value;
    setActualProtein(newValue);
    setIsManualEntry(true);
    
    // Save to localStorage as backup
    localStorage.setItem(`actual_protein_${today}`, newValue);
    localStorage.setItem(`is_manual_entry_${today}`, JSON.stringify(true));
  };
  
  // Toggle between auto and manual mode
  const toggleEntryMode = () => {
    if (isManualEntry) {
      // Cambiar a modo automático
      const { calories, protein } = calculateNutrientsFromMeals();
      setActualCalories(calories.toString());
      setActualProtein(protein.toString());
      setIsManualEntry(false);
      localStorage.setItem(`is_manual_entry_${today}`, JSON.stringify(false));
    } else {
      // Cambiar a modo manual
      setIsManualEntry(true);
      localStorage.setItem(`is_manual_entry_${today}`, JSON.stringify(true));
    }
  };
  
  // Calculate excess/deficit
  const calculateExcessDeficit = () => {
    if (!userProfile || !actualCalories || 
        !(userProfile.goal_calories || userProfile.daily_calories)) {
      return null;
    }
    
    const targetCalories = userProfile.goal_calories || userProfile.daily_calories;
    return parseInt(actualCalories, 10) - targetCalories;
  };
  
  // Save tracking data using TrackingService
  const saveTrackingData = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    
    try {
      const excessDeficit = calculateExcessDeficit();
      const numCalories = actualCalories ? parseInt(actualCalories, 10) : null;
      const numProtein = actualProtein ? parseInt(actualProtein, 10) : null;
      
      const trackingData = {
        tracking_date: today,
        completed_meals: completedMeals,
        calorie_note: numCalories ? `Calorías consumidas: ${numCalories}` : "",
        actual_calories: numCalories,
        actual_protein: numProtein, // Nuevo campo
        excess_deficit: excessDeficit
      };
      
      console.log("Saving tracking data:", trackingData);
      
      // Use TrackingService
      const response = await TrackingService.saveTracking(trackingData);
      console.log("Save response:", response);
      
      setSuccess("Seguimiento guardado correctamente");
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error("Error saving tracking data:", err);
      setError("Error al guardar los datos de seguimiento: " + (err.message || "Error desconocido"));
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <Card elevation={3}>
        <CardContent sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress size={40} />
        </CardContent>
      </Card>
    );
  }
  
  // Calculate excess/deficit for display
  const excessDeficit = calculateExcessDeficit();
  
  return (
    <Card elevation={3}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '10px' }} />
            Seguimiento Diario
          </Typography>
          
          <Button 
            size="small" 
            startIcon={<FontAwesomeIcon icon={faSyncAlt} />}
            onClick={loadData}
            disabled={loading || saving}
          >
            Actualizar
          </Button>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}
        
        <Box sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle1">
              Comidas completadas hoy ({new Date().toLocaleDateString()}):
            </Typography>
            
            <Box>
              <Chip 
                label={isManualEntry ? "Entrada Manual" : "Cálculo Automático"} 
                size="small" 
                color={isManualEntry ? "primary" : "default"}
                sx={{ mr: 1 }}
              />
              <Tooltip title={isManualEntry ? "Cambiar a cálculo automático" : "Cambiar a entrada manual"}>
                <IconButton size="small" onClick={toggleEntryMode}>
                  <FontAwesomeIcon icon={isManualEntry ? faCalculator : faEdit} />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
          
          <Grid container spacing={1} sx={{ mb: 3 }}>
            {Object.entries(mealDefaults).map(([meal, defaults]) => (
              <Grid item xs={6} sm={4} key={meal}>
                <Tooltip title={`${defaults.calories} kcal, ${defaults.protein}g proteína`}>
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
                    <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {completedMeals[meal] && <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '5px', color: '#2e7d32' }} />}
                      {meal}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {defaults.calories} kcal | {defaults.protein}g prot
                    </Typography>
                  </Paper>
                </Tooltip>
              </Grid>
            ))}
          </Grid>
          
          <Divider sx={{ my: 2 }} />
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField 
                fullWidth
                type="number"
                label="Calorías consumidas hoy (kcal)"
                placeholder="Ej: 2000"
                value={actualCalories}
                onChange={handleCaloriesChange}
                variant="outlined"
                size="small"
                disabled={!isManualEntry}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField 
                fullWidth
                type="number"
                label="Proteínas consumidas hoy (g)"
                placeholder="Ej: 120"
                value={actualProtein}
                onChange={handleProteinChange}
                variant="outlined"
                size="small"
                disabled={!isManualEntry}
              />
            </Grid>
          </Grid>
          
          {userProfile && (userProfile.goal_calories || userProfile.daily_calories) && (
            <Box sx={{ my: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Tu objetivo diario es de {userProfile.goal_calories || userProfile.daily_calories} calorías
              </Typography>
              
              {excessDeficit !== null && (
                <Chip 
                  label={excessDeficit > 0 
                    ? `Exceso: +${excessDeficit} kcal` 
                    : `Déficit: ${excessDeficit} kcal`}
                  color={excessDeficit > 0 ? "warning" : "success"}
                  size="small"
                />
              )}
            </Box>
          )}
          
          <Button
            variant="contained"
            color="primary"
            fullWidth
            onClick={saveTrackingData}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
            sx={{ mt: 2 }}
          >
            {saving ? 'Guardando...' : 'Guardar Seguimiento'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default DailyTracking;