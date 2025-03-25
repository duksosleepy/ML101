from __future__ import annotations

import uuid
from typing import Any, cast

import reflex as rx
from jinja2 import Environment


# Component to handle intersection observation (from paste-3.txt)
class IntersectionObserverEntry(rx.Base):
    """An entry for the IntersectionObserver."""

    intersection_ratio: float
    is_intersecting: bool
    time: float


def _intersect_event_signature(
    data: rx.Var[IntersectionObserverEntry],
) -> tuple[rx.Var[IntersectionObserverEntry]]:
    return (data,)


class IntersectionObserver(rx.el.Div):
    """A component that observes intersection with the viewport."""

    root: rx.Var[str]
    root_margin: rx.Var[str] = rx.Var.create("0px")
    threshold: rx.Var[float] = rx.Var.create(1.0)

    on_intersect: rx.EventHandler[_intersect_event_signature]
    on_non_intersect: rx.EventHandler[_intersect_event_signature]

    @classmethod
    def create(cls, *children, **props):
        if "id" not in props:
            props["id"] = rx.vars.get_unique_variable_name()
        return super().create(*children, **props)

    def _exclude_props(self) -> list[str]:
        return [
            "root",
            "root_margin",
            "threshold",
            "on_intersect",
            "on_non_intersect",
        ]

    def add_imports(self) -> rx.ImportDict | list[rx.ImportDict]:
        return {
            "react": [
                rx.ImportVar(tag="useEffect"),
                rx.ImportVar(tag="useState"),
            ],
        }

    def add_custom_code(self) -> list[str]:
        return [
            """
const extractEntry = (entry) => ({
    intersection_ratio: entry.intersectionRatio,
    is_intersecting: entry.isIntersecting,
    time: entry.time,
})"""
        ]

    def add_hooks(self) -> list[str | rx.Var]:
        on_intersect = self.event_triggers.get("on_intersect")
        on_non_intersect = self.event_triggers.get("on_non_intersect")
        if on_intersect is None and on_non_intersect is None:
            return []
        on_intersect = (
            rx.Var.create(on_intersect) if on_intersect is not None else "undefined"
        )
        on_non_intersect = (
            rx.Var.create(on_non_intersect)
            if on_non_intersect is not None
            else "undefined"
        )
        return [
            Environment()
            .from_string("""
// IntersectionObserver
const [enableObserver_{{ ref }}, setEnableObserver_{{ ref }}] = useState(1)
useEffect(() => {
    if (!{{ root }} || !{{ ref }}.current) {
        // The root/target element is not found, so trigger the effect again, later.
        if (!{{ root }}) {
          console.log("Warning: observation root " + {{ root }} + " not found, will try again.")
        }
        if (!{{ ref }}.current) {
          console.log("Warning: observation target element not found, will try again.")
        }
        const timeout = setTimeout(
            () => setEnableObserver_{{ ref }}((cnt) => cnt + 1),
            enableObserver_{{ ref }} * 100,
        )
        return () => clearTimeout(timeout)
    }
    const on_intersect = {{ on_intersect }}
    const on_non_intersect = {{ on_non_intersect }}
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (on_intersect !== undefined && entry.isIntersecting) {
                on_intersect(extractEntry(entry))
            }
            if (on_non_intersect !== undefined && !entry.isIntersecting) {
                on_non_intersect(extractEntry(entry))
            }
        });
    }, {
        root: {{ root }},
        rootMargin: {{ root_margin }},
        threshold: {{ threshold }},
    })
    if ({{ ref }}.current) {
        observer.observe({{ ref }}.current)
        return () => observer.disconnect()
    }
}, [ enableObserver_{{ ref }}, {{ ref }} ]);
""")
            .render(
                on_intersect=on_intersect,
                on_non_intersect=on_non_intersect,
                root=(
                    f"document.querySelector({self.root!s})"
                    if self.root is not None
                    else "document"
                ),
                root_margin=self.root_margin,
                threshold=self.threshold,
                ref=self.get_ref(),
            )
        ]


intersection_observer = IntersectionObserver.create


# Configuration class for AudioVisualizer
class AudioVisualizerConfig(rx.Base):
    """Configuration for the audio visualizer."""

    enabled: bool = True
    fftSize: int = 1024
    smoothingTimeConstant: float = 0.8
    minDecibels: float = -90
    maxDecibels: float = -10
    barColor: str = "#06b6d4"  # cyan-500
    barCount: int = 60
    barWidth: int = 2
    barSpacing: int = 1
    refreshRate: int = 30  # ms


# Media device information class
class MediaDeviceInfo(rx.Base):
    """Information about a media device."""

    kind: str
    label: str
    deviceId: str
    groupId: str


# WebSocket connection state constants
CONNECTION_STATES = {
    "CONNECTING": "connecting",
    "CONNECTED": "connected",
    "DISCONNECTED": "disconnected",
    "RECONNECTING": "reconnecting",
    "ERROR": "error",
    "CLOSED": "closed",
}


# Audio visualizer component
class AudioVisualizer(rx.Component):
    """A component for visualizing audio levels."""

    # Component properties
    stream: rx.Var[str]
    config: rx.Var[AudioVisualizerConfig] = rx.Var.create(AudioVisualizerConfig())

    @classmethod
    def create(cls, *children, **props) -> AudioVisualizer:
        """Create a new AudioVisualizer component."""
        props.setdefault("id", rx.vars.get_unique_variable_name())
        return cast(AudioVisualizer, super().create(*children, **props))

    def render(self) -> dict:
        return {
            "tag": "canvas",
            "width": 300,
            "height": 80,
        }

    def add_imports(self) -> rx.ImportDict:
        return {
            "react": [
                "useEffect",
                "useRef",
            ]
        }

    def add_hooks(self) -> list[str | rx.Var]:
        return [
            Environment()
            .from_string("""
// Audio Visualizer
const canvasRef = {{ ref }};
const animationRef = useRef(null);
const analyserRef = useRef(null);
const audioContextRef = useRef(null);
const streamSourceRef = useRef(null);

// Setup and draw the visualizer
useEffect(() => {
    const stream = {{ stream }};
    const config = {{ config }};

    if (!stream || !config.enabled || !canvasRef.current) {
        return;
    }

    // Set up audio context and analyzer
    const setupAnalyser = () => {
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }

        // If we already have a source, disconnect it
        if (streamSourceRef.current) {
            streamSourceRef.current.disconnect();
        }

        // Create analyzer node
        if (!analyserRef.current) {
            analyserRef.current = audioContextRef.current.createAnalyser();
            analyserRef.current.fftSize = config.fftSize;
            analyserRef.current.smoothingTimeConstant = config.smoothingTimeConstant;
            analyserRef.current.minDecibels = config.minDecibels;
            analyserRef.current.maxDecibels = config.maxDecibels;
        }

        // Connect stream to analyzer
        streamSourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
        streamSourceRef.current.connect(analyserRef.current);
    };

    // Draw visualization
    const draw = () => {
        if (!canvasRef.current || !analyserRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Get frequency data
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);

        // Calculate bar width and spacing
        const barCount = Math.min(config.barCount, bufferLength);
        const barWidth = config.barWidth;
        const barSpacing = config.barSpacing;
        const totalBarWidth = barWidth + barSpacing;

        // Center the bars in the canvas
        const startX = (width - (barCount * totalBarWidth)) / 2;

        // Draw bars
        ctx.fillStyle = config.barColor;
        for (let i = 0; i < barCount; i++) {
            // Use a logarithmic scale to sample frequency data (more emphasis on lower frequencies)
            const dataIndex = Math.floor(Math.pow(i / barCount, 2) * bufferLength);
            const value = dataArray[dataIndex];

            // Calculate bar height as a percentage of canvas height
            const barHeight = (value / 255) * height;

            // Position bar at the bottom of the canvas
            const x = startX + (i * totalBarWidth);
            const y = height - barHeight;

            ctx.fillRect(x, y, barWidth, barHeight);
        }

        // Request next frame
        animationRef.current = requestAnimationFrame(draw);
    };

    // Initialize and start visualization
    try {
        setupAnalyser();
        draw();

        // Set up refresh interval
        const refreshInterval = setInterval(() => {
            // Cancel any pending animation frame
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }

            // Request a new frame
            animationRef.current = requestAnimationFrame(draw);
        }, config.refreshRate);

        // Clean up
        return () => {
            clearInterval(refreshInterval);
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    } catch (error) {
        console.error('Error setting up audio visualizer:', error);
    }
}, [{{ stream }}, {{ config }}]);
""")
            .render(
                ref="useRef(null)",
                stream=self.stream,
                config=self.config,
            )
        ]


# WebRTC audio recorder component
class WebRTCAudioRecorder(rx.Component):
    """A component for recording and streaming audio via WebRTC and WebSockets."""

    # Component properties
    # Base configuration
    base_url: rx.Var[str] = rx.Var.create("localhost")
    secure: rx.Var[bool] = rx.Var.create(False)
    endpoint_path: rx.Var[str] = rx.Var.create("/audio/{id}/stream")

    # Audio settings
    buffer_size: rx.Var[int] = rx.Var.create(4096)
    sample_rate: rx.Var[int] = rx.Var.create(16000)
    channels: rx.Var[int] = rx.Var.create(1)
    device_id: rx.Var[str]
    session_id: rx.Var[str]

    # Connection settings
    reconnect_attempts: rx.Var[int] = rx.Var.create(5)
    reconnect_interval: rx.Var[int] = rx.Var.create(2000)
    ping_interval: rx.Var[int] = rx.Var.create(30000)

    # Event handlers
    on_connection_state_change: rx.EventHandler
    on_error: rx.EventHandler
    on_data_received: rx.EventHandler

    @classmethod
    def create(cls, *children, **props) -> WebRTCAudioRecorder:
        """Create a new WebRTCAudioRecorder component."""
        props.setdefault("id", rx.vars.get_unique_variable_name())
        return cast(WebRTCAudioRecorder, super().create(*children, **props))

    def render(self) -> dict:
        return {}

    def add_imports(self) -> rx.ImportDict:
        return {
            "react": [
                "useCallback",
                "useEffect",
                "useState",
                "useRef",
            ]
        }

    def add_custom_code(self) -> list[str]:
        return [
            """
// Helper to build WebSocket URL
const buildWebSocketUrl = (baseUrl, secure, path, sessionId) => {
    const protocol = secure ? 'wss' : 'ws';
    const formattedPath = path.replace('{id}', sessionId);
    return `${protocol}://${baseUrl}${formattedPath}`;
};

// Helper to create a WebSocket with reconnection logic
const createReconnectingWebSocket = (url, options = {}) => {
    const {
        onOpen,
        onClose,
        onError,
        onMessage,
        onReconnecting,
        onMaxAttemptsReached,
        reconnectAttempts = 5,
        reconnectInterval = 2000,
        maxReconnectInterval = 30000,
        reconnectDecay = 1.5,
    } = options;

    let ws = null;
    let reconnectCount = 0;
    let reconnectTimeout = null;
    let forceClosed = false;

    // Calculate backoff time
    const getBackoffTime = () => {
        return Math.min(
            reconnectInterval * Math.pow(reconnectDecay, reconnectCount),
            maxReconnectInterval
        );
    };

    // Connect WebSocket
    const connect = () => {
        // Clear any existing timeout
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }

        // Create new WebSocket
        ws = new WebSocket(url);

        // Setup event handlers
        ws.onopen = (event) => {
            reconnectCount = 0;
            if (onOpen) onOpen(event);
        };

        ws.onclose = (event) => {
            if (onClose) onClose(event);

            // If not forcefully closed, attempt reconnection
            if (!forceClosed && reconnectCount < reconnectAttempts) {
                reconnectCount++;
                if (onReconnecting) onReconnecting(reconnectCount, getBackoffTime());

                reconnectTimeout = setTimeout(() => {
                    connect();
                }, getBackoffTime());
            } else if (!forceClosed && reconnectCount >= reconnectAttempts) {
                if (onMaxAttemptsReached) onMaxAttemptsReached();
            }
        };

        ws.onerror = (error) => {
            if (onError) onError(error);
        };

        ws.onmessage = (event) => {
            if (onMessage) onMessage(event);
        };
    };

    // Start connection
    connect();

    // Return interface
    return {
        // Send data
        send: (data) => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(data);
                return true;
            }
            return false;
        },

        // Close connection
        close: () => {
            forceClosed = true;
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
                reconnectTimeout = null;
            }
            if (ws) {
                ws.close();
            }
        },

        // Get WebSocket instance
        getWebSocket: () => ws,

        // Check if connection is open
        isConnected: () => ws && ws.readyState === WebSocket.OPEN,

        // Get connection state
        getState: () => {
            if (!ws) return 'disconnected';
            switch(ws.readyState) {
                case WebSocket.CONNECTING: return 'connecting';
                case WebSocket.OPEN: return 'connected';
                case WebSocket.CLOSING: return 'closing';
                case WebSocket.CLOSED: return 'closed';
                default: return 'unknown';
            }
        },
    };
};

// Helper for audio processing
const createAudioProcessor = (stream, options = {}) => {
    const {
        audioContext,
        bufferSize = 4096,
        sampleRate = 16000,
        channels = 1,
        onAudioProcess,
        onError,
    } = options;

    let context = audioContext;
    let source = null;
    let processor = null;
    let analyser = null;
    let active = false;

    // Initialize audio processing
    const init = () => {
        try {
            // Create audio context if not provided
            if (!context) {
                context = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: sampleRate || 44100,
                });
            }

            // Create source from stream
            source = context.createMediaStreamSource(stream);

            // Create analyser for visualization
            analyser = context.createAnalyser();
            analyser.fftSize = 2048;
            analyser.smoothingTimeConstant = 0.8;

            // Connect source to analyser
            source.connect(analyser);

            // Determine processing method based on browser support
            if (context.audioWorklet) {
                // Modern approach with Audio Worklet
                setupAudioWorklet();
            } else {
                // Fallback with ScriptProcessor
                setupScriptProcessor();
            }

            active = true;
            return true;
        } catch (error) {
            if (onError) onError(`Error initializing audio processor: ${error.message}`);
            return false;
        }
    };

    // Set up Audio Worklet
    const setupAudioWorklet = async () => {
        try {
            // Create worklet processor code
            const workletCode = `
                class AudioStreamProcessor extends AudioWorkletProcessor {
                    constructor() {
                        super();
                        this.bufferSize = ${bufferSize};
                        this.buffer = new Float32Array(this.bufferSize);
                        this.bufferIndex = 0;
                        this.sampleRate = ${sampleRate};
                        this.resample = sampleRate !== ${context.sampleRate};
                        this.channels = ${channels};
                    }

                    process(inputs, outputs, parameters) {
                        const input = inputs[0][0];
                        if (!input) return true;

                        // Resample if needed (simple downsampling by skipping samples)
                        if (this.resample) {
                            const ratio = ${context.sampleRate} / this.sampleRate;
                            for (let i = 0; i < input.length; i += ratio) {
                                const index = Math.floor(i);
                                if (index < input.length) {
                                    this.buffer[this.bufferIndex++] = input[index];

                                    // If buffer is full, send it
                                    if (this.bufferIndex >= this.bufferSize) {
                                        this.port.postMessage({
                                            audioData: this.buffer.slice(0),
                                            sampleRate: this.sampleRate,
                                            channels: this.channels
                                        });
                                        this.bufferIndex = 0;
                                    }
                                }
                            }
                        } else {
                            // No resampling needed
                            for (let i = 0; i < input.length; i++) {
                                this.buffer[this.bufferIndex++] = input[i];

                                // If buffer is full, send it
                                if (this.bufferIndex >= this.bufferSize) {
                                    this.port.postMessage({
                                        audioData: this.buffer.slice(0),
                                        sampleRate: this.sampleRate,
                                        channels: this.channels
                                    });
                                    this.bufferIndex = 0;
                                }
                            }
                        }
                        return true;
                    }
                }

                registerProcessor('audio-stream-processor', AudioStreamProcessor);
            `;

            // Create a Blob and URL for the worklet code
            const blob = new Blob([workletCode], { type: 'application/javascript' });
            const workletUrl = URL.createObjectURL(blob);

            // Load the worklet
            await context.audioWorklet.addModule(workletUrl);

            // Create worklet node
            processor = new AudioWorkletNode(context, 'audio-stream-processor');

            // Handle messages from worklet
            processor.port.onmessage = (e) => {
                if (onAudioProcess && active) {
                    onAudioProcess(e.data);
                }
            };

            // Connect nodes
            source.connect(processor);
            processor.connect(context.destination);

            // Clean up URL
            URL.revokeObjectURL(workletUrl);
        } catch (error) {
            if (onError) onError(`Error setting up AudioWorklet: ${error.message}`);
            // Fall back to ScriptProcessor
            setupScriptProcessor();
        }
    };

    // Set up ScriptProcessor (fallback)
    const setupScriptProcessor = () => {
        try {
            // Create script processor
            processor = context.createScriptProcessor(bufferSize, channels, channels);

            // Handle audio processing
            processor.onaudioprocess = (event) => {
                if (onAudioProcess && active) {
                    const inputBuffer = event.inputBuffer;
                    const channelData = new Float32Array(bufferSize);

                    // Get data from first channel
                    inputBuffer.copyFromChannel(channelData, 0);

                    onAudioProcess({
                        audioData: channelData,
                        sampleRate: context.sampleRate,
                        channels: channels
                    });
                }
            };

            // Connect nodes
            source.connect(processor);
            processor.connect(context.destination);
        } catch (error) {
            if (onError) onError(`Error setting up ScriptProcessor: ${error.message}`);
        }
    };

    // Initialize
    const success = init();

    // Return interface
    return {
        // Check if processor is active
        isActive: () => active,

        // Stop processing
        stop: () => {
            active = false;

            // Disconnect nodes
            if (processor) {
                if (source) source.disconnect(processor);
                processor.disconnect();
            }

            if (source && analyser) {
                source.disconnect(analyser);
            }

            // Close context if created internally
            if (context && !audioContext) {
                context.close();
            }

            // Clear references
            processor = null;
            source = null;
            if (!audioContext) context = null;
        },

        // Get audio context
        getAudioContext: () => context,

        // Get analyser node
        getAnalyser: () => analyser,

        // Get media stream
        getStream: () => stream,

        // Success state
        success,
    };
};
"""
        ]

    def add_hooks(self) -> list[str | rx.Var]:
        on_connection_state_change = self.event_triggers.get(
            "on_connection_state_change"
        )
        if isinstance(on_connection_state_change, rx.EventChain):
            on_connection_state_change = rx.Var.create(on_connection_state_change)

        on_error = self.event_triggers.get("on_error")
        if isinstance(on_error, rx.EventChain):
            on_error = rx.Var.create(on_error)
        if on_error is None:
            on_error = "console.error"

        on_data_received = self.event_triggers.get("on_data_received")
        if isinstance(on_data_received, rx.EventChain):
            on_data_received = rx.Var.create(on_data_received)

        # WebRTC and WebSocket implementation
        return [
            Environment()
            .from_string("""
// WebRTC Audio Recorder
const [recordingState, setRecordingState] = useState('inactive');
const [connectionState, setConnectionState] = useState('disconnected');
const [mediaDevices, setMediaDevices] = useState([]);
const [error, setError] = useState(null);
const [stats, setStats] = useState({
    bytesTransferred: 0,
    packetsTransferred: 0,
    avgLatency: 0,
    connectionUptime: 0,
    reconnectAttempts: 0,
});

// Store values in refs for external access
refs['recorder_state_{{ ref }}'] = recordingState;
refs['connection_state_{{ ref }}'] = connectionState;
refs['mediadevices_{{ ref }}'] = mediaDevices;
refs['stats_{{ ref }}'] = stats;
refs['error_{{ ref }}'] = error;

// References
const socketRef = useRef(null);
const mediaStreamRef = useRef(null);
const audioProcessorRef = useRef(null);
const audioContextRef = useRef(null);
const startTimeRef = useRef(null);
const statsIntervalRef = useRef(null);
const pingIntervalRef = useRef(null);
const streamRef = useRef(null);
const latencyMeasurementsRef = useRef([]);

// Function to enumerate media devices
const updateMediaDevices = () => {
    if (!navigator.mediaDevices?.enumerateDevices) {
        const errorMsg = "enumerateDevices() not supported on your browser!";
        setError(errorMsg);
        {{ on_error }}(errorMsg);
    } else {
        navigator.mediaDevices
            .enumerateDevices()
            .then((devices) => {
                const audioInputs = devices.filter(
                    (device) => device.deviceId && device.kind === "audioinput"
                );
                setMediaDevices(audioInputs);
            })
            .catch((err) => {
                const errorMsg = `${err.name}: ${err.message}`;
                setError(errorMsg);
                {{ on_error }}(errorMsg);
            });
    }
};

// Function to update connection state
const updateConnectionState = (state) => {
    setConnectionState(state);
    {{ on_connection_state_change }}(state);
};

// Function to update error state
const handleError = (errorMsg) => {
    setError(errorMsg);
    {{ on_error }}(errorMsg);
};

// Function to start WebSocket connection
const startWebSocket = () => {
    const sessionId = {{ session_id }} || crypto.randomUUID();
    const wsUrl = buildWebSocketUrl(
        {{ base_url }},
        {{ secure }},
        {{ endpoint_path }},
        sessionId
    );

    console.log(`Connecting to WebSocket: ${wsUrl}`);
    updateConnectionState('connecting');

    try {
        // If there's an existing socket, close it
        if (socketRef.current) {
            socketRef.current.close();
        }

        // Create new reconnecting WebSocket
        socketRef.current = createReconnectingWebSocket(wsUrl, {
            onOpen: () => {
                console.log('WebSocket connected');
                updateConnectionState('connected');
                startTimeRef.current = Date.now();

                // Start ping interval to keep connection alive
                if (pingIntervalRef.current) {
                    clearInterval(pingIntervalRef.current);
                }

                pingIntervalRef.current = setInterval(() => {
                    if (socketRef.current && socketRef.current.isConnected()) {
                        // Send ping message
                        socketRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
                    }
                }, {{ ping_interval }});

                // Start stats interval
                if (statsIntervalRef.current) {
                    clearInterval(statsIntervalRef.current);
                }

                statsIntervalRef.current = setInterval(() => {
                    if (startTimeRef.current) {
                        const uptime = Math.floor((Date.now() - startTimeRef.current) / 1000);

                        // Calculate average latency
                        let avgLatency = 0;
                        if (latencyMeasurementsRef.current.length > 0) {
                            avgLatency = latencyMeasurementsRef.current.reduce((a, b) => a + b, 0) /
                                latencyMeasurementsRef.current.length;
                        }

                        setStats(prevStats => ({
                            ...prevStats,
                            connectionUptime: uptime,
                            avgLatency: Math.round(avgLatency),
                        }));
                    }
                }, 1000);
            },

            onClose: () => {
                console.log('WebSocket closed');
                updateConnectionState('disconnected');

                // Clear intervals
                if (pingIntervalRef.current) {
                    clearInterval(pingIntervalRef.current);
                    pingIntervalRef.current = null;
                }

                if (statsIntervalRef.current) {
                    clearInterval(statsIntervalRef.current);
                    statsIntervalRef.current = null;
                }
            },

            onError: (error) => {
                console.error('WebSocket error:', error);
                handleError(`WebSocket error: ${error}`);
                updateConnectionState('error');
            },

            onMessage: (event) => {
                try {
                    const data = JSON.parse(event.data);

                    // Handle ping response (pong)
                    if (data.type === 'pong') {
                        const latency = Date.now() - data.timestamp;
                        latencyMeasurementsRef.current.push(latency);

                        // Keep only the last 10 measurements
                        if (latencyMeasurementsRef.current.length > 10) {
                            latencyMeasurementsRef.current.shift();
                        }
                    }
                    // Handle transcript data
                    else if (data.type === 'transcript') {
                        if ({{ on_data_received }}) {
                            {{ on_data_received }}(data);
                        }
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            },

            onReconnecting: (attempt, delay) => {
                console.log(`WebSocket reconnecting (attempt ${attempt}, delay ${delay}ms)`);
                updateConnectionState('reconnecting');

                setStats(prevStats => ({
                    ...prevStats,
                    reconnectAttempts: attempt,
                }));
            },

            onMaxAttemptsReached: () => {
                console.error('WebSocket max reconnect attempts reached');
                updateConnectionState('error');
                handleError('Maximum reconnection attempts reached');
            },

            reconnectAttempts: {{ reconnect_attempts }},
            reconnectInterval: {{ reconnect_interval }},
        });

        return true;
    } catch (error) {
        handleError(`Failed to create WebSocket: ${error.message}`);
        return false;
    }
};

// Function to get user media (microphone)
const getUserMedia = async (deviceId) => {
    const constraints = {
        audio: deviceId ? { deviceId: { exact: deviceId } } : true,
    };

    try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);

        // Update device list after permission is granted
        if (mediaDevices.length === 0) {
            updateMediaDevices();
        }

        // Store stream
        mediaStreamRef.current = stream;
        streamRef.current = stream;

        return stream;
    } catch (error) {
        handleError(`Error accessing microphone: ${error.message}`);
        throw error;
    }
};

// Function to start audio streaming
const createAudioStreamer = (stream) => {
    try {
        // Create audio processor
        audioProcessorRef.current = createAudioProcessor(stream, {
            audioContext: audioContextRef.current,
            bufferSize: {{ buffer_size }},
            sampleRate: {{ sample_rate }},
            channels: {{ channels }},

            onAudioProcess: (data) => {
                if (
                    socketRef.current &&
                    socketRef.current.isConnected() &&
                    recordingState === 'recording'
                ) {
                    // Convert Float32Array to Buffer
                    const buffer = data.audioData.buffer;

                    // Send audio data to server
                    const success = socketRef.current.send(buffer);

                    if (success) {
                        // Update stats
                        setStats(prevStats => ({
                            ...prevStats,
                            bytesTransferred: prevStats.bytesTransferred + buffer.byteLength,
                            packetsTransferred: prevStats.packetsTransferred + 1,
                        }));
                    }
                }
            },

            onError: (errorMsg) => {
                handleError(errorMsg);
            }
        });

        // Store audio context
        if (audioProcessorRef.current.success) {
            audioContextRef.current = audioProcessorRef.current.getAudioContext();
            return true;
        }

        return false;
    } catch (error) {
        handleError(`Error setting up audio streaming: ${error.message}`);
        return false;
    }
};

// Function to start recording
refs['start_recording_{{ ref }}'] = useCallback(async () => {
    if (recordingState === 'recording') {
        console.log("Already recording");
        return false;
    }

    try {
        // Reset stats
        setStats({
            bytesTransferred: 0,
            packetsTransferred: 0,
            avgLatency: 0,
            connectionUptime: 0,
            reconnectAttempts: 0,
        });

        // Reset error
        setError(null);

        // Start WebSocket
        const socketStarted = startWebSocket();
        if (!socketStarted) {
            return false;
        }

        // Get user media
        const stream = await getUserMedia({{ device_id }});

        // Create audio streamer
        const streamerStarted = createAudioStreamer(stream);
        if (!streamerStarted) {
            // Clean up if streamer failed
            if (socketRef.current) {
                socketRef.current.close();
            }

            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach(track => track.stop());
                mediaStreamRef.current = null;
            }

            return false;
        }

        // Update recording state
        setRecordingState('recording');
        return true;
    } catch (error) {
        console.error('Error starting recording:', error);
        handleError(`Error starting recording: ${error.message}`);
        return false;
    }
}, [recordingState, {{ device_id }}]);

// Function to stop recording
refs['stop_recording_{{ ref }}'] = useCallback(() => {
    // Update recording state
    setRecordingState('inactive');

    // Stop audio processor
    if (audioProcessorRef.current) {
        audioProcessorRef.current.stop();
        audioProcessorRef.current = null;
    }

    // Stop media tracks
    if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
        streamRef.current = null;
    }

    // Close WebSocket
    if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
    }

    // Clear intervals
    if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
    }

    if (statsIntervalRef.current) {
        clearInterval(statsIntervalRef.current);
        statsIntervalRef.current = null;
    }

    // Reset refs
    startTimeRef.current = null;
    latencyMeasurementsRef.current = [];

    return true;
}, []);

// Function to get audio stream for visualizer
refs['get_stream_{{ ref }}'] = useCallback(() => {
    return streamRef.current;
}, []);

// Clean up on component unmount
useEffect(() => {
    return () => {
        if (recordingState === 'recording') {
            refs['stop_recording_{{ ref }}']();
        }
    };
}, []);

// Enumerate devices on mount
useEffect(() => {
    updateMediaDevices();
}, []);
""")
            .render(
                ref=self.get_ref(),
                on_connection_state_change=on_connection_state_change
                if on_connection_state_change is not None
                else "console.log",
                on_error=on_error,
                on_data_received=on_data_received
                if on_data_received is not None
                else "undefined",
                base_url=self.base_url,
                secure=self.secure,
                endpoint_path=self.endpoint_path,
                buffer_size=self.buffer_size,
                sample_rate=self.sample_rate,
                channels=self.channels,
                device_id=str(self.device_id)
                if self.device_id is not None
                else "undefined",
                session_id=str(self.session_id)
                if self.session_id is not None
                else "undefined",
                reconnect_attempts=self.reconnect_attempts,
                reconnect_interval=self.reconnect_interval,
                ping_interval=self.ping_interval,
            )
        ]

    def start(self):
        """Start recording audio."""
        return rx.call_script(f"refs['start_recording_{self.get_ref()}']()")

    def stop(self):
        """Stop recording audio."""
        return rx.call_script(f"refs['stop_recording_{self.get_ref()}']()")

    def get_stream(self):
        """Get the current audio stream for visualization."""
        return rx.call_script(f"refs['get_stream_{self.get_ref()}']()")

    @property
    def is_recording(self) -> rx.Var[bool]:
        """Whether recording is in progress."""
        return rx.Var(
            f"(refs['recorder_state_{self.get_ref()}'] === 'recording')",
            _var_type=bool,
        )

    @property
    def recorder_state(self) -> rx.Var[str]:
        """Current state of the recorder."""
        return rx.Var(
            f"(refs['recorder_state_{self.get_ref()}'])",
            _var_type=str,
        )

    @property
    def connection_state(self) -> rx.Var[str]:
        """Current state of the WebSocket connection."""
        return rx.Var(
            f"(refs['connection_state_{self.get_ref()}'])",
            _var_type=str,
        )

    @property
    def media_devices(self) -> rx.Var[list[MediaDeviceInfo]]:
        """Available media devices."""
        return rx.Var(
            f"(refs['mediadevices_{self.get_ref()}'])",
            _var_type=list[MediaDeviceInfo],
        )

    @property
    def stats(self) -> rx.Var[dict[str, Any]]:
        """Streaming statistics."""
        return rx.Var(
            f"(refs['stats_{self.get_ref()}'])",
            _var_type=dict[str, Any],
        )

    @property
    def error(self) -> rx.Var[str]:
        """Current error message, if any."""
        return rx.Var(
            f"(refs['error_{self.get_ref()}'])",
            _var_type=str,
        )


class State(rx.State):
    """The app state."""

    has_error: bool = False
    connection_state: str = "disconnected"
    error_message: str = ""
    buffer_size: int = 4096
    sample_rate: int = 16000
    device_id: str = ""
    session_id: str = ""
    transcript: list[str] = []
    server_url: str = "localhost"
    secure_connection: bool = False
    show_stats: bool = False
    visualizer_config: AudioVisualizerConfig = AudioVisualizerConfig()

    def __init__(self):
        super().__init__()
        # Generate a session ID when the state is initialized
        self.session_id = str(uuid.uuid4())

    @rx.event
    def on_connection_state_change(self, state: str):
        """Handle connection state changes."""
        self.connection_state = state
        if state == "error":
            self.has_error = True

    @rx.event
    def on_error(self, error_msg: str):
        """Handle errors."""
        self.has_error = True
        self.error_message = error_msg
        print(f"Error: {error_msg}")

    @rx.event
    def on_data_received(self, data: dict[str, Any]):
        """Handle data received from the server."""
        if data.get("type") == "transcript" and "text" in data:
            self.transcript.append(data["text"])

    @rx.event
    def set_buffer_size(self, value: list[int | float]):
        """Set the buffer size for audio recording."""
        self.buffer_size = int(value[0])
        # Stop recording when buffer size changes
        return recorder.stop()

    @rx.event
    def set_sample_rate(self, value: list[int | float]):
        """Set the sample rate for audio recording."""
        self.sample_rate = int(value[0])
        # Stop recording when sample rate changes
        return recorder.stop()

    @rx.event
    def set_device_id(self, value: str):
        """Set the device ID for audio recording."""
        self.device_id = value
        # Stop recording when device changes
        return recorder.stop()

    @rx.event
    def set_server_url(self, value: str):
        """Set the server URL."""
        self.server_url = value
        # Stop recording when server URL changes
        return recorder.stop()

    @rx.event
    def toggle_secure_connection(self):
        """Toggle secure connection (ws/wss)."""
        self.secure_connection = not self.secure_connection
        # Stop recording when secure connection changes
        return recorder.stop()

    @rx.event
    def toggle_stats(self):
        """Toggle showing stats."""
        self.show_stats = not self.show_stats

    @rx.event
    def toggle_visualizer(self):
        """Toggle audio visualizer."""
        self.visualizer_config.enabled = not self.visualizer_config.enabled

    @rx.event
    def generate_new_session(self):
        """Generate a new session ID."""
        self.session_id = str(uuid.uuid4())
        return recorder.stop()

    @rx.event
    def set_transcript(self, value: list[str]):
        """Set the transcript."""
        self.transcript = value

    @rx.event
    def on_load(self):
        """Handle page load."""
        # We can autoconnect when the page loads
        # return recorder.start()
        # Or leave it to user to start manually


# Create the audio recorder instance
recorder = WebRTCAudioRecorder.create(
    on_connection_state_change=State.on_connection_state_change,
    on_error=State.on_error,
    on_data_received=State.on_data_received,
    buffer_size=State.buffer_size,
    sample_rate=State.sample_rate,
    device_id=State.device_id,
    session_id=State.session_id,
    base_url=State.server_url,
    secure=State.secure_connection,
)


def connection_status_badge() -> rx.Component:
    """Create a connection status badge."""
    return rx.flex(
        rx.cond(
            State.connection_state == "connected",
            rx.badge("Connected", color_scheme="green"),
            rx.cond(
                State.connection_state == "connecting",
                rx.badge("Connecting", color_scheme="yellow"),
                rx.cond(
                    State.connection_state == "reconnecting",
                    rx.badge("Reconnecting", color_scheme="orange"),
                    rx.cond(
                        State.connection_state == "error",
                        rx.badge("Error", color_scheme="red"),
                        rx.badge("Disconnected", color_scheme="gray"),
                    ),
                ),
            ),
        ),
        rx.cond(
            recorder.is_recording,
            rx.badge("Recording", color_scheme="red"),
        ),
        gap="2",
    )


def input_device_select() -> rx.Component:
    """Create a device selection dropdown."""
    return rx.select.root(
        rx.select.trigger(placeholder="Select Input Device"),
        rx.select.content(
            rx.foreach(
                recorder.media_devices,
                lambda device: rx.cond(
                    device.deviceId & device.kind == "audioinput",
                    rx.select.item(
                        device.label or f"Device {device.deviceId}",
                        value=device.deviceId,
                    ),
                ),
            ),
        ),
        on_change=State.set_device_id,
    )


def transcript() -> rx.Component:
    """Create a transcript display area."""
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(State.transcript, lambda text: rx.text(text, width="100%")),
            intersection_observer(
                height="1px",
                id="end-of-transcript",
                root="#scroller",
                on_non_intersect=lambda _: rx.scroll_to("end-of-transcript"),
                visibility="hidden",
            ),
        ),
        id="scroller",
        width="100%",
        height="50vh",
    )


def stats_display() -> rx.Component:
    """Create a stats display."""
    return rx.cond(
        State.show_stats,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("Connection Statistics", font_weight="bold"),
                    rx.spacer(),
                    rx.icon_button(
                        "x",
                        on_click=State.toggle_stats,
                        size="xs",
                    ),
                    width="100%",
                ),
                rx.divider(),
                rx.grid(
                    rx.grid_item(
                        rx.stat(
                            rx.stat_number(
                                f"{recorder.stats.bytesTransferred / 1024:.1f} KB"
                            ),
                            rx.stat_help_text("Data Transferred"),
                        ),
                        col_span=1,
                    ),
                    rx.grid_item(
                        rx.stat(
                            rx.stat_number(f"{recorder.stats.packetsTransferred}"),
                            rx.stat_help_text("Packets Sent"),
                        ),
                        col_span=1,
                    ),
                    rx.grid_item(
                        rx.stat(
                            rx.stat_number(f"{recorder.stats.avgLatency} ms"),
                            rx.stat_help_text("Average Latency"),
                        ),
                        col_span=1,
                    ),
                    rx.grid_item(
                        rx.stat(
                            rx.stat_number(f"{recorder.stats.connectionUptime} s"),
                            rx.stat_help_text("Connection Uptime"),
                        ),
                        col_span=1,
                    ),
                    rx.grid_item(
                        rx.stat(
                            rx.stat_number(f"{recorder.stats.reconnectAttempts}"),
                            rx.stat_help_text("Reconnect Attempts"),
                        ),
                        col_span=1,
                    ),
                    template_columns="repeat(5, 1fr)",
                    gap=4,
                ),
            ),
            padding="4",
            border_radius="md",
            border="1px solid #eaeaea",
            background="white",
            width="100%",
        ),
    )


def index() -> rx.Component:
    """Create the main page."""
    return rx.container(
        rx.vstack(
            rx.hstack(
                rx.heading("WebRTC Audio Streaming", size="lg"),
                rx.spacer(),
                connection_status_badge(),
                width="100%",
            ),
            # Configuration card
            rx.card(
                rx.accordion(
                    rx.accordion_item(
                        rx.accordion_button(
                            rx.text("Connection Settings"),
                            rx.accordion_icon(),
                        ),
                        rx.accordion_panel(
                            rx.vstack(
                                rx.grid(
                                    rx.grid_item(
                                        rx.form_control(
                                            rx.form_label("Server URL"),
                                            rx.input(
                                                value=State.server_url,
                                                on_change=State.set_server_url,
                                                placeholder="localhost",
                                            ),
                                        ),
                                        col_span=2,
                                    ),
                                    rx.grid_item(
                                        rx.form_control(
                                            rx.form_label("Session ID"),
                                            rx.hstack(
                                                rx.text(
                                                    State.session_id,
                                                    font_family="monospace",
                                                ),
                                                rx.icon_button(
                                                    "refresh-cw",
                                                    size="xs",
                                                    on_click=State.generate_new_session,
                                                ),
                                            ),
                                        ),
                                        col_span=2,
                                    ),
                                    rx.grid_item(
                                        rx.form_control(
                                            rx.form_label("Secure Connection"),
                                            rx.switch(
                                                checked=State.secure_connection,
                                                on_change=State.toggle_secure_connection,
                                            ),
                                        ),
                                        col_span=1,
                                    ),
                                    template_columns="repeat(5, 1fr)",
                                    gap=4,
                                ),
                            ),
                        ),
                    ),
                    rx.accordion_item(
                        rx.accordion_button(
                            rx.text("Audio Settings"),
                            rx.accordion_icon(),
                        ),
                        rx.accordion_panel(
                            rx.vstack(
                                rx.grid(
                                    rx.grid_item(
                                        rx.form_control(
                                            rx.form_label("Buffer Size"),
                                            rx.slider(
                                                min=1024,
                                                max=16384,
                                                step=1024,
                                                value=[State.buffer_size],
                                                on_change=State.set_buffer_size,
                                            ),
                                            rx.form_helper_text(
                                                f"{State.buffer_size} bytes"
                                            ),
                                        ),
                                        col_span=2,
                                    ),
                                    rx.grid_item(
                                        rx.form_control(
                                            rx.form_label("Sample Rate"),
                                            rx.select.root(
                                                rx.select.trigger(
                                                    rx.text(f"{State.sample_rate} Hz"),
                                                ),
                                                rx.select.content(
                                                    rx.select.item(
                                                        "8000 Hz", value=8000
                                                    ),
                                                    rx.select.item(
                                                        "16000 Hz", value=16000
                                                    ),
                                                    rx.select.item(
                                                        "22050 Hz", value=22050
                                                    ),
                                                    rx.select.item(
                                                        "44100 Hz", value=44100
                                                    ),
                                                    rx.select.item(
                                                        "48000 Hz", value=48000
                                                    ),
                                                ),
                                                on_change=lambda value: State.set_sample_rate(
                                                    [int(value)]
                                                ),
                                            ),
                                        ),
                                        col_span=1,
                                    ),
                                    rx.grid_item(
                                        rx.form_control(
                                            rx.form_label("Input Device"),
                                            rx.cond(
                                                recorder.media_devices,
                                                input_device_select(),
                                                rx.text("Loading input devices..."),
                                            ),
                                        ),
                                        col_span=2,
                                    ),
                                    rx.grid_item(
                                        rx.form_control(
                                            rx.form_label("Visualizer"),
                                            rx.switch(
                                                checked=State.visualizer_config.enabled,
                                                on_change=State.toggle_visualizer,
                                            ),
                                        ),
                                        col_span=1,
                                    ),
                                    template_columns="repeat(5, 1fr)",
                                    gap=4,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            # Recorder component (hidden)
            recorder,
            # Error display
            rx.cond(
                State.has_error,
                rx.callout(
                    State.error_message,
                    icon="alert-triangle",
                    color_scheme="red",
                    width="100%",
                ),
            ),
            # Audio visualizer
            rx.cond(
                State.visualizer_config.enabled,
                rx.box(
                    AudioVisualizer.create(
                        stream=recorder.get_stream(),
                        config=State.visualizer_config,
                    ),
                    width="100%",
                    border_radius="md",
                    border="1px solid #eaeaea",
                    padding="2",
                    background="white",
                ),
            ),
            # Control buttons
            rx.hstack(
                rx.cond(
                    recorder.is_recording,
                    rx.button(
                        "Stop Streaming",
                        on_click=recorder.stop(),
                        color_scheme="red",
                        left_icon="square",
                    ),
                    rx.button(
                        "Start Streaming",
                        on_click=recorder.start(),
                        color_scheme="green",
                        left_icon="mic",
                    ),
                ),
                rx.button(
                    rx.cond(
                        State.show_stats,
                        "Hide Stats",
                        "Show Stats",
                    ),
                    on_click=State.toggle_stats,
                    variant="outline",
                ),
                rx.spacer(),
                width="100%",
            ),
            # Stats display
            stats_display(),
            # Transcript card
            rx.card(
                rx.hstack(
                    rx.text("Transcript (from backend)"),
                    rx.spinner(loading=State.connection_state == "connected"),
                    rx.spacer(),
                    rx.icon_button(
                        "trash-2",
                        on_click=State.set_transcript([]),
                        margin_bottom="4px",
                    ),
                    align="center",
                ),
                rx.divider(),
                transcript(),
                rx.cond(
                    State.transcript,
                    rx.fragment(),
                    rx.text(
                        "This area will display transcripts if your backend implements them.",
                        font_style="italic",
                        color="gray",
                        font_size="sm",
                    ),
                ),
            ),
            style=rx.Style({"width": "100%", "> *": {"width": "100%"}}),
            spacing="4",
        ),
        size="2",
        margin_y="2em",
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
