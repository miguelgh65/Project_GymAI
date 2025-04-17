// src/shared/DayMeals.js
// (Asegúrate de que este archivo esté en esta ubicación: front_end_react/src/shared/DayMeals.js)

import React, { useMemo, useCallback } from 'react';
import { Paper, Typography, Divider, Alert } from '@mui/material'; // Quitado Paper si no se usa aquí
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBowlFood } from '@fortawesome/free-solid-svg-icons';

// Importaciones locales (asumen que estos archivos están en la misma carpeta 'src/shared/')
import MealSelector from './MealSelector';
import MacroSummary from './MacroSummary';

// Importación de utilidades (ajusta la ruta si tu carpeta utils está en otro lugar)
import { getNutritionSummary } from '../services/nutrition/utils'; // <-- Ruta corregida
const DayMeals = ({
    // dayName, // Nombre del día ya no es necesario para la lógica interna si usamos dayIndex
    dayIndex, // Índice del día (0-6) - Usado para llamar a los handlers
    mealData, // Objeto con los datos de comida para este día: { Desayuno: {meal, quantity, unit}, ... }
    meals, // Lista completa de comidas disponibles [{id, name, calories, protein, ...}]
    onChange, // fn(dayIndex, mealType, selectedMealObject | null)
    onQuantityChange, // fn(dayIndex, mealType, newQuantityString)
    onUnitChange, // fn(dayIndex, mealType, newUnitString)
    onRemove, // fn(dayIndex, mealType)
    mealTypeKeys = ["Desayuno", "Almuerzo", "Comida", "Merienda", "Cena", "Otro"] // Tipos de comida a mostrar
}) => {

    // Cálculo de macros para este día específico
    const calculateDayMacros = useCallback(() => {
        const selectedMeals = Object.entries(mealData || {}) // Usar {} como fallback si mealData es undefined
            .filter(([_, data]) => data?.meal && (typeof data.quantity === 'number' || data.quantity === '0')) // Asegurar que hay comida y cantidad (puede ser 0)
            .map(([_, data]) => {
                 // Verificar si la comida tiene datos de macros
                 if (typeof data.meal.calories !== 'number') {
                     console.warn(`Meal '${data.meal.name}' (ID: ${data.meal.id}) is missing nutritional data.`);
                     return { calories: 0, proteins: 0, carbohydrates: 0, fats: 0 };
                 }
                 // Calcular ratio basado en unidad (simplificado)
                 const baseUnit = 100;
                 const currentUnit = data.unit?.toLowerCase() || 'g';
                 const quantity = data.quantity || 0;
                 // Asume ratio 1 si no es 'g' o 'ml', puede necesitar ajuste
                 const ratio = (currentUnit === 'g' || currentUnit === 'ml') ? quantity / baseUnit : quantity;

                 return {
                     calories: (data.meal.calories || 0) * ratio,
                     // Usa los nombres de campo correctos de tu objeto 'meal'
                     proteins: (data.meal.protein || data.meal.proteins || 0) * ratio,
                     carbohydrates: (data.meal.carbohydrates || 0) * ratio,
                     fats: (data.meal.fat || data.meal.fats || 0) * ratio
                 };
             });

        if (selectedMeals.length === 0) return null; // No hay comidas válidas con macros

        // Sumar los macros calculados
        const totalMacros = selectedMeals.reduce((total, current) => ({
            calories: total.calories + (current.calories || 0),
            proteins: total.proteins + (current.proteins || 0),
            carbohydrates: total.carbohydrates + (current.carbohydrates || 0),
            fats: total.fats + (current.fats || 0)
        }), { calories: 0, proteins: 0, carbohydrates: 0, fats: 0 });

        // Usar la utilidad para obtener el resumen formateado
        return getNutritionSummary(totalMacros);
    }, [mealData]); // Depende solo de los datos de comida de este día

    // Memorizar el resultado del cálculo de macros
    const dayMacros = useMemo(calculateDayMacros, [calculateDayMacros]);

    // Memorizar si hay alguna comida asignada en este día
    const hasMealsAssigned = useMemo(() => Object.values(mealData || {}).some(item => item?.meal), [mealData]);

    return (
        // El Paper y margen se eliminan para que el componente padre (TabPanel) lo controle
        <>
            {/* Renderizar un MealSelector por cada tipo de comida */}
            {mealTypeKeys.map(mealType => (
                <MealSelector
                    key={mealType}
                    meals={meals} // Pasar lista de comidas disponibles
                    mealType={mealType} // Pasar el tipo ("Desayuno", etc.)
                    // Datos actuales para este tipo de comida en este día
                    selectedMeal={mealData?.[mealType]?.meal || null}
                    quantity={mealData?.[mealType]?.quantity ?? ''} // Usar ?? para mostrar 0 correctamente
                    unit={mealData?.[mealType]?.unit || 'g'} // Default 'g'
                    // Pasar handlers con el índice del día para que el hook padre sepa qué día actualizar
                    onSelect={(type, meal) => onChange(dayIndex, type, meal)}
                    onQuantityChange={(type, quantity) => onQuantityChange(dayIndex, type, quantity)}
                    onUnitChange={(type, unit) => onUnitChange(dayIndex, type, unit)}
                    onRemove={(type) => onRemove(dayIndex, type)}
                    // Deshabilitar selector si no hay comidas disponibles
                    disabled={!meals || meals.length === 0}
                />
            ))}

            <Divider sx={{ my: 2 }} />

            {/* Mostrar resumen de macros o mensaje si no hay comidas */}
            {hasMealsAssigned ? (
                <>
                    <Typography variant="subtitle2" gutterBottom>Macros totales del día:</Typography>
                    {dayMacros ? (
                        <MacroSummary macros={dayMacros} />
                    ) : (
                        // Mensaje si las comidas asignadas no tienen info nutricional
                        <Typography variant="body2" color="text.secondary">
                            No se pueden calcular macros (verifica datos nutricionales de las comidas).
                        </Typography>
                    )}
                </>
            ) : (
                <Alert severity="info" icon={<FontAwesomeIcon icon={faBowlFood} />} sx={{ mt: 1 }}>
                    No hay comidas asignadas para este día.
                </Alert>
            )}
        </>
    );
};

export default DayMeals;