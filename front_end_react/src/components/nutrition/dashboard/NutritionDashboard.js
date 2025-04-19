// src/components/nutrition/dashboard/NutritionDashboard.js - Versión corregida
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Button, Grid, 
  CircularProgress, Alert, Paper, Divider, LinearProgress,
  Chip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faCalculator, faUtensils, faEdit, faPlus,
  faFire, faDrumstickBite, faAppleAlt, faOilCan,
  faChartPie, faChartLine, faSyncAlt
} from '@fortawesome/free-solid-svg-icons';
import { NutritionCalculator, MealPlanService } from '../../../services/NutritionService';
import { useNavigate } from 'react-router-dom';

const NutritionDashboard = ({ user }) => {
  const [profile, setProfile] = useState(null);
  const [activePlans, setActivePlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [plansLoading, setPlansLoading] = useState(true); // Separar los estados de carga
  const [error, setError] = useState(null);
  const [plansError, setPlansError] = useState(null); // Separar errores
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [applyingToPlans, setApplyingToPlans] = useState(false);
  const navigate = useNavigate();
  
  // Cargar perfil nutricional del usuario al inicio
  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        console.log("Intentando cargar perfil nutricional...");
        const profileData = await NutritionCalculator.getProfile();
        console.log("Datos de perfil recibidos:", profileData);
        
        if (profileData) {
          setProfile(profileData);
        }
      } catch (err) {
        console.error("Error al cargar perfil nutricional:", err);
        setError("No se pudo cargar tu perfil nutricional. Puedes introducir los datos manualmente.");
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);
  
  // Cargar planes activos en un efecto separado
  useEffect(() => {
    loadActivePlans();
  }, []);

  // Función separada para cargar planes activos
  const loadActivePlans = async () => {
    try {
      setPlansLoading(true);
      setPlansError(null);
      console.log("Dashboard: Cargando planes activos...");
      
      const plansResponse = await MealPlanService.getAll(true);
      console.log("Dashboard: Planes activos recibidos:", plansResponse);
      
      // IMPORTANTE: Verificar específicamente que meal_plans está presente
      if (!plansResponse || !plansResponse.meal_plans) {
        throw new Error("Formato de respuesta inválido - no se encontró meal_plans");
      }
      
      setActivePlans(plansResponse.meal_plans);
      
      // Agregar información de diagnóstico en la consola
      console.log("Planes cargados:", plansResponse.meal_plans.length);
      console.log("¿Planes desde localStorage?", plansResponse.fromLocalStorage === true);
      console.log("¿Planes desde API?", plansResponse.fromAPI === true);
      
    } catch (err) {
      console.error("Error cargando planes activos:", err);
      setPlansError("No se pudieron cargar tus planes activos. " + err.message);
    } finally {
      setPlansLoading(false);
    }
  };
  
  // Aplicar los objetivos del perfil a un plan seleccionado
  const applyProfileToPlan = async () => {
    if (!selectedPlanId || !profile) {
      console.error("No hay plan seleccionado o perfil para aplicar");
      return;
    }
    
    setApplyingToPlans(true);
    try {
      // Primero, obtener el plan completo
      console.log(`Dashboard: Aplicando objetivos al plan ${selectedPlanId}...`);
      const plan = await MealPlanService.getById(selectedPlanId);
      
      // Verificar que tenemos los datos necesarios en el perfil
      if (!profile.goal_calories || !profile.target_protein_g || 
          !profile.target_carbs_g || !profile.target_fat_g) {
        throw new Error("El perfil nutricional no tiene objetivos completos");
      }
      
      // Actualizar con los objetivos del perfil
      const updatedPlan = {
        ...plan,
        target_calories: profile.goal_calories,
        target_protein_g: profile.target_protein_g,
        target_carbs_g: profile.target_carbs_g,
        target_fat_g: profile.target_fat_g
      };
      
      // Enviar actualización
      console.log("Dashboard: Actualizando plan con objetivos:", updatedPlan);
      await MealPlanService.update(selectedPlanId, updatedPlan);
      
      // Recargar planes activos para reflejar cambios
      await loadActivePlans();
      
      alert("¡Objetivos aplicados correctamente al plan!");
    } catch (err) {
      console.error("Error al aplicar objetivos:", err);
      setError("No se pudieron aplicar los objetivos al plan seleccionado: " + 
               (err.message || "Error desconocido"));
    } finally {
      setApplyingToPlans(false);
      setSelectedPlanId(null);
    }
  };
  
  // Crear un nuevo plan con los objetivos del perfil
  const createPlanWithProfile = () => {
    if (!profile) {
      console.error("No hay perfil para crear plan");
      return;
    }
    
    // Verificar que tenemos los datos necesarios en el perfil
    if (!profile.goal_calories || !profile.target_protein_g || 
        !profile.target_carbs_g || !profile.target_fat_g) {
      setError("El perfil nutricional no tiene objetivos completos");
      return;
    }
    
    // Guardar objetivos temporalmente
    console.log("Dashboard: Guardando objetivos para nuevo plan:", {
      target_calories: profile.goal_calories,
      target_protein_g: profile.target_protein_g,
      target_carbs_g: profile.target_carbs_g,
      target_fat_g: profile.target_fat_g
    });
    
    localStorage.setItem('temp_nutrition_targets', JSON.stringify({
      target_calories: profile.goal_calories,
      target_protein_g: profile.target_protein_g,
      target_carbs_g: profile.target_carbs_g,
      target_fat_g: profile.target_fat_g
    }));
    
    // Navegar a crear plan
    navigate('/nutrition');
    localStorage.setItem('nutrition_tab', '2'); // Tab de creación
    window.location.reload();
  };
  
  // Ir a la calculadora de macros
  const goToMacroCalculator = () => {
    // Navegar a la pestaña de calculadora
    localStorage.setItem('nutrition_tab', '8');
    window.location.reload();
  };
  
  // Calcular porcentaje de macros
  const calculateMacroPercentages = () => {
    if (!profile) return { protein: 0, carbs: 0, fat: 0 };
    
    // Verifica si existen los campos necesarios
    const hasRequiredFields = 
      profile.target_protein_g != null && 
      profile.target_carbs_g != null && 
      profile.target_fat_g != null;
    
    if (!hasRequiredFields) {
      console.warn("El perfil no tiene todos los campos de macros necesarios:", profile);
      return { protein: 0, carbs: 0, fat: 0 };
    }
    
    const proteinCals = profile.target_protein_g * 4;
    const carbsCals = profile.target_carbs_g * 4;
    const fatCals = profile.target_fat_g * 9;
    const totalCals = proteinCals + carbsCals + fatCals;
    
    if (totalCals === 0) return { protein: 0, carbs: 0, fat: 0 };
    
    return {
      protein: Math.round((proteinCals / totalCals) * 100) || 0,
      carbs: Math.round((carbsCals / totalCals) * 100) || 0,
      fat: Math.round((fatCals / totalCals) * 100) || 0
    };
  };
  
  const macroPercentages = calculateMacroPercentages();
  
  // Estados para renderizado condicional
  const hasProfile = profile !== null;
  const hasTargets = hasProfile && 
                     profile.goal_calories != null && 
                     profile.target_protein_g != null && 
                     profile.target_carbs_g != null && 
                     profile.target_fat_g != null;
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom>Dashboard Nutricional</Typography>
      
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      
      {!hasProfile ? (
        <Alert severity="info" sx={{ mb: 3 }}>
          No tienes un perfil nutricional configurado. 
          Usa la calculadora de macros para establecer tus objetivos.
          
          <Button 
            variant="contained"
            color="primary"
            startIcon={<FontAwesomeIcon icon={faCalculator} />}
            onClick={goToMacroCalculator}
            sx={{ mt: 2 }}
          >
            Ir a Calculadora de Macros
          </Button>
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {/* Resumen del perfil nutricional */}
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={faChartPie} style={{ marginRight: '10px' }} />
                  Tus Objetivos Nutricionales
                </Typography>
                
                <Box sx={{ mt: 3 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          Objetivo Diario: {profile.goal_calories || 0} kcal
                        </Typography>
                        <Typography variant="body2" gutterBottom>
                          Basado en tus características físicas, nivel de actividad y meta de {profile.goal || 'mantenimiento'}.
                        </Typography>
                      </Box>
                      
                      <Divider sx={{ mb: 2 }} />
                    </Grid>
                    
                    <Grid item xs={12} sm={4}>
                      <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#e8f5e9' }}>
                        <Typography variant="h5" color="#2e7d32">
                          {profile.target_protein_g || 0}g
                        </Typography>
                        <Typography variant="body2">Proteínas</Typography>
                        <Typography variant="caption" display="block">
                          {macroPercentages.protein}% de calorías
                        </Typography>
                        <Chip 
                          label={`${Math.round((profile.target_protein_g || 0) / 7)}g/día`}
                          size="small"
                          color="success"
                          sx={{ mt: 1 }}
                        />
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={4}>
                      <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#e3f2fd' }}>
                        <Typography variant="h5" color="#1565c0">
                          {profile.target_carbs_g || 0}g
                        </Typography>
                        <Typography variant="body2">Carbohidratos</Typography>
                        <Typography variant="caption" display="block">
                          {macroPercentages.carbs}% de calorías
                        </Typography>
                        <Chip 
                          label={`${Math.round((profile.target_carbs_g || 0) / 7)}g/día`}
                          size="small"
                          color="primary"
                          sx={{ mt: 1 }}
                        />
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={4}>
                      <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#fff3e0' }}>
                        <Typography variant="h5" color="#e65100">
                          {profile.target_fat_g || 0}g
                        </Typography>
                        <Typography variant="body2">Grasas</Typography>
                        <Typography variant="caption" display="block">
                          {macroPercentages.fat}% de calorías
                        </Typography>
                        <Chip 
                          label={`${Math.round((profile.target_fat_g || 0) / 7)}g/día`}
                          size="small"
                          color="warning"
                          sx={{ mt: 1 }}
                        />
                      </Paper>
                    </Grid>
                  </Grid>
                </Box>
                
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<FontAwesomeIcon icon={faCalculator} />}
                    onClick={goToMacroCalculator}
                  >
                    Recalcular Objetivos
                  </Button>
                  
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<FontAwesomeIcon icon={faPlus} />}
                    onClick={createPlanWithProfile}
                    disabled={!hasTargets}
                  >
                    Crear Plan con Estos Objetivos
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Aplicar a planes activos */}
          <Grid item xs={12} md={6}>
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
                ) : plansLoading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <CircularProgress />
                  </Box>
                ) : plansError ? (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {plansError}
                    <Button 
                      size="small" 
                      sx={{ ml: 2 }} 
                      onClick={loadActivePlans}
                      startIcon={<FontAwesomeIcon icon={faSyncAlt} />}
                    >
                      Reintentar
                    </Button>
                  </Alert>
                ) : activePlans.length === 0 ? (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    No tienes planes de comida activos. Crea un plan primero para aplicarle tus objetivos nutricionales.
                  </Alert>
                ) : (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="body2" gutterBottom>
                      Selecciona un plan de comida activo para aplicarle tus objetivos nutricionales actuales:
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
              </CardContent>
            </Card>
          </Grid>
          
          {/* Progreso actual */}
          <Grid item xs={12}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={faChartLine} style={{ marginRight: '10px' }} />
                  Resumen Semanal
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Próximamente: Una vista resumida de tu progreso alimenticio semanal comparado con tus objetivos.
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        <FontAwesomeIcon icon={faFire} style={{ marginRight: '8px' }} />
                        Calorías Consumidas
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Próximamente: Seguimiento de tus calorías consumidas vs. objetivo
                      </Typography>
                      <LinearProgress variant="determinate" value={0} sx={{ height: 10, borderRadius: 5 }} />
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        <FontAwesomeIcon icon={faDrumstickBite} style={{ marginRight: '8px' }} />
                        Proteínas Consumidas
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Próximamente: Seguimiento de proteínas consumidas vs. objetivo
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={0} 
                        color="success"
                        sx={{ height: 10, borderRadius: 5 }} 
                      />
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default NutritionDashboard;