import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { PieChart } from 'recharts';

function MacroDisplay({ calories, proteins, carbs, fats, title = "Macronutrientes" }) {
  // Calculate macro percentages
  const proteinCalories = proteins * 4;
  const carbCalories = carbs * 4;
  const fatCalories = fats * 9;
  const totalCalories = proteinCalories + carbCalories + fatCalories;
  
  const proteinPercentage = Math.round((proteinCalories / totalCalories) * 100) || 0;
  const carbPercentage = Math.round((carbCalories / totalCalories) * 100) || 0;
  const fatPercentage = Math.round((fatCalories / totalCalories) * 100) || 0;
  
  // Chart data
  const data = [
    { name: 'Proteínas', value: proteinCalories, percentage: proteinPercentage, color: '#4CAF50' },
    { name: 'Carbohidratos', value: carbCalories, percentage: carbPercentage, color: '#2196F3' },
    { name: 'Grasas', value: fatCalories, percentage: fatPercentage, color: '#FFC107' }
  ];
  
  return (
    <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>{title}</Typography>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ width: '40%' }}>
          <PieChart width={150} height={150}>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              outerRadius={60}
              fill="#8884d8"
              dataKey="value"
              nameKey="name"
              label={({ name, percentage }) => `${name}: ${percentage}%`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value} kcal`} />
          </PieChart>
        </Box>
        
        <Box sx={{ width: '60%' }}>
          <Box sx={{ mb: 1 }}>
            <Typography variant="body1" fontWeight="bold">
              Total: {calories} kcal
            </Typography>
          </Box>
          
          {data.map((macro, index) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box 
                sx={{ 
                  width: 16, 
                  height: 16, 
                  backgroundColor: macro.color, 
                  borderRadius: '50%',
                  mr: 1 
                }} 
              />
              <Typography variant="body2">
                {macro.name}: {macro.percentage}% ({macro.name === 'Proteínas' ? proteins : 
                                                    macro.name === 'Carbohidratos' ? carbs : fats}g)
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Paper>
  );
}

export default MacroDisplay;