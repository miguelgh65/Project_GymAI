// src/components/nutrition/calculator/components/FormSections/PhysicalDataSection.js
import React from 'react';
import {
    Box, Typography, TextField, Grid, Slider
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRuler, faWeight } from '@fortawesome/free-solid-svg-icons';

const PhysicalDataSection = ({ formData, handleChange, handleSliderChange }) => {
    return (
        <>
            <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <FontAwesomeIcon icon={faRuler} style={{ marginRight: '10px', color: '#666' }} />
                    <TextField
                        fullWidth
                        id="height"
                        name="height"
                        label={`Altura (${formData.units === 'metric' ? 'cm' : 'in'})`}
                        type="number"
                        size="small"
                        value={formData.height}
                        onChange={handleChange}
                        InputProps={{
                            inputProps: {
                                min: formData.units === 'metric' ? 120 : 48,
                                max: formData.units === 'metric' ? 220 : 84,
                                step: 0.1
                            }
                        }}
                    />
                </Box>
                <Slider
                    value={typeof formData.height === 'number' ? formData.height : 0}
                    onChange={handleSliderChange('height')}
                    aria-labelledby="height-slider"
                    min={formData.units === 'metric' ? 120 : 48}
                    max={formData.units === 'metric' ? 220 : 84}
                    step={formData.units === 'metric' ? 1 : 0.5}
                    size="small"
                    sx={{ mt: -1 }}
                />
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <FontAwesomeIcon icon={faWeight} style={{ marginRight: '10px', color: '#666' }} />
                    <TextField
                        fullWidth
                        id="weight"
                        name="weight"
                        label={`Peso (${formData.units === 'metric' ? 'kg' : 'lb'})`}
                        type="number"
                        size="small"
                        value={formData.weight}
                        onChange={handleChange}
                        InputProps={{
                            inputProps: {
                                min: formData.units === 'metric' ? 40 : 88,
                                max: formData.units === 'metric' ? 200 : 440,
                                step: 0.1
                            }
                        }}
                    />
                </Box>
                <Slider
                    value={typeof formData.weight === 'number' ? formData.weight : 0}
                    onChange={handleSliderChange('weight')}
                    aria-labelledby="weight-slider"
                    min={formData.units === 'metric' ? 40 : 88}
                    max={formData.units === 'metric' ? 200 : 440}
                    step={formData.units === 'metric' ? 0.5 : 1}
                    size="small"
                    sx={{ mt: -1 }}
                />
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
                <TextField
                    fullWidth
                    id="body_fat_percentage"
                    name="body_fat_percentage"
                    label="% Grasa Corporal"
                    type="number"
                    size="small"
                    value={formData.body_fat_percentage || ''}
                    onChange={handleChange}
                    InputProps={{
                        inputProps: { min: 3, max: 60, step: 0.1 },
                        endAdornment: <Typography variant="caption" sx={{mr: 1}}>%</Typography>
                    }}
                    helperText={formData.formula === 'katch_mcardle' ? 'Requerido por Katch-McArdle' : 'Opcional'}
                    required={formData.formula === 'katch_mcardle'}
                />
                <Slider
                    value={typeof formData.body_fat_percentage === 'number' ? formData.body_fat_percentage : 0}
                    onChange={handleSliderChange('body_fat_percentage')}
                    aria-labelledby="bodyfat-slider"
                    min={3}
                    max={60}
                    step={0.5}
                    size="small"
                    sx={{ mt: -1 }}
                />
            </Grid>
        </>
    );
};

export default PhysicalDataSection;