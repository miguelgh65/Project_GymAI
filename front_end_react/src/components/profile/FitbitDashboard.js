// src/components/profile/FitbitDashboard.js
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Tabs,
  Tab,
  CircularProgress,
  Button,
  IconButton
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faSync,
  faInfoCircle
} from '@fortawesome/free-solid-svg-icons';
import ApiService from '../../services/ApiService';

// Importar componentes modulares
import FitbitProfileSummary from './fitbit/FitbitProfileSummary';
import FitbitActivityData from './fitbit/FitbitActivityData';
import FitbitHeartRate from './fitbit/FitbitHeartRate';
import FitbitSleepData from './fitbit/FitbitSleepData';

function FitbitDashboard({ user }) {
  const [activeTab, setActiveTab] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Datos de Fitbit
  const [profileData, setProfileData] = useState(null);
  const [activityData, setActivityData] = useState(null);
  const [heartRateData, setHeartRateData] = useState(null);
  const [sleepData, setSleepData] = useState(null);
  
  // Fecha para consultas
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().substring(0, 10) // formato YYYY-MM-DD
  );
  
  useEffect(() => {
    if (user) {
      loadProfileData();
    }
  }, [user]);
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    
    // Cargar datos según la pestaña seleccionada
    switch(newValue) {
      case 0: // Resumen
        loadProfileData();
        loadActivityData();
        break;
      case 1: // Actividad
        loadActivityData();
        break;
      case 2: // Frecuencia cardíaca
        loadHeartRateData();
        break;
      case 3: // Sueño
        loadSleepData();
        break;
      default:
        break;
    }
  };
  
  const loadProfileData = async () => {
    setIsLoading(true);
    try {
      const response = await ApiService.getFitbitData('profile');
      if (response.success) {
        setProfileData(response.data);
      } else {
        setError('No se pudieron cargar los datos del perfil');
      }
    } catch (error) {
      console.error('Error al cargar datos del perfil:', error);
      setError('Error al cargar datos del perfil');
    } finally {
      setIsLoading(false);
    }
  };
  
  const loadActivityData = async () => {
    setIsLoading(true);
    try {
      const response = await ApiService.getFitbitData('activity_summary', selectedDate);
      if (response.success) {
        setActivityData(response.data);
      } else {
        setError('No se pudieron cargar los datos de actividad');
      }
    } catch (error) {
      console.error('Error al cargar datos de actividad:', error);
      setError('Error al cargar datos de actividad');
    } finally {
      setIsLoading(false);
    }
  };
  
  const loadHeartRateData = async () => {
    setIsLoading(true);
    try {
      const response = await ApiService.getFitbitData('heart_rate_intraday', selectedDate, '1min');
      if (response.success) {
        setHeartRateData(response.data);
      } else {
        setError('No se pudieron cargar los datos de frecuencia cardíaca');
      }
    } catch (error) {
      console.error('Error al cargar datos de frecuencia cardíaca:', error);
      setError('Error al cargar datos de frecuencia cardíaca');
    } finally {
      setIsLoading(false);
    }
  };
  
  const loadSleepData = async () => {
    setIsLoading(true);
    try {
      const response = await ApiService.getFitbitData('sleep_log', selectedDate);
      if (response.success) {
        setSleepData(response.data);
      } else {
        setError('No se pudieron cargar los datos de sueño');
      }
    } catch (error) {
      console.error('Error al cargar datos de sueño:', error);
      setError('Error al cargar datos de sueño');
    } finally {
      setIsLoading(false);
    }
  };
  
  const refreshCurrentData = () => {
    // Actualizar datos según la pestaña activa
    switch(activeTab) {
      case 0:
        loadProfileData();
        loadActivityData();
        break;
      case 1:
        loadActivityData();
        break;
      case 2:
        loadHeartRateData();
        break;
      case 3:
        loadSleepData();
        break;
      default:
        break;
    }
  };

  return (
    <Box sx={{ bgcolor: 'background.paper', borderRadius: 1, boxShadow: 1, overflow: 'hidden' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h5" component="h2">
          Dashboard Fitbit
        </Typography>
        <Box>
          <IconButton 
            color="primary" 
            onClick={refreshCurrentData}
            disabled={isLoading}
            title="Actualizar datos"
          >
            <FontAwesomeIcon icon={faSync} spin={isLoading} />
          </IconButton>
          <IconButton
            color="info"
            title="Información"
          >
            <FontAwesomeIcon icon={faInfoCircle} />
          </IconButton>
        </Box>
      </Box>
      
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange} 
        variant="scrollable"
        scrollButtons="auto"
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Resumen" />
        <Tab label="Actividad" />
        <Tab label="Ritmo Cardíaco" />
        <Tab label="Sueño" />
      </Tabs>
      
      <Box sx={{ p: 2 }}>
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}
        
        {!isLoading && error && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body1" color="error">
              {error}
            </Typography>
            <Button 
              variant="outlined" 
              color="primary" 
              onClick={refreshCurrentData}
              sx={{ mt: 2 }}
            >
              Reintentar
            </Button>
          </Box>
        )}
        
        {!isLoading && !error && (
          <Box sx={{ mt: 2 }}>
            {activeTab === 0 && (
              <FitbitProfileSummary 
                profileData={profileData} 
                activityData={activityData} 
                sleepData={sleepData} 
              />
            )}
            {activeTab === 1 && (
              <FitbitActivityData 
                activityData={activityData} 
              />
            )}
            {activeTab === 2 && (
              <FitbitHeartRate 
                heartRateData={heartRateData} 
                selectedDate={selectedDate} 
              />
            )}
            {activeTab === 3 && (
              <FitbitSleepData 
                sleepData={sleepData} 
              />
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
}

export default FitbitDashboard;