// src/services/nutrition/constants.js
// Constants for nutrition services

// Base API URL prefix
export const API_BASE = '/api/nutrition';

// LocalStorage keys
export const LOCAL_STORAGE_MEAL_PLANS_KEY = 'local_meal_plans';

// Helper for logging
export const logDebug = (message, data = null) => {
  const timestamp = new Date().toISOString();
  const prefix = `[NutritionService ${timestamp}]`;
  
  if (data) {
    console.log(`${prefix} ${message}`, data);
  } else {
    console.log(`${prefix} ${message}`);
  }
};