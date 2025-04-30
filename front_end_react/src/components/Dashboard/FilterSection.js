// src/components/Dashboard/FilterSection.js
import React from 'react';
import {
  Card, CardContent, Select, MenuItem, TextField, Button,
  Grid, Typography, CircularProgress, InputLabel, FormControl, Box
} from '@mui/material';

function FilterSection({
  exerciseList,
  selectedExercise,
  onExerciseChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  onApplyFilters,
  loading,
  loadingExercises // Para saber si la lista de ejercicios está cargando
}) {
  return (
    <Card className="filter-section" elevation={3}>
      <CardContent>
        <Grid container spacing={3} alignItems="flex-end">
          {/* Selector Ejercicio */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth variant="outlined">
              <InputLabel id="ejercicio-select-label">Ejercicio</InputLabel>
              <Select
                labelId="ejercicio-select-label"
                label="Ejercicio"
                id="ejercicio-select"
                value={selectedExercise}
                onChange={(e) => onExerciseChange(e.target.value)}
                disabled={loadingExercises || loading}
                className="select-input"
              >
                <MenuItem value="">
                  <em>{loadingExercises ? 'Cargando...' : 'Selecciona un ejercicio'}</em>
                </MenuItem>
                {exerciseList.map((ejercicio, index) => (
                  <MenuItem key={index} value={ejercicio}>{ejercicio}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Fechas */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom sx={{mb: 1, display: {xs: 'block', md:'none'}}}>Período:</Typography> {/* Label for mobile */}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Desde"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => onDateFromChange(e.target.value)}
                  variant="outlined"
                  className="date-input"
                  InputLabelProps={{ shrink: true }}
                  disabled={loading}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Hasta"
                  type="date"
                  value={dateTo}
                  onChange={(e) => onDateToChange(e.target.value)}
                  variant="outlined"
                  className="date-input"
                  InputLabelProps={{ shrink: true }}
                  disabled={loading}
                />
              </Grid>
            </Grid>
          </Grid>

          {/* Botón Aplicar */}
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              onClick={onApplyFilters}
              disabled={!selectedExercise || loading} // Deshabilitado si carga o no hay ejercicio
              className="primary-btn"
              sx={{ height: '56px' }} // Para alinear con TextFields
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Aplicar'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

export default FilterSection;