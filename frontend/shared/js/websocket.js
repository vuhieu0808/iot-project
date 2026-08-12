/**
 * GymTag - WebSocket Realtime Client
 */

import { API_BASE_URL } from './api.js';

export class GymTagWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.statusCallbacks = [];
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 10000;
  }

  getWsUrl() {
    const httpUrl = new URL(API_BASE_URL);
    const wsProtocol = httpUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProtocol}//${httpUrl.host}/ws`;
  }

  connect() {
    const url = this.getWsUrl();
    console.log(`Connecting WebSocket to ${url}...`);
    this.notifyStatus('connecting');

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket Connection Established.');
        this.reconnectAttempts = 0;
        this.notifyStatus('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          this.dispatchEvent(msg.type, msg.data);
        } catch (e) {
          console.error('Error parsing WS message:', e);
        }
      };

      this.ws.onclose = () => {
        this.notifyStatus('disconnected');
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
        this.notifyStatus('error');
      };
    } catch (e) {
      console.error('Failed to instantiate WebSocket:', e);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
    console.log(`Scheduling WS reconnect in ${Math.round(delay)}ms...`);
    setTimeout(() => this.connect(), delay);
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  onStatusChange(callback) {
    this.statusCallbacks.push(callback);
  }

  notifyStatus(status) {
    this.statusCallbacks.forEach(cb => cb(status));
  }

  dispatchEvent(eventType, data) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).forEach(cb => cb(data));
    }
  }
}

export const wsClient = new GymTagWebSocket();
