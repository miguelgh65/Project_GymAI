import React from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios'; // Import axios here
import './index.css'; // Or your main CSS file
import App from './App';
import { BrowserRouter } from 'react-router-dom';

// *** SET AXIOS DEFAULTS GLOBALLY HERE ***
axios.defaults.withCredentials = true;

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);