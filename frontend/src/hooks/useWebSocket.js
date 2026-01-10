import { useEffect, useRef, useState, useCallback } from 'react';

const useWebSocket = (url, options = {}) => {
    const [lastMessage, setLastMessage] = useState(null);
    const [readyState, setReadyState] = useState(0);
    const ws = useRef(null);
    const reconnectTimeout = useRef(null);
    const shouldReconnect = useRef(true);

    const { onOpen, onClose, onError, reconnectInterval = 3000 } = options;

    const connect = useCallback(() => {
        try {
            ws.current = new WebSocket(url);

            ws.current.onopen = (event) => {
                console.log('WebSocket connected');
                setReadyState(1);
                if (onOpen) onOpen(event);

                if (reconnectTimeout.current) {
                    clearTimeout(reconnectTimeout.current);
                    reconnectTimeout.current = null;
                }
            };

            ws.current.onmessage = (event) => {
                setLastMessage(event.data);
            };

            ws.current.onerror = (event) => {
                console.error('WebSocket error:', event);
                if (onError) onError(event);
            };

            ws.current.onclose = (event) => {
                console.log('WebSocket closed');
                setReadyState(3);
                if (onClose) onClose(event);

                if (shouldReconnect.current) {
                    console.log(`Reconnecting in ${reconnectInterval}ms...`);
                    reconnectTimeout.current = setTimeout(() => {
                        connect();
                    }, reconnectInterval);
                }
            };
        } catch (error) {
            console.error('WebSocket connection error:', error);
        }
    }, [url, onOpen, onClose, onError, reconnectInterval]);

    useEffect(() => {
        connect();

        return () => {
            shouldReconnect.current = false;
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
            }
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [connect]);

    const sendMessage = useCallback((data) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket is not connected');
        }
    }, []);

    const sendCommand = useCallback((command) => {
        sendMessage({
            type: 'command',
            command: command
        });
    }, [sendMessage]);

    return {
        sendMessage,
        sendCommand,
        lastMessage,
        readyState
    };
};

export default useWebSocket;