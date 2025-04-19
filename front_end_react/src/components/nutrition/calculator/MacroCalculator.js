// src/components/nutrition/calculator/MacroCalculator.js
import React, { useState, useEffect } from 'react';
import {
    Box, Typography, TextField, Button, Card, CardContent,
    FormControl, InputLabel, Select, MenuItem, Grid,
    Slider, Alert as MuiAlert, CircularProgress, Divider, Paper // Renombrado Alert a MuiAlert para evitar conflicto con estado 'alert'
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
// Añadidos los iconos que faltaban para los nuevos botones
import { faCalculator, faChartPie, faDumbbell, faWeight, faRuler, faSave, faArrowRight } from '@fortawesome/free-solid-svg-icons';
// Asumiendo que NutritionCalculator es el objeto/clase exportado desde NutritionService
import { NutritionCalculator } from '../../../services/NutritionService';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useNavigate } from 'react-router-dom'; // Importar useNavigate

const MacroCalculator = ({ user }) => {
    const [loading, setLoading] = useState(false); // Para carga inicial del perfil
    const [calculating, setCalculating] = useState(false); // Para el proceso de cálculo/guardado
    const [error, setError] = useState(null); // Para errores generales o de cálculo
    const [alert, setAlert] = useState(null); // Para mensajes de éxito/info (ej. guardado)
    const [profile, setProfile] = useState(null);
    const [results, setResults] = useState(null);
    const navigate = useNavigate(); // Hook para navegación

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
            setError(null); // Limpiar errores previos
            setAlert(null); // Limpiar alertas previas
            try {
                // Usar el método estático/objeto importado
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
                    // Asegurarse que la estructura de profileData.macros sea la esperada
                    if (profileData.goal_calories && profileData.macros && profileData.macros.protein) {
                         setResults({
                            bmr: profileData.bmr,
                            tdee: profileData.tdee,
                            bmi: profileData.bmi,
                            goal_calories: profileData.goal_calories,
                            macros: profileData.macros // Asume que ya tiene la estructura { protein: {grams, calories, percentage}, ... }
                        });
                    }
                }
            } catch (err) {
                console.error("Error loading nutrition profile:", err);
                setError("No se pudo cargar tu perfil nutricional. Puedes introducir los datos manualmente.");
            } finally {
                setLoading(false);
            }
        };

        loadProfile();
    }, []); // Se ejecuta solo al montar el componente

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

        // Validación simple (se puede mejorar)
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
            // Asegurarse de enviar los datos numéricos como números
             const dataToSend = {
                ...formData,
                age: parseInt(formData.age, 10),
                height: parseFloat(formData.height),
                weight: parseFloat(formData.weight),
                body_fat_percentage: formData.body_fat_percentage ? parseFloat(formData.body_fat_percentage) : null,
            };
            const result = await NutritionCalculator.calculateMacros(dataToSend);
            setResults(result);
        } catch (err) {
            console.error("Error calculating macros:", err);
            setError(err.message || "Error al calcular los macros. Revisa los datos o inténtalo de nuevo.");
             setResults(null); // Asegurar que no queden resultados viejos si hay error
        } finally {
            setCalculating(false);
        }
    };

    // --- NUEVAS FUNCIONES HANDLER para los botones ---
    const handleApplyToNewPlan = () => {
        if (!results) {
            setAlert({ type: 'error', message: 'No hay resultados de macros para aplicar. Calcula primero.' });
            return;
        }
        // Extraer los objetivos del estado 'results'
        const initialTargets = {
            calories: results.goal_calories,
            protein: results.macros.protein.grams,
            carbs: results.macros.carbs.grams,
            fat: results.macros.fat.grams,
            // Podrías incluir el nombre del perfil si se guardó o generar uno
            profileName: profile?.name || `Calculado ${new Date().toLocaleDateString()}`
        };
        // Navegar a la ruta de creación de plan pasando el estado
        navigate('/nutrition/meal-plans/new', { state: { initialTargets } });
    };

    const handleSaveProfile = async () => {
        if (!results) {
             setAlert({ type: 'error', message: 'Calcula los macros antes de guardar el perfil.' });
            return;
        }
        setCalculating(true); // Indicar que se está procesando
        setAlert(null);
        setError(null);

        // Construir el objeto de perfil para guardar
        // Incluye los inputs del formulario y los resultados calculados
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
            macros: results.macros, // Guardar el objeto completo de macros
            // Metadatos
            last_calculated: new Date().toISOString()
        };

        try {
             // Llamar al método saveProfile del servicio importado
            const saved = await NutritionCalculator.saveProfile(profileToSave);
            if (saved) {
                setAlert({ type: 'success', message: 'Perfil nutricional guardado con éxito.' });
                setProfile(saved); // Actualizar el estado del perfil local con la respuesta
            } else {
                 // Si saveProfile devuelve null o undefined en caso de error no capturado
                throw new Error('No se recibió confirmación al guardar el perfil.');
            }
        } catch (err) {
            console.error("Error saving nutrition profile:", err);
            setAlert({ type: 'error', message: err.message || 'Ocurrió un error al guardar el perfil.' });
             // No limpiar resultados si falla el guardado
        } finally {
            setCalculating(false); // Terminar estado de procesamiento
        }
    };
    // --- FIN NUEVAS FUNCIONES HANDLER ---


    // Componente para gráfico de macros (sin cambios)
    const MacroChart = ({ macros }) => {
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
                        label={({ name, percent }) => percent > 0 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''} // No mostrar 0%
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip
                        formatter={(value, name, props) => [`${value.toFixed(0)} kcal (${(props.payload.percent * 100).toFixed(1)}%)`, name]}
                    />
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
        );
    };

    // Renderizado de resultados (sin cambios funcionales, solo estéticos menores)
    const renderResults = () => {
        if (!results) return null;

        // Validar que la estructura de results y results.macros sea la esperada
         if (!results.macros || !results.macros.protein || !results.macros.carbs || !results.macros.fat) {
            return <MuiAlert severity="warning" sx={{ mt: 3 }}>Resultados incompletos recibidos.</MuiAlert>;
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
                                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>Métricas Estimadas:</Typography>
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
                                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>Macronutrientes Diarios (Gramos):</Typography>
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
                                {/* Renderizar gráfico solo si hay datos válidos */}
                                {results.macros.protein.calories != null && results.macros.carbs.calories != null && results.macros.fat.calories != null ? (
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

                     {/* Mostrar Error General o de Cálculo */}
                    {error && (
                        <MuiAlert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                            {error}
                        </MuiAlert>
                    )}
                    {/* Mostrar Alerta de Éxito/Info */}
                     {alert && (
                         <MuiAlert severity={alert.type || 'info'} sx={{ mb: 3 }} onClose={() => setAlert(null)}>
                             {alert.message}
                         </MuiAlert>
                     )}


                    <form onSubmit={handleSubmit}>
                        <Grid container spacing={3}>
                            {/* --- Fila 1: Unidades, Fórmula, Género, Edad --- */}
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
                                    value={typeof formData.age === 'number' ? formData.age : 0} // Controlar valor para slider
                                    onChange={handleSliderChange('age')}
                                    aria-labelledby="age-slider"
                                    min={15}
                                    max={100}
                                    size="small"
                                    sx={{ mt: -1 }} // Ajustar espaciado slider
                                />
                            </Grid>

                            {/* --- Fila 2: Altura, Peso, % Grasa --- */}
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
                                    required={formData.formula === 'katch_mcardle'} // Marcar como requerido si es Katch
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

                             {/* --- Fila 3: Nivel Actividad, Objetivo, Intensidad --- */}
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
                                        // Deshabilitar si el objetivo es mantener
                                        disabled={formData.goal === 'maintain'}
                                    >
                                         {/* Ajustar valores si el servicio los espera diferentes */}
                                        <MenuItem value="light">{formData.goal === 'lose' ? 'Ligero (≈ -250 kcal)' : 'Ligero (≈ +250 kcal)'}</MenuItem>
                                        <MenuItem value="normal">{formData.goal === 'lose' ? 'Normal (≈ -500 kcal)' : 'Normal (≈ +500 kcal)'}</MenuItem>
                                        <MenuItem value="aggressive">{formData.goal === 'lose' ? 'Agresivo (≈ -750 kcal)' : 'Agresivo (≈ +750 kcal)'}</MenuItem>
                                        <MenuItem value="very_aggressive">{formData.goal === 'lose' ? 'Muy Agresivo (≈ -1000 kcal)' : 'Muy Agresivo (≈ +1000 kcal)'}</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            {/* --- Fila 4: Botón Calcular --- */}
                            <Grid item xs={12} sx={{ textAlign: 'center', mt: 2 }}>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    color="primary"
                                    size="large"
                                    disabled={calculating} // Usar 'calculating' para deshabilitar
                                    startIcon={calculating ? <CircularProgress size={20} color="inherit" /> : <FontAwesomeIcon icon={faCalculator} />}
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

             {/* --- NUEVOS Botones para Guardar Perfil y Aplicar a Plan --- */}
             {/* Se muestran solo si hay resultados y no se está calculando/guardando */}
            {results && !calculating && (
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 3, mb: 2 }}>
                     <Button
                         variant="contained"
                         color="secondary"
                         onClick={handleApplyToNewPlan}
                         disabled={calculating} // Deshabilitado mientras calcula/guarda
                         startIcon={<FontAwesomeIcon icon={faArrowRight} />}
                     >
                         Aplicar a Nuevo Plan
                     </Button>
                     <Button
                         variant="outlined"
                         color="primary"
                         onClick={handleSaveProfile}
                         disabled={calculating} // Deshabilitado mientras calcula/guarda
                         startIcon={calculating ? <CircularProgress size={20} color="inherit"/> :<FontAwesomeIcon icon={faSave} />}
                     >
                         {/* Cambiar texto si está guardando (aunque 'calculating' ya lo deshabilita) */}
                         {calculating ? 'Guardando...' : 'Guardar como Perfil'}
                     </Button>
                </Box>
            )}
             {/* --- FIN NUEVOS Botones --- */}

        </Box>
    );
}; // FIN DEL COMPONENTE MacroCalculator

// ¡¡¡ IMPORTANTE !!!
// El código que tenías aquí debajo (async saveProfile, saveLocalProfile, etc.)
// NO pertenece a este archivo de componente React.
// Ese código debe estar dentro de tu clase/objeto NutritionCalculator
// en el archivo del servicio: src/services/NutritionService.js

export default MacroCalculator;