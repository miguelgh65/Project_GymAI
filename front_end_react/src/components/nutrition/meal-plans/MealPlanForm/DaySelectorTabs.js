// src/components/nutrition/meal-plans/MealPlanForm/DaySelectorTabs.js
import React from 'react';
import { Tabs, Tab, Paper } from '@mui/material';

const DaySelectorTabs = ({ days, activeTab, onChange }) => {
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Tabs
        value={activeTab}
        onChange={(event, newValue) => onChange(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
      >
        {days.map((day, index) => (
          <Tab key={index} label={day} />
        ))}
      </Tabs>
    </Paper>
  );
};

export default DaySelectorTabs;