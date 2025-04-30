// src/components/nutrition/shared/NutritionSummary.js
import React from 'react';
import { 
  Box, Typography, Paper, Grid, Divider, 
  Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, useTheme
} from '@mui/material';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const MacroPieChart = ({ macros }) => {
  const theme = useTheme();
  
  // Datos para el gráfico de tarta
  const data = [
    { name: 'Proteínas', value: macros.macros.proteins.grams * 4, color: theme.palette.success.main },
    { name: 'Carbohidratos', value: macros.macros.carbs.grams * 4, color: theme.palette.primary.main },
    { name: 'Grasas', value: macros.macros.fats.grams * 9, color: theme.palette.warning.main }
  ];
  
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip 
          formatter={(value) => `${Math.round(value)} kcal`}
          labelFormatter={(name) => `${name}`}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

const DailyMacroTable = ({ dailyMacros }) => {
  return (
    <TableContainer component={Paper} elevation={0} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Día</TableCell>
            <TableCell align="right">Calorías</TableCell>
            <TableCell align="right">Proteínas</TableCell>
            <TableCell align="right">Carbos</TableCell>
            <TableCell align="right">Grasas</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.entries(dailyMacros).map(([day, macros]) => (
            <TableRow key={day}>
              <TableCell component="th" scope="row">{day}</TableCell>
              <TableCell align="right">{macros.calories} kcal</TableCell>
              <TableCell align="right">{macros.macros.proteins.grams}g</TableCell>
              <TableCell align="right">{macros.macros.carbs.grams}g</TableCell>
              <TableCell align="right">{macros.macros.fats.grams}g</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const NutritionSummary = ({ totalMacros, dailyMacros, userProfile }) => {
  // Calcular el balance calórico diario
  const getCalorieBalance = () => {
    if (!userProfile || !userProfile.goal_calories) return null;
    
    const dailyAverage = totalMacros.calories / 7; // Asumiendo plan semanal
    const difference = dailyAverage - userProfile.goal_calories;
    const percentage = Math.round((difference / userProfile.goal_calories) * 100);
    
    return {
      difference,
      percentage,
      isDeficit: difference < 0
    };
  };
  
  const calorieBalance = getCalorieBalance();
  
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>Resumen Nutricional</Typography>
      
      <Grid container spacing={3}>
        {/* Gráfico de macros */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Distribución de Macronutrientes</Typography>
            <MacroPieChart macros={totalMacros} />
            <Box mt={2}>
              <Grid container spacing={2} textAlign="center">
                <Grid item xs={4}>
                  <Typography variant="body2" color="text.secondary">Proteínas</Typography>
                  <Typography variant="h6">{totalMacros.macros.proteins.percentage}%</Typography>
                  <Typography variant="body2">{totalMacros.macros.proteins.grams}g</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2" color="text.secondary">Carbohidratos</Typography>
                  <Typography variant="h6">{totalMacros.macros.carbs.percentage}%</Typography>
                  <Typography variant="body2">{totalMacros.macros.carbs.grams}g</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2" color="text.secondary">Grasas</Typography>
                  <Typography variant="h6">{totalMacros.macros.fats.percentage}%</Typography>
                  <Typography variant="body2">{totalMacros.macros.fats.grams}g</Typography>
                </Grid>
              </Grid>
            </Box>
          </Paper>
        </Grid>
        
        {/* Calorías y balance */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Balance Calórico</Typography>
            
            <Box my={2} textAlign="center">
              <Typography variant="h4" component="div" gutterBottom>
                {totalMacros.calories} kcal
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Promedio diario: {Math.round(totalMacros.calories / 7)} kcal
              </Typography>
            </Box>
            
            {userProfile && calorieBalance && (
              <Box mt={3}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2">
                  Tu meta diaria: {userProfile.goal_calories} kcal
                </Typography>
                
                <Typography 
                  variant="body1" 
                  color={calorieBalance.isDeficit ? "success.main" : "error.main"}
                  fontWeight="bold"
                  mt={1}
                >
                  {calorieBalance.isDeficit 
                    ? `Déficit de ${Math.abs(calorieBalance.difference)} kcal (${Math.abs(calorieBalance.percentage)}%)` 
                    : `Exceso de ${calorieBalance.difference} kcal (${calorieBalance.percentage}%)`}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" mt={1}>
                  {calorieBalance.isDeficit 
                    ? "Estás consumiendo menos calorías que tu meta diaria." 
                    : "Estás consumiendo más calorías que tu meta diaria."}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* Tabla de macros diarios */}
        <Grid item xs={12}>
          <Paper elevation={1} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Desglose por Día</Typography>
            <DailyMacroTable dailyMacros={dailyMacros} />
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default NutritionSummary;