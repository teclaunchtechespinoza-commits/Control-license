/**
 * WhatsApp Handler - Core Baileys Integration
 * Gerencia conexão, mensagens e sessão do WhatsApp
 */

const { 
    makeWASocket, 
    useMultiFileAuthState, 
    DisconnectReason,
    isJidBroadcast,
    isJidGroup,
    isJidUser 
} = require('@whiskeysockets/baileys');
const { logger } = require('./utils/logger');
const path = require('path');

class WhatsAppHandler {
    constructor() {
        this.socket = null;
        this.qrCode = null;
        this.connectionStatus = 'disconnected';
        this.userInfo = null;
        this.startTime = new Date();
        this.lastActivity = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    async initialize() {
        try {
            logger.info('📱 Initializing Baileys WhatsApp connection...');
            
            // Setup auth state (session management)
            const authPath = path.join(__dirname, 'auth_info');
            const { state, saveCreds } = await useMultiFileAuthState(authPath);

            // Create WhatsApp socket
            this.socket = makeWASocket({
                auth: state,
                printQRInTerminal: false, // We'll handle QR display ourselves
                browser: [
                    process.env.WHATSAPP_BROWSER_NAME || 'Sales Dashboard Bot',
                    'Chrome',
                    '120.0.0'
                ],
                connectTimeoutMs: 60000,
                defaultQueryTimeoutMs: 60000,
                keepAliveIntervalMs: 10000,
                logger: this.createBaileysLogger()
            });

            // Setup event listeners
            this.setupEventListeners(saveCreds);

            logger.info('✅ Baileys WhatsApp handler initialized');
            return true;

        } catch (error) {
            logger.error('❌ Failed to initialize WhatsApp handler:', error);
            throw error;
        }
    }

    setupEventListeners(saveCreds) {
        if (!this.socket) return;

        // Connection updates (QR, connected, disconnected)
        this.socket.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                this.qrCode = qr;
                this.connectionStatus = 'qr_generated';
                logger.info('📱 QR Code generated - scan with WhatsApp');
            }

            if (connection === 'close') {
                const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
                
                this.connectionStatus = 'disconnected';
                this.userInfo = null;
                
                logger.warn(`Connection closed due to ${lastDisconnect?.error?.output?.statusCode || 'unknown'}, reconnecting: ${shouldReconnect}`);

                if (shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const delay = Math.min(this.reconnectAttempts * 5000, 30000); // Max 30s delay
                    
                    logger.info(`⏳ Reconnecting in ${delay/1000}s... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    
                    setTimeout(() => {
                        this.initialize();
                    }, delay);
                } else {
                    logger.error('❌ Max reconnection attempts reached or logged out');
                    this.connectionStatus = 'failed';
                }

            } else if (connection === 'open') {
                this.connectionStatus = 'connected';
                this.qrCode = null;
                this.reconnectAttempts = 0;
                this.userInfo = this.socket.user;
                this.lastActivity = new Date();

                logger.info(`✅ WhatsApp connected successfully! User: ${this.userInfo?.name || this.userInfo?.id}`);
            }
        });

        // Save credentials when updated
        this.socket.ev.on('creds.update', saveCreds);

        // Handle incoming messages (for future bidirectional communication)
        this.socket.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type === 'notify') {
                for (const message of messages) {
                    if (!message.key.fromMe && message.message) {
                        await this.handleIncomingMessage(message);
                    }
                }
            }
        });

        // Handle message status updates (sent, delivered, read)
        this.socket.ev.on('messages.update', (updates) => {
            for (const update of updates) {
                if (update.update.status) {
                    logger.debug(`📋 Message ${update.key.id} status: ${update.update.status}`);
                }
            }
        });
    }

    async handleIncomingMessage(message) {
        try {
            const phoneNumber = message.key.remoteJid?.replace('@s.whatsapp.net', '');
            const messageText = message.message.conversation || 
                             message.message.extendedTextMessage?.text || 
                             '[Media/Unsupported message]';

            this.lastActivity = new Date();

            logger.info(`📨 Received message from ${phoneNumber}: ${messageText.substring(0, 100)}...`);

            // Here we could forward to FastAPI for processing
            // For now, we'll just log it
            
        } catch (error) {
            logger.error('Error handling incoming message:', error);
        }
    }

    async sendMessage(phoneNumber, text, options = {}) {
        try {
            if (!this.socket || this.connectionStatus !== 'connected') {
                throw new Error('WhatsApp is not connected');
            }

            // Format phone number for WhatsApp
            const jid = this.formatPhoneNumber(phoneNumber);

            logger.info(`📤 Sending message to ${phoneNumber} (${jid})`);

            // Send message
            const sentMessage = await this.socket.sendMessage(jid, { text });

            this.lastActivity = new Date();

            return {
                success: true,
                message_id: sentMessage.key.id,
                phone_number: phoneNumber,
                jid: jid,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            logger.error(`Error sending message to ${phoneNumber}:`, error);
            
            return {
                success: false,
                error: error.message,
                phone_number: phoneNumber,
                timestamp: new Date().toISOString()
            };
        }
    }

    formatPhoneNumber(phone) {
        // Remove all non-numeric characters
        let cleanPhone = phone.replace(/\D/g, '');
        
        // Add country code if missing
        if (cleanPhone.length === 11 && cleanPhone.startsWith('11')) {
            cleanPhone = '55' + cleanPhone; // Brazil
        } else if (cleanPhone.length === 10) {
            cleanPhone = '5511' + cleanPhone; // Brazil with 11 area code
        } else if (!cleanPhone.startsWith('55') && cleanPhone.length > 10) {
            cleanPhone = '55' + cleanPhone;
        }

        // Return in WhatsApp format
        return cleanPhone + '@s.whatsapp.net';
    }

    // Public API methods
    isConnected() {
        return this.connectionStatus === 'connected' && this.socket?.user;
    }

    getConnectionStatus() {
        return this.connectionStatus;
    }

    getQRCode() {
        return this.qrCode;
    }

    getUserInfo() {
        return this.userInfo;
    }

    getUptime() {
        if (this.connectionStatus !== 'connected') return null;
        return Math.floor((new Date() - this.startTime) / 1000);
    }

    getLastActivity() {
        return this.lastActivity;
    }

    async disconnect() {
        if (this.socket) {
            await this.socket.logout();
            this.socket = null;
        }
        this.connectionStatus = 'disconnected';
        this.userInfo = null;
        this.qrCode = null;
    }
}

// Factory function to create WhatsApp connection
async function createWhatsAppConnection() {
    const handler = new WhatsAppHandler();
    await handler.initialize();
    return handler;
}

module.exports = {
    WhatsAppHandler,
    createWhatsAppConnection
};