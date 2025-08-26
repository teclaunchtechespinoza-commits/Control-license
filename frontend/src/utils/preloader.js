import axios from 'axios';

// Preload common API endpoints
const commonEndpoints = [
  '/licenses',
  '/sales-dashboard/summary',
  '/my-tenant'
];

class Preloader {
  constructor() {
    this.preloadCache = new Map();
    this.preloadPromises = new Map();
  }

  // Preload data for faster navigation
  async preloadEndpoint(endpoint) {
    if (this.preloadCache.has(endpoint)) {
      return this.preloadCache.get(endpoint);
    }

    if (this.preloadPromises.has(endpoint)) {
      return this.preloadPromises.get(endpoint);
    }

    const promise = this.fetchAndCache(endpoint);
    this.preloadPromises.set(endpoint, promise);
    
    return promise;
  }

  async fetchAndCache(endpoint) {
    try {
      const response = await axios.get(endpoint, { 
        timeout: 5000,
        headers: {
          'Cache-Control': 'max-age=300' // 5 minutes cache
        }
      });
      
      this.preloadCache.set(endpoint, {
        data: response.data,
        timestamp: Date.now()
      });
      
      return response.data;
    } catch (error) {
      console.warn(`Preload failed for ${endpoint}:`, error.message);
      this.preloadPromises.delete(endpoint);
      return null;
    }
  }

  // Get cached data if available
  getCached(endpoint) {
    const cached = this.preloadCache.get(endpoint);
    if (cached && Date.now() - cached.timestamp < 300000) { // 5 minutes
      return cached.data;
    }
    return null;
  }

  // Preload common data on app start
  async preloadCommonData() {
    const promises = commonEndpoints.map(endpoint => 
      this.preloadEndpoint(endpoint).catch(() => null)
    );
    
    await Promise.allSettled(promises);
  }

  // Clear old cache entries
  cleanup() {
    const now = Date.now();
    for (const [key, value] of this.preloadCache.entries()) {
      if (now - value.timestamp > 600000) { // 10 minutes
        this.preloadCache.delete(key);
      }
    }
  }

  // Prefetch data for likely next page
  prefetchForNavigation(currentPath) {
    const prefetchMap = {
      '/dashboard': ['/licenses', '/vendas'],
      '/licenses': ['/dashboard', '/vendas'],
      '/admin': ['/clientes', '/cadastros'],
      '/tenants': ['/tenants/stats']
    };

    const toPrefetch = prefetchMap[currentPath] || [];
    toPrefetch.forEach(endpoint => {
      this.preloadEndpoint(endpoint);
    });
  }
}

// Singleton instance
export const preloader = new Preloader();

// Initialize on app start
export const initializePreloader = () => {
  // Preload common data
  setTimeout(() => {
    preloader.preloadCommonData();
  }, 1000); // Wait 1 second after app load

  // Setup cleanup interval
  setInterval(() => {
    preloader.cleanup();
  }, 300000); // Clean every 5 minutes
};

// Hook for using preloaded data
export const usePreloadedData = (endpoint) => {
  return preloader.getCached(endpoint);
};