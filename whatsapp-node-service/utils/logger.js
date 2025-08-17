/**
 * Logging utility for WhatsApp Service
 * Winston-based logger with file and console output
 */

const winston = require('winston');
const path = require('path');

// Log levels
const logLevels = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3
};

// Custom format for console output
const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'HH:mm:ss' }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
    return `${timestamp} ${level}: ${message} ${metaStr}`;
  })
);

// Custom format for file output
const fileFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.json()
);

// Create logger instance
const logger = winston.createLogger({
  levels: logLevels,
  level: process.env.LOG_LEVEL || 'info',
  defaultMeta: { service: 'whatsapp-service' },
  transports: [
    // Console output
    new winston.transports.Console({
      format: consoleFormat,
      handleExceptions: true
    }),
    
    // File output - errors
    new winston.transports.File({
      filename: path.join(__dirname, '../logs/error.log'),
      level: 'error',
      format: fileFormat,
      maxsize: 5242880, // 5MB
      maxFiles: 5,
      handleExceptions: true
    }),
    
    // File output - combined
    new winston.transports.File({
      filename: path.join(__dirname, '../logs/combined.log'),
      format: fileFormat,
      maxsize: 5242880, // 5MB
      maxFiles: 5
    })
  ],
  exitOnError: false
});

// Create logs directory if it doesn't exist
const fs = require('fs');
const logsDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Helper function for structured logging
const logWithContext = (level, message, context = {}) => {
  logger.log(level, message, {
    timestamp: new Date().toISOString(),
    pid: process.pid,
    ...context
  });
};

// Export configured logger and helpers
module.exports = {
  logger,
  logWithContext,
  
  // Convenience methods
  info: (message, context) => logWithContext('info', message, context),
  error: (message, context) => logWithContext('error', message, context),
  warn: (message, context) => logWithContext('warn', message, context),
  debug: (message, context) => logWithContext('debug', message, context)
};