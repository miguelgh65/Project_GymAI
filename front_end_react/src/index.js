// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
// <<< 1. Importar BrowserRouter >>>
import { BrowserRouter } from 'react-router-dom';

import './index.css';
import App from './App';

// --- Font Awesome imports (sin cambios) ---
import { library } from '@fortawesome/fontawesome-svg-core';
import { fab } from '@fortawesome/free-brands-svg-icons';
import { fas } from '@fortawesome/free-solid-svg-icons';
import '@fortawesome/fontawesome-free/css/all.min.css';
library.add(fab, fas);
// --- Fin Font Awesome ---

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    {/* <<< 2. Envolver App con BrowserRouter >>> */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);