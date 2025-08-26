import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// Simple in-memory cache
const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export const useApiCache = (url, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const cancelTokenRef = useRef();

  useEffect(() => {
    const fetchData = async () => {
      // Check cache first
      const cacheKey = url;
      const cachedData = cache.get(cacheKey);
      
      if (cachedData && Date.now() - cachedData.timestamp < CACHE_DURATION) {
        setData(cachedData.data);
        setLoading(false);
        return;
      }

      // Cancel previous request if exists
      if (cancelTokenRef.current) {
        cancelTokenRef.current.cancel('Request canceled due to new request');
      }

      // Create new cancel token
      cancelTokenRef.current = axios.CancelToken.source();

      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(url, {
          cancelToken: cancelTokenRef.current.token,
          timeout: 10000 // 10 second timeout
        });

        // Cache the result
        cache.set(cacheKey, {
          data: response.data,
          timestamp: Date.now()
        });

        setData(response.data);
      } catch (err) {
        if (!axios.isCancel(err)) {
          console.error(`API Error for ${url}:`, err);
          setError(err.response?.data?.detail || err.message || 'Erro na requisição');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Cleanup function
    return () => {
      if (cancelTokenRef.current) {
        cancelTokenRef.current.cancel('Component unmounted');
      }
    };
  }, [url, ...dependencies]);

  return { data, loading, error };
};

// Hook for multiple API calls with batching
export const useApiBatch = (urls) => {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    const fetchBatch = async () => {
      setLoading(true);
      const results = {};
      const errorResults = {};

      // Execute all requests in parallel but with limit
      const promises = urls.map(async ({ key, url }) => {
        try {
          // Check cache first
          const cachedData = cache.get(url);
          if (cachedData && Date.now() - cachedData.timestamp < CACHE_DURATION) {
            results[key] = cachedData.data;
            return;
          }

          const response = await axios.get(url, { timeout: 8000 });
          
          // Cache result
          cache.set(url, {
            data: response.data,
            timestamp: Date.now()
          });
          
          results[key] = response.data;
        } catch (error) {
          console.error(`Batch API Error for ${key}:`, error);
          errorResults[key] = error.response?.data?.detail || error.message;
          results[key] = null; // Set to null instead of undefined
        }
      });

      await Promise.allSettled(promises);
      
      setData(results);
      setErrors(errorResults);
      setLoading(false);
    };

    if (urls.length > 0) {
      fetchBatch();
    }
  }, [urls]);

  return { data, loading, errors };
};

// Clear cache utility
export const clearApiCache = (pattern) => {
  if (pattern) {
    for (const key of cache.keys()) {
      if (key.includes(pattern)) {
        cache.delete(key);
      }
    }
  } else {
    cache.clear();
  }
};