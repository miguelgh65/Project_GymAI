// src/components/profile/ConnectedAccounts.js
import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Button,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  Chip,
  Alert,
  CircularProgress,
  Link
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faGoogle, faTelegram } from '@fortawesome/free-brands-svg-icons';
import { faLink, faCircleNodes, faCheckCircle, faCopy } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';
// CORRECCIÓN: Importar desde src/services (ruta relativa correcta)
import AuthService from '../../services/AuthService';

const ConnectedAccounts = ({ user, onUpdate }) => {
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [linkCode, setLinkCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const generateTelegramCode = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await axios.post('/api/generate-link-code');
      if (response.data.success && response.data.code) {
        setLinkCode(response.data.code);
        setLinkDialogOpen(true);
      } else {
        setError('Error generando código de enlace. Por favor intenta de nuevo.');
      }
    } catch (error) {
      console.error('Error generando código de Telegram:', error);
      setError('Error generando código de enlace. Por favor intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseDialog = () => {
    setLinkDialogOpen(false);
    // After closing dialog, refresh user data to show newly connected accounts
    if (onUpdate) onUpdate();
  };

  const copyCodeToClipboard = () => {
    if (!linkCode) return;
    navigator.clipboard.writeText(linkCode).then(() => {
      setSuccess('Código copiado al portapapeles');
      setTimeout(() => setSuccess(null), 3000);
    }).catch(err => {
      console.error('Error al copiar:', err);
      setError('No se pudo copiar el código');
      setTimeout(() => setError(null), 3000);
    });
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FontAwesomeIcon 
            icon={faCircleNodes} 
            style={{ color: '#00B0B9', marginRight: '10px', fontSize: '1.5rem' }} 
          />
          <Typography variant="h6">Cuentas Conectadas</Typography>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Google Account */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <FontAwesomeIcon 
                icon={faGoogle} 
                style={{ color: '#DB4437', marginRight: '10px', fontSize: '1.2rem' }} 
              />
              <Box>
                <Typography variant="body1">Google Account</Typography>
                <Typography variant="body2" color="textSecondary">
                  {user?.email || 'No email available'}
                </Typography>
              </Box>
            </Box>
            
            <Chip 
              label={user?.has_google ? "Conectado" : "No Conectado"}
              color={user?.has_google ? "success" : "default"}
              variant={user?.has_google ? "filled" : "outlined"}
              size="small"
            />
          </Box>
          
          {/* Telegram Account */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <FontAwesomeIcon 
                icon={faTelegram} 
                style={{ color: '#0088cc', marginRight: '10px', fontSize: '1.2rem' }} 
              />
              <Box>
                <Typography variant="body1">Telegram Bot</Typography>
                <Typography variant="body2" color="textSecondary">
                  Para seguimiento móvil de ejercicios
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {user?.has_telegram ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography component="span" sx={{ color: 'success.main', fontWeight: 'bold', mr: 2, display: 'flex', alignItems: 'center' }}>
                    <FontAwesomeIcon icon={faCheckCircle} style={{marginRight: 4}}/> Conectado
                  </Typography>
                  <Link href="https://t.me/RoonieColemAi_dev_bot" target="_blank" rel="noopener noreferrer" sx={{ fontSize: '0.875rem' }}>
                    Abrir Bot
                  </Link>
                </Box>
              ) : (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<FontAwesomeIcon icon={faLink} />}
                  onClick={generateTelegramCode}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={20} /> : 'Conectar'}
                </Button>
              )}
            </Box>
          </Box>
        </Box>
        
        {/* Link Dialog */}
        <Dialog open={linkDialogOpen} onClose={handleCloseDialog}>
          <DialogTitle>Conectar Bot de Telegram</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Envía este código a nuestro bot de Telegram para conectar tu cuenta:
            </DialogContentText>
            <TextField
              autoFocus
              margin="dense"
              fullWidth
              variant="outlined"
              value={linkCode}
              InputProps={{
                readOnly: true,
                style: { fontWeight: 'bold', fontSize: '1.5rem', textAlign: 'center' }
              }}
            />
            <DialogContentText sx={{ mt: 2 }}>
              1. Abre Telegram y busca <b>@RoonieColemAi_dev_bot</b><br />
              2. Inicia un chat con el bot<br />
              3. Envía el comando <b>/vincular {linkCode}</b><br />
              4. Recibirás una confirmación cuando estés conectado
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={copyCodeToClipboard} color="primary">
              Copiar Código
            </Button>
            <Button onClick={handleCloseDialog}>Cerrar</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default ConnectedAccounts;