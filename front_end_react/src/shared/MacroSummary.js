// src/components/nutrition/shared/MacroSummary.js
import React from 'react';
import { Box, Typography, Grid, Tooltip } from '@mui/material'; // <-- Añadido Tooltip aquí
const MacroSummary = ({ macros }) => {
    // Añadir validación más robusta
    if (!macros || !macros.macros || typeof macros.calories === 'undefined') {
         // console.warn("MacroSummary: Invalid or incomplete macros data received", macros);
        return <Typography variant="body2" color="text.secondary">Datos de macros no disponibles.</Typography>;
    }

    const formatValue = (value, decimals = 1) => value?.toFixed(decimals) ?? '0.0';
    const formatPercentage = (value) => value?.toFixed(0) ?? '0';

    return (
        <Box sx={{ mt: 1, mb: 2 }}>
            <Grid container spacing={1}>
                <Grid item xs={12}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        Total: {macros.calories?.toFixed(0) ?? 0} kcal
                    </Typography>
                </Grid>
                <Grid item xs={4}>
                    <Tooltip title={`${formatValue(macros.macros.proteins?.grams)}g`} placement="top">
                        <Typography variant="body2" color="text.secondary">
                            Prot: {formatPercentage(macros.macros.proteins?.percentage)}%
                        </Typography>
                    </Tooltip>
                </Grid>
                <Grid item xs={4}>
                     <Tooltip title={`${formatValue(macros.macros.carbs?.grams)}g`} placement="top">
                        <Typography variant="body2" color="text.secondary">
                            Carb: {formatPercentage(macros.macros.carbs?.percentage)}%
                        </Typography>
                     </Tooltip>
                </Grid>
                <Grid item xs={4}>
                     <Tooltip title={`${formatValue(macros.macros.fats?.grams)}g`} placement="top">
                        <Typography variant="body2" color="text.secondary">
                            Grasa: {formatPercentage(macros.macros.fats?.percentage)}%
                        </Typography>
                     </Tooltip>
                </Grid>
            </Grid>
        </Box>
    );
};

export default MacroSummary; // Exportar como default o nombrado