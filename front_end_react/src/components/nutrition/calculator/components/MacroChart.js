// src/components/nutrition/calculator/components/MacroChart.js
import React from 'react';
import { Typography } from '@mui/material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';

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
                <RechartsTooltip
                    formatter={(value, name, props) => 
                        [`${value.toFixed(0)} kcal (${(props.payload.percent * 100).toFixed(1)}%)`, name]
                    }
                />
                <Legend />
            </PieChart>
        </ResponsiveContainer>
    );
};

export default MacroChart;