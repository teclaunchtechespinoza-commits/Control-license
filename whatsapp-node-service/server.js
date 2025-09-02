/**
 * WhatsApp Integration Service
 * Integração completa com Baileys para Sales Dashboard
 * Arquitetura: Express + Baileys + Redis + FastAPI Integration
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { createWhatsAppConnection } = require('./whatsapp-handler');
const { logger } = require('./utils/logger');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
    credentials: true
}));
app.use(express.json());

// Global WhatsApp connection instance
let whatsappInstance = null;

// Initialize WhatsApp connection
async function initializeWhatsApp() {
    try {
        logger.info('🚀 Initializing WhatsApp Service...');
        whatsappInstance = await createWhatsAppConnection();
        logger.info('✅ WhatsApp Service initialized successfully');
    } catch (error) {
        logger.error('❌ Failed to initialize WhatsApp Service:', error);
        // Retry after 10 seconds
        setTimeout(initializeWhatsApp, 10000);
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy',
        service: 'WhatsApp Integration Service',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        whatsapp_connected: whatsappInstance?.isConnected() || false
    });
});

// Get QR Code for WhatsApp connection
app.get('/qr', async (req, res) => {
    try {
        if (!whatsappInstance) {
            return res.status(503).json({ 
                error: 'WhatsApp service not initialized',
                qr: null 
            });
        }

        const qrCode = await whatsappInstance.getQRCode();
        res.json({ 
            qr: qrCode,
            status: whatsappInstance.getConnectionStatus()
        });
    } catch (error) {
        logger.error('Error getting QR code:', error);
        res.status(500).json({ 
            error: error.message,
            qr: null 
        });
    }
});

// Get connection status
app.get('/status', (req, res) => {
    try {
        if (!whatsappInstance) {
            return res.json({
                connected: false,
                status: 'service_not_initialized',
                user: null,
                uptime: null
            });
        }

        const status = whatsappInstance.getConnectionStatus();
        const userInfo = whatsappInstance.getUserInfo();
        
        res.json({
            connected: whatsappInstance.isConnected(),
            status: status,
            user: userInfo,
            uptime: whatsappInstance.getUptime(),
            last_activity: whatsappInstance.getLastActivity()
        });
    } catch (error) {
        logger.error('Error getting status:', error);
        res.status(500).json({ 
            connected: false,
            error: error.message 
        });
    }
});

// Send WhatsApp message
app.post('/send', async (req, res) => {
    try {
        const { phone_number, message, message_id, context } = req.body;

        // Validation
        if (!phone_number || !message) {
            return res.status(400).json({ 
                success: false,
                error: 'phone_number and message are required' 
            });
        }

        if (!whatsappInstance || !whatsappInstance.isConnected()) {
            return res.status(503).json({ 
                success: false,
                error: 'WhatsApp is not connected' 
            });
        }

        logger.info(`📤 Sending message to ${phone_number}: ${message.substring(0, 50)}...`);

        const result = await whatsappInstance.sendMessage(phone_number, message, {
            message_id,
            context
        });

        if (result.success) {
            logger.info(`✅ Message sent successfully to ${phone_number}`);
            
            // Notify FastAPI about successful send (optional)
            try {
                await notifyFastAPI('message_sent', {
                    phone_number,
                    message_id: result.message_id,
                    status: 'sent',
                    timestamp: new Date().toISOString()
                });
            } catch (notifyError) {
                logger.warn('Failed to notify FastAPI:', notifyError);
            }
        }

        res.json(result);

    } catch (error) {
        logger.error('Error sending message:', error);
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

// Bulk send messages
app.post('/send-bulk', async (req, res) => {
    try {
        const { messages } = req.body;

        if (!Array.isArray(messages) || messages.length === 0) {
            return res.status(400).json({ 
                success: false,
                error: 'messages array is required' 
            });
        }

        if (!whatsappInstance || !whatsappInstance.isConnected()) {
            return res.status(503).json({ 
                success: false,
                error: 'WhatsApp is not connected' 
            });
        }

        logger.info(`📤 Sending bulk messages: ${messages.length} messages`);

        const results = [];
        
        for (const msg of messages) {
            try {
                const result = await whatsappInstance.sendMessage(
                    msg.phone_number, 
                    msg.message,
                    { message_id: msg.message_id, context: msg.context }
                );
                
                results.push({
                    phone_number: msg.phone_number,
                    ...result
                });

                // Delay between messages to avoid spam detection
                if (messages.length > 1) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }

            } catch (msgError) {
                logger.error(`Error sending to ${msg.phone_number}:`, msgError);
                results.push({
                    phone_number: msg.phone_number,
                    success: false,
                    error: msgError.message
                });
            }
        }

        const successCount = results.filter(r => r.success).length;
        const failCount = results.length - successCount;

        logger.info(`✅ Bulk send completed: ${successCount} sent, ${failCount} failed`);

        res.json({
            success: true,
            total: results.length,
            sent: successCount,
            failed: failCount,
            results
        });

    } catch (error) {
        logger.error('Error in bulk send:', error);
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

// Restart connection
app.post('/restart', async (req, res) => {
    try {
        logger.info('🔄 Restarting WhatsApp connection...');
        
        if (whatsappInstance) {
            await whatsappInstance.disconnect();
        }
        
        whatsappInstance = await createWhatsAppConnection();
        
        logger.info('✅ WhatsApp connection restarted successfully');
        res.json({ 
            success: true,
            message: 'WhatsApp connection restarted' 
        });
    } catch (error) {
        logger.error('Error restarting connection:', error);
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

// Helper function to notify FastAPI
async function notifyFastAPI(event, data) {
    const axios = require('axios');
    const fastApiUrl = process.env.FASTAPI_URL || 'http://localhost:8001';
    
    try {
        await axios.post(`${fastApiUrl}/api/whatsapp/webhook`, {
            event,
            data,
            timestamp: new Date().toISOString()
        }, {
            timeout: 5000
        });
    } catch (error) {
        logger.debug(`FastAPI notification failed for ${event}:`, error.message);
    }
}

// Error handling middleware
app.use((error, req, res, next) => {
    logger.error('Express error:', error);
    res.status(500).json({ 
        success: false,
        error: 'Internal server error' 
    });
});

// Graceful shutdown
process.on('SIGINT', async () => {
    logger.info('🛑 Shutting down WhatsApp Service...');
    
    if (whatsappInstance) {
        await whatsappInstance.disconnect();
    }
    
    logger.info('✅ WhatsApp Service shut down gracefully');
    process.exit(0);
});

// Start server
app.listen(PORT, () => {
    logger.info(`🚀 WhatsApp Service started on port ${PORT}`);
    logger.info(`📱 Health check: http://localhost:${PORT}/health`);
    
    // Initialize WhatsApp connection after server starts
    initializeWhatsApp();
});

// Opcional: adicionar também uma checagem por IP allowlist aqui, se desejar.
// Ou validar assinatura HMAC no corpo para garantir integridade de payload.

module.exports = { app };