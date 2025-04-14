// src/components/admin/LogViewer.js
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box, Typography, Paper, List, ListItem, ListItemText, ListItemIcon, Button,
  Divider, IconButton, FormControl, InputLabel, Select, MenuItem, Snackbar,
  TextField, Dialog, DialogTitle, DialogContent, DialogActions, Tab, Tabs,
  AppBar, Toolbar, CircularProgress, Alert, Grid, Card, CardContent, Chip
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faInfoCircle, faExclamationTriangle, faBug, faSearch,
  faDownload, faTrash, faCopy, faTimes, faDatabase, faNetworkWired,
  faSync, faUsersCog, faHistory, faFilter, faCubes, faCheckCircle,
  faHourglassHalf, faExclamationCircle, faLink, faClipboard
} from '@fortawesome/free-solid-svg-icons';
import LoggingService from '../../services/LoggingService';
import AuthService from '../../services/AuthService';

// Componente para mostrar un entry de log
const LogEntry = ({ log, onSelect, isSelected }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'error': return faExclamationTriangle;
      case 'warning': return faExclamationCircle;
      case 'debug': return faBug;
      default: return faInfoCircle;
    }
  };
  
  const getColor = (type) => {
    switch (type) {
      case 'error': return 'error.main';
      case 'warning': return 'warning.main';
      case 'debug': return 'grey.600';
      default: return 'info.main';
    }
  };
  
  // Formatear timestamp para mejor legibilidad
  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      // Mostrar solo hora:minutos:segundos para claridad
      return date.toLocaleTimeString();
    } catch (e) {
      return timestamp || 'N/A';
    }
  };
  
  return (
    <ListItem 
      button 
      onClick={() => onSelect(log)} 
      sx={{ 
        borderLeft: `4px solid ${getColor(log.type)}`,
        backgroundColor: isSelected ? 'rgba(0, 0, 0, 0.04)' : 'transparent',
        '&:hover': {
          backgroundColor: 'rgba(0, 0, 0, 0.08)',
        }
      }}
    >
      <ListItemIcon sx={{ color: getColor(log.type), minWidth: 40 }}>
        <FontAwesomeIcon icon={getIcon(log.type)} />
      </ListItemIcon>
      <ListItemText 
        primary={log.message}
        secondary={formatTimestamp(log.timestamp)}
        primaryTypographyProps={{ 
          fontWeight: log.type === 'error' ? 'bold' : 'normal',
          variant: 'body2',
          noWrap: true
        }}
        secondaryTypographyProps={{ 
          variant: 'caption', 
          color: 'text.secondary' 
        }}
      />
    </ListItem>
  );
};

// Panel de información del sistema
const SystemInfoPanel = ({ systemInfo, onRefresh }) => {
  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Información del sistema</Typography>
        <Button 
          size="small" 
          startIcon={<FontAwesomeIcon icon={faSync} />}
          onClick={onRefresh}
        >
          Actualizar
        </Button>
      </Box>
      
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                <FontAwesomeIcon icon={faDatabase} style={{ marginRight: 8 }} /> Almacenamiento
              </Typography>
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" component="div">
                  <strong>LocalStorage:</strong> {systemInfo?.storage?.localStorage?.available ? '✓' : '✗'}
                </Typography>
                {systemInfo?.storage?.localStorage?.hasToken && (
                  <Typography variant="body2" color="success.main">
                    Token JWT almacenado
                  </Typography>
                )}
                {systemInfo?.storage?.localStorage?.error && (
                  <Typography variant="body2" color="error">
                    Error: {systemInfo.storage.localStorage.error}
                  </Typography>
                )}
              </Box>
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" component="div">
                  <strong>SessionStorage:</strong> {systemInfo?.storage?.sessionStorage?.available ? '✓' : '✗'}
                </Typography>
                {systemInfo?.storage?.sessionStorage?.error && (
                  <Typography variant="body2" color="error">
                    Error: {systemInfo.storage.sessionStorage.error}
                  </Typography>
                )}
              </Box>
              
              <Box>
                <Typography variant="body2" component="div">
                  <strong>Cookies:</strong> {systemInfo?.storage?.cookies?.available ? '✓' : '✗'}
                </Typography>
                {systemInfo?.storage?.cookies?.error && (
                  <Typography variant="body2" color="error">
                    Error: {systemInfo.storage.cookies.error}
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                <FontAwesomeIcon icon={faNetworkWired} style={{ marginRight: 8 }} /> Navegador
              </Typography>
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" component="div">
                  <strong>Online:</strong> {systemInfo?.browser?.onLine ? '✓' : '✗'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" component="div">
                  <strong>Cookies habilitadas:</strong> {systemInfo?.browser?.cookiesEnabled ? '✓' : '✗'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" component="div">
                  <strong>Plataforma:</strong> {systemInfo?.browser?.platform || 'N/A'}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="body2" component="div">
                  <strong>Zona horaria:</strong> {systemInfo?.browser?.timezone || 'N/A'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                <FontAwesomeIcon icon={faUsersCog} style={{ marginRight: 8 }} /> Sesión
              </Typography>
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" component="div">
                  <strong>ID de sesión:</strong> {systemInfo?.sessionId || 'N/A'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" component="div">
                  <strong>Autenticado:</strong> {systemInfo?.auth?.hasToken ? '✓' : '✗'}
                </Typography>
                {systemInfo?.auth?.tokenSource && (
                  <Typography variant="body2" color="text.secondary">
                    Fuente: {systemInfo.auth.tokenSource}
                  </Typography>
                )}
              </Box>
              
              <Box>
                <Typography variant="body2" component="div">
                  <strong>Último intento de autenticación:</strong> {systemInfo?.auth?.lastAuthAttempt || 'N/A'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Componente principal
function LogViewer({ user }) {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);
  const [diagnosticModalOpen, setDiagnosticModalOpen] = useState(false);
  const [diagnosticData, setDiagnosticData] = useState(null);
  const [alertMessage, setAlertMessage] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [isExporting, setIsExporting] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [logsAutoRefresh, setLogsAutoRefresh] = useState(false);
  const autoRefreshTimerRef = useRef(null);
  
  // Cargar logs iniciales
  useEffect(() => {
    refreshLogs();
    loadSystemInfo();
    
    // Clean up timer
    return () => {
      if (autoRefreshTimerRef.current) {
        clearInterval(autoRefreshTimerRef.current);
      }
    };
  }, []);
  
  // Efecto para filtrado
  useEffect(() => {
    applyFilters();
  }, [logs, filter, searchQuery]);
  
  // Configurar autorefresh
  useEffect(() => {
    if (autoRefreshTimerRef.current) {
      clearInterval(autoRefreshTimerRef.current);
      autoRefreshTimerRef.current = null;
    }
    
    if (logsAutoRefresh) {
      autoRefreshTimerRef.current = setInterval(refreshLogs, 5000); // Cada 5 segundos
    }
    
    return () => {
      if (autoRefreshTimerRef.current) {
        clearInterval(autoRefreshTimerRef.current);
      }
    };
  }, [logsAutoRefresh]);
  
  const refreshLogs = useCallback(() => {
    setLogs(LoggingService.getLogs());
    setIsLoading(false);
  }, []);
  
  const loadSystemInfo = useCallback(() => {
    try {
      const info = AuthService.getDiagnosticInfo();
      setSystemInfo(info.system);
    } catch (error) {
      console.error('Error obteniendo info del sistema:', error);
      setAlertMessage({
        type: 'error',
        message: 'Error obteniendo información del sistema'
      });
    }
  }, []);
  
  const clearLogs = () => {
    if (window.confirm('¿Estás seguro de eliminar todos los logs? Esta acción no se puede deshacer.')) {
      LoggingService.clearLogs();
      refreshLogs();
      setSelectedLog(null);
      setAlertMessage({
        type: 'success',
        message: 'Logs eliminados correctamente'
      });
    }
  };
  
  const applyFilters = () => {
    let filtered = [...logs];
    
    // Filtrar por tipo
    if (filter !== 'all') {
      filtered = filtered.filter(log => log.type === filter);
    }
    
    // Filtrar por búsqueda
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(query) || 
        (log.details && JSON.stringify(log.details).toLowerCase().includes(query))
      );
    }
    
    setFilteredLogs(filtered);
  };
  
  const handleDownloadLogs = () => {
    setIsExporting(true);
    
    try {
      const data = {
        logs: logs,
        systemInfo: systemInfo,
        exportedAt: new Date().toISOString(),
        userInfo: {
          id: user?.id,
          email: user?.email
        }
      };
      
      const jsonString = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `logs_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setAlertMessage({
        type: 'success',
        message: 'Logs exportados correctamente'
      });
    } catch (error) {
      console.error('Error al exportar logs:', error);
      setAlertMessage({
        type: 'error',
        message: 'Error al exportar logs: ' + error.message
      });
    } finally {
      setIsExporting(false);
    }
  };
  
  const handleCopyDiagnostic = () => {
    if (!diagnosticData) return;
    
    try {
      const text = JSON.stringify(diagnosticData, null, 2);
      navigator.clipboard.writeText(text);
      setAlertMessage({
        type: 'success',
        message: 'Diagnóstico copiado al portapapeles'
      });
    } catch (error) {
      console.error('Error al copiar diagnóstico:', error);
      setAlertMessage({
        type: 'error',
        message: 'Error al copiar diagnóstico: ' + error.message
      });
    }
  };
  
  const handleShowFullDiagnostic = () => {
    try {
      const diagnosticInfo = {
        system: systemInfo,
        logs: logs.slice(0, 100), // Limitamos a 100 logs para no ser demasiado grande
        timestamp: new Date().toISOString(),
        browser: {
          userAgent: navigator.userAgent,
          language: navigator.language,
          platform: navigator.platform
        }
      };
      
      setDiagnosticData(diagnosticInfo);
      setDiagnosticModalOpen(true);
    } catch (error) {
      console.error('Error al generar diagnóstico completo:', error);
      setAlertMessage({
        type: 'error',
        message: 'Error al generar diagnóstico: ' + error.message
      });
    }
  };
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Filtro por nivel de severidad (tipo)
  const getLevelCounts = () => {
    const counts = {
      info: 0,
      warning: 0,
      error: 0,
      debug: 0
    };
    
    logs.forEach(log => {
      if (counts[log.type] !== undefined) {
        counts[log.type]++;
      }
    });
    
    return counts;
  };
  
  const levelCounts = getLevelCounts();
  
  // Búsqueda avanzada
  const handleSearch = (e) => {
    if (e.key === 'Enter' || e.type === 'click') {
      applyFilters();
    }
  };
  
  // Si no hay usuario o falta permisos, mostrar error
  if (!user) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Debes iniciar sesión para acceder al visor de logs.
        </Alert>
      </Box>
    );
  }
  
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Barra superior con título y controles */}
      <AppBar position="static" color="default" elevation={0}>
        <Toolbar sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h5" component="div" sx={{ flexGrow: 1 }}>
            <FontAwesomeIcon icon={faHistory} style={{ marginRight: '10px' }} />
            Visor de logs del sistema
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip 
              icon={<FontAwesomeIcon icon={faInfoCircle} />} 
              label={`Info: ${levelCounts.info}`} 
              color="primary" 
              size="small" 
              variant={filter === 'info' ? 'filled' : 'outlined'}
              onClick={() => setFilter(filter === 'info' ? 'all' : 'info')}
            />
            <Chip 
              icon={<FontAwesomeIcon icon={faExclamationCircle} />} 
              label={`Warnings: ${levelCounts.warning}`} 
              color="warning" 
              size="small"
              variant={filter === 'warning' ? 'filled' : 'outlined'}
              onClick={() => setFilter(filter === 'warning' ? 'all' : 'warning')}
            />
            <Chip 
              icon={<FontAwesomeIcon icon={faExclamationTriangle} />} 
              label={`Errores: ${levelCounts.error}`} 
              color="error" 
              size="small"
              variant={filter === 'error' ? 'filled' : 'outlined'}
              onClick={() => setFilter(filter === 'error' ? 'all' : 'error')}
            />
            <Chip 
              icon={<FontAwesomeIcon icon={faBug} />} 
              label={`Debug: ${levelCounts.debug}`} 
              color="default" 
              size="small"
              variant={filter === 'debug' ? 'filled' : 'outlined'}
              onClick={() => setFilter(filter === 'debug' ? 'all' : 'debug')}
            />
          </Box>
        </Toolbar>
        
        {/* Tabs para navegar entre secciones */}
        <Box>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab label="Logs" icon={<FontAwesomeIcon icon={faHistory} />} iconPosition="start" />
            <Tab label="Sistema" icon={<FontAwesomeIcon icon={faCubes} />} iconPosition="start" />
          </Tabs>
        </Box>
      </AppBar>
      
      {/* Cuerpo - Tab de Logs */}
      {tabValue === 0 && (
        <Box sx={{ p: 2, flexGrow: 1, height: 'calc(100% - 130px)', display: 'flex', flexDirection: 'column' }}>
          {/* Controles de filtro y búsqueda */}
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TextField
                placeholder="Buscar en logs..."
                size="small"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearch}
                InputProps={{
                  endAdornment: (
                    <IconButton 
                      size="small" 
                      onClick={handleSearch}
                      disabled={searchQuery.length === 0}
                    >
                      <FontAwesomeIcon icon={faSearch} />
                    </IconButton>
                  )
                }}
                sx={{ minWidth: '250px' }}
              />
              
              <IconButton 
                size="small" 
                color="primary" 
                onClick={refreshLogs}
                title="Refrescar logs"
              >
                <FontAwesomeIcon icon={faSync} />
              </IconButton>
              
              <Button
                size="small"
                variant={logsAutoRefresh ? "contained" : "outlined"}
                color={logsAutoRefresh ? "primary" : "inherit"}
                startIcon={<FontAwesomeIcon icon={faHourglassHalf} />}
                onClick={() => setLogsAutoRefresh(!logsAutoRefresh)}
                sx={{ ml: 1 }}
              >
                Auto-refresh
              </Button>
            </Box>
            
            <Box>
              <Button
                variant="outlined"
                size="small"
                startIcon={<FontAwesomeIcon icon={faDownload} />}
                onClick={handleDownloadLogs}
                disabled={isExporting || logs.length === 0}
              >
                {isExporting ? <CircularProgress size={20} /> : 'Exportar'}
              </Button>
              
              <Button
                variant="outlined"
                color="error"
                size="small"
                startIcon={<FontAwesomeIcon icon={faTrash} />}
                onClick={clearLogs}
                disabled={logs.length === 0}
                sx={{ ml: 1 }}
              >
                Limpiar
              </Button>
              
              <Button
                variant="outlined"
                color="info"
                size="small"
                startIcon={<FontAwesomeIcon icon={faLink} />}
                onClick={handleShowFullDiagnostic}
                sx={{ ml: 1 }}
              >
                Diagnóstico
              </Button>
            </Box>
          </Box>
          
          {/* Panel de visualización de logs */}
          <Box sx={{ flexGrow: 1, display: 'flex', border: '1px solid rgba(0, 0, 0, 0.12)', borderRadius: 1, overflow: 'hidden' }}>
            {/* Lista de logs */}
            <Box sx={{ width: '50%', borderRight: '1px solid rgba(0, 0, 0, 0.12)', overflow: 'auto' }}>
              {isLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <CircularProgress size={30} />
                </Box>
              ) : filteredLogs.length > 0 ? (
                <List disablePadding>
                  {filteredLogs.map((log, index) => (
                    <LogEntry 
                      key={index} 
                      log={log} 
                      onSelect={setSelectedLog} 
                      isSelected={selectedLog === log}
                    />
                  ))}
                </List>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <FontAwesomeIcon icon={filter !== 'all' || searchQuery ? faFilter : faCheckCircle} size="2x" style={{ marginBottom: '16px', opacity: 0.5 }} />
                  <Typography variant="body2" color="text.secondary">
                    {filter !== 'all' || searchQuery ? 
                      'No hay logs que coincidan con tus filtros' : 
                      logs.length === 0 ? 
                        'No hay logs disponibles' : 
                        'Selecciona un tipo de log para ver detalles'
                    }
                  </Typography>
                </Box>
              )}
            </Box>
            
            {/* Detalle de log seleccionado */}
            <Box sx={{ width: '50%', p: 2, bgcolor: '#f8f9fa', overflow: 'auto' }}>
              {selectedLog ? (
                <>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      Detalle de Log
                      {selectedLog.type === 'error' && (
                        <Chip
                          label="ERROR"
                          color="error"
                          size="small"
                          sx={{ ml: 1, verticalAlign: 'middle' }}
                        />
                      )}
                      {selectedLog.type === 'warning' && (
                        <Chip
                          label="WARNING"
                          color="warning"
                          size="small"
                          sx={{ ml: 1, verticalAlign: 'middle' }}
                        />
                      )}
                    </Typography>
                    
                    <IconButton
                      size="small"
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(selectedLog, null, 2));
                        setAlertMessage({
                          type: 'success',
                          message: 'Log copiado al portapapeles'
                        });
                      }}
                      title="Copiar al portapapeles"
                    >
                      <FontAwesomeIcon icon={faCopy} />
                    </IconButton>
                  </Box>
                  
                  <Divider sx={{ mb: 2 }} />
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Fecha:</strong> {new Date(selectedLog.timestamp).toLocaleString()}
                  </Typography>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Mensaje:</strong> {selectedLog.message}
                  </Typography>
                  
                  {selectedLog.url && (
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>URL:</strong> {selectedLog.url}
                    </Typography>
                  )}
                  
                  {selectedLog.sessionId && (
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>ID Sesión:</strong> {selectedLog.sessionId}
                    </Typography>
                  )}
                  
                  {selectedLog.details && (
                    <>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mt: 2, mb: 1 }}>
                        Datos Adicionales:
                      </Typography>
                      <Box 
                        component="pre" 
                        sx={{ 
                          bgcolor: 'background.paper', 
                          p: 1.5, 
                          borderRadius: 1, 
                          fontSize: '0.75rem',
                          overflow: 'auto',
                          maxHeight: '300px',
                          border: '1px solid rgba(0,0,0,0.1)'
                        }}
                      >
                        {typeof selectedLog.details === 'string' 
                          ? selectedLog.details 
                          : JSON.stringify(selectedLog.details, null, 2)
                        }
                      </Box>
                    </>
                  )}
                </>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column' }}>
                  <FontAwesomeIcon icon={faClipboard} size="2x" style={{ marginBottom: '16px', opacity: 0.5 }} />
                  <Typography variant="body2" color="text.secondary">
                    Selecciona un log para ver sus detalles
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        </Box>
      )}
      
      {/* Tab de Sistema */}
      {tabValue === 1 && (
        <Box sx={{ p: 2, height: 'calc(100% - 130px)', overflow: 'auto' }}>
          {systemInfo ? 
            <SystemInfoPanel systemInfo={systemInfo} onRefresh={loadSystemInfo} /> : 
            <Box sx={{ display: 'flex', justifyContent: 'center', pt: 4 }}>
              <CircularProgress />
            </Box>
          }
        </Box>
      )}
      
      {/* Modal de diagnóstico completo */}
      <Dialog 
        open={diagnosticModalOpen} 
        onClose={() => setDiagnosticModalOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Diagnóstico completo del sistema
          <IconButton
            aria-label="close"
            onClick={() => setDiagnosticModalOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <FontAwesomeIcon icon={faTimes} />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {diagnosticData ? (
            <Box 
              component="pre" 
              sx={{ 
                fontSize: '0.75rem',
                overflow: 'auto',
                maxHeight: '70vh'
              }}
            >
              {JSON.stringify(diagnosticData, null, 2)}
            </Box>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={handleCopyDiagnostic} 
            startIcon={<FontAwesomeIcon icon={faCopy} />}
          >
            Copiar al portapapeles
          </Button>
          <Button 
            onClick={handleDownloadLogs}
            startIcon={<FontAwesomeIcon icon={faDownload} />}
          >
            Exportar todo
          </Button>
          <Button onClick={() => setDiagnosticModalOpen(false)}>
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Alerta para notificaciones */}
      <Snackbar
        open={!!alertMessage}
        autoHideDuration={5000}
        onClose={() => setAlertMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setAlertMessage(null)} 
          severity={alertMessage?.type || 'info'} 
          sx={{ width: '100%' }}
        >
          {alertMessage?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default LogViewer;