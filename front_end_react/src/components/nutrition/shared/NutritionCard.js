// src/components/nutrition/shared/NutritionCard.js
import React from 'react';
import { Card, CardContent, Typography, Grid } from '@mui/material';
import MacroDisplay from './MacroDisplay'; // Reutiliza tu componente de macros si aplica

// Define qué props esperas. Ejemplo: un objeto con nombre, macros, etc.
const NutritionCard = ({ title, data }) => {
  // Asume que 'data' tiene una estructura como:
  // { name: 'Pollo Asado', description: '...', calories: 300, protein: 30, carbs: 5, fat: 15, ...otros }
  // O podrías pasar props individuales: title, calories, protein, carbs, fat, ...

  const macros = {
     calories: data?.calories || 0,
     protein: data?.protein || 0,
     carbs: data?.carbs || 0,
     fat: data?.fat || 0
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" component="div" gutterBottom>
          {title || data?.name || 'Información Nutricional'}
        </Typography>

        {data?.description && (
           <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {data.description}
           </Typography>
        )}

        {/* Muestra los macros usando el componente dedicado */}
        <MacroDisplay macros={macros} />

         {/* Puedes añadir más detalles aquí si los tienes en 'data' */}
         {/* Ejemplo: */}
         {/*
         <Typography variant="caption" display="block" sx={{ mt: 1 }}>
             ID: {data?.id}
         </Typography>
         */}

      </CardContent>
    </Card>
  );
};

export default NutritionCard;