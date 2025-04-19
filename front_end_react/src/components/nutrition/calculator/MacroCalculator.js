// src/components/nutrition/calculator/MacroCalculator.js
import React, { useState, useEffect } from 'react';
import {
    Box, Typography, TextField, Button, Card, CardContent,
    FormControl, InputLabel, Select, MenuItem, Grid,
    Slider, Alert, CircularProgress, Divider, Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
    faCalculator, faChartPie, faDumbbell, faWeight, 
    faRuler, faSave, faArrowRight 
} from '@fortawesome/free-solid-svg-icons';
import { NutritionCalculator } from '../../../services/NutritionService';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useNavigate } from 'react-router-dom';

const MacroCalculator = ({ user }) => {
    const [loading, setLoading] = useState(false);
    const [calculating, setCalculating] = useState(false);
    const [error, setError] = useState(null);
    const [alert, setAlert] = useState(null);
    const [profile, setProfile] = useState(null);
    const [results, setResults] = useState(null);
    const navigate = useNavigate();

    // Formulario
    const [formData, setFormData] = useState({
        units: 'metric',
        formula: 'mifflin_st_jeor',
        gender: 'male',
        age: 30,
        height: 175, // cm
        weight: 75, // kg
        body_fat_percentage: null,
        activity_level: 'moderate',
        goal: 'maintain',
        goal_intensity: 'normal'
    });

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
            // Convertir datos numéricos a números antes de enviar
            const dataToSend = {
                ...formData,
                age: parseInt(formData.age, 10),
                height: parseFloat(formData.height),
                weight: parseFloat(formData.weight),
                body_fat_percentage: formData.body_fat_percentage ? parseFloat(formData.body_fat_percentage) : null,
            };
            
            console.log("Enviando datos para cálculo:", dataToSend);
            const result = await NutritionCalculator.calculateMacros(dataToSend);
            console.log("Resultados recibidos:", result);
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
            target_fat_g: results.macros.fat.grams
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

    // Componente para gráfico de macros
    const MacroChart = ({ macros }) => {
        if (!macros) return null;
        
        const data = [
            { name: 'Proteínas', value: macros.protein.calories, color: '#4caf50' },
            { name: 'Carbohidratos', value: macros.carbs.calories, color: '#2196f3' },
            { name: 'Grasas', value: macros.fat.calories, color: '#ff9800' }
        ];

        // Validar datos antes de renderizar gráfico
        if (data.some(item => typeof item.value !== 'number' || isNaN(item.value))) {
            console.warn("Datos inválidos para MacroChart:", data);
            return <Typography variant="caption" color="error">Datos de calorías inválidos para el gráfico.</Typography>;
        }

        return (
            <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        fill="#8884d8"
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }) => 
                            percent > 0 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''
                        }
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip
                        formatter={(value, name, props) => 
                            [`${value.toFixed(0)} kcal (${(props.payload.percent * 100).toFixed(1)}%)`, name]
                        }
                    />
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
        );
    };

    // Renderizado de resultados
    const renderResults = () => {
        if (!results) return null;

        // Validar estructura de resultados
        if (!results.macros || !results.macros.protein || !results.macros.carbs || !results.macros.fat) {
            console.error("Estructura de resultados inválida:", results);
            return <Alert severity="warning" sx={{ mt: 3 }}>Resultados incompletos recibidos.</Alert>;
        }

        return (
            <Card sx={{ mt: 4, boxShadow: 3 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                        <FontAwesomeIcon icon={faChartPie} style={{ marginRight: '10px' }} />
                        Resultados del Cálculo
                    </Typography>
                    <Divider sx={{ mb: 3 }}/>

                    <Grid container spacing={3}>
                        <Grid item xs={12} md={6}>
                            <Box>
                                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                                    Métricas Estimadas:
                                </Typography>
                                <Typography variant="body1">
                                    <strong>BMR (Metabolismo Basal):</strong> {results.bmr?.toFixed(0) ?? 'N/A'} kcal
                                </Typography>
                                <Typography variant="body1">
                                    <strong>TDEE (Gasto Energético Diario):</strong> {results.tdee?.toFixed(0) ?? 'N/A'} kcal
                                </Typography>
                                <Typography variant="body1">
                                    <strong>BMI (Índice de Masa Corporal):</strong> {results.bmi?.toFixed(1) ?? 'N/A'}
                                </Typography>
                                <Typography variant="h6" sx={{ mt: 2, fontWeight: 'bold', color: 'secondary.main' }}>
                                    Objetivo Diario: {results.goal_calories?.toFixed(0) ?? 'N/A'} kcal
                                </Typography>
                            </Box>

                            <Box sx={{ mt: 3 }}>
                                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                                    Macronutrientes Diarios (Gramos):
                                </Typography>
                                <Grid container spacing={1}>
                                    <Grid item xs={4}>
                                        <Paper elevation={1} sx={{ p: 1.5, textAlign: 'center', bgcolor: '#e8f5e9' }}>
                                            <Typography variant="h6" color="#2e7d32">
                                                {results.macros.protein.grams?.toFixed(0) ?? 'N/A'}g
                                            </Typography>
                                            <Typography variant="body2">Proteínas</Typography>
                                            <Typography variant="caption" display="block">
                                                {results.macros.protein.percentage?.toFixed(0) ?? 'N/A'}%
                                            </Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper elevation={1} sx={{ p: 1.5, textAlign: 'center', bgcolor: '#e3f2fd' }}>
                                            <Typography variant="h6" color="#1565c0">
                                                {results.macros.carbs.grams?.toFixed(0) ?? 'N/A'}g
                                            </Typography>
                                            <Typography variant="body2">Carbohidratos</Typography>
                                            <Typography variant="caption" display="block">
                                                {results.macros.carbs.percentage?.toFixed(0) ?? 'N/A'}%
                                            </Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper elevation={1} sx={{ p: 1.5, textAlign: 'center', bgcolor: '#fff3e0' }}>
                                            <Typography variant="h6" color="#e65100">
                                                {results.macros.fat.grams?.toFixed(0) ?? 'N/A'}g
                                            </Typography>
                                            <Typography variant="body2">Grasas</Typography>
                                            <Typography variant="caption" display="block">
                                                {results.macros.fat.percentage?.toFixed(0) ?? 'N/A'}%
                                            </Typography>
                                        </Paper>
                                    </Grid>
                                </Grid>
                            </Box>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                                <Typography variant="subtitle1" gutterBottom align="center">
                                    Distribución Calórica (%)
                                </Typography>
                                
                                {results.macros.protein.calories != null && 
                                 results.macros.carbs.calories != null && 
                                 results.macros.fat.calories != null ? (
                                    <MacroChart macros={results.macros} />
                                ) : (
                                    <Typography variant="caption">Datos insuficientes para gráfico.</Typography>
                                )}
                            </Box>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
        );
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
                            {/* Fila 1: Unidades, Fórmula, Género, Edad */}
                            <Grid item xs={12} sm={6} md={3}>
                                <FormControl fullWidth size="small">
                                    <InputLabel id="units-label">Unidades</InputLabel>
                                    <Select
                                        labelId="units-label"
                                        id="units"
                                        name="units"
                                        value={formData.units}
                                        onChange={handleChange}
                                        label="Unidades"
                                    >
                                        <MenuItem value="metric">Métrico (kg/cm)</MenuItem>
                                        <MenuItem value="imperial">Imperial (lb/in)</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            
                            <Grid item xs={12} sm={6} md={3}>
                                <FormControl fullWidth size="small">
                                    <InputLabel id="formula-label">Fórmula</InputLabel>
                                    <Select
                                        labelId="formula-label"
                                        id="formula"
                                        name="formula"
                                        value={formData.formula}
                                        onChange={handleChange}
                                        label="Fórmula"
                                    >
                                        <MenuItem value="mifflin_st_jeor">Mifflin-St Jeor</MenuItem>
                                        <MenuItem value="harris_benedict">Harris-Benedict</MenuItem>
                                        <MenuItem value="katch_mcardle">Katch-McArdle</MenuItem>
                                        <MenuItem value="who">OMS</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            
                            <Grid item xs={12} sm={6} md={3}>
                                <FormControl fullWidth size="small">
                                    <InputLabel id="gender-label">Género</InputLabel>
                                    <Select
                                        labelId="gender-label"
                                        id="gender"
                                        name="gender"
                                        value={formData.gender}
                                        onChange={handleChange}
                                        label="Género"
                                    >
                                        <MenuItem value="male">Masculino</MenuItem>
                                        <MenuItem value="female">Femenino</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            
                            <Grid item xs={12} sm={6} md={3}>
                                <TextField
                                    fullWidth
                                    id="age"
                                    name="age"
                                    label="Edad"
                                    type="number"
                                    size="small"
                                    value={formData.age}
                                    onChange={handleChange}
                                    InputProps={{ inputProps: { min: 15, max: 100 } }}
                                />
                                <Slider
                                    value={typeof formData.age === 'number' ? formData.age : 0}
                                    onChange={handleSliderChange('age')}
                                    aria-labelledby="age-slider"
                                    min={15}
                                    max={100}
                                    size="small"
                                    sx={{ mt: -1 }}
                                />
                            </Grid>

                            {/* Fila 2: Altura, Peso, % Grasa */}
                            <Grid item xs={12} sm={6} md={4}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <FontAwesomeIcon icon={faRuler} style={{ marginRight: '10px', color: '#666' }} />
                                    <TextField
                                        fullWidth
                                        id="height"
                                        name="height"
                                        label={`Altura (${formData.units === 'metric' ? 'cm' : 'in'})`}
                                        type="number"
                                        size="small"
                                        value={formData.height}
                                        onChange={handleChange}
                                        InputProps={{
                                            inputProps: {
                                                min: formData.units === 'metric' ? 120 : 48,
                                                max: formData.units === 'metric' ? 220 : 84,
                                                step: 0.1
                                            }
                                        }}
                                    />
                                </Box>
                                <Slider
                                    value={typeof formData.height === 'number' ? formData.height : 0}
                                    onChange={handleSliderChange('height')}
                                    aria-labelledby="height-slider"
                                    min={formData.units === 'metric' ? 120 : 48}
                                    max={formData.units === 'metric' ? 220 : 84}
                                    step={formData.units === 'metric' ? 1 : 0.5}
                                    size="small"
                                    sx={{ mt: -1 }}
                                />
                            </Grid>
                            
                            <Grid item xs={12} sm={6} md={4}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <FontAwesomeIcon icon={faWeight} style={{ marginRight: '10px', color: '#666' }} />
                                    <TextField
                                        fullWidth
                                        id="weight"
                                        name="weight"
                                        label={`Peso (${formData.units === 'metric' ? 'kg' : 'lb'})`}
                                        type="number"
                                        size="small"
                                        value={formData.weight}
                                        onChange={handleChange}
                                        InputProps={{
                                            inputProps: {
                                                min: formData.units === 'metric' ? 40 : 88,
                                                max: formData.units === 'metric' ? 200 : 440,
                                                step: 0.1
                                            }
                                        }}
                                    />
                                </Box>
                                <Slider
                                    value={typeof formData.weight === 'number' ? formData.weight : 0}
                                    onChange={handleSliderChange('weight')}
                                    aria-labelledby="weight-slider"
                                    min={formData.units === 'metric' ? 40 : 88}
                                    max={formData.units === 'metric' ? 200 : 440}
                                    step={formData.units === 'metric' ? 0.5 : 1}
                                    size="small"
                                    sx={{ mt: -1 }}
                                />
                            </Grid>
                            
                            <Grid item xs={12} sm={6} md={4}>
                                <TextField
                                    fullWidth
                                    id="body_fat_percentage"
                                    name="body_fat_percentage"
                                    label="% Grasa Corporal"
                                    type="number"
                                    size="small"
                                    value={formData.body_fat_percentage || ''}
                                    onChange={handleChange}
                                    InputProps={{
                                        inputProps: { min: 3, max: 60, step: 0.1 },
                                        endAdornment: <Typography variant="caption" sx={{mr: 1}}>%</Typography>
                                    }}
                                    helperText={formData.formula === 'katch_mcardle' ? 'Requerido por Katch-McArdle' : 'Opcional'}
                                    required={formData.formula === 'katch_mcardle'}
                                />
                                <Slider
                                    value={typeof formData.body_fat_percentage === 'number' ? formData.body_fat_percentage : 0}
                                    onChange={handleSliderChange('body_fat_percentage')}
                                    aria-labelledby="bodyfat-slider"
                                    min={3}
                                    max={60}
                                    step={0.5}
                                    size="small"
                                    sx={{ mt: -1 }}
                                />
                            </Grid>

                            {/* Fila 3: Nivel Actividad, Objetivo, Intensidad */}
                            <Grid item xs={12} sm={6} md={4}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <FontAwesomeIcon icon={faDumbbell} style={{ marginRight: '10px', color: '#666' }} />
                                    <FormControl fullWidth size="small">
                                        <InputLabel id="activity-level-label">Nivel Actividad</InputLabel>
                                        <Select
                                            labelId="activity-level-label"
                                            id="activity_level"
                                            name="activity_level"
                                            value={formData.activity_level}
                                            onChange={handleChange}
                                            label="Nivel Actividad"
                                        >
                                            <MenuItem value="sedentary">Sedentario</MenuItem>
                                            <MenuItem value="light">Ligero (1-3 días/sem)</MenuItem>
                                            <MenuItem value="moderate">Moderado (3-5 días/sem)</MenuItem>
                                            <MenuItem value="active">Activo (6-7 días/sem)</MenuItem>
                                            <MenuItem value="very_active">Muy Activo (intenso diario)</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Box>
                            </Grid>
                            
                            <Grid item xs={12} sm={6} md={4}>
                                <FormControl fullWidth size="small">
                                    <InputLabel id="goal-label">Objetivo</InputLabel>
                                    <Select
                                        labelId="goal-label"
                                        id="goal"
                                        name="goal"
                                        value={formData.goal}
                                        onChange={handleChange}
                                        label="Objetivo"
                                    >
                                        <MenuItem value="maintain">Mantener Peso</MenuItem>
                                        <MenuItem value="lose">Perder Peso</MenuItem>
                                        <MenuItem value="gain">Ganar Peso</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            
                            <Grid item xs={12} sm={6} md={4}>
                                <FormControl fullWidth size="small">
                                    <InputLabel id="goal-intensity-label">Intensidad</InputLabel>
                                    <Select
                                        labelId="goal-intensity-label"
                                        id="goal_intensity"
                                        name="goal_intensity"
                                        value={formData.goal_intensity}
                                        onChange={handleChange}
                                        label="Intensidad"
                                        disabled={formData.goal === 'maintain'}
                                    >
                                        <MenuItem value="light">
                                            {formData.goal === 'lose' ? 'Ligero (≈ -250 kcal)' : 'Ligero (≈ +250 kcal)'}
                                        </MenuItem>
                                        <MenuItem value="normal">
                                            {formData.goal === 'lose' ? 'Normal (≈ -500 kcal)' : 'Normal (≈ +500 kcal)'}
                                        </MenuItem>
                                        <MenuItem value="aggressive">
                                            {formData.goal === 'lose' ? 'Agresivo (≈ -750 kcal)' : 'Agresivo (≈ +750 kcal)'}
                                        </MenuItem>
                                        <MenuItem value="very_aggressive">
                                            {formData.goal === 'lose' ? 'Muy Agresivo (≈ -1000 kcal)' : 'Muy Agresivo (≈ +1000 kcal)'}
                                        </MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            {/* Fila 4: Botón Calcular */}
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
            {renderResults()}

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

export default MacroCalculator;