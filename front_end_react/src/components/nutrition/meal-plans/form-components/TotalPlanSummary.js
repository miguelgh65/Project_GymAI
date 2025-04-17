import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import MacroSummary from '../../../../shared/MacroSummary'; // Reutilizar componente existente

/**
 * Componente para mostrar el resumen nutricional total del plan.
 * @param {object} totalMacros - Objeto con las macros totales calculadas {calories, protein_g, ...}.
 * @param {object} targetMacros - Objetivos totales del plan (opcional, para comparación).
 */
function TotalPlanSummary({ totalMacros, targetMacros }) {
   const safeTotalMacros = totalMacros || { calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 };
   const safeTargetMacros = targetMacros || {}; // Objeto vacío si no se proporcionan

  return (
    <Paper elevation={2} sx={{ p: 2, mt: 3, mb: 2 }}>
      <Typography variant="h5" gutterBottom>Plan Nutrition Summary</Typography>
       {/* Asume que MacroSummary puede recibir targetMacros para mostrar comparación */}
       <MacroSummary macros={safeTotalMacros} targetMacros={safeTargetMacros} />
       {/* Si MacroSummary no maneja targets, puedes añadir la lógica de comparación aquí:
       {targetMacros && Object.keys(targetMacros).length > 0 && (
           <Box sx={{mt: 2}}>
               <Typography variant="subtitle2">Target:</Typography>
               <Typography variant="body2">
                   Cals: {targetMacros.calories ?? 'N/A'}, P: {targetMacros.protein_g ?? 'N/A'}g, C: {targetMacros.carbohydrates_g ?? 'N/A'}g, F: {targetMacros.fat_g ?? 'N/A'}g
               </Typography>
               // ... Lógica para mostrar diferencias o porcentajes ...
           </Box>
       )}
       */}
    </Paper>
  );
}

export default TotalPlanSummary;