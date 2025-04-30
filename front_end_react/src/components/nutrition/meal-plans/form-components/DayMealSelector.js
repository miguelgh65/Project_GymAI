import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  TextField,
  Divider,
  Paper,
  Tooltip,
} from '@mui/material';
// Importar FontAwesomeIcon y el icono de papelera
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';
// Quitar la importación de DeleteIcon: import DeleteIcon from '@mui/icons-material/Delete';
import MacroSummary from '../../../../shared/MacroSummary'; // Reutilizar componente existente

/**
 * Componente para mostrar, editar y eliminar comidas de un día específico del plan.
 * (Modificado para usar Font Awesome en lugar de MUI Icons)
 * @param {string} date - La fecha del día (YYYY-MM-DD).
 * @param {Array} meals - Array de mealItems para este día. mealItem debe tener id único (e.g., meal_plan_item_id), name, quantity, unit, macros.
 * @param {object} dailyTotal - Objeto con las macros totales calculadas para este día.
 * @param {function} onRemoveMeal - Callback llamado con (date, mealItemId) para eliminar.
 * @param {function} onUpdateQuantity - Callback llamado con (date, mealItemId, newQuantity).
 * @param {object} targetMacros - Objetivos diarios (opcional, para comparación).
 */
function DayMealSelector({ date, meals = [], dailyTotal, onRemoveMeal, onUpdateQuantity, targetMacros, disabled }) { // Añadido disabled prop

  const handleQuantityChange = (mealItemId, value) => {
    const newQuantity = value === '' ? '' : Number(value);
     // Permitir borrar o números positivos
    if (value === '' || (!isNaN(newQuantity) && newQuantity >= 0)) {
       onUpdateQuantity(date, mealItemId, newQuantity === '' ? 0 : newQuantity); // Enviar 0 si está vacío temporalmente
    }
  };

  // Asegurar que dailyTotal no es undefined
  const safeDailyTotal = dailyTotal || { calories: 0, protein_g: 0, carbohydrates_g: 0, fat_g: 0 };

  return (
    <Paper elevation={1} sx={{ p: 2, opacity: disabled ? 0.7 : 1 }}> {/* Atenuar si está disabled */}
      <Typography variant="h6" gutterBottom>Meals for {date}</Typography>
      <List dense sx={{maxHeight: 400, overflowY: 'auto'}}>
        {meals.length > 0 ? (
          meals.map((mealItem, index) => (
            <React.Fragment key={mealItem.id || mealItem.meal_plan_item_id || `meal-${date}-${mealItem.meal_id}-${index}`}>
              <ListItem
                sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', pl: 0 }} // Ajustar padding left
                secondaryAction={
                   <Tooltip title="Remove Meal">
                    <span> {/* Span para tooltip en botón deshabilitado */}
                     <IconButton
                        edge="end"
                        aria-label="delete"
                        onClick={() => onRemoveMeal(date, mealItem.id || mealItem.meal_plan_item_id)} // Pasar el ID único del item
                        disabled={disabled}
                        size="small" // Ajustar tamaño si es necesario
                        sx={{ color: 'error.main' }} // Usar color de error del tema MUI
                    >
                        {/* Usar el icono de Font Awesome */}
                        <FontAwesomeIcon icon={faTrash} />
                     </IconButton>
                     </span>
                   </Tooltip>
                }
              >
                <ListItemText
                  primary={mealItem.name}
                  secondary={`C:${mealItem.calories || 0} P:${mealItem.protein_g || 0}g C:${mealItem.carbohydrates_g || 0}g F:${mealItem.fat_g || 0}g (per ${mealItem.unit || 'serving'})`}
                  sx={{ flexGrow: 1, minWidth: '200px', wordBreak: 'break-word' }}
                />
                 <TextField
                    label="Qty"
                    type="number"
                    size="small"
                    value={mealItem.quantity ?? ''}
                    onChange={(e) => handleQuantityChange(mealItem.id || mealItem.meal_plan_item_id, e.target.value)}
                    sx={{ width: '80px', mr: 1 }}
                    inputProps={{ min: 0, step: 0.1 }} // Permitir decimales si es necesario
                    disabled={disabled}
                 />
                 <Typography variant="body2" sx={{ minWidth: '50px' }}>{mealItem.unit || 'servings'}</Typography>

              </ListItem>
              {index < meals.length - 1 && <Divider component="li" />}
            </React.Fragment>
          ))
        ) : (
          <ListItem>
            <ListItemText primary="No meals added for this day." sx={{textAlign: 'center', fontStyle: 'italic', color: 'text.secondary'}} />
          </ListItem>
        )}
      </List>
      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle1">Daily Totals:</Typography>
      <MacroSummary macros={safeDailyTotal} />
    </Paper>
  );
}

export default DayMealSelector;