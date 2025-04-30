// src/services/nutrition/NutritionCalculator.js
// Service for calculating nutritional values

import axios from 'axios';
import { API_BASE } from './constants';

/**
 * Service for calculating nutritional values and managing nutrition profiles
 */
class NutritionCalculatorService {
  constructor() {
    // Añadir soporte para almacenamiento local como fallback
    this.LOCAL_STORAGE_KEY = 'nutrition_profile';
    
    // Debugging para ver si las rutas son correctas
    console.log("NutritionCalculator iniciado con API_BASE:", API_BASE);
  }

  /**
   * Calculate macros based on user inputs
   * @param {Object} data - User biometric and goal data
   * @returns {Object} Calculated macros and nutrition values
   */
  async calculateMacros(data) {
    try {
      console.log("NutritionCalculator: Calculando macros con datos:", data);
      
      // Comprobar si tenemos una API configurada
      if (!API_BASE) {
        console.warn("API_BASE no está definido, usando cálculo local");
        throw new Error("API_BASE no definido");
      }
      
      // Intentar usar la API primero
      const response = await axios.post(`${API_BASE}/calculate-macros`, data, {
        timeout: 5000 // 5 segundos de timeout
      });
      
      console.log("Respuesta de API:", response.data);
      return response.data;
    } catch (error) {
      console.error('Error en API de cálculo de macros:', error);
      console.log("Usando cálculo local como fallback");
      
      // Proporcionar cálculo local como fallback
      const bmr = this.calculateBMR(data);
      const tdee = this.calculateTDEE(bmr, data.activity_level);
      const goalCalories = this.calculateGoalCalories(tdee, data.goal, data.goal_intensity);
      const bmi = this.calculateBMI(data);
      const macros = this.calculateMacroRatio(goalCalories, data.goal);
      
      // Preparar respuesta en formato similar a la API
      return {
        bmr: Math.round(bmr),
        tdee: Math.round(tdee),
        bmi: bmi,
        goal_calories: Math.round(goalCalories),
        macros: macros
      };
    }
  }

  /**
   * Get user's nutrition profile
   * @returns {Object|null} User nutrition profile or null if not found
   */
  async getProfile() {
    try {
      console.log("NutritionCalculator: Obteniendo perfil nutricional");
      
      // Comprobar si tenemos una API configurada
      if (!API_BASE) {
        console.warn("API_BASE no está definido, usando datos locales");
        throw new Error("API_BASE no definido");
      }
      
      // Intentar obtener de la API primero
      const response = await axios.get(`${API_BASE}/profile`, {
        timeout: 5000 // 5 segundos de timeout
      });
      
      console.log("Perfil de API:", response.data);
      
      if (response.data?.profile) {
        // Guardar en localStorage como respaldo
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(response.data.profile));
        return response.data.profile;
      }
      
      throw new Error("Formato de respuesta inválido o perfil no encontrado");
    } catch (error) {
      console.error('Error al obtener perfil nutricional de API:', error);
      
      // Intentar obtener de localStorage como fallback
      try {
        const localProfile = localStorage.getItem(this.LOCAL_STORAGE_KEY);
        if (localProfile) {
          console.log("Usando perfil de localStorage:", localProfile);
          const profile = JSON.parse(localProfile);
          return profile;
        }
      } catch (localError) {
        console.error('Error al leer perfil de localStorage:', localError);
      }
      
      return null;
    }
  }
  
  /**
   * Save user's nutrition profile
   * @param {Object} profileData - User profile data
   * @returns {Object|null} Saved profile or null if error
   */
  async saveProfile(profileData) {
    try {
      console.log("NutritionCalculator: Guardando perfil:", profileData);
      
      // Asegurarse de que tenemos todos los campos requeridos para el dashboard
      const completeProfileData = {
        ...profileData,
        // Asegurarnos de que estos campos existen para el dashboard
        target_protein_g: profileData.target_protein_g || profileData.macros?.protein?.grams || 0,
        target_carbs_g: profileData.target_carbs_g || profileData.macros?.carbs?.grams || 0,
        target_fat_g: profileData.target_fat_g || profileData.macros?.fat?.grams || 0,
        updated_at: new Date().toISOString()
      };
      
      // Guardar en localStorage primero como respaldo
      localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(completeProfileData));
      console.log("Perfil guardado en localStorage:", completeProfileData);
      
      // Comprobar si tenemos una API configurada
      if (!API_BASE) {
        console.warn("API_BASE no está definido, guardando solo localmente");
        return completeProfileData;
      }
      
      // Intentar guardar en la API
      const response = await axios.post(`${API_BASE}/profile`, completeProfileData, {
        timeout: 5000 // 5 segundos de timeout
      });
      
      console.log("Respuesta de API al guardar perfil:", response.data);
      
      if (response.data?.profile || response.data?.success) {
        const savedProfile = response.data.profile || completeProfileData;
        // Actualizar localStorage con datos del servidor
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(savedProfile));
        return savedProfile;
      }
      
      // Si la API responde pero no proporciona datos válidos, usar los datos locales
      return completeProfileData;
    } catch (error) {
      console.error('Error al guardar perfil en API:', error);
      console.log("Usando perfil guardado localmente como respuesta");
      
      // Ya hemos guardado en localStorage antes, así que simplemente devolvemos esos datos
      try {
        const localProfile = localStorage.getItem(this.LOCAL_STORAGE_KEY);
        if (localProfile) {
          return JSON.parse(localProfile);
        }
      } catch (localError) {
        console.error('Error al leer perfil de localStorage después de guardar:', localError);
      }
      
      throw new Error("No se pudo guardar el perfil nutricional ni localmente ni en el servidor");
    }
  }
  
  // ========== MÉTODOS AUXILIARES PARA CÁLCULOS LOCALES ==========
  
  /**
   * Calculate Basal Metabolic Rate (BMR)
   * @param {Object} data - User data
   * @returns {number} BMR in calories
   */
  calculateBMR(data) {
    if (data.formula === 'mifflin_st_jeor') {
      // Mifflin-St Jeor Equation
      if (data.gender === 'male') {
        return (10 * data.weight) + (6.25 * data.height) - (5 * data.age) + 5;
      } else {
        return (10 * data.weight) + (6.25 * data.height) - (5 * data.age) - 161;
      }
    } else if (data.formula === 'katch_mcardle' && data.body_fat_percentage) {
      // Katch-McArdle Formula - requires body fat percentage
      const leanBodyMass = data.weight * (1 - (data.body_fat_percentage / 100));
      return 370 + (21.6 * leanBodyMass);
    } else if (data.formula === 'harris_benedict') {
      // Harris-Benedict
      if (data.gender === 'male') {
        return 88.362 + (13.397 * data.weight) + (4.799 * data.height) - (5.677 * data.age);
      } else {
        return 447.593 + (9.247 * data.weight) + (3.098 * data.height) - (4.330 * data.age);
      }
    } else {
      // WHO formula
      // Implementación simplificada usando Harris-Benedict como fallback
      if (data.gender === 'male') {
        return 88.362 + (13.397 * data.weight) + (4.799 * data.height) - (5.677 * data.age);
      } else {
        return 447.593 + (9.247 * data.weight) + (3.098 * data.height) - (4.330 * data.age);
      }
    }
  }
  
  /**
   * Calculate Total Daily Energy Expenditure (TDEE)
   * @param {number} bmr - Basal Metabolic Rate
   * @param {string} activityLevel - User activity level
   * @returns {number} TDEE in calories
   */
  calculateTDEE(bmr, activityLevel) {
    const activityMultipliers = {
      sedentary: 1.2,
      light: 1.375,
      moderate: 1.55,
      active: 1.725,
      very_active: 1.9
    };
    
    const multiplier = activityMultipliers[activityLevel] || 1.2;
    return bmr * multiplier;
  }
  
  /**
   * Calculate goal calories based on TDEE and user goals
   * @param {number} tdee - Total Daily Energy Expenditure
   * @param {string} goal - User goal (maintain, lose, gain)
   * @param {string} intensity - Goal intensity
   * @returns {number} Goal calories
   */
  calculateGoalCalories(tdee, goal, intensity) {
    if (goal === 'maintain') return tdee;
    
    const adjustments = {
      lose: {
        light: -250,
        normal: -500,
        aggressive: -750,
        very_aggressive: -1000
      },
      gain: {
        light: 250,
        normal: 500,
        aggressive: 750,
        very_aggressive: 1000
      }
    };
    
    // Asegurarse de que adjustments[goal] existe
    if (!adjustments[goal]) return tdee;
    
    // Asegurarse de que adjustments[goal][intensity] existe
    const adjustment = adjustments[goal][intensity] || 0;
    return tdee + adjustment;
  }
  
  /**
   * Calculate Body Mass Index (BMI)
   * @param {Object} data - User data
   * @returns {number} BMI value
   */
  calculateBMI(data) {
    // Weight in kg, height in cm
    const heightInMeters = data.height / 100;
    return Math.round((data.weight / (heightInMeters * heightInMeters)) * 10) / 10;
  }
  
  /**
   * Calculate macro ratios based on calories and goal
   * @param {number} calories - Total calories
   * @param {string} goal - User goal
   * @returns {Object} Calculated macros
   */
  calculateMacroRatio(calories, goal) {
    let proteinPct, carbsPct, fatPct;
    
    if (goal === 'lose') {
      proteinPct = 0.4; // 40%
      fatPct = 0.35;    // 35%
      carbsPct = 0.25;  // 25%
    } else if (goal === 'gain') {
      proteinPct = 0.3; // 30%
      fatPct = 0.3;     // 30%
      carbsPct = 0.4;   // 40%
    } else {
      // maintain
      proteinPct = 0.3; // 30%
      fatPct = 0.3;     // 30%
      carbsPct = 0.4;   // 40%
    }
    
    const proteinCalories = calories * proteinPct;
    const carbsCalories = calories * carbsPct;
    const fatCalories = calories * fatPct;
    
    const proteinGrams = Math.round(proteinCalories / 4);
    const carbsGrams = Math.round(carbsCalories / 4);
    const fatGrams = Math.round(fatCalories / 9);
    
    return {
      protein: {
        grams: proteinGrams,
        calories: Math.round(proteinCalories),
        percentage: Math.round(proteinPct * 100)
      },
      carbs: {
        grams: carbsGrams,
        calories: Math.round(carbsCalories),
        percentage: Math.round(carbsPct * 100)
      },
      fat: {
        grams: fatGrams,
        calories: Math.round(fatCalories),
        percentage: Math.round(fatPct * 100)
      }
    };
  }
}

// Create and export the singleton instance
export const NutritionCalculator = new NutritionCalculatorService();