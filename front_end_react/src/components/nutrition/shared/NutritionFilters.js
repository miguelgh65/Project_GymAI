import React, { useState } from 'react';
import { Box, TextField, Button, InputAdornment, IconButton, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faTimes, faFilter } from '@fortawesome/free-solid-svg-icons';

function NutritionFilters({ 
  onSearch, 
  searchPlaceholder = "Buscar...",
  options = null,
  initialSearch = '',
  initialFilter = ''
}) {
  const [searchTerm, setSearchTerm] = useState(initialSearch);
  const [filterValue, setFilterValue] = useState(initialFilter);
  
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  const handleFilterChange = (e) => {
    setFilterValue(e.target.value);
    // If filter affects search immediately, uncomment this:
    // handleSubmit(e, e.target.value);
  };
  
  const clearSearch = () => {
    setSearchTerm('');
    if (initialSearch) {
      onSearch && onSearch('', filterValue);
    }
  };
  
  const handleSubmit = (e, filter = filterValue) => {
    e.preventDefault();
    onSearch && onSearch(searchTerm, filter);
  };
  
  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', alignItems: 'flex-end', gap: 1, flexWrap: 'wrap' }}>
      <TextField
        placeholder={searchPlaceholder}
        value={searchTerm}
        onChange={handleSearchChange}
        variant="outlined"
        size="small"
        sx={{ flexGrow: 1, minWidth: { xs: '100%', sm: 'auto' } }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <FontAwesomeIcon icon={faSearch} />
            </InputAdornment>
          ),
          endAdornment: searchTerm && (
            <InputAdornment position="end">
              <IconButton
                aria-label="clear search"
                onClick={clearSearch}
                edge="end"
                size="small"
              >
                <FontAwesomeIcon icon={faTimes} />
              </IconButton>
            </InputAdornment>
          )
        }}
      />
      
      {options && (
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel id="filter-select-label">Filtrar por</InputLabel>
          <Select
            labelId="filter-select-label"
            value={filterValue}
            onChange={handleFilterChange}
            label="Filtrar por"
            displayEmpty
          >
            <MenuItem value="">
              <em>Todos</em>
            </MenuItem>
            {options.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
      
      <Button 
        type="submit"
        variant="contained"
        disableElevation
        startIcon={<FontAwesomeIcon icon={faFilter} />}
      >
        Aplicar
      </Button>
    </Box>
  );
}

export default NutritionFilters;