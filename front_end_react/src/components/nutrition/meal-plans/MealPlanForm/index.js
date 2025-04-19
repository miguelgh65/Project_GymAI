// src/components/nutrition/meal-plans/MealPlanForm/index.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Alert, CircularProgress, Button } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faSave } from '@fortawesome/free-solid-svg-icons';
import { MealService, MealPlanService, NutritionCalculator } from '../../../../services/NutritionService';

// Importar subcomponentes
import PlanBasicInfo from './PlanBasicInfo';
import NutritionTargets from './NutritionTargets';
import DaySelectorTabs from './DaySelectorTabs';
import MealSelector from './MealSelector';
import DayMealsList from './DayMealsList';
import ProgressSection from './ProgressSection';
import PlanSummary from './PlanSummary';

const MealPlanForm = ({ editId, onSaveSuccess }) => {
  const { planId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(planId || editId);
  const id = planId || editId;

  // Estado principal del formulario
  const [planName, setPlanName] = useState('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [items, setItems] = useState([]);
  
  // Estado para objetivos nutricionales
  const [targetCalories, setTargetCalories] = useState('');
  const [targetProtein, setTargetProtein] = useState('');
  const [targetCarbs, setTargetCarbs] = useState('');
  const [targetFat, setTargetFat] = useState('');
  const [userNutritionProfile, setUserNutritionProfile] = useState(null);
  
  // Estado para comidas disponibles
  const [availableMeals, setAvailableMeals] = useState([]);
  
  // Estado de control del formulario
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Estado para la navegación de pestañas de días
  const [activeTab, setActiveTab] = useState(0);

  const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  
  // Cargar perfil nutricional del usuario
  useEffect(() => {
    const loadNutritionProfile = async () => {
      try {
        const profile = await NutritionCalculator.getProfile();
        if (profile) {
          console.log("Perfil nutricional cargado:", profile);
          setUserNutritionProfile(profile);
          
          // Si no hay objetivos en el plan, usar los del perfil como valores predeterminados
          if (!targetCalories && profile.goal_calories) {
            setTargetCalories(profile.goal_calories.toString());
          }
          if (!targetProtein && profile.target_protein_g) {
            setTargetProtein(profile.target_protein_g.toString());
          }
          if (!targetCarbs && profile.target_carbs_g) {
            setTargetCarbs(profile.target_carbs_g.toString());
          }
          if (!targetFat && profile.target_fat_g) {
            setTargetFat(profile.target_fat_g.toString());
          }
        }
        
        // Verificar si hay objetivos temporales guardados
        const tempTargets = localStorage.getItem('temp_nutrition_targets');
        if (tempTargets) {
          try {
            const targets = JSON.parse(tempTargets);
            // Aplicar objetivos temporales si existen
            setTargetCalories(targets.target_calories.toString());
            setTargetProtein(targets.target_protein_g.toString());
            setTargetCarbs(targets.target_carbs_g.toString());
            setTargetFat(targets.target_fat_g.toString());
            // Eliminar después de usarlos
            localStorage.removeItem('temp_nutrition_targets');
          } catch (error) {
            console.error('Error al procesar objetivos temporales:', error);
          }
        }
      } catch (error) {
        console.error("Error al cargar perfil nutricional:", error);
      }
    };
    
    loadNutritionProfile();
  }, [targetCalories, targetProtein, targetCarbs, targetFat]);

  // Cargar datos si estamos editando
  useEffect(() => {
    if (isEditing && id) {
      setLoading(true);
      MealPlanService.getById(id)
        .then(data => {
          console.log("Datos del plan cargados:", data);
          setPlanName(data.plan_name || data.name || '');
          setDescription(data.description || '');
          setIsActive(data.is_active !== undefined ? data.is_active : true);
          
          // Cargar objetivos nutricionales
          if (data.target_calories) setTargetCalories(data.target_calories.toString());
          if (data.target_protein_g) setTargetProtein(data.target_protein_g.toString());
          if (data.target_carbs_g) setTargetCarbs(data.target_carbs_g.toString());
          if (data.target_fat_g) setTargetFat(data.target_fat_g.toString());
          
          // Transformar items si existen
          if (data.items && Array.isArray(data.items)) {
            setItems(data.items.map(item => ({
              ...item,
              day_of_week: item.day_of_week || getDayFromDate(item.plan_date) || 'Lunes',
              meal_type: item.meal_type?.replace('MealTime.', '') || 'Comida'
            })));
          }
          
          setLoading(false);
        })
        .catch(err => {
          console.error("Error fetching meal plan:", err);
          setError(err.message || 'Error al cargar el plan.');
          setLoading(false);
        });
    }
  }, [id, isEditing]);

  // Cargar comidas disponibles
  useEffect(() => {
    MealService.getAll()
      .then(response => {
        const meals = response.meals || [];
        console.log(`Cargadas ${meals.length} comidas disponibles`);
        setAvailableMeals(meals);
      })
      .catch(err => {
        console.error("Error fetching available meals:", err);
        setError("Error al cargar el listado de comidas disponibles.");
      });
  }, []);

  // Función para obtener el día de la semana de una fecha
  const getDayFromDate = (dateString) => {
    if (!dateString) return null;
    
    try {
      const date = new Date(dateString);
      const dayIndex = date.getDay(); // 0 = Domingo, 1 = Lunes, ...
      // Ajustar para que 0 = Lunes, 6 = Domingo
      const adjustedIndex = dayIndex === 0 ? 6 : dayIndex - 1;
      return daysOfWeek[adjustedIndex];
    } catch (error) {
      console.error("Error parsing date:", error);
      return null;
    }
  };

  // Función para manejar cambios en información básica
  const handleBasicInfoChange = (field, value) => {
    switch (field) {
      case 'name':
        setPlanName(value);
        break;
      case 'description':
        setDescription(value);
        break;
      case 'is_active':
        setIsActive(value);
        break;
      default:
        break;
    }
  };
  
  // Función para manejar cambios en objetivos nutricionales
  const handleTargetsChange = (field, value) => {
    switch (field) {
      case 'calories':
        setTargetCalories(value);
        break;
      case 'protein':
        setTargetProtein(value);
        break;
      case 'carbs':
        setTargetCarbs(value);
        break;
      case 'fat':
        setTargetFat(value);
        break;
      default:
        break;
    }
  };
  
  // Función para añadir una comida
  const handleAddMeal = (meal, quantity, unit, mealType) => {
    // Calcular factor para los macros
    const factor = parseFloat(quantity) / 100; // Asumiendo que los macros son por 100g/ml

    const newItem = {
      meal_id: meal.id,
      meal_name: meal.name || meal.meal_name,
      day_of_week: daysOfWeek[activeTab],
      meal_type: mealType,
      quantity: parseFloat(quantity),
      unit: unit || 'g',
      // Incluir propiedades nutricionales si existen
      calories: meal.calories ? Math.round(meal.calories * factor) : null,
      protein_g: meal.protein_g || meal.proteins ? 
                 Math.round((meal.protein_g || meal.proteins) * factor * 10) / 10 : null,
      carbohydrates_g: meal.carbohydrates_g || meal.carbohydrates ? 
                       Math.round((meal.carbohydrates_g || meal.carbohydrates) * factor * 10) / 10 : null,
      fat_g: meal.fat_g || meal.fats ? 
             Math.round((meal.fat_g || meal.fats) * factor * 10) / 10 : null
    };

    setItems([...items, newItem]);
  };
  
  // Función para eliminar una comida
  const handleRemoveMeal = (index) => {
    setItems(items.filter((_, i) => i !== index));
  };
  
  // Función para enviar el formulario
  const handleSubmit = async () => {
    if (!planName.trim()) {
      setError("El nombre del plan es obligatorio");
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);

    const planData = {
      plan_name: planName,
      description: description,
      is_active: isActive,
      target_calories: targetCalories ? parseFloat(targetCalories) : null,
      target_protein_g: targetProtein ? parseFloat(targetProtein) : null,
      target_carbs_g: targetCarbs ? parseFloat(targetCarbs) : null,
      target_fat_g: targetFat ? parseFloat(targetFat) : null,
      items: items.map(item => ({
        meal_id: item.meal_id,
        day_of_week: item.day_of_week,
        meal_type: item.meal_type,
        quantity: item.quantity,
        unit: item.unit || 'g'
      }))
    };

    try {
      if (isEditing) {
        await MealPlanService.update(id, planData);
        setSuccess('Plan actualizado con éxito.');
      } else {
        await MealPlanService.create(planData);
        setSuccess('Plan creado con éxito.');
      }
      
      // Notificar éxito si hay callback
      if (onSaveSuccess) {
        setTimeout(() => onSaveSuccess(), 1500);
      } else {
        // Redirigir después de un éxito
        setTimeout(() => navigate('/nutrition'), 1500);
      }
    } catch (err) {
      console.error("Error saving meal plan:", err);
      setError(err.message || 'Error al guardar el plan.');
    } finally {
      setLoading(false);
    }
  };
  
  // Filtrar items para el día activo
  const getActiveTabItems = () => {
    return items.filter(item => item.day_of_week === daysOfWeek[activeTab]);
  };
  
  if (loading && isEditing) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      </Box>
      
      <PlanBasicInfo 
        name={planName}
        description={description}
        isActive={isActive}
        onChange={handleBasicInfoChange}
      />
      
      <NutritionTargets 
        calories={targetCalories}
        protein={targetProtein}
        carbs={targetCarbs}
        fat={targetFat}
        profile={userNutritionProfile}
        onChange={handleTargetsChange}
      />
      
      <DaySelectorTabs 
        days={daysOfWeek}
        activeTab={activeTab}
        onChange={setActiveTab}
      />
      
      <ProgressSection 
        targetCalories={targetCalories}
        targetProtein={targetProtein}
        targetCarbs={targetCarbs}
        targetFat={targetFat}
        items={items}
        activeDay={daysOfWeek[activeTab]}
      />
      
      <MealSelector 
        meals={availableMeals}
        onAddMeal={handleAddMeal}
      />
      
      <DayMealsList 
        items={getActiveTabItems()}
        onRemove={handleRemoveMeal}
      />
      
      <PlanSummary 
        items={items}
        days={daysOfWeek}
        targetCalories={targetCalories}
        targetProtein={targetProtein}
        targetCarbs={targetCarbs}
        targetFat={targetFat}
      />
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          variant="outlined"
          startIcon={<FontAwesomeIcon icon={faArrowLeft} />}
          onClick={() => navigate('/nutrition')}
        >
          Cancelar
        </Button>
        
        <Button
          type="button"
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={loading || !planName.trim()}
          startIcon={loading ? <CircularProgress size={20} /> : <FontAwesomeIcon icon={faSave} />}
        >
          {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
        </Button>
      </Box>
    </Box>
  );
};

export default MealPlanForm;