// src/services/nutrition/NutritionCalculator.js
// Service for calculating nutritional values

import axios from 'axios';
import { API_BASE } from './constants';

/**
 * Service for calculating nutritional values
 */
class NutritionCalculatorService {
  /**
   * Calculate macros based on user inputs
   * @param {Object} data - User biometric and goal data
   * @returns {Object} Calculated macros and nutrition values
   */
  async calculateMacros(data) {
    try {
      const response = await axios.post(`${API_BASE}/calculate-macros`, data);
      return response.data;
    } catch (error) {
      console.error('Error calculating macros:', error);
      
      // Provide local calculation as fallback
      const bmr = this.calculateBMR(data);
      const tdee = this.calculateTDEE(bmr, data.activity_level);
      const goalCalories = this.calculateGoalCalories(tdee, data.goal, data.goal_intensity);
      
      return {
        bmr: Math.round(bmr),
        tdee: Math.round(tdee),
        bmi: this.calculateBMI(data),
        goal_calories: Math.round(goalCalories),
        macros: this.calculateMacroRatio(goalCalories, data.goal)
      };
    }
  }

  /**
   * Get user's nutrition profile
   * @returns {Object|null} User nutrition profile or null if not found
   */
  async getProfile() {
    try {
      const response = await axios.get(`${API_BASE}/profile`);
      return response.data?.profile || null;
    } catch (error) {
      console.error('Error fetching nutrition profile:', error);
      return null;
    }
  }
  
  // Helper methods for local calculations
  
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
    } else {
      // Default to Harris-Benedict
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
    
    return bmr * (activityMultipliers[activityLevel] || 1.2);
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
        normal: -500,
        aggressive: -1000
      },
      gain: {
        normal: 500,
        aggressive: 1000
      }
    };
    
    return tdee + (adjustments[goal]?.[intensity] || 0);
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
      proteins: {
        grams: proteinGrams,
        calories: Math.round(proteinCalories),
        percentage: Math.round(proteinPct * 100)
      },
      carbs: {
        grams: carbsGrams,
        calories: Math.round(carbsCalories),
        percentage: Math.round(carbsPct * 100)
      },
      fats: {
        grams: fatGrams,
        calories: Math.round(fatCalories),
        percentage: Math.round(fatPct * 100)
      }
    };
  }
}

// Create and export the singleton instance
export const NutritionCalculator = new NutritionCalculatorService();