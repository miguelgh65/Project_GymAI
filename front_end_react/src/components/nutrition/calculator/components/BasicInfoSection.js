// src/components/nutrition/calculator/components/FormSections/BasicInfoSection.js
import React from 'react';
import {
    TextField, FormControl, InputLabel, Select,
    MenuItem, Grid, Slider
} from '@mui/material';

const BasicInfoSection = ({ formData, handleChange, handleSliderChange }) => {
    return (
        <>
            <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                    <InputLabel id="units-label">Unidades</InputLabel>
                    <Select
                        labelId="units-label"
                        id="units"
                        name="units"
                        value={formData.units}
                        onChange={handleChange}
                        label="Unidades"
                    >
                        <MenuItem value="metric">Métrico (kg/cm)</MenuItem>
                        <MenuItem value="imperial">Imperial (lb/in)</MenuItem>
                    </Select>
                </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                    <InputLabel id="formula-label">Fórmula</InputLabel>
                    <Select
                        labelId="formula-label"
                        id="formula"
                        name="formula"
                        value={formData.formula}
                        onChange={handleChange}
                        label="Fórmula"
                    >
                        <MenuItem value="mifflin_st_jeor">Mifflin-St Jeor</MenuItem>
                        <MenuItem value="harris_benedict">Harris-Benedict</MenuItem>
                        <MenuItem value="katch_mcardle">Katch-McArdle</MenuItem>
                        <MenuItem value="who">OMS</MenuItem>
                    </Select>
                </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                    <InputLabel id="gender-label">Género</InputLabel>
                    <Select
                        labelId="gender-label"
                        id="gender"
                        name="gender"
                        value={formData.gender}
                        onChange={handleChange}
                        label="Género"
                    >
                        <MenuItem value="male">Masculino</MenuItem>
                        <MenuItem value="female">Femenino</MenuItem>
                    </Select>
                </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
                <TextField
                    fullWidth
                    id="age"
                    name="age"
                    label="Edad"
                    type="number"
                    size="small"
                    value={formData.age}
                    onChange={handleChange}
                    InputProps={{ inputProps: { min: 15, max: 100 } }}
                />
                <Slider
                    value={typeof formData.age === 'number' ? formData.age : 0}
                    onChange={handleSliderChange('age')}
                    aria-labelledby="age-slider"
                    min={15}
                    max={100}
                    size="small"
                    sx={{ mt: -1 }}
                />
            </Grid>
        </>
    );
};

export default BasicInfoSection;