import React from 'react';
import { Loader2, Shield } from 'lucide-react';

const LoadingSpinner = ({ message = 'Carregando...' }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
          <Shield className="w-8 h-8 text-white" />
        </div>
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          {message}
        </h2>
        <p className="text-gray-500">
          Aguarde um momento...
        </p>
      </div>
    </div>
  );
};

export default LoadingSpinner;