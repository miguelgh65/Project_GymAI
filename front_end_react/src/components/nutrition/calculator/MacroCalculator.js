// src/components/nutrition/calculator/MacroCalculator.js
import React, { useState, useEffect } from 'react';
import {
    Box, Typography, Button, Card, CardContent,
    Grid, Alert, CircularProgress, Divider
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
    faCalculator, faSave, faArrowRight
} from '@fortawesome/free-solid-svg-icons';
import { NutritionCalculator } from '../../../services/nutrition/NutritionCalculator';
import { useNavigate } from 'react-router-dom';

// Importación de componentes
import MacroDistributionSelector from './components/MacroDistributionSelector';
import ResultsDisplay from './components/ResultsDisplay';
import BasicInfoSection from './components/BasicInfoSection';
import PhysicalDataSection from './components/PhysicalDataSection';
import GoalsSection from './components/GoalsSection';
import { DEFAULT_FORM_VALUES, DEFAULT_MACRO_DISTRIBUTION } from './constants';

const MacroCalculator = ({ user }) => {
    const [loading, setLoading] = useState(false);
    const [calculating, setCalculating] = useState(false);
    const [error, setError] = useState(null);
    const [alert, setAlert] = useState(null);
    const [profile, setProfile] = useState(null);
    const [results, setResults] = useState(null);
    const navigate = useNavigate();

    // Estado de distribución de macros
    const [macroDistribution, setMacroDistribution] = useState(DEFAULT_MACRO_DISTRIBUTION);

    // Estado del formulario
    const [formData, setFormData] = useState(DEFAULT_FORM_VALUES);

    // Manejador para cambios en el formulario
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        // Limpiar resultados y alertas si cambian los datos del formulario
        setResults(null);
        setError(null);
        setAlert(null);
    };

    // Manejador para cambios en sliders
    const handleSliderChange = (name) => (e, newValue) => {
        setFormData(prev => ({
            ...prev,
            [name]: newValue
        }));
        // Limpiar resultados y alertas si cambian los datos del formulario
        setResults(null);
        setError(null);
        setAlert(null);
    };

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
                    // Inicializar el formulario con los datos del perfil
                    setFormData({
                        units: profileData.units || 'metric',
                        formula: profileData.formula || 'mifflin_st_jeor',
                        gender: profileData.gender || 'male',
                        age: profileData.age || 30,
                        height: profileData.height || 175,
                        weight: profileData.weight || 75,
                        body_fat_percentage: profileData.body_fat_percentage || null,
                        activity_level: profileData.activity_level || 'moderate',
                        goal: profileData.goal || 'maintain',
                        goal_intensity: profileData.goal_intensity || 'normal'
                    });

                    // Si hay resultados en el perfil, mostrarlos
                    if (profileData.goal_calories && profileData.macros) {
                        setResults({
                            bmr: profileData.bmr,
                            tdee: profileData.tdee,
                            bmi: profileData.bmi,
                            goal_calories: profileData.goal_calories,
                            macros: profileData.macros
                        });
                        
                        // Inicializar distribución de macros basada en el perfil
                        if (profileData.macros.protein && profileData.macros.carbs && profileData.macros.fat) {
                            setMacroDistribution({
                                protein: profileData.macros.protein.percentage || 25,
                                carbs: profileData.macros.carbs.percentage || 50,
                                fat: profileData.macros.fat.percentage || 25
                            });
                        }
                    }
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

    // Manejador para enviar el formulario de cálculo
    const handleSubmit = async (e) => {
        e.preventDefault();
        setCalculating(true);
        setError(null);
        setAlert(null);
        setResults(null); // Limpiar resultados previos antes de calcular

        // Validación simple
        if (!formData.age || !formData.height || !formData.weight) {
            setError("Por favor, completa los campos de edad, altura y peso.");
            setCalculating(false);
            return;
        }
        
        if (formData.formula === 'katch_mcardle' && !formData.body_fat_percentage) {
            setError("La fórmula Katch-McArdle requiere el % de grasa corporal.");
            setCalculating(false);
            return;
        }

        try {
            // Verificar que los porcentajes sumen 100%
            const totalPercentage = macroDistribution.protein + macroDistribution.carbs + macroDistribution.fat;
            if (Math.abs(totalPercentage - 100) > 0.5) {
                setError(`Los porcentajes de macros deben sumar 100% (actual: ${totalPercentage.toFixed(1)}%)`);
                setCalculating(false);
                return;
            }
            
            // Convertir datos numéricos a números antes de enviar
            const dataToSend = {
                ...formData,
                age: parseInt(formData.age, 10),
                height: parseFloat(formData.height),
                weight: parseFloat(formData.weight),
                body_fat_percentage: formData.body_fat_percentage ? parseFloat(formData.body_fat_percentage) : null,
                // Incluir la distribución de macros - asegurar que son números exactos
                macro_distribution: {
                    protein: parseFloat(macroDistribution.protein.toFixed(1)),
                    carbs: parseFloat(macroDistribution.carbs.toFixed(1)),
                    fat: parseFloat(macroDistribution.fat.toFixed(1))
                }
            };
            
            console.log("Enviando datos para cálculo:", dataToSend);
            console.log("Distribución de macros enviada:", dataToSend.macro_distribution);
            
            const result = await NutritionCalculator.calculateMacros(dataToSend);
            console.log("Resultados recibidos:", result);
            
            // Verificar si los porcentajes de macros en el resultado coinciden con los enviados
            const resultProteinPct = result.macros?.protein?.percentage || 0;
            const resultCarbsPct = result.macros?.carbs?.percentage || 0;
            const resultFatPct = result.macros?.fat?.percentage || 0;
            
            console.log("Porcentajes recibidos:", {
                protein: resultProteinPct,
                carbs: resultCarbsPct,
                fat: resultFatPct
            });
            
            // Aplicar un umbral de diferencia aceptable (3%)
            const proteinDiff = Math.abs(resultProteinPct - macroDistribution.protein);
            const carbsDiff = Math.abs(resultCarbsPct - macroDistribution.carbs);
            const fatDiff = Math.abs(resultFatPct - macroDistribution.fat);
            
            if (proteinDiff > 3 || carbsDiff > 3 || fatDiff > 3) {
                console.warn("La API no respetó los porcentajes de macros enviados. Recalculando localmente.");
                
                // Recalcular macros según los porcentajes deseados
                const goalCalories = result.goal_calories;
                const proteinGrams = Math.round((goalCalories * (macroDistribution.protein / 100)) / 4);
                const carbsGrams = Math.round((goalCalories * (macroDistribution.carbs / 100)) / 4);
                const fatGrams = Math.round((goalCalories * (macroDistribution.fat / 100)) / 9);
                
                // Corregir los macros en el resultado
                result.macros = {
                    protein: {
                        grams: proteinGrams,
                        calories: Math.round(proteinGrams * 4),
                        percentage: Math.round(macroDistribution.protein)
                    },
                    carbs: {
                        grams: carbsGrams,
                        calories: Math.round(carbsGrams * 4),
                        percentage: Math.round(macroDistribution.carbs)
                    },
                    fat: {
                        grams: fatGrams,
                        calories: Math.round(fatGrams * 9),
                        percentage: Math.round(macroDistribution.fat)
                    }
                };
                
                console.log("Macros recalculados:", result.macros);
            }
            
            setResults(result);
        } catch (err) {
            console.error("Error calculando macros:", err);
            setError(err.message || "Error al calcular los macros. Revisa los datos o inténtalo de nuevo.");
            setResults(null);
        } finally {
            setCalculating(false);
        }
    };

    // Función para aplicar resultados a un nuevo plan
    const handleApplyToNewPlan = () => {
        if (!results) {
            setAlert({ type: 'error', message: 'No hay resultados de macros para aplicar. Calcula primero.' });
            return;
        }
        
        // Extraer objetivos del estado 'results'
        const initialTargets = {
            calories: results.goal_calories,
            protein: results.macros.protein.grams,
            carbs: results.macros.carbs.grams,
            fat: results.macros.fat.grams,
            profileName: profile?.name || `Calculado ${new Date().toLocaleDateString()}`
        };
        
        // Guardar en localStorage para usar al crear un nuevo plan
        localStorage.setItem('temp_nutrition_targets', JSON.stringify({
            target_calories: initialTargets.calories,
            target_protein_g: initialTargets.protein,
            target_carbs_g: initialTargets.carbs,
            target_fat_g: initialTargets.fat
        }));
        
        // Navegar a la creación de plan
        navigate('/nutrition');
        localStorage.setItem('nutrition_tab', '2'); // Tab de creación de plan
        window.location.reload();
    };

    // Función para guardar perfil
    const handleSaveProfile = async () => {
        if (!results) {
            setAlert({ type: 'error', message: 'Calcula los macros antes de guardar el perfil.' });
            return;
        }
        
        setCalculating(true);
        setAlert(null);
        setError(null);

        // Construir objeto de perfil para guardar
        const profileToSave = {
            // Inputs
            units: formData.units,
            formula: formData.formula,
            gender: formData.gender,
            age: parseInt(formData.age, 10),
            height: parseFloat(formData.height),
            weight: parseFloat(formData.weight),
            body_fat_percentage: formData.body_fat_percentage ? parseFloat(formData.body_fat_percentage) : null,
            activity_level: formData.activity_level,
            goal: formData.goal,
            goal_intensity: formData.goal_intensity,
            // Resultados calculados
            bmr: results.bmr,
            tdee: results.tdee,
            bmi: results.bmi,
            goal_calories: results.goal_calories,
            macros: results.macros,
            // Metadatos
            last_calculated: new Date().toISOString(),
            // Campos para el dashboard (importante)
            target_protein_g: results.macros.protein.grams,
            target_carbs_g: results.macros.carbs.grams,
            target_fat_g: results.macros.fat.grams,
            // Añadir distribución de macros
            macro_distribution: macroDistribution
        };

        try {
            console.log("Guardando perfil:", profileToSave);
            const saved = await NutritionCalculator.saveProfile(profileToSave);
            
            if (saved) {
                setAlert({ type: 'success', message: 'Perfil nutricional guardado con éxito.' });
                setProfile(saved);
            } else {
                throw new Error('No se recibió confirmación al guardar el perfil.');
            }
        } catch (err) {
            console.error("Error al guardar perfil nutricional:", err);
            setAlert({ type: 'error', message: err.message || 'Ocurrió un error al guardar el perfil.' });
        } finally {
            setCalculating(false);
        }
    };

    // Renderizado principal del componente
    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>Cargando perfil...</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: { xs: 1, sm: 2 } }}>
            <Card elevation={2}>
                <CardContent>
                    <Typography variant="h5" gutterBottom>
                        <FontAwesomeIcon icon={faCalculator} style={{ marginRight: '10px' }} />
                        Calculadora de Macros
                    </Typography>
                    <Divider sx={{ mb: 3 }}/>

                    {/* Mensajes de Error/Alerta */}
                    {error && (
                        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                            {error}
                        </Alert>
                    )}
                    
                    {alert && (
                        <Alert severity={alert.type || 'info'} sx={{ mb: 3 }} onClose={() => setAlert(null)}>
                            {alert.message}
                        </Alert>
                    )}

                    {/* Formulario */}
                    <form onSubmit={handleSubmit}>
                        <Grid container spacing={3}>
                            {/* Información básica: Unidades, Fórmula, Género, Edad */}
                            <BasicInfoSection 
                                formData={formData} 
                                handleChange={handleChange} 
                                handleSliderChange={handleSliderChange} 
                            />
                            
                            {/* Datos físicos: Altura, Peso, % Grasa */}
                            <PhysicalDataSection 
                                formData={formData} 
                                handleChange={handleChange} 
                                handleSliderChange={handleSliderChange} 
                            />

                            {/* Objetivos: Nivel Actividad, Objetivo, Intensidad */}
                            <GoalsSection 
                                formData={formData} 
                                handleChange={handleChange} 
                            />
                            
                            {/* Selector de distribución de macros */}
                            <Grid item xs={12}>
                                <MacroDistributionSelector 
                                    distribution={macroDistribution} 
                                    onChange={setMacroDistribution} 
                                    disabled={calculating}
                                />
                            </Grid>

                            {/* Botón Calcular */}
                            <Grid item xs={12} sx={{ textAlign: 'center', mt: 2 }}>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    color="primary"
                                    size="large"
                                    disabled={calculating}
                                    startIcon={calculating ? 
                                        <CircularProgress size={20} color="inherit" /> : 
                                        <FontAwesomeIcon icon={faCalculator} />
                                    }
                                >
                                    {calculating ? 'Calculando...' : 'Calcular Macros'}
                                </Button>
                            </Grid>
                        </Grid>
                    </form>
                </CardContent>
            </Card>

            {/* Renderizar resultados si existen */}
            {results && <ResultsDisplay results={results} />}

            {/* Botones para Guardar Perfil y Aplicar a Plan */}
            {results && !calculating && (
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 3, mb: 2 }}>
                    <Button
                        variant="contained"
                        color="secondary"
                        onClick={handleApplyToNewPlan}
                        disabled={calculating}
                        startIcon={<FontAwesomeIcon icon={faArrowRight} />}
                    >
                        Aplicar a Nuevo Plan
                    </Button>
                    <Button
                        variant="outlined"
                        color="primary"
                        onClick={handleSaveProfile}
                        disabled={calculating}
                        startIcon={calculating ? 
                            <CircularProgress size={20} color="inherit"/> :
                            <FontAwesomeIcon icon={faSave} />
                        }
                    >
                        {calculating ? 'Guardando...' : 'Guardar como Perfil'}
                    </Button>
                </Box>
            )}
        </Box>
    );
};

// Asegurarse de que haya una exportación por defecto
export default MacroCalculator;