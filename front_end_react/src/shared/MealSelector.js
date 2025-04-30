// src/components/nutrition/shared/MealSelector.js
import React, { useState } from 'react';
import { Grid, Typography, Autocomplete, TextField, Tooltip, IconButton } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';

const MealSelector = ({
    meals,              // Lista de comidas disponibles [{id, name, ...}]
    mealType,           // String: "Desayuno", "Comida", etc.
    selectedMeal,       // Objeto meal seleccionado o null
    quantity,           // Valor numérico o string vacío
    unit,               // String: "g", "ml", "unidad"
    onSelect,           // fn(mealType, selectedMealObject | null)
    onQuantityChange,   // fn(mealType, newQuantityString)
    onUnitChange,       // fn(mealType, newUnitString)
    onRemove,           // fn(mealType)
    disabled = false    // Prop para deshabilitar todo el selector
}) => {
    // El estado local para el texto del Autocomplete es útil
    const [searchText, setSearchText] = useState('');

    return (
        <Grid container spacing={1} alignItems="center" sx={{ mb: 1.5 }}>
            {/* Etiqueta del Tipo de Comida */}
            <Grid item xs={12} sm={2.5}>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>{mealType}:</Typography>
            </Grid>

            {/* Selector Autocomplete */}
            <Grid item xs={12} sm={5}>
                <Autocomplete
                    options={meals || []}
                    getOptionLabel={(option) => option?.name || ''} // Más seguro con ?.
                    value={selectedMeal} // Controlado desde el hook padre
                    onChange={(event, newValue) => onSelect(mealType, newValue)}
                    inputValue={searchText}
                    onInputChange={(event, newInputValue) => {
                         // Solo actualizamos el estado local, no notificamos al padre aquí
                         setSearchText(newInputValue);
                    }}
                    isOptionEqualToValue={(option, value) => option?.id === value?.id}
                    renderInput={(params) => (
                        <TextField
                            {...params}
                            variant="outlined"
                            placeholder="Selecciona comida"
                            size="small"
                            fullWidth
                        />
                    )}
                    disabled={disabled || !meals || meals.length === 0} // Deshabilitado general o si no hay comidas
                    size="small"
                />
            </Grid>

            {/* Input Cantidad */}
            <Grid item xs={5} sm={2}>
                <TextField
                    type="number"
                    label="Cantidad"
                    value={quantity ?? ''} // Mostrar vacío si es null/undefined
                    onChange={(e) => onQuantityChange(mealType, e.target.value)}
                    size="small"
                    fullWidth
                    InputProps={{ inputProps: { min: 0, step: 1 } }}
                    disabled={disabled || !selectedMeal} // Deshabilitar si no hay comida seleccionada
                />
            </Grid>

            {/* Input Unidad */}
            <Grid item xs={4} sm={1.5}>
                 <TextField
                    label="Unidad"
                    value={unit || 'g'} // Default 'g'
                    onChange={(e) => onUnitChange(mealType, e.target.value)}
                    size="small"
                    fullWidth
                    placeholder="g"
                    disabled={disabled || !selectedMeal}
                 />
            </Grid>

            {/* Botón Eliminar */}
            <Grid item xs={3} sm={1} sx={{ textAlign: 'right' }}>
                <Tooltip title={`Quitar ${mealType}`}>
                    {/* Span necesario para Tooltip en botón deshabilitado */}
                    <span>
                        <IconButton
                            color="error"
                            size="small"
                            onClick={() => onRemove(mealType)}
                            disabled={disabled || !selectedMeal}
                            aria-label={`Quitar ${mealType}`}
                        >
                            <FontAwesomeIcon icon={faTrash} size="xs" />
                        </IconButton>
                    </span>
                </Tooltip>
            </Grid>
        </Grid>
    );
};

export default MealSelector;