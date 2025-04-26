// src/components/nutrition/calculator/components/ResultsDisplay.js
import React from 'react';
import {
    Box, Typography, Card, CardContent,
    Grid, Alert, Divider, Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartPie } from '@fortawesome/free-solid-svg-icons';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import MacroChart from './MacroChart';

const ResultsDisplay = ({ results }) => {
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

export default ResultsDisplay;