// src/components/nutrition/calculator/components/useMacroCalculatorForm.js
import { useState } from 'react';
import { DEFAULT_FORM_VALUES } from '../constants';

export const useMacroCalculatorForm = () => {
  // Estado inicial del formulario
  const [formData, setFormData] = useState(DEFAULT_FORM_VALUES);

  // Manejador para cambios en el formulario
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Manejador para cambios en sliders
  const handleSliderChange = (name) => (e, newValue) => {
    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  return {
    formData,
    setFormData,
    handleChange,
    handleSliderChange
  };
};

export default useMacroCalculatorForm;