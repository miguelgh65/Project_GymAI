// src/components/nutrition/meal-plans/MealPlanForm/DayMealsList.js
import React from 'react';
import { 
  Typography, Card, CardContent, List, ListItem, 
  ListItemText, IconButton, Box, Tooltip, Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faMinus, faCoffee, faSun, 
  faUtensils, faCookie, faMoon, faEllipsisH
} from '@fortawesome/free-solid-svg-icons';

const DayMealsList = ({ items, onRemove }) => {
  // Tipos de comida
  const mealTypes = [
    { value: 'Desayuno', label: 'Desayuno', icon: faCoffee },
    { value: 'Almuerzo', label: 'Almuerzo', icon: faSun },
    { value: 'Comida', label: 'Comida', icon: faUtensils },
    { value: 'Merienda', label: 'Merienda', icon: faCookie },
    { value: 'Cena', label: 'Cena', icon: faMoon },
    { value: 'Otro', label: 'Otro', icon: faEllipsisH }
  ];
  
  // Obtener icono para tipo de comida
  const getMealTypeIcon = (type) => {
    const mealType = mealTypes.find(t => t.value === type);
    return mealType ? mealType.icon : faUtensils;
  };
  
  // Agrupar comidas por tipo
  const groupMealsByType = () => {
    const grouped = {};
    
    mealTypes.forEach(type => {
      grouped[type.value] = [];
    });
    
    items.forEach(item => {
      const type = item.meal_type || 'Otro';
      if (!grouped[type]) {
        grouped[type] = [];
      }
      grouped[type].push(item);
    });
    
    return grouped;
  };
  
  // Calcular totales de macros para un tipo de comida
  const calculateMealTypeTotals = (type) => {
    const typeItems = items.filter(item => item.meal_type === type);
    
    const totals = {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    };
    
    typeItems.forEach(item => {
      if (item.calories) totals.calories += item.calories;
      if (item.protein_g) totals.protein_g += item.protein_g;
      if (item.carbohydrates_g) totals.carbs_g += item.carbohydrates_g;
      if (item.fat_g) totals.fat_g += item.fat_g;
    });
    
    return totals;
  };
  
  // Obtener grupos de comidas
  const groupedItems = groupMealsByType();
  
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>Comidas seleccionadas:</Typography>
      
      {mealTypes.map((type) => {
        const typeItems = groupedItems[type.value] || [];
        const typeTotals = calculateMealTypeTotals(type.value);
        
        return (
          <Card 
            key={type.value} 
            variant="outlined" 
            sx={{ 
              mb: 2, 
              borderColor: typeItems.length ? 'primary.main' : 'grey.300' 
            }}
          >
            <CardContent sx={{ py: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center' }}>
                  <FontAwesomeIcon icon={type.icon} style={{ marginRight: '8px' }} />
                  {type.label}
                </Typography>
                
                {typeItems.length > 0 && (
                  <Typography variant="caption" color="text.secondary">
                    <Tooltip title="Calorías | Proteínas | Carbohidratos | Grasas">
                      <span>
                        {typeTotals.calories} kcal | 
                        P: {typeTotals.protein_g}g | 
                        C: {typeTotals.carbs_g}g | 
                        G: {typeTotals.fat_g}g
                      </span>
                    </Tooltip>
                  </Typography>
                )}
              </Box>
              
              {typeItems.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mt: 1 }}>
                  No hay comidas asignadas
                </Typography>
              ) : (
                <List dense>
                  {typeItems.map((item, idx) => (
                    <ListItem 
                      key={idx}
                      secondaryAction={
                        <IconButton 
                          edge="end" 
                          aria-label="delete" 
                          onClick={() => onRemove(items.findIndex(i => i === item))}
                          size="small"
                          color="error"
                        >
                          <FontAwesomeIcon icon={faMinus} />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={
                          <Typography variant="body2" noWrap>
                            {item.meal_name || `Comida ID: ${item.meal_id}`}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            {item.quantity} {item.unit || 'g'} | 
                            {item.calories ? ` ${item.calories} kcal |` : ''} 
                            {item.protein_g ? ` P: ${item.protein_g}g |` : ''} 
                            {item.carbohydrates_g ? ` C: ${item.carbohydrates_g}g |` : ''} 
                            {item.fat_g ? ` G: ${item.fat_g}g` : ''}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        );
      })}
    </Paper>
  );
};

export default DayMealsList;