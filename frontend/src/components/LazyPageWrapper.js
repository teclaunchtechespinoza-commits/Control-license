import React, { Suspense } from 'react';
import OptimizedLoadingSpinner from './OptimizedLoadingSpinner';

// Higher-order component for lazy loading pages
export const withLazyLoading = (Component, fallback = null) => {
  return React.forwardRef((props, ref) => (
    <Suspense fallback={fallback || <OptimizedLoadingSpinner text="Carregando página..." />}>
      <Component {...props} ref={ref} />
    </Suspense>
  ));
};

// Page wrapper with error boundary
class PageErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Page Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-64 space-y-4">
          <div className="text-red-600 text-lg font-semibold">
            Ops! Algo deu errado
          </div>
          <div className="text-gray-600 text-center max-w-md">
            {this.state.error?.message || 'Erro inesperado ao carregar a página'}
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Recarregar Página
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Optimized page wrapper
export const LazyPageWrapper = ({ children, title }) => {
  React.useEffect(() => {
    if (title) {
      document.title = `${title} - License Manager`;
    }
  }, [title]);

  return (
    <PageErrorBoundary>
      <div className="min-h-screen bg-gray-50 p-6">
        {children}
      </div>
    </PageErrorBoundary>
  );
};

export default LazyPageWrapper;