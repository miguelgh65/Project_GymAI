// src/components/Dashboard/SessionsTable.js
import React from 'react';
import { Card, CardContent, Typography, Box, Divider } from '@mui/material';

function SessionsTable({ sessionData = [] }) { // Valor por defecto []

  const formatDate = (dateString) => {
     if (!dateString) return 'N/A';
     try {
       return new Date(dateString).toLocaleDateString('es-ES', {
         day: '2-digit',
         month: '2-digit',
         year: 'numeric'
       });
     } catch (e) {
       return dateString; // Devolver original si falla
     }
  }

  return (
    <Card className="table-container" elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom>Sesiones Recientes</Typography>
        <Divider sx={{ mb: 2 }} />
        <Box className="table-responsive">
          <table id="sessions-table" className="sessions-table">
            <thead>
              <tr>
                <th>Fecha</th>
                {/* <th>Series Detalle</th> // Quitado si no se envían las series */}
                <th>Peso Máx.</th>
                <th>Reps Totales</th>
                <th>Volumen</th>
              </tr>
            </thead>
            <tbody>
              {sessionData.length > 0 ? (
                // Mostrar solo las últimas 10 o menos si hay pocas
                sessionData.slice(-10).reverse().map((session, index) => (
                  <tr key={index}>
                    <td>{formatDate(session.fecha)}</td>
                    {/*
                    // Descomentar si decides enviar las series desde el backend
                    <td>
                      {session.series && Array.isArray(session.series)
                        ? session.series.map(s => `${s.repeticiones}x${s.peso}kg`).join(' ')
                        : 'N/A'}
                    </td>
                    */}
                    <td>{session.max_peso ?? 0} kg</td>
                    <td>{session.total_reps ?? 0}</td>
                    <td>{session.volumen ?? 0} kg</td>
                  </tr>
                ))
              ) : (
                <tr className="empty-state">
                  <td colSpan="4"> {/* Ajustar colSpan si cambias columnas */}
                     Selecciona un ejercicio y aplica filtros para ver sus datos.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Box>
      </CardContent>
    </Card>
  );
}

export default SessionsTable;