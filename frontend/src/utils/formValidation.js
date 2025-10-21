/**
 * 📝 Enhanced Form Validation Utilities
 * 
 * Provides consistent form validation with Portuguese error messages
 * and integration with enhanced error handling system
 */

import { toast } from 'sonner';

// Field validation rules
export const validationRules = {
  required: (value, fieldName) => {
    if (!value || (typeof value === 'string' && value.trim() === '')) {
      return `${fieldName} é obrigatório`;
    }
    return null;
  },

  email: (value, fieldName = 'Email') => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (value && !emailRegex.test(value)) {
      return `${fieldName} deve ter um formato válido`;
    }
    return null;
  },

  minLength: (minLength) => (value, fieldName) => {
    if (value && value.length < minLength) {
      return `${fieldName} deve ter pelo menos ${minLength} caracteres`;
    }
    return null;
  },

  maxLength: (maxLength) => (value, fieldName) => {
    if (value && value.length > maxLength) {
      return `${fieldName} deve ter no máximo ${maxLength} caracteres`;
    }
    return null;
  },

  phone: (value, fieldName = 'Telefone') => {
    const phoneRegex = /^[\d\s\(\)\-\+]+$/;
    if (value && !phoneRegex.test(value)) {
      return `${fieldName} deve conter apenas números e símbolos válidos`;
    }
    return null;
  },

  cpf: (value, fieldName = 'CPF') => {
    if (value) {
      const cleanCpf = value.replace(/\D/g, '');
      if (cleanCpf.length !== 11) {
        return `${fieldName} deve ter 11 dígitos`;
      }
      // Basic CPF validation (could be enhanced)
      if (!/^\d{11}$/.test(cleanCpf)) {
        return `${fieldName} deve conter apenas números`;
      }
    }
    return null;
  },

  cnpj: (value, fieldName = 'CNPJ') => {
    if (value) {
      const cleanCnpj = value.replace(/\D/g, '');
      if (cleanCnpj.length !== 14) {
        return `${fieldName} deve ter 14 dígitos`;
      }
    }
    return null;
  },

  strongPassword: (value, fieldName = 'Senha') => {
    if (value) {
      const hasUpperCase = /[A-Z]/.test(value);
      const hasLowerCase = /[a-z]/.test(value);
      const hasNumbers = /\d/.test(value);
      const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(value);
      const isLongEnough = value.length >= 8;

      if (!isLongEnough) {
        return `${fieldName} deve ter pelo menos 8 caracteres`;
      }
      if (!hasUpperCase) {
        return `${fieldName} deve conter pelo menos uma letra maiúscula`;
      }
      if (!hasLowerCase) {
        return `${fieldName} deve conter pelo menos uma letra minúscula`;
      }
      if (!hasNumbers) {
        return `${fieldName} deve conter pelo menos um número`;
      }
      if (!hasSpecialChar) {
        return `${fieldName} deve conter pelo menos um caractere especial`;
      }
    }
    return null;
  }
};

// Field definitions with Portuguese names
export const fieldNames = {
  // User fields
  name: 'Nome da Empresa',  // Contexto de empresa
  email: 'Email',
  password: 'Senha',
  confirmPassword: 'Confirmação de Senha',
  phone: 'Telefone',
  
  // Company fields
  companyName: 'Nome da Empresa',
  fantasyName: 'Nome Fantasia', 
  cnpj: 'CNPJ',
  socialReason: 'Razão Social',
  
  // Address fields
  address: 'Endereço',
  city: 'Cidade',
  state: 'Estado',
  zipCode: 'CEP',
  country: 'País',
  neighborhood: 'Bairro',
  
  // Client fields (PF)
  cpf: 'CPF',
  rg: 'RG',
  birthDate: 'Data de Nascimento',
  
  // License fields
  licenseName: 'Nome da Licença',
  licenseType: 'Tipo de Licença',
  expirationDate: 'Data de Expiração',
  value: 'Valor',
  
  // General fields
  description: 'Descrição',
  observations: 'Observações',
  status: 'Status',
  category: 'Categoria',
  plan: 'Plano',
  size: 'Porte'
};

/**
 * Validate a single field with multiple rules
 * @param {*} value - Field value
 * @param {string} fieldKey - Field key for getting display name
 * @param {Array} rules - Array of validation rules
 * @returns {string|null} Error message or null if valid
 */
export function validateField(value, fieldKey, rules = []) {
  const fieldName = fieldNames[fieldKey] || fieldKey;
  
  for (const rule of rules) {
    const error = rule(value, fieldName);
    if (error) {
      return error;
    }
  }
  
  return null;
}

/**
 * Validate entire form object
 * @param {Object} formData - Form data object
 * @param {Object} validationSchema - Validation schema
 * @returns {Object} { isValid, errors }
 */
export function validateForm(formData, validationSchema) {
  const errors = {};
  let isValid = true;
  
  Object.keys(validationSchema).forEach(fieldKey => {
    const rules = validationSchema[fieldKey];
    const value = formData[fieldKey];
    
    const error = validateField(value, fieldKey, rules);
    if (error) {
      errors[fieldKey] = error;
      isValid = false;
    }
  });
  
  return { isValid, errors };
}

/**
 * Show enhanced validation error toast with field details
 * @param {Object} errors - Validation errors object
 */
export function showValidationErrors(errors) {
  const errorCount = Object.keys(errors).length;
  if (errorCount === 0) return;
  
  const errorList = Object.entries(errors).map(([field, message]) => {
    const fieldName = fieldNames[field] || field;
    return `• ${fieldName}: ${message}`;
  });
  
  const mainMessage = `${errorCount} campo${errorCount > 1 ? 's' : ''} ${errorCount > 1 ? 'precisam' : 'precisa'} de correção:`;
  
  toast.error('Erro de validação', {
    description: (
      <div>
        <div className="font-medium mb-2">{mainMessage}</div>
        <div className="text-sm space-y-1">
          {errorList.map((error, index) => (
            <div key={index}>{error}</div>
          ))}
        </div>
      </div>
    ),
    duration: 6000
  });
}

/**
 * React hook for form validation
 * @param {Object} validationSchema - Validation schema
 * @returns {Object} Validation utilities
 */
export function useFormValidation(validationSchema) {
  const [errors, setErrors] = React.useState({});
  
  const validateSingleField = (fieldKey, value) => {
    const rules = validationSchema[fieldKey] || [];
    const error = validateField(value, fieldKey, rules);
    
    setErrors(prev => ({
      ...prev,
      [fieldKey]: error
    }));
    
    return !error;
  };
  
  const validateAllFields = (formData) => {
    const { isValid, errors: validationErrors } = validateForm(formData, validationSchema);
    setErrors(validationErrors);
    
    if (!isValid) {
      showValidationErrors(validationErrors);
    }
    
    return isValid;
  };
  
  const clearErrors = () => {
    setErrors({});
  };
  
  const clearFieldError = (fieldKey) => {
    setErrors(prev => ({
      ...prev,
      [fieldKey]: null
    }));
  };
  
  return {
    errors,
    validateSingleField,
    validateAllFields,
    clearErrors,
    clearFieldError,
    hasErrors: Object.keys(errors).some(key => errors[key])
  };
}

// Common validation schemas
export const schemas = {
  // User registration/profile
  user: {
    name: [validationRules.required, validationRules.minLength(2)],
    email: [validationRules.required, validationRules.email],
    password: [validationRules.required, validationRules.strongPassword],
    phone: [validationRules.phone]
  },
  
  // Login form
  login: {
    email: [validationRules.required, validationRules.email],
    password: [validationRules.required]
  },
  
  // Company form
  company: {
    companyName: [validationRules.required, validationRules.minLength(2)],
    cnpj: [validationRules.cnpj],
    city: [validationRules.required],
    state: [validationRules.required],
    country: [validationRules.required]
  },
  
  // Client PF form
  clientPF: {
    name: [validationRules.required, validationRules.minLength(2)],
    cpf: [validationRules.required, validationRules.cpf],
    email: [validationRules.email],
    phone: [validationRules.phone]
  },
  
  // Client PJ form  
  clientPJ: {
    companyName: [validationRules.required, validationRules.minLength(2)],
    cnpj: [validationRules.required, validationRules.cnpj],
    email: [validationRules.email],
    phone: [validationRules.phone]
  },
  
  // License form
  license: {
    licenseName: [validationRules.required, validationRules.minLength(2)],
    expirationDate: [validationRules.required],
    value: [validationRules.required]
  }
};

/**
 * Enhanced API error handler for forms
 * @param {Error} error - API error
 * @param {Function} setFieldErrors - Function to set field-specific errors
 */
export function handleApiFormError(error, setFieldErrors) {
  const errorData = error.response?.data;
  
  if (errorData?.error_code === 'VALIDATION_ERROR' && errorData.errors) {
    // Convert API field errors to form errors
    const fieldErrors = {};
    
    errorData.errors.forEach(err => {
      const fieldKey = err.field;
      fieldErrors[fieldKey] = err.message;
    });
    
    if (setFieldErrors) {
      setFieldErrors(fieldErrors);
    }
    
    // Show summary toast
    const errorCount = errorData.errors.length;
    toast.error('Erro de validação', {
      description: `${errorCount} campo${errorCount > 1 ? 's' : ''} ${errorCount > 1 ? 'precisam' : 'precisa'} de correção`,
      duration: 4000
    });
    
  } else {
    // Generic error - already handled by api.js interceptor
    console.log('Generic API error handled by interceptor');
  }
}

// Export React hook if React is available
let React;
try {
  React = require('react');
} catch (e) {
  // React not available, hook won't work but other functions will
}

export default {
  validationRules,
  fieldNames,
  validateField,
  validateForm,
  showValidationErrors,
  useFormValidation,
  schemas,
  handleApiFormError
};