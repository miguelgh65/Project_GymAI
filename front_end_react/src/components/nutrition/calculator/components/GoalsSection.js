// src/components/nutrition/calculator/components/FormSections/GoalsSection.js
import React from 'react';
import {
    Box, FormControl, InputLabel, Select,
    MenuItem, Grid
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faDumbbell } from '@fortawesome/free-solid-svg-icons';

const GoalsSection = ({ formData, handleChange }) => {
    return (
        <>
            <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <FontAwesomeIcon icon={faDumbbell} style={{ marginRight: '10px', color: '#666' }} />
                    <FormControl fullWidth size="small">
                        <InputLabel id="activity-level-label">Nivel Actividad</InputLabel>
                        <Select
                            labelId="activity-level-label"
                            id="activity_level"
                            name="activity_level"
                            value={formData.activity_level}
                            onChange={handleChange}
                            label="Nivel Actividad"
                        >
                            <MenuItem value="sedentary">Sedentario</MenuItem>
                            <MenuItem value="light">Ligero (1-3 días/sem)</MenuItem>
                            <MenuItem value="moderate">Moderado (3-5 días/sem)</MenuItem>
                            <MenuItem value="active">Activo (6-7 días/sem)</MenuItem>
                            <MenuItem value="very_active">Muy Activo (intenso diario)</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth size="small">
                    <InputLabel id="goal-label">Objetivo</InputLabel>
                    <Select
                        labelId="goal-label"
                        id="goal"
                        name="goal"
                        value={formData.goal}
                        onChange={handleChange}
                        label="Objetivo"
                    >
                        <MenuItem value="maintain">Mantener Peso</MenuItem>
                        <MenuItem value="lose">Perder Peso</MenuItem>
                        <MenuItem value="gain">Ganar Peso</MenuItem>
                    </Select>
                </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth size="small">
                    <InputLabel id="goal-intensity-label">Intensidad</InputLabel>
                    <Select
                        labelId="goal-intensity-label"
                        id="goal_intensity"
                        name="goal_intensity"
                        value={formData.goal_intensity}
                        onChange={handleChange}
                        label="Intensidad"
                        disabled={formData.goal === 'maintain'}
                    >
                        <MenuItem value="light">
                            {formData.goal === 'lose' ? 'Ligero (≈ -250 kcal)' : 'Ligero (≈ +250 kcal)'}
                        </MenuItem>
                        <MenuItem value="normal">
                            {formData.goal === 'lose' ? 'Normal (≈ -500 kcal)' : 'Normal (≈ +500 kcal)'}
                        </MenuItem>
                        <MenuItem value="aggressive">
                            {formData.goal === 'lose' ? 'Agresivo (≈ -750 kcal)' : 'Agresivo (≈ +750 kcal)'}
                        </MenuItem>
                        <MenuItem value="very_aggressive">
                            {formData.goal === 'lose' ? 'Muy Agresivo (≈ -1000 kcal)' : 'Muy Agresivo (≈ +1000 kcal)'}
                        </MenuItem>
                    </Select>
                </FormControl>
            </Grid>
        </>
    );
};

export default GoalsSection;