// src/components/nutrition/NutritionPage.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, Tabs, Tab, Paper } from '@mui/material';

// Importa los componentes necesarios
import IngredientList from './ingredients/IngredientList';
import IngredientForm from './ingredients/IngredientForm';
import MealList from './meals/MealList';
import MealForm from './meals/MealForm';
import MealPlanList from './meal-plans/MealPlanList';
import MealPlanForm from './meal-plans/MealPlanForm'; // Cambiado a MealPlanForm (refactorizado)
import MealPlanCalendar from './meal-plans/MealPlanCalendar';
import MacroCalculator from './calculator/MacroCalculator';
import NutritionDashboard from './dashboard/NutritionDashboard'; // Nuevo componente de dashboard

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
const NutritionPage = ({ user }) => { 
  // Revisa si hay un tab guardado en localStorage para recuperarlo
  const getSavedTab = () => {
    const savedTab = localStorage.getItem('nutrition_tab');
    if (savedTab !== null) {
      localStorage.removeItem('nutrition_tab');
      return parseInt(savedTab, 10);
    }
    return 0; // Por defecto, empezamos con Dashboard
  };

  // Estado para controlar la pestaña activa
  const [currentTab, setCurrentTab] = useState(getSavedTab());
  
  // Estado para manejar la edición de un plan existente
  const [editPlanId, setEditPlanId] = useState(null);

  // Verifica si hay un plan para editar en localStorage
  useEffect(() => {
    const storedEditPlanId = localStorage.getItem('nutrition_edit_plan_id');
    if (storedEditPlanId) {
      setEditPlanId(storedEditPlanId);
      setCurrentTab(2); // Ir a la pestaña de creación/edición
      localStorage.removeItem('nutrition_edit_plan_id');
    }
  }, []);

  // Manejador de cambio de pestaña
  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
    
    // Si cambiamos de la pestaña de edición, limpiar el ID de edición
    if (currentTab === 2 && newValue !== 2) {
      setEditPlanId(null);
    }
  };

  // Función para ir a crear un nuevo plan
  const goToCreatePlan = () => {
    setEditPlanId(null);
    setCurrentTab(2);
  };
  
  // Función para ir a editar un plan existente
  const goToEditPlan = (id) => {
    setEditPlanId(id);
    setCurrentTab(2);
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
            {/* Nueva pestaña de Dashboard */}
            <Tab label="Dashboard" id="nutrition-tab-0" aria-controls="nutrition-tabpanel-0"/>
            
            {/* Pestañas existentes (ahora con índices desplazados) */}
            <Tab label="Planes de Nutrición" id="nutrition-tab-1" aria-controls="nutrition-tabpanel-1"/>
            <Tab label="Crear Plan" id="nutrition-tab-2" aria-controls="nutrition-tabpanel-2"/>
            <Tab label="Calendario Plan" id="nutrition-tab-3" aria-controls="nutrition-tabpanel-3"/>
            <Tab label="Comidas" id="nutrition-tab-4" aria-controls="nutrition-tabpanel-4"/>
            <Tab label="Crear Comida" id="nutrition-tab-5" aria-controls="nutrition-tabpanel-5"/>
            <Tab label="Ingredientes" id="nutrition-tab-6" aria-controls="nutrition-tabpanel-6"/>
            <Tab label="Añadir Ingrediente" id="nutrition-tab-7" aria-controls="nutrition-tabpanel-7"/>
            <Tab label="Calculadora" id="nutrition-tab-8" aria-controls="nutrition-tabpanel-8"/>
          </Tabs>
        </Box>
        
        {/* Paneles con el contenido de cada pestaña */}
        <TabPanel value={currentTab} index={0}>
          <NutritionDashboard user={user} />
        </TabPanel>
        
        <TabPanel value={currentTab} index={1}>
          <MealPlanList 
            onCreateNew={goToCreatePlan} 
            onEdit={goToEditPlan} 
          />
        </TabPanel>
        
        <TabPanel value={currentTab} index={2}>
          <MealPlanForm 
            key={`plan-form-${editPlanId || 'new'}`}
            editId={editPlanId}
            onSaveSuccess={() => setCurrentTab(1)} 
          />
        </TabPanel>
        
        <TabPanel value={currentTab} index={3}>
          <MealPlanCalendar />
        </TabPanel>
        
        <TabPanel value={currentTab} index={4}>
          <MealList />
        </TabPanel>
        
        <TabPanel value={currentTab} index={5}>
          <MealForm key={`meal-form-${currentTab}`} />
        </TabPanel>
        
        <TabPanel value={currentTab} index={6}>
          <IngredientList />
        </TabPanel>
        
        <TabPanel value={currentTab} index={7}>
          <IngredientForm key={`ingredient-form-${currentTab}`} />
        </TabPanel>
        
        <TabPanel value={currentTab} index={8}>
          <MacroCalculator user={user} />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default NutritionPage;