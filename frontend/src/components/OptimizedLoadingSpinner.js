import React from 'react';

const OptimizedLoadingSpinner = ({ size = 'md', text = 'Carregando...' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8', 
    lg: 'w-12 h-12'
  };

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className={`${sizeClasses[size]} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin`}></div>
      {text && <p className="mt-2 text-sm text-gray-500">{text}</p>}
    </div>
  );
};

// Skeleton loading for lists
export const SkeletonLoader = ({ lines = 3, height = 'h-4' }) => (
  <div className="space-y-3 animate-pulse">
    {Array.from({ length: lines }).map((_, i) => (
      <div key={i} className={`bg-gray-200 rounded ${height} w-full`}></div>
    ))}
  </div>
);

// Card skeleton
export const CardSkeleton = () => (
  <div className="animate-pulse">
    <div className="bg-gray-200 rounded-lg p-4 space-y-3">
      <div className="h-4 bg-gray-300 rounded w-3/4"></div>
      <div className="h-3 bg-gray-300 rounded w-1/2"></div>
      <div className="h-6 bg-gray-300 rounded w-full"></div>
    </div>
  </div>
);

export default OptimizedLoadingSpinner;