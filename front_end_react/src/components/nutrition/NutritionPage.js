// src/components/nutrition/NutritionPage.js
import React, { useState } from 'react';
import { Box, Typography, Tabs, Tab, Paper } from '@mui/material';

// Importa los componentes que ya tienes desde sus subcarpetas
import IngredientList from './ingredients/IngredientList';
import IngredientForm from './ingredients/IngredientForm';
import MealList from './meals/MealList';
import MealForm from './meals/MealForm';
import MealPlanList from './meal-plans/MealPlanList';
import MealPlanForm from './meal-plans/MealPlanForm';
import MealPlanCalendar from './meal-plans/MealPlanCalendar';

// Componente helper para los paneles de las pestañas
function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`nutrition-tabpanel-${index}`}
      aria-labelledby={`nutrition-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}> {/* Añade padding top */}
          {children}
        </Box>
      )}
    </div>
  );
}

// Componente principal de la página de Nutrición
const NutritionPage = ({ user }) => { // Recibe user si lo necesitas pasar a subcomponentes
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
       <Typography variant="h4" component="h1" gutterBottom>
         Gestión de Nutrición
       </Typography>
       <Paper elevation={2} sx={{ width: '100%'}}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
                value={currentTab}
                onChange={handleTabChange}
                aria-label="Secciones de nutrición"
                variant="scrollable" // Para que funcione bien en móvil
                scrollButtons="auto" // Muestra botones si no caben todas
            >
              {/* Pestañas para las vistas principales */}
              <Tab label="Ingredientes" id="nutrition-tab-0" aria-controls="nutrition-tabpanel-0"/>
              <Tab label="Comidas" id="nutrition-tab-1" aria-controls="nutrition-tabpanel-1"/>
              <Tab label="Planes Comida" id="nutrition-tab-2" aria-controls="nutrition-tabpanel-2"/>
              <Tab label="Calendario Plan" id="nutrition-tab-3" aria-controls="nutrition-tabpanel-3"/>
              {/* Pestañas para formularios (opcional, podrías usar Modales o páginas separadas) */}
              <Tab label="Añadir Ingrediente" id="nutrition-tab-4" aria-controls="nutrition-tabpanel-4"/>
              <Tab label="Crear Comida" id="nutrition-tab-5" aria-controls="nutrition-tabpanel-5"/>
              <Tab label="Crear Plan" id="nutrition-tab-6" aria-controls="nutrition-tabpanel-6"/>
            </Tabs>
          </Box>
          {/* Paneles con el contenido de cada pestaña */}
          <TabPanel value={currentTab} index={0}>
            <IngredientList />
          </TabPanel>
          <TabPanel value={currentTab} index={1}>
            <MealList />
          </TabPanel>
          <TabPanel value={currentTab} index={2}>
            <MealPlanList />
          </TabPanel>
           <TabPanel value={currentTab} index={3}>
             <MealPlanCalendar />
          </TabPanel>
           <TabPanel value={currentTab} index={4}>
            {/* Pasar key diferente resetea el estado del form si cambias de pestaña y vuelves */}
            <IngredientForm key={`ingredient-form-${currentTab}`} />
          </TabPanel>
           <TabPanel value={currentTab} index={5}>
            <MealForm key={`meal-form-${currentTab}`} />
          </TabPanel>
           <TabPanel value={currentTab} index={6}>
            <MealPlanForm key={`mealplan-form-${currentTab}`} />
          </TabPanel>
       </Paper>
    </Box>
  );
};

export default NutritionPage;