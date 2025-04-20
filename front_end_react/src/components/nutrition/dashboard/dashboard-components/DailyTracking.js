// src/components/nutrition/dashboard/dashboard-components/DailyTracking.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, 
  Paper, TextField, Button, CircularProgress, Alert,
  Switch, FormControlLabel, Dialog, DialogTitle, DialogContent,
  DialogActions, Chip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faCheckCircle, faSave, faSyncAlt, faInfoCircle,
  faExclamationTriangle
} from '@fortawesome/free-solid-svg-icons';
import { NutritionCalculator } from '../../../../services/NutritionService';
import ApiService from '../../../../services/ApiService';

const DailyTracking = () => {
  const [completedMeals, setCompletedMeals] = useState({
    Desayuno: false,
    Almuerzo: false, 
    Comida: false,
    Merienda: false,
    Cena: false
  });
  
  const [calorieNote, setCalorieNote] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [useLocalStorage, setUseLocalStorage] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [apiInfo, setApiInfo] = useState({
    baseUrl: ApiService.baseURL || window.location.origin,
    endpoints: {
      profile: '/api/nutrition/profile',
      tracking: '/api/nutrition/tracking',
      dayTracking: '/api/nutrition/tracking/day'
    },
    lastResponse: null,
    lastError: null
  });
  
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
  
  // Direct API calls instead of using a service to debug
  const directApiGet = async (endpoint) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error("No authentication token found");
      
      const response = await fetch(`${apiInfo.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error calling ${endpoint}:`, error);
      throw error;
    }
  };
  
  const directApiPost = async (endpoint, data) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error("No authentication token found");
      
      const response = await fetch(`${apiInfo.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error calling ${endpoint}:`, error);
      throw error;
    }
  };
  
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
        const profileData = await directApiGet('/api/nutrition/profile');
        console.log("Profile data:", profileData);
        
        setApiInfo(prev => ({
          ...prev,
          lastResponse: JSON.stringify(profileData).substring(0, 200) + "..."
        }));
        
        if (profileData && profileData.profile) {
          setUserProfile(profileData.profile);
        } else if (profileData) {
          setUserProfile(profileData);
        }
      } catch (profileErr) {
        console.error("Error loading profile:", profileErr);
        setApiInfo(prev => ({
          ...prev,
          lastError: profileErr.toString()
        }));
      }
      
      // Only try to load tracking if not using localStorage mode
      if (!useLocalStorage) {
        try {
          console.log(`Loading tracking data for ${today}...`);
          const trackingResponse = await directApiGet(`/api/nutrition/tracking/day/${today}`);
          console.log("Tracking data:", trackingResponse);
          
          const trackingData = trackingResponse.tracking;
          
          if (trackingData) {
            setCompletedMeals(trackingData.completed_meals || {
              Desayuno: false,
              Almuerzo: false, 
              Comida: false,
              Merienda: false,
              Cena: false
            });
            setCalorieNote(trackingData.calorie_note || '');
          } else {
            console.log("No tracking data found for today");
            // Load from localStorage as fallback
            loadFromLocalStorage();
          }
        } catch (trackingErr) {
          console.error("Error loading tracking data:", trackingErr);
          setApiInfo(prev => ({
            ...prev,
            lastError: trackingErr.toString()
          }));
          
          // Fall back to localStorage
          loadFromLocalStorage();
          setError("No se pudo cargar los datos de seguimiento. Se utilizarán datos locales.");
        }
      } else {
        // Load from localStorage if that mode is selected
        loadFromLocalStorage();
      }
    } catch (err) {
      console.error("General error in loadData:", err);
      setError("Error al cargar datos. Comprueba la conexión e inténtalo nuevamente.");
    } finally {
      setLoading(false);
    }
  };
  
  // Load data from localStorage
  const loadFromLocalStorage = () => {
    try {
      console.log("Loading from localStorage fallback");
      const savedMeals = localStorage.getItem(`completed_meals_${today}`);
      const savedNote = localStorage.getItem(`calorie_note_${today}`);
      
      if (savedMeals) {
        setCompletedMeals(JSON.parse(savedMeals));
      }
      
      if (savedNote) {
        setCalorieNote(savedNote);
      }
    } catch (err) {
      console.error("Error loading from localStorage:", err);
    }
  };
  
  // Toggle a meal's completion status
  const toggleMealCompleted = (mealType) => {
    const newCompletedMeals = { 
      ...completedMeals,
      [mealType]: !completedMeals[mealType]
    };
    
    setCompletedMeals(newCompletedMeals);
    
    // Always save to localStorage as backup
    localStorage.setItem(`completed_meals_${today}`, JSON.stringify(newCompletedMeals));
  };
  
  // Handle changes to the calorie note
  const handleCalorieNoteChange = (event) => {
    const newNote = event.target.value;
    setCalorieNote(newNote);
    
    // Always save to localStorage as backup
    localStorage.setItem(`calorie_note_${today}`, newNote);
  };
  
  // Save tracking data using direct API call
  const saveTrackingData = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    
    try {
      // Calculate excess/deficit if profile exists
      let excessDeficit = null;
      let actualCalories = null;
      
      if (userProfile && (userProfile.goal_calories || userProfile.daily_calories) && calorieNote) {
        // Try to extract a number from the calorie note
        const calorieMatch = calorieNote.match(/\d+/);
        if (calorieMatch) {
          actualCalories = parseInt(calorieMatch[0], 10);
          const targetCalories = userProfile.goal_calories || userProfile.daily_calories;
          excessDeficit = actualCalories - targetCalories;
        }
      }
      
      const trackingData = {
        tracking_date: today,
        completed_meals: completedMeals,
        calorie_note: calorieNote,
        actual_calories: actualCalories,
        excess_deficit: excessDeficit
      };
      
      console.log("Saving tracking data:", trackingData);
      
      if (!useLocalStorage) {
        const response = await directApiPost('/api/nutrition/tracking', trackingData);
        console.log("Save response:", response);
        
        setApiInfo(prev => ({
          ...prev,
          lastResponse: JSON.stringify(response).substring(0, 200) + "..."
        }));
      }
      
      setSuccess("Seguimiento guardado correctamente" + (useLocalStorage ? " (solo localmente)" : ""));
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error("Error saving tracking data:", err);
      
      setApiInfo(prev => ({
        ...prev,
        lastError: err.toString()
      }));
      
      setError("Error al guardar los datos de seguimiento: " + err.message);
    } finally {
      setSaving(false);
    }
  };
  
  const handleToggleMode = () => {
    setUseLocalStorage(!useLocalStorage);
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
  
  return (
    <Card elevation={3}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '10px' }} />
            Seguimiento Diario
          </Typography>
          
          <Box display="flex" alignItems="center">
            <Button 
              size="small" 
              color="primary"
              onClick={() => setShowDiagnostics(true)}
              sx={{ mr: 1 }}
            >
              <FontAwesomeIcon icon={faInfoCircle} style={{ marginRight: '4px' }} />
              Diagnóstico
            </Button>
            
            <Button 
              size="small" 
              startIcon={<FontAwesomeIcon icon={faSyncAlt} />}
              onClick={loadData}
              disabled={loading || saving}
            >
              Actualizar
            </Button>
          </Box>
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
        
        <FormControlLabel
          control={
            <Switch
              checked={useLocalStorage}
              onChange={handleToggleMode}
              color="primary"
            />
          }
          label="Usar solo almacenamiento local (para desarrollo)"
          sx={{ mb: 2 }}
        />
        
        {useLocalStorage && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <FontAwesomeIcon icon={faExclamationTriangle} style={{ marginRight: '8px' }} />
            Modo local activado. Los datos no se sincronizarán con el servidor.
          </Alert>
        )}
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Comidas completadas hoy:
          </Typography>
          
          <Grid container spacing={1} sx={{ mb: 3 }}>
            {Object.keys(completedMeals).map((meal) => (
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
            sx={{ mb: 2 }}
          />
          
          {userProfile && (userProfile.goal_calories || userProfile.daily_calories) && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Tu objetivo diario es de {userProfile.goal_calories || userProfile.daily_calories} calorías
            </Typography>
          )}
          
          <Button
            variant="contained"
            color="primary"
            fullWidth
            onClick={saveTrackingData}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faSave} />}
          >
            {saving ? 'Guardando...' : 'Guardar Seguimiento'}
          </Button>
          
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1, textAlign: 'center' }}>
            * Los datos de seguimiento se guardan en el servidor y localmente como respaldo
          </Typography>
        </Box>
        
        {/* Diagnostics dialog */}
        <Dialog open={showDiagnostics} onClose={() => setShowDiagnostics(false)} maxWidth="md" fullWidth>
          <DialogTitle>Diagnóstico de API</DialogTitle>
          <DialogContent>
            <Typography variant="subtitle1" gutterBottom>Configuración API</Typography>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Base URL:</strong> {apiInfo.baseUrl}
              </Typography>
              <Typography variant="body2">
                <strong>Token presente:</strong> {localStorage.getItem('token') ? 'Sí' : 'No'}
              </Typography>
              <Typography variant="body2">
                <strong>Endpoints:</strong>
              </Typography>
              <Box ml={2}>
                {Object.entries(apiInfo.endpoints).map(([key, endpoint]) => (
                  <Chip 
                    key={key}
                    label={`${key}: ${endpoint}`}
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            </Box>
            
            <Typography variant="subtitle1" gutterBottom>Última respuesta</Typography>
            <Paper sx={{ p: 2, mb: 2, bgcolor: '#f5f5f5', maxHeight: 200, overflow: 'auto' }}>
              <Typography variant="body2" fontFamily="monospace" whiteSpace="pre-wrap">
                {apiInfo.lastResponse || 'No hay respuesta reciente'}
              </Typography>
            </Paper>
            
            {apiInfo.lastError && (
              <>
                <Typography variant="subtitle1" gutterBottom color="error">Último error</Typography>
                <Paper sx={{ p: 2, bgcolor: '#fff4f4', maxHeight: 200, overflow: 'auto' }}>
                  <Typography variant="body2" fontFamily="monospace" whiteSpace="pre-wrap" color="error">
                    {apiInfo.lastError}
                  </Typography>
                </Paper>
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowDiagnostics(false)}>Cerrar</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default DailyTracking;