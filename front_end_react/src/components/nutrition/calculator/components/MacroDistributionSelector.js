// src/components/nutrition/calculator/components/MacroDistributionSelector.js
import React, { useState, useEffect } from 'react'; // Añadido useEffect si se necesita lógica adicional
import {
  Typography, FormControl, InputLabel, Select, MenuItem,
  Grid, Slider, Alert, Paper, Chip, Box
} from '@mui/material';
import { PRESET_DISTRIBUTIONS, MACRO_RECOMMENDATIONS, CALORIES_PER_GRAM } from '../constants';

const MacroDistributionSelector = ({ distribution, onChange, disabled, totalCalories }) => {
  // Estado para gestionar el preset seleccionado y errores locales si son necesarios
  const [selectedPreset, setSelectedPreset] = useState("custom"); // Inicializar en custom si se edita
  const [error, setError] = useState(null); // Error local para validaciones instantáneas

  // Sincronizar el preset si la distribución cambia desde fuera
  useEffect(() => {
      let foundPreset = "custom";
      for (const [key, preset] of Object.entries(PRESET_DISTRIBUTIONS)) {
          if (key !== 'custom' &&
              preset.carbs === distribution.carbs &&
              preset.protein === distribution.protein &&
              preset.fat === distribution.fat) {
              foundPreset = key;
              break;
          }
      }
      setSelectedPreset(foundPreset);
  }, [distribution]);


  // Cuando cambia el preset seleccionado
  const handlePresetChange = (e) => {
    const newPresetKey = e.target.value;
    setSelectedPreset(newPresetKey);
    setError(null); // Limpiar error al cambiar preset

    if (newPresetKey !== "custom") {
      const newDistribution = PRESET_DISTRIBUTIONS[newPresetKey];
      // Llamar a onChange con el objeto completo {carbs, protein, fat}
      onChange({
        carbs: newDistribution.carbs,
        protein: newDistribution.protein,
        fat: newDistribution.fat
      });
    }
    // Si se selecciona "custom", no se hace nada, se mantiene la distribución actual
  };

  // Ajustar un macro individualmente con Slider
  const handleSliderChange = (macro, value) => {
    // Clonar la distribución actual para modificarla
    const currentDistribution = { ...distribution };
    const oldValue = currentDistribution[macro];
    const diff = value - oldValue;

    // Identificar los otros dos macros
    const otherMacros = ["carbs", "protein", "fat"].filter(m => m !== macro);
    const macro1 = otherMacros[0];
    const macro2 = otherMacros[1];

    // Calcular los nuevos valores para los otros macros
    let newMacro1Value = currentDistribution[macro1] - diff / 2;
    let newMacro2Value = currentDistribution[macro2] - diff / 2;

    // Crear la nueva distribución tentativa
    let newDistribution = {
        ...currentDistribution,
        [macro]: value,
        [macro1]: newMacro1Value,
        [macro2]: newMacro2Value
    };

    // Ajustar para asegurar que la suma sea exactamente 100 y no haya negativos
    // Redondear valores para evitar problemas de precisión flotante
    newDistribution[macro] = Math.round(value);
    newDistribution[macro1] = Math.round(newDistribution[macro1]);
    newDistribution[macro2] = Math.round(newDistribution[macro2]);

    // Calcular la suma redondeada
    let roundedSum = newDistribution.carbs + newDistribution.protein + newDistribution.fat;

    // Ajustar el último macro modificado si la suma no es 100
    if (roundedSum !== 100) {
      // Preferiblemente ajustar el macro que NO se está moviendo activamente
      // o uno de los otros si es necesario
      const adjustment = 100 - roundedSum;
      // Ajustamos el segundo macro 'otro'
      newDistribution[macro2] += adjustment;
    }

     // Validar que ningún valor sea negativo (puede pasar con ajustes grandes)
     if (newDistribution.carbs < 0) newDistribution.carbs = 0;
     if (newDistribution.protein < 0) newDistribution.protein = 0;
     if (newDistribution.fat < 0) newDistribution.fat = 0;

     // Recalcular suma y ajustar si es necesario de nuevo por los mínimos de 0
     roundedSum = newDistribution.carbs + newDistribution.protein + newDistribution.fat;
     if (roundedSum !== 100) {
        const adjustment = 100 - roundedSum;
         // Reajustar el macro que se movió originalmente si es posible
         if (newDistribution[macro] + adjustment >= 0) {
            newDistribution[macro] += adjustment;
         } else {
             // Si no, ajustar otro (esto puede ser complejo, simplificamos)
             // Podríamos distribuir el ajuste o ajustar el que tenga más margen
             if(newDistribution[macro1] + adjustment >=0) newDistribution[macro1]+= adjustment;
             else if(newDistribution[macro2] + adjustment >=0) newDistribution[macro2]+= adjustment;
         }
     }


    // Limpiar error local y actualizar estado padre
    setError(null);
    setSelectedPreset("custom"); // Cambiar a custom al mover sliders
    onChange(newDistribution); // Pasar el objeto completo
  };

  // Calcular calorías por macro para los Chips (si totalCalories está disponible)
  const getMacroCalories = (macro) => {
    if (!totalCalories || typeof totalCalories !== 'number' || totalCalories <= 0) return 0;
    const percentage = distribution[macro] / 100;
    return Math.round(percentage * totalCalories);
  };


  // ** ARREGLO BUG: Redondear suma antes de comparar **
  const totalPercentage = distribution.carbs + distribution.protein + distribution.fat;
  const roundedTotal = Math.round(totalPercentage);
  const showSumError = roundedTotal !== 100;


  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>Distribución de Macronutrientes</Typography>

      {/* Mostrar error local si existe */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Selector de Preset */}
      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel id="macro-distribution-preset">Perfil de macros</InputLabel>
        <Select
          labelId="macro-distribution-preset"
          value={selectedPreset}
          onChange={handlePresetChange}
          label="Perfil de macros"
          disabled={disabled}
        >
          {/* Asegurarse que PRESET_DISTRIBUTIONS no sea undefined */}
          {PRESET_DISTRIBUTIONS && Object.entries(PRESET_DISTRIBUTIONS).map(([key, preset]) => (
            <MenuItem key={key} value={key}>{preset.name}</MenuItem>
          ))}
           <MenuItem value="custom">Personalizado</MenuItem>
        </Select>
      </FormControl>

      {/* Sliders para cada Macro */}
      <Grid container spacing={2}>
        {/* Carbohidratos */}
        <Grid item xs={12}>
          <Typography gutterBottom>
            Carbohidratos: {distribution.carbs}%
            {totalCalories > 0 && (
              <Chip
                label={`${getMacroCalories('carbs')} kcal`}
                size="small"
                sx={{ ml: 1, bgcolor: 'info.light', color: 'info.contrastText' }}
              />
            )}
          </Typography>
          <Slider
            value={distribution.carbs}
            onChange={(e, value) => handleSliderChange("carbs", value)}
            min={5}
            max={80} // Ampliado rango máximo
            disabled={disabled} // Ya no depende de 'custom', siempre editable
            sx={{ color: "#2196f3" }}
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            Recomendado: {MACRO_RECOMMENDATIONS.carbs.recommended}
          </Typography>
        </Grid>

        {/* Proteínas */}
        <Grid item xs={12}>
          <Typography gutterBottom>
            Proteínas: {distribution.protein}%
             {totalCalories > 0 && (
              <Chip
                label={`${getMacroCalories('protein')} kcal`}
                size="small"
                sx={{ ml: 1, bgcolor: 'success.light', color: 'success.contrastText' }}
              />
            )}
          </Typography>
          <Slider
            value={distribution.protein}
            onChange={(e, value) => handleSliderChange("protein", value)}
            min={10}
            max={50} // Ampliado rango máximo
            disabled={disabled}
            sx={{ color: "#4caf50" }}
             valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            Recomendado: {MACRO_RECOMMENDATIONS.protein.recommended}
          </Typography>
        </Grid>

        {/* Grasas */}
        <Grid item xs={12}>
          <Typography gutterBottom>
            Grasas: {distribution.fat}%
             {totalCalories > 0 && (
              <Chip
                label={`${getMacroCalories('fat')} kcal`}
                size="small"
                sx={{ ml: 1, bgcolor: 'warning.light', color: 'warning.contrastText' }}
              />
            )}
          </Typography>
          <Slider
            value={distribution.fat}
            onChange={(e, value) => handleSliderChange("fat", value)}
            min={10}
            max={70} // Ampliado rango máximo
            disabled={disabled}
            sx={{ color: "#ff9800" }}
             valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            Recomendado: {MACRO_RECOMMENDATIONS.fat.recommended}
          </Typography>
        </Grid>
      </Grid>

      {/* Total y Mensaje de Error de Suma */}
      <Box sx={{ mt: 2, pt: 2, borderTop: '1px dashed rgba(0, 0, 0, 0.12)' }}>
        <Typography variant="body2" fontWeight="medium">
          Total: {roundedTotal}% {/* Mostrar total redondeado */}
          {/* ** USAR showSumError (basado en el total redondeado) ** */}
          {showSumError && (
            <Typography component="span" color="error.main" sx={{ ml: 1 }}>
              (La suma debe ser 100%)
            </Typography>
          )}
        </Typography>
      </Box>
    </Paper>
  );
};

export default MacroDistributionSelector;