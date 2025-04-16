// src/components/nutrition/calculator/MacroCalculator.js
import React, { useState, useEffect } from 'react';
import { 
    Box, Typography, TextField, Button, Card, CardContent, 
    FormControl, InputLabel, Select, MenuItem, Grid,
    Slider, Alert, CircularProgress, Divider, Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalculator, faChartPie, faDumbbell, faWeight, faRuler } from '@fortawesome/free-solid-svg-icons';
import { NutritionCalculator } from '../../../services/NutritionService';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const MacroCalculator = ({ user }) => {
    const [loading, setLoading] = useState(false);
    const [calculating, setCalculating] = useState(false);
    const [error, setError] = useState(null);
    const [profile, setProfile] = useState(null);
    const [results, setResults] = useState(null);
    
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
            setLoading(true);
            try {
                const profileData = await NutritionCalculator.getProfile();
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
                console.error("Error loading nutrition profile:", err);
                setError("No se pudo cargar tu perfil nutricional.");
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
    };
    
    // Manejador para cambios en sliders
    const handleSliderChange = (name) => (e, newValue) => {
        setFormData(prev => ({
            ...prev,
            [name]: newValue
        }));
    };
    
    // Manejador para enviar el formulario
    const handleSubmit = async (e) => {
        e.preventDefault();
        setCalculating(true);
        setError(null);
        
        try {
            const result = await NutritionCalculator.calculateMacros(formData);
            setResults(result);
        } catch (err) {
            console.error("Error calculating macros:", err);
            setError("Error al calcular los macros. Por favor, inténtalo de nuevo.");
        } finally {
            setCalculating(false);
        }
    };
    
    // Componente para gráfico de macros
    const MacroChart = ({ macros }) => {
        const data = [
            { name: 'Proteínas', value: macros.protein.calories, color: '#4caf50' },
            { name: 'Carbohidratos', value: macros.carbs.calories, color: '#2196f3' },
            { name: 'Grasas', value: macros.fat.calories, color: '#ff9800' }
        ];
        
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
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip 
                        formatter={(value) => [`${value} kcal`, 'Calorías']}
                    />
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
        );
    };
    
    // Renderizado de resultados
    const renderResults = () => {
        if (!results) return null;
        
        return (
            <Card sx={{ mt: 4 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        <FontAwesomeIcon icon={faChartPie} style={{ marginRight: '10px' }} />
                        Resultados del Cálculo
                    </Typography>
                    
                    <Grid container spacing={3}>
                        <Grid item xs={12} md={6}>
                            <Box>
                                <Typography variant="subtitle1" gutterBottom>Métricas Básicas:</Typography>
                                <Typography variant="body1">
                                    <strong>BMR (Metabolismo Basal):</strong> {results.bmr} kcal
                                </Typography>
                                <Typography variant="body1">
                                    <strong>TDEE (Gasto Energético Diario):</strong> {results.tdee} kcal
                                </Typography>
                                <Typography variant="body1">
                                    <strong>BMI (Índice de Masa Corporal):</strong> {results.bmi}
                                </Typography>
                                <Typography variant="body1" sx={{ mt: 2, fontWeight: 'bold', fontSize: '1.2rem' }}>
                                    Objetivo Diario: {results.goal_calories} kcal
                                </Typography>
                            </Box>
                            
                            <Box sx={{ mt: 3 }}>
                                <Typography variant="subtitle1" gutterBottom>Macronutrientes Diarios:</Typography>
                                <Grid container spacing={2}>
                                    <Grid item xs={4}>
                                        <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#e8f5e9' }}>
                                            <Typography variant="h6" color="#2e7d32">
                                                {results.macros.protein.grams}g
                                            </Typography>
                                            <Typography variant="body2">Proteínas</Typography>
                                            <Typography variant="caption" display="block">
                                                {results.macros.protein.percentage}%
                                            </Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#e3f2fd' }}>
                                            <Typography variant="h6" color="#1565c0">
                                                {results.macros.carbs.grams}g
                                            </Typography>
                                            <Typography variant="body2">Carbohidratos</Typography>
                                            <Typography variant="caption" display="block">
                                                {results.macros.carbs.percentage}%
                                            </Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: '#fff3e0' }}>
                                            <Typography variant="h6" color="#e65100">
                                                {results.macros.fat.grams}g
                                            </Typography>
                                            <Typography variant="body2">Grasas</Typography>
                                            <Typography variant="caption" display="block">
                                                {results.macros.fat.percentage}%
                                            </Typography>
                                        </Paper>
                                    </Grid>
                                </Grid>
                            </Box>
                        </Grid>
                        
                        <Grid item xs={12} md={6}>
                            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                                <Typography variant="subtitle1" gutterBottom align="center">
                                    Distribución Calórica
                                </Typography>
                                <MacroChart macros={results.macros} />
                            </Box>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
        );
    };
    
    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
            </Box>
        );
    }
    
    return (
        <Box sx={{ p: 2 }}>
            <Card>
                <CardContent>
                    <Typography variant="h5" gutterBottom>
                        <FontAwesomeIcon icon={faCalculator} style={{ marginRight: '10px' }} />
                        Calculadora de Macros
                    </Typography>
                    
                    {error && (
                        <Alert severity="error" sx={{ mb: 3 }}>
                            {error}
                        </Alert>
                    )}
                    
                    <form onSubmit={handleSubmit}>
                        <Grid container spacing={3}>
                            {/* Unidades */}
                            <Grid item xs={12} sm={6} md={3}>
                                <FormControl fullWidth>
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
                            
                            {/* Fórmula */}
                            <Grid item xs={12} sm={6} md={3}>
                                <FormControl fullWidth>
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
                            
                            {/* Género */}
                            <Grid item xs={12} sm={6} md={3}>
                                <FormControl fullWidth>
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
                            
                            {/* Edad */}
                            <Grid item xs={12} sm={6} md={3}>
                                <TextField
                                    fullWidth
                                    id="age"
                                    name="age"
                                    label="Edad"
                                    type="number"
                                    value={formData.age}
                                    onChange={handleChange}
                                    InputProps={{ inputProps: { min: 15, max: 100 } }}
                                />
                                <Slider
                                    value={formData.age}
                                    onChange={handleSliderChange('age')}
                                    aria-labelledby="age-slider"
                                    min={15}
                                    max={100}
                                    valueLabelDisplay="auto"
                                />
                            </Grid>
                            
                            {/* Altura */}
                            <Grid item xs={12} sm={6} md={4}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <FontAwesomeIcon icon={faRuler} style={{ marginRight: '10px' }} />
                                    <TextField
                                        fullWidth
                                        id="height"
                                        name="height"
                                        label={`Altura (${formData.units === 'metric' ? 'cm' : 'pulgadas'})`}
                                        type="number"
                                        value={formData.height}
                                        onChange={handleChange}
                                        InputProps={{ 
                                            inputProps: { 
                                                min: formData.units === 'metric' ? 120 : 48, 
                                                max: formData.units === 'metric' ? 220 : 84 
                                            } 
                                        }}
                                    />
                                </Box>
                                <Slider
                                    value={formData.height}
                                    onChange={handleSliderChange('height')}
                                    aria-labelledby="height-slider"
                                    min={formData.units === 'metric' ? 120 : 48}
                                    max={formData.units === 'metric' ? 220 : 84}
                                    valueLabelDisplay="auto"
                                />
                            </Grid>
                            
                            {/* Peso */}
                            <Grid item xs={12} sm={6} md={4}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <FontAwesomeIcon icon={faWeight} style={{ marginRight: '10px' }} />
                                    <TextField
                                        fullWidth
                                        id="weight"
                                        name="weight"
                                        label={`Peso (${formData.units === 'metric' ? 'kg' : 'libras'})`}
                                        type="number"
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
                                    value={formData.weight}
                                    onChange={handleSliderChange('weight')}
                                    aria-labelledby="weight-slider"
                                    min={formData.units === 'metric' ? 40 : 88}
                                    max={formData.units === 'metric' ? 200 : 440}
                                    valueLabelDisplay="auto"
                                />
                            </Grid>
                            
                            {/* % Grasa Corporal (opcional) */}
                            <Grid item xs={12} sm={6} md={4}>
                                <TextField
                                    fullWidth
                                    id="body_fat_percentage"
                                    name="body_fat_percentage"
                                    label="% Grasa Corporal (opcional)"
                                    type="number"
                                    value={formData.body_fat_percentage || ''}
                                    onChange={handleChange}
                                    InputProps={{ 
                                        inputProps: { min: 5, max: 50, step: 0.1 },
                                        endAdornment: <InputLabel>%</InputLabel>
                                    }}
                                    helperText="Necesario para la fórmula Katch-McArdle"
                                />
                            </Grid>
                            
                            {/* Nivel de Actividad */}
                            <Grid item xs={12} sm={6} md={4}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <FontAwesomeIcon icon={faDumbbell} style={{ marginRight: '10px' }} />
                                    <FormControl fullWidth>
                                        <InputLabel id="activity-level-label">Nivel de Actividad</InputLabel>
                                        <Select
                                            labelId="activity-level-label"
                                            id="activity_level"
                                            name="activity_level"
                                            value={formData.activity_level}
                                            onChange={handleChange}
                                            label="Nivel de Actividad"
                                        >
                                            <MenuItem value="sedentary">Sedentario (poco o nada de ejercicio)</MenuItem>
                                            <MenuItem value="light">Ligero (ejercicio 1-3 días/semana)</MenuItem>
                                            <MenuItem value="moderate">Moderado (ejercicio 3-5 días/semana)</MenuItem>
                                            <MenuItem value="active">Activo (ejercicio 6-7 días/semana)</MenuItem>
                                            <MenuItem value="very_active">Muy Activo (ejercicio intenso diario)</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Box>
                            </Grid>
                            
                            {/* Objetivo */}
                            <Grid item xs={12} sm={6} md={4}>
                                <FormControl fullWidth>
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
                            
                            {/* Intensidad del Objetivo */}
                            <Grid item xs={12} sm={6} md={4}>
                                <FormControl fullWidth>
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
                                        <MenuItem value="normal">Normal (±300-500 kcal/día)</MenuItem>
                                        <MenuItem value="aggressive">Agresivo (±500-1000 kcal/día)</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            
                            {/* Botón de cálculo */}
                            <Grid item xs={12}>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    color="primary"
                                    size="large"
                                    disabled={calculating}
                                    startIcon={calculating ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faCalculator} />}
                                >
                                    {calculating ? 'Calculando...' : 'Calcular Macros'}
                                </Button>
                            </Grid>
                        </Grid>
                    </form>
                </CardContent>
            </Card>
            
            {renderResults()}
        </Box>
    );
};

export default MacroCalculator;