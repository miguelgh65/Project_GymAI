// src/services/AuthService.js - Fixed version
import axios from 'axios';

class AuthService {
  // Login with Google
  async loginWithGoogle(googleToken) {
    try {
      console.log("AuthService: Sending Google token to backend for verification");
      
      const response = await axios.post('/api/auth/google/verify', {
        id_token: googleToken
      });
      
      console.log("AuthService: Backend response received", response.status);
      
      if (response.data.success && response.data.access_token) {
        console.log("AuthService: Login successful, storing token and user data");
        
        // Store the token in localStorage
        this.storeToken(response.data.access_token);
        
        // Store user data
        if (response.data.user) {
          this.storeUser(response.data.user);
        }
        
        return response.data;
      } else {
        const errorMsg = response.data.message || 'Authentication failed';
        console.error("AuthService: Login failed:", errorMsg);
        throw new Error(errorMsg);
      }
    } catch (error) {
      console.error("AuthService: Login error:", error);
      throw error;
    }
  }

  // Store token with fallbacks
  storeToken(token) {
    if (!token) return false;
    
    try {
      localStorage.setItem('access_token', token);
      console.log("Token stored in localStorage");
      return true;
    } catch (e) {
      console.error("Failed to store token in localStorage:", e);
      
      // Fallback to cookies
      try {
        document.cookie = `access_token=${token}; path=/; max-age=86400`;
        console.log("Token stored in cookies as fallback");
        return true;
      } catch (e2) {
        console.error("Failed to store token in cookies:", e2);
        return false;
      }
    }
  }

  // Store user data with fallbacks
  storeUser(user) {
    if (!user) return false;
    
    try {
      localStorage.setItem('user', JSON.stringify(user));
      console.log("User data stored in localStorage");
      return true;
    } catch (e) {
      console.error("Failed to store user in localStorage:", e);
      
      // Fallback to cookies
      try {
        document.cookie = `user=${JSON.stringify(user)}; path=/; max-age=86400`;
        console.log("User data stored in cookies as fallback");
        return true;
      } catch (e2) {
        console.error("Failed to store user in cookies:", e2);
        return false;
      }
    }
  }

  // Get token with fallbacks
  getToken() {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        return token;
      }
    } catch (e) {
      console.warn("Error accessing localStorage:", e);
    }
    
    // Try from cookies
    try {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('access_token=')) {
          return cookie.substring('access_token='.length);
        }
      }
    } catch (e) {
      console.warn("Error accessing cookies:", e);
    }
    
    return null;
  }

  // Get current user
  getCurrentUser() {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        return JSON.parse(userStr);
      }
    } catch (e) {
      console.warn("Error accessing localStorage for user:", e);
    }
    
    // Try from cookies
    try {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('user=')) {
          const userStr = cookie.substring('user='.length);
          return JSON.parse(userStr);
        }
      }
    } catch (e) {
      console.warn("Error accessing cookies for user:", e);
    }
    
    return null;
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.getToken();
  }

  // Logout
  async logout() {
    console.log("AuthService: Logging out");
    
    // Try to call backend logout (but don't wait for it)
    try {
      axios.get('/api/logout').catch(e => console.warn("Backend logout failed:", e));
    } catch (e) {
      console.warn("Error calling logout endpoint:", e);
    }
    
    // Clear localStorage
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    } catch (e) {
      console.warn("Error clearing localStorage:", e);
    }
    
    // Clear cookies
    try {
      document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      document.cookie = "user=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    } catch (e) {
      console.warn("Error clearing cookies:", e);
    }
    
    return true;
  }
}

// Export as singleton instance
export default new AuthService();