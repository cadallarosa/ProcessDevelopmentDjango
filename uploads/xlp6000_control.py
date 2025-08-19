import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, MATCH
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import serial
import serial.tools.list_ports
import time
import threading
import json
from datetime import datetime, timedelta
import numpy as np
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XLP6000Controller:
    """XLP 6000 Syringe Pump Controller with Advanced Manual Control"""

    def __init__(self):
        self.serial_connection = None
        self.is_connected = False
        self.pump_address = 1
        self.baud_rate = 9600
        self.current_position = 0
        self.target_position = 0
        self.valve_position = "Bypass"
        self.syringe_size = 1.0  # mL
        self.speed_settings = {
            'start_speed': 50,
            'top_speed': 1000,
            'cutoff_speed': 50
        }
        self.command_history = deque(maxlen=100)
        self.status = "Disconnected"
        self.errors = []
        self.operation_log = deque(maxlen=500)

        # Flow control settings
        self.current_flow_rate = 0.0  # mL/min
        self.target_flow_rate = 0.0   # mL/min
        self.is_continuous_mode = False
        self.flow_direction = "aspirate"  # "aspirate" or "dispense"
        self.operation_state = "idle"  # "idle", "aspirating", "dispensing", "paused"

        # Safety settings
        self.pressure_limit = 150.0  # psi
        self.pressure_alarm = False
        self.emergency_stop = False

        # Quick presets
        self.flow_presets = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]  # mL/min
        self.volume_presets = [10, 50, 100, 500, 1000, 5000]  # μL

        # Real-time data storage
        self.data_buffer = {
            'time': deque(maxlen=1000),
            'pressure': deque(maxlen=1000),
            'flow_rate': deque(maxlen=1000),
            'volume': deque(maxlen=1000),
            'position': deque(maxlen=1000),
            'temperature': deque(maxlen=1000)
        }

        # Method storage
        self.method_steps = []
        self.current_method_step = 0
        self.is_running = False
        self.is_paused = False

        # Gradient mixing
        self.gradient_enabled = False
        self.gradient_profile = []

        # Threading for continuous operations
        self.operation_thread = None
        self.stop_operation = threading.Event()

    def get_available_ports(self):
        """Get list of available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port, baud_rate=9600):
        """Connect to XLP 6000 pump"""
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.is_connected = True
            self.status = "Connected"
            self.baud_rate = baud_rate
            logger.info(f"Connected to XLP 6000 on {port}")

            # Initialize pump
            self.send_command("ZR")  # Initialize command
            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            self.status = f"Connection Error: {e}"
            return False

    def disconnect(self):
        """Disconnect from pump"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False
        self.status = "Disconnected"
        logger.info("Disconnected from XLP 6000")

    def send_command(self, command):
        """Send command to XLP 6000"""
        if not self.is_connected or not self.serial_connection:
            logger.warning("Not connected to pump")
            return False

        try:
            # Format command with address and proper termination
            full_command = f"/{self.pump_address}{command}\r"
            self.serial_connection.write(full_command.encode())

            # Add to command history
            self.command_history.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'command': full_command.strip()
            })

            logger.info(f"Sent command: {full_command.strip()}")

            # Read response if available
            time.sleep(0.1)  # Small delay for response
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.read(self.serial_connection.in_waiting).decode()
                logger.info(f"Response: {response.strip()}")
                return response

            return True

        except Exception as e:
            logger.error(f"Command failed: {e}")
            return False

    def move_valve(self, position):
        """Move valve to specified position"""
        position_commands = {
            'Input': 'I',
            'Output': 'O',
            'Bypass': 'B'
        }

        if position in position_commands:
            command = f"{position_commands[position]}R"
            if self.send_command(command):
                self.valve_position = position
                return True
        return False

    def move_syringe_absolute(self, position):
        """Move syringe to absolute position (0-6000)"""
        if 0 <= position <= 6000:
            command = f"A{position}R"
            if self.send_command(command):
                self.target_position = position
                return True
        return False

    def aspirate(self, volume_ul):
        """Aspirate specified volume in microliters"""
        increments = int((6000 * volume_ul) / (self.syringe_size * 1000))
        if increments > 0:
            command = f"P{increments}R"
            return self.send_command(command)
        return False

    def dispense(self, volume_ul):
        """Dispense specified volume in microliters"""
        increments = int((6000 * volume_ul) / (self.syringe_size * 1000))
        if increments > 0:
            command = f"D{increments}R"
            return self.send_command(command)
        return False

    def set_speed_profile(self, start_speed, top_speed, cutoff_speed):
        """Set pump speed profile"""
        command = f"v{start_speed}V{top_speed}c{cutoff_speed}"
        if self.send_command(command):
            self.speed_settings.update({
                'start_speed': start_speed,
                'top_speed': top_speed,
                'cutoff_speed': cutoff_speed
            })
            return True
        return False

    def query_status(self):
        """Query pump status"""
        return self.send_command("Q")

    def start_continuous_flow(self, flow_rate, direction="aspirate"):
        """Start continuous flow at specified rate"""
        self.target_flow_rate = flow_rate
        self.flow_direction = direction
        self.is_continuous_mode = True
        self.operation_state = "aspirating" if direction == "aspirate" else "dispensing"

        # Convert flow rate to steps/sec
        steps_per_sec = int((flow_rate * 6000) / (self.syringe_size * 60))

        if direction == "aspirate":
            command = f"v{steps_per_sec}V{steps_per_sec}c{steps_per_sec}P6000R"
        else:
            command = f"v{steps_per_sec}V{steps_per_sec}c{steps_per_sec}D6000R"

        self.log_operation(f"Started continuous {direction} at {flow_rate} mL/min")
        return self.send_command(command)

    def stop_continuous_flow(self):
        """Stop continuous flow"""
        self.is_continuous_mode = False
        self.current_flow_rate = 0.0
        self.target_flow_rate = 0.0
        self.operation_state = "idle"
        self.log_operation("Stopped continuous flow")
        return self.send_command("T")  # Terminate command

    def pause_operation(self):
        """Pause current operation"""
        if self.operation_state in ["aspirating", "dispensing"]:
            self.is_paused = True
            self.operation_state = "paused"
            self.log_operation("Operation paused")
            return self.send_command("T")
        return False

    def resume_operation(self):
        """Resume paused operation"""
        if self.is_paused:
            self.is_paused = False
            if self.is_continuous_mode:
                return self.start_continuous_flow(self.target_flow_rate, self.flow_direction)
            self.log_operation("Operation resumed")
        return False

    def emergency_stop(self):
        """Emergency stop all operations"""
        self.emergency_stop = True
        self.stop_continuous_flow()
        self.is_paused = False
        self.operation_state = "idle"
        self.log_operation("EMERGENCY STOP ACTIVATED", level="ERROR")
        return self.send_command("T")

    def prime_system(self, volume=1000):
        """Prime the system by aspirating and dispensing"""
        self.log_operation(f"Priming system with {volume}μL")
        self.move_valve("Input")
        time.sleep(0.5)
        self.aspirate(volume)
        time.sleep(1)
        self.move_valve("Output")
        time.sleep(0.5)
        self.dispense(volume)
        self.move_valve("Bypass")
        return True

    def purge_system(self, cycles=3):
        """Purge system with multiple cycles"""
        self.log_operation(f"Purging system - {cycles} cycles")
        for i in range(cycles):
            self.prime_system()
            time.sleep(0.5)
        return True

    def log_operation(self, message, level="INFO"):
        """Log operation with timestamp"""
        log_entry = {
            'timestamp': datetime.now(),
            'message': message,
            'level': level,
            'pump_position': self.current_position,
            'valve_position': self.valve_position
        }
        self.operation_log.append(log_entry)
        logger.info(f"[{level}] {message}")

    def check_pressure_safety(self):
        """Check if pressure is within safe limits"""
        if self.data_buffer['pressure']:
            current_pressure = self.data_buffer['pressure'][-1]
            if current_pressure > self.pressure_limit:
                self.pressure_alarm = True
                self.log_operation(f"Pressure alarm: {current_pressure:.1f} psi > {self.pressure_limit} psi", "WARNING")
                return False
        return True

    def add_data_point(self):
        """Add simulated data point for real-time plotting"""
        current_time = datetime.now()
        self.data_buffer['time'].append(current_time)

        # Simulate more realistic data based on operation state
        base_pressure = 120 if self.operation_state == "idle" else 140
        pressure_noise = 2 if self.is_continuous_mode else 5
        pressure = np.random.normal(base_pressure, pressure_noise)

        # Add pressure spikes during valve changes
        if self.operation_state in ["aspirating", "dispensing"]:
            pressure += np.random.normal(10, 3)

        self.data_buffer['pressure'].append(max(0, pressure))
        self.data_buffer['flow_rate'].append(self.current_flow_rate + np.random.normal(0, 0.1))
        self.data_buffer['volume'].append(np.random.normal(50, 2))
        self.data_buffer['position'].append(self.current_position + np.random.normal(0, 5))
        self.data_buffer['temperature'].append(np.random.normal(23.5, 0.2))

        # Update current flow rate towards target
        if self.is_continuous_mode:
            flow_diff = self.target_flow_rate - self.current_flow_rate
            self.current_flow_rate += flow_diff * 0.1  # Smooth ramping
        else:
            self.current_flow_rate *= 0.95  # Decay to zero

        # Check safety
        self.check_pressure_safety()

    def create_gradient(self, start_flow, end_flow, duration_min, steps=10):
        """Create a gradient profile for flow rate changes"""
        gradient_steps = []
        time_per_step = duration_min / steps

        for i in range(steps + 1):
            progress = i / steps
            current_flow = start_flow + (end_flow - start_flow) * progress
            gradient_steps.append({
                'time_min': i * time_per_step,
                'flow_rate': current_flow,
                'step': i
            })

        self.gradient_profile = gradient_steps
        self.gradient_enabled = True
        self.log_operation(f"Created gradient: {start_flow} to {end_flow} mL/min over {duration_min} min")
        return gradient_steps

    def execute_gradient_step(self, step_index):
        """Execute a specific gradient step"""
        if step_index < len(self.gradient_profile):
            step = self.gradient_profile[step_index]
            self.start_continuous_flow(step['flow_rate'], self.flow_direction)
            self.log_operation(f"Gradient step {step['step']}: {step['flow_rate']:.2f} mL/min")
            return True
        return False

    def get_gradient_status(self):
        """Get current gradient execution status"""
        return {
            'enabled': self.gradient_enabled,
            'profile': self.gradient_profile,
            'current_step': getattr(self, 'current_gradient_step', 0),
            'total_steps': len(self.gradient_profile) if self.gradient_profile else 0
        }


# Initialize controller
controller = XLP6000Controller()

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
])

app.title = "XLP 6000 Control System"

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --primary-color: #2563eb;
                --primary-hover: #1d4ed8;
                --secondary-color: #64748b;
                --success-color: #059669;
                --success-hover: #047857;
                --warning-color: #d97706;
                --warning-hover: #b45309;
                --danger-color: #dc2626;
                --danger-hover: #b91c1c;
                --info-color: #0891b2;
                --info-hover: #0e7490;
                --background-main: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                --background-card: rgba(255, 255, 255, 0.95);
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --border-color: #e2e8f0;
                --shadow-light: 0 1px 3px rgba(0,0,0,0.1);
                --shadow-medium: 0 4px 6px rgba(0,0,0,0.1);
                --shadow-heavy: 0 10px 15px rgba(0,0,0,0.1);
            }
            
            body { 
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                margin: 0;
                background: var(--background-main);
                color: var(--text-primary);
                line-height: 1.6;
            }
            
            .main-header {
                background: linear-gradient(135deg, #1e40af 0%, #3730a3 50%, #581c87 100%);
                color: white;
                padding: 1.5rem 2rem;
                box-shadow: var(--shadow-heavy);
                border-bottom: 3px solid #fbbf24;
            }
            
            .main-header h1 {
                background: linear-gradient(45deg, #fbbf24, #f59e0b);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .status-connected { 
                color: var(--success-color); 
                font-weight: 600;
                text-shadow: 0 0 10px rgba(5, 150, 105, 0.3);
            }
            
            .status-disconnected { 
                color: var(--danger-color); 
                font-weight: 600;
                text-shadow: 0 0 10px rgba(220, 38, 38, 0.3);
            }
            
            .card {
                background: var(--background-card);
                border-radius: 16px;
                box-shadow: var(--shadow-medium);
                padding: 1.5rem;
                margin: 0.75rem;
                border: 1px solid var(--border-color);
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                height: fit-content;
            }
            
            .card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-heavy);
            }
            
            .metric-card {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--info-color) 100%);
                color: white;
                text-align: center;
                border-radius: 12px;
                padding: 1rem;
                box-shadow: var(--shadow-medium);
                transition: all 0.3s ease;
                border: 2px solid rgba(255,255,255,0.1);
            }
            
            .metric-card:hover {
                transform: scale(1.05);
                box-shadow: var(--shadow-heavy);
            }
            
            .metric-card.pressure {
                background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
            }
            
            .metric-card.flow {
                background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            }
            
            .metric-card.volume {
                background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
            }
            
            .metric-card.temperature {
                background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
            }
            
            .control-button {
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                cursor: pointer;
                margin: 0.25rem;
                font-weight: 600;
                font-size: 0.875rem;
                transition: all 0.2s ease;
                box-shadow: var(--shadow-light);
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .control-button:hover {
                background: var(--primary-hover);
                transform: translateY(-1px);
                box-shadow: var(--shadow-medium);
            }
            
            .control-button:active {
                transform: translateY(0);
            }
            
            .control-button.success {
                background: var(--success-color);
            }
            
            .control-button.success:hover {
                background: var(--success-hover);
            }
            
            .control-button.warning {
                background: var(--warning-color);
            }
            
            .control-button.warning:hover {
                background: var(--warning-hover);
            }
            
            .control-button.danger {
                background: var(--danger-color);
            }
            
            .control-button.danger:hover {
                background: var(--danger-hover);
            }
            
            .control-button.info {
                background: var(--info-color);
            }
            
            .control-button.info:hover {
                background: var(--info-hover);
            }
            
            .valve-button-active {
                background: var(--success-color) !important;
                box-shadow: 0 0 20px rgba(5, 150, 105, 0.4) !important;
                border: 2px solid rgba(255,255,255,0.3) !important;
            }
            
            .emergency-button {
                background: var(--danger-color) !important;
                animation: pulse-red 2s infinite;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .emergency-button:hover {
                background: var(--danger-hover) !important;
                box-shadow: 0 0 20px rgba(220, 38, 38, 0.6) !important;
            }
            
            @keyframes pulse-red {
                0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
                100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
            }
            
            .pump-visual {
                background: linear-gradient(145deg, #f1f5f9, #e2e8f0);
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
                border: 2px solid var(--border-color);
                position: relative;
                overflow: hidden;
            }
            
            .pump-visual::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary-color), var(--success-color), var(--warning-color));
            }
            
            .progress-bar {
                background: var(--border-color);
                border-radius: 10px;
                height: 8px;
                overflow: hidden;
                margin: 0.5rem 0;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--success-color), var(--primary-color));
                transition: width 0.3s ease;
                border-radius: 10px;
            }
            
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }
            
            .status-idle { background: var(--secondary-color); }
            .status-running { background: var(--success-color); }
            .status-warning { background: var(--warning-color); }
            .status-error { background: var(--danger-color); }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            
            .quick-preset {
                display: inline-block;
                background: rgba(37, 99, 235, 0.1);
                border: 2px solid var(--primary-color);
                color: var(--primary-color);
                padding: 0.5rem 1rem;
                border-radius: 20px;
                margin: 0.25rem;
                cursor: pointer;
                transition: all 0.2s ease;
                font-weight: 600;
                font-size: 0.875rem;
            }
            
            .quick-preset:hover {
                background: var(--primary-color);
                color: white;
                transform: scale(1.05);
            }
            
            .tabs {
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                margin-bottom: 2rem;
                overflow: hidden;
                box-shadow: var(--shadow-light);
            }
            
            .tab {
                background: transparent !important;
                border: none !important;
                color: var(--text-secondary) !important;
                font-weight: 600 !important;
                padding: 1rem 2rem !important;
                transition: all 0.3s ease !important;
            }
            
            .tab--selected {
                background: var(--primary-color) !important;
                color: white !important;
                box-shadow: var(--shadow-light) !important;
            }
            
            .operation-log {
                background: #1e293b;
                color: #e2e8f0;
                border-radius: 8px;
                padding: 1rem;
                max-height: 300px;
                overflow-y: auto;
                font-family: 'Fira Code', monospace;
                font-size: 0.875rem;
                line-height: 1.4;
            }
            
            .log-entry {
                padding: 0.25rem 0;
                border-bottom: 1px solid rgba(226, 232, 240, 0.1);
            }
            
            .log-timestamp {
                color: #64748b;
                font-size: 0.75rem;
            }
            
            .log-info { color: #0891b2; }
            .log-warning { color: #d97706; }
            .log-error { color: #dc2626; }
            
            .slider-container {
                margin: 0.5rem 0;
                padding: 0.75rem;
                background: rgba(37, 99, 235, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(37, 99, 235, 0.1);
            }
            
            .layout-row {
                display: flex;
                gap: 1rem;
                margin: 1rem 0;
                align-items: stretch;
            }
            
            .layout-col {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .layout-col-narrow {
                flex: 0 0 300px;
            }
            
            .layout-col-wide {
                flex: 2;
            }
            
            .control-group {
                margin-bottom: 1.5rem;
            }
            
            .control-group:last-child {
                margin-bottom: 0;
            }
            
            .button-group {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .input-group {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            
            .input-row {
                display: flex;
                gap: 0.75rem;
                align-items: flex-end;
            }
            
            .input-label {
                font-weight: 600;
                color: var(--text-primary);
                font-size: 0.875rem;
                margin-bottom: 0.25rem;
                display: block;
            }
            
            .form-input {
                padding: 0.5rem 0.75rem;
                border: 2px solid var(--border-color);
                border-radius: 6px;
                font-size: 0.875rem;
                transition: border-color 0.2s ease;
                background: white;
            }
            
            .form-input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }
            
            .section-title {
                font-size: 1.25rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .metric-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 0.75rem;
                margin: 1rem 0;
            }
            
            .pid-component {
                display: inline-block;
                margin: 5px;
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .pid-valve {
                width: 60px;
                height: 40px;
                background: #e2e8f0;
                border: 3px solid #64748b;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 0.75rem;
                transition: all 0.3s ease;
                position: relative;
            }
            
            .pid-valve.active {
                background: #10b981;
                border-color: #059669;
                color: white;
                box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
            }
            
            .pid-pipe {
                height: 8px;
                background: #64748b;
                transition: all 0.3s ease;
                position: relative;
            }
            
            .pid-pipe.flow-active {
                background: #10b981;
                box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
                animation: flow-pulse 2s infinite;
            }
            
            .pid-pump {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                border: 4px solid #1e40af;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                color: white;
                font-size: 0.75rem;
                transition: all 0.3s ease;
                position: relative;
                margin: 20px;
            }
            
            .pid-pump.active {
                animation: pump-pulse 1.5s infinite;
                transform: scale(1.05);
            }
            
            .pid-syringe {
                width: 60px;
                height: 120px;
                background: linear-gradient(180deg, #f3f4f6 0%, #e5e7eb 100%);
                border: 3px solid #9ca3af;
                border-radius: 8px;
                position: relative;
                margin: 10px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-end;
                overflow: hidden;
            }
            
            .pid-syringe-plunger {
                width: 50px;
                height: 10px;
                background: #6b7280;
                border-radius: 2px;
                position: absolute;
                transition: all 0.8s ease;
            }
            
            .pid-syringe-liquid {
                width: 100%;
                background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
                transition: all 0.8s ease;
                border-radius: 0 0 5px 5px;
            }
            
            @keyframes pump-pulse {
                0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
                70% { box-shadow: 0 0 0 20px rgba(59, 130, 246, 0); }
                100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
            }
            
            @keyframes flow-pulse {
                0% { opacity: 0.6; }
                50% { opacity: 1; }
                100% { opacity: 0.6; }
            }
            
            .pid-container {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 10px;
                min-height: 200px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1([
                html.I(className="fas fa-flask", style={'marginRight': '10px'}),
                "XLP 6000 Control System"
            ], style={'margin': '0', 'fontSize': '1.5rem'}),
            html.P("Advanced Syringe Pump Controller",
                   style={'margin': '0', 'opacity': '0.8', 'fontSize': '0.9rem'})
        ], style={'flex': '1'}),

        html.Div([
            html.Div(id='connection-status', style={'marginRight': '1rem'}),
            html.Button([
                html.I(className="fas fa-play", style={'marginRight': '5px'}),
                "Run Method"
            ], id='run-method-btn', className='control-button'),
            html.Button([
                html.I(className="fas fa-pause", style={'marginRight': '5px'}),
                "Pause"
            ], id='pause-method-btn', className='control-button'),
            html.Button([
                html.I(className="fas fa-stop", style={'marginRight': '5px'}),
                "Stop"
            ], id='stop-method-btn', className='control-button emergency-button'),
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], className='main-header', style={'display': 'flex', 'alignItems': 'center'}),

    # Navigation Tabs
    dcc.Tabs(id='main-tabs', value='dashboard', className='tabs', children=[
        dcc.Tab(label='📊 Live Dashboard', value='dashboard', className='tab'),
        dcc.Tab(label='🎛️ Manual Control', value='manual', className='tab'),
        dcc.Tab(label='⚡ Quick Actions', value='quick', className='tab'),
        dcc.Tab(label='🧪 Method Editor', value='method', className='tab'),
        dcc.Tab(label='⚙️ Configuration', value='config', className='tab'),
        dcc.Tab(label='📋 Operation Log', value='log', className='tab'),
    ], style={'marginBottom': '20px'}),

    # Main content area
    html.Div(id='tab-content'),

    # Interval components for real-time updates
    dcc.Interval(id='realtime-interval', interval=1000, n_intervals=0),
    dcc.Interval(id='status-interval', interval=5000, n_intervals=0),

    # Storage components
    dcc.Store(id='method-store', data=[]),
    dcc.Store(id='pump-state-store', data={}),
])


# Dashboard Layout
def create_dashboard_layout():
    return html.Div([
        # Compact System Status Cards
        html.Div([
            html.Div([
                html.Div([html.Span(className="status-indicator status-running"), "PRESSURE"],
                         style={'fontSize': '0.75rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                html.H2(id='pressure-display', children="0.0 psi",
                        style={'margin': '0', 'fontSize': '1.8rem', 'fontWeight': '700'}),
                html.Div(id='pressure-status', children="Normal",
                         style={'margin': '2px 0 0 0', 'opacity': '0.9', 'fontSize': '0.75rem'})
            ], className='metric-card pressure'),

            html.Div([
                html.Div([html.Span(className="status-indicator status-running"), "FLOW RATE"],
                         style={'fontSize': '0.75rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                html.H2(id='flow-display', children="0.0 mL/min",
                        style={'margin': '0', 'fontSize': '1.8rem', 'fontWeight': '700'}),
                html.Div(id='flow-status', children="Stable",
                         style={'margin': '2px 0 0 0', 'opacity': '0.9', 'fontSize': '0.75rem'})
            ], className='metric-card flow'),

            html.Div([
                html.Div([html.Span(className="status-indicator status-idle"), "VOLUME"],
                         style={'fontSize': '0.75rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                html.H2(id='volume-display', children="0 μL",
                        style={'margin': '0', 'fontSize': '1.8rem', 'fontWeight': '700'}),
                html.Div(id='volume-status', children="Ready",
                         style={'margin': '2px 0 0 0', 'opacity': '0.9', 'fontSize': '0.75rem'})
            ], className='metric-card volume'),

            html.Div([
                html.Div([html.Span(className="status-indicator status-idle"), "PUMP STATUS"],
                         style={'fontSize': '0.75rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                html.H2(id='pump-status-display-compact', children="IDLE",
                        style={'margin': '0', 'fontSize': '1.8rem', 'fontWeight': '700'}),
                html.Div(id='pump-position-display', children="Pos: 0",
                         style={'margin': '2px 0 0 0', 'opacity': '0.9', 'fontSize': '0.75rem'})
            ], className='metric-card'),

            html.Div([
                html.Div([html.Span(className="status-indicator status-idle"), "VALVE STATUS"],
                         style={'fontSize': '0.75rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                html.H2(id='valve-status-display-compact', children="BYPASS",
                        style={'margin': '0', 'fontSize': '1.8rem', 'fontWeight': '700'}),
                html.Div(id='valve-flow-display', children="No Flow",
                         style={'margin': '2px 0 0 0', 'opacity': '0.9', 'fontSize': '0.75rem'})
            ], className='metric-card'),
        ], className='metric-grid'),

        # Visual System Status and Real-time Monitoring
        html.Div([
            # Visual Pump Status
            html.Div([
                html.H3([html.I(className="fas fa-eye", style={'marginRight': '10px'}), "System Visualization"], 
                        className='section-title'),
                
                # Pump Position Visual
                html.Div([
                    html.H4("Pump Position", style={'textAlign': 'center', 'marginBottom': '15px', 'fontSize': '1rem'}),
                    html.Div([
                        html.Div("Bottom (0)", style={'fontSize': '0.75rem', 'color': 'var(--text-secondary)'}),
                        html.Div(className='progress-bar', children=[
                            html.Div(id='pump-progress', className='progress-fill', style={'width': '0%'})
                        ]),
                        html.Div("Top (6000)", style={'fontSize': '0.75rem', 'color': 'var(--text-secondary)', 'textAlign': 'right'}),
                    ], style={'margin': '10px 0'}),
                    html.Div(id='position-text', children="Position: 0 / 6000", 
                             style={'textAlign': 'center', 'fontWeight': '600', 'margin': '10px 0', 'fontSize': '0.875rem'})
                ], className='pump-visual'),
                
                # P&ID Diagram
                html.Div([
                    html.H4("System P&ID Diagram", style={'textAlign': 'center', 'marginBottom': '15px', 'fontSize': '1rem'}),
                    html.Div(id='pid-diagram', style={'padding': '20px', 'minHeight': '300px'})
                ], className='pump-visual'),
                
                # Operation Status
                html.Div([
                    html.H4("Current Operation", style={'marginBottom': '15px', 'fontSize': '1rem'}),
                    html.Div(id='operation-status-display')
                ], className='pump-visual')
            ], className='card layout-col-narrow'),
            
            # Real-time Chart
            html.Div([
                html.H3([html.I(className="fas fa-chart-line", style={'marginRight': '10px'}), "Real-time Monitoring"],
                        className='section-title'),
                dcc.Graph(id='realtime-chart', style={'height': '450px'})
            ], className='card layout-col-wide'),

            # System Status and History
            html.Div([
                html.H3([html.I(className="fas fa-info-circle", style={'marginRight': '10px'}), "System Status"],
                        className='section-title'),
                html.Div(id='pump-status-display', style={'marginBottom': '1.5rem'}),
                html.Hr(style={'margin': '1rem 0', 'border': '1px solid var(--border-color)'}),
                html.H4([html.I(className="fas fa-history", style={'marginRight': '8px'}), "Recent Commands"],
                        style={'fontSize': '1rem', 'marginBottom': '1rem'}),
                html.Div(id='command-history-display')
            ], className='card layout-col-narrow')
        ], className='layout-row')
    ], style={'margin': '1.5rem', 'maxWidth': '1400px', 'marginLeft': 'auto', 'marginRight': 'auto'})


# Manual Control Layout
def create_manual_control_layout():
    return html.Div([
        # Top Row - Valve and Syringe Control
        html.Div([
            # Valve Control
            html.Div([
                html.H3([html.I(className="fas fa-exchange-alt", style={'marginRight': '8px'}), "Valve Control"],
                        className='section-title'),
                html.Div([
                    html.Label("Select Valve Position:", className='input-label'),
                    html.Div([
                        html.Button("Input", id='valve-input-btn', className='control-button',
                                    style={'width': '90px'}),
                        html.Button("Output", id='valve-output-btn', className='control-button',
                                    style={'width': '90px'}),
                        html.Button("Bypass", id='valve-bypass-btn', className='control-button valve-button-active',
                                    style={'width': '90px'}),
                    ], className='button-group', style={'marginBottom': '1rem'})
                ], className='control-group'),
                html.Div([
                    html.Label("Direct Port Access:", className='input-label'),
                    html.Div([
                        dcc.Input(id='direct-port-input', type='number', min=1, max=9,
                                  className='form-input', style={'width': '80px'}),
                        html.Button("Move", id='move-port-btn', className='control-button')
                    ], className='input-row')
                ], className='control-group')
            ], className='card layout-col'),

            # Syringe Control
            html.Div([
                html.H3([html.I(className="fas fa-syringe", style={'marginRight': '8px'}), "Syringe Control"],
                        className='section-title'),
                html.Div([
                    html.Label("Absolute Position (0-6000 steps):", className='input-label'),
                    html.Div([
                        dcc.Input(id='absolute-position-input', type='number', min=0, max=6000, value=0,
                                  className='form-input', style={'width': '120px'}),
                        html.Button("Move", id='move-absolute-btn', className='control-button')
                    ], className='input-row')
                ], className='control-group'),
                html.Div([
                    html.Label("Quick Positions:", className='input-label'),
                    html.Div([
                        html.Button("Bottom (0)", id='move-bottom-btn', className='control-button',
                                    style={'width': '110px'}),
                        html.Button("Top (6000)", id='move-top-btn', className='control-button',
                                    style={'width': '110px'}),
                    ], className='button-group')
                ], className='control-group')
            ], className='card layout-col')
        ], className='layout-row'),

        # Bottom Row - Volume and Speed Control
        html.Div([
            # Aspirate/Dispense Control
            html.Div([
                html.H3([html.I(className="fas fa-tint", style={'marginRight': '8px'}), "Volume Control"],
                        className='section-title'),
                html.Div([
                    html.Label("Volume (μL):", className='input-label'),
                    dcc.Input(id='volume-input', type='number', min=1, max=50000, value=100,
                              className='form-input', style={'width': '120px'})
                ], className='input-group'),
                html.Div([
                    html.Button([html.I(className="fas fa-arrow-up", style={'marginRight': '6px'}), "Aspirate"],
                                id='aspirate-btn', className='control-button success',
                                style={'width': '130px'}),
                    html.Button([html.I(className="fas fa-arrow-down", style={'marginRight': '6px'}), "Dispense"],
                                id='dispense-btn', className='control-button danger',
                                style={'width': '130px'}),
                ], className='button-group')
            ], className='card layout-col'),

            # Speed Control
            html.Div([
                html.H3([html.I(className="fas fa-tachometer-alt", style={'marginRight': '8px'}), "Speed Settings"],
                        className='section-title'),
                html.Div([
                    html.Label("Start Speed:", className='input-label'),
                    html.Div([
                        dcc.Slider(id='start-speed-slider', min=1, max=1000, value=50, step=1,
                                   tooltip={"placement": "bottom", "always_visible": True})
                    ], className='slider-container')
                ], className='control-group'),
                html.Div([
                    html.Label("Top Speed:", className='input-label'),
                    html.Div([
                        dcc.Slider(id='top-speed-slider', min=1, max=5800, value=1000, step=1,
                                   tooltip={"placement": "bottom", "always_visible": True})
                    ], className='slider-container')
                ], className='control-group'),
                html.Div([
                    html.Label("Cutoff Speed:", className='input-label'),
                    html.Div([
                        dcc.Slider(id='cutoff-speed-slider', min=1, max=1000, value=50, step=1,
                                   tooltip={"placement": "bottom", "always_visible": True})
                    ], className='slider-container')
                ], className='control-group'),
                html.Button([html.I(className="fas fa-check", style={'marginRight': '8px'}), "Apply Settings"], 
                           id='apply-speed-btn', className='control-button success',
                           style={'width': '100%', 'marginTop': '1rem'})
            ], className='card layout-col')
        ], className='layout-row')
    ], style={'margin': '1.5rem', 'maxWidth': '1400px', 'marginLeft': 'auto', 'marginRight': 'auto'})


# Method Editor Layout
def create_method_editor_layout():
    return html.Div([
        html.Div([
            # Method Steps Display
            html.Div([
                html.H3([html.I(className="fas fa-list"), " Method Steps"]),
                html.Div([
                    html.Button([html.I(className="fas fa-upload"), " Load"], className='control-button',
                                style={'margin': '5px'}),
                    html.Button([html.I(className="fas fa-download"), " Save"], className='control-button',
                                style={'margin': '5px'}),
                    html.Button([html.I(className="fas fa-trash"), " Clear"], id='clear-method-btn',
                                className='control-button', style={'margin': '5px', 'background': '#ef4444'}),
                ]),
                html.Div(id='method-steps-display',
                         style={'marginTop': '20px', 'maxHeight': '400px', 'overflowY': 'auto'})
            ], className='card', style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'}),

            # Step Editor
            html.Div([
                html.H3("Add Method Step"),
                html.Div([
                    html.Label("Step Type:"),
                    dcc.Dropdown(
                        id='step-type-dropdown',
                        options=[
                            {'label': 'Aspirate', 'value': 'aspirate'},
                            {'label': 'Dispense', 'value': 'dispense'},
                            {'label': 'Move Valve', 'value': 'move_valve'},
                            {'label': 'Wait/Delay', 'value': 'wait'},
                            {'label': 'Wash', 'value': 'wash'}
                        ],
                        value='aspirate'
                    )
                ], style={'marginBottom': '15px'}),

                html.Div([
                    html.Label("Volume (μL):"),
                    dcc.Input(id='step-volume-input', type='number', value=100, min=1, max=50000)
                ], style={'marginBottom': '15px'}),

                html.Div([
                    html.Label("Speed (steps/sec):"),
                    dcc.Input(id='step-speed-input', type='number', value=1000, min=1, max=5800)
                ], style={'marginBottom': '15px'}),

                html.Div([
                    html.Label("Valve Position:"),
                    dcc.Dropdown(
                        id='step-valve-dropdown',
                        options=[
                            {'label': 'Input', 'value': 'Input'},
                            {'label': 'Output', 'value': 'Output'},
                            {'label': 'Bypass', 'value': 'Bypass'}
                        ],
                        value='Input'
                    )
                ], style={'marginBottom': '15px'}),

                html.Div([
                    html.Label("Description:"),
                    dcc.Input(id='step-description-input', type='text', placeholder="Step description")
                ], style={'marginBottom': '15px'}),

                html.Button("Add Step", id='add-step-btn', className='control-button', style={'width': '100%'})
            ], className='card',
                style={'width': '35%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '5%'})
        ])
    ], style={'margin': '20px'})


# Configuration Layout
def create_configuration_layout():
    return html.Div([
        html.Div([
            # Communication Settings
            html.Div([
                html.H3([html.I(className="fas fa-plug"), " Communication Settings"]),
                html.Div([
                    html.Label("Serial Port:"),
                    dcc.Dropdown(id='port-dropdown', placeholder="Select port"),
                ], style={'marginBottom': '15px'}),

                html.Div([
                    html.Label("Baud Rate:"),
                    dcc.Dropdown(
                        id='baud-dropdown',
                        options=[
                            {'label': '9600', 'value': 9600},
                            {'label': '38400', 'value': 38400}
                        ],
                        value=9600
                    )
                ], style={'marginBottom': '15px'}),

                html.Div([
                    html.Label("Pump Address:"),
                    dcc.Input(id='pump-address-input', type='number', min=0, max=14, value=1)
                ], style={'marginBottom': '15px'}),

                html.Button("Connect", id='connect-btn', className='control-button',
                            style={'width': '48%', 'background': '#10b981'}),
                html.Button("Disconnect", id='disconnect-btn', className='control-button',
                            style={'width': '48%', 'marginLeft': '4%', 'background': '#ef4444'})
            ], className='card', style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top'}),

            # Pump Configuration
            html.Div([
                html.H3([html.I(className="fas fa-cog"), " Pump Configuration"]),
                html.Div([
                    html.Label("Valve Type:"),
                    dcc.Dropdown(
                        id='valve-type-dropdown',
                        options=[
                            {'label': '3-Port Valve', 'value': '3-port'},
                            {'label': '4-Port Valve', 'value': '4-port'},
                            {'label': 'T-Valve', 'value': 't-valve'},
                            {'label': '6-Port Distribution', 'value': '6-port'},
                            {'label': '9-Port Distribution', 'value': '9-port'}
                        ],
                        value='3-port'
                    )
                ], style={'marginBottom': '15px'}),

                html.Div([
                    html.Label("Syringe Size:"),
                    dcc.Dropdown(
                        id='syringe-size-dropdown',
                        options=[
                            {'label': '50 μL', 'value': 0.05},
                            {'label': '100 μL', 'value': 0.1},
                            {'label': '250 μL', 'value': 0.25},
                            {'label': '500 μL', 'value': 0.5},
                            {'label': '1.0 mL', 'value': 1.0},
                            {'label': '2.5 mL', 'value': 2.5},
                            {'label': '5.0 mL', 'value': 5.0},
                            {'label': '10 mL', 'value': 10.0},
                            {'label': '25 mL', 'value': 25.0},
                            {'label': '50 mL', 'value': 50.0}
                        ],
                        value=1.0
                    )
                ], style={'marginBottom': '15px'}),

                html.Button("Initialize Pump", id='init-pump-btn', className='control-button',
                            style={'width': '48%', 'background': '#f59e0b'}),
                html.Button("Query Status", id='query-status-btn', className='control-button',
                            style={'width': '48%', 'marginLeft': '4%'})
            ], className='card',
                style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '10%'})
        ]),

        html.Div([
            # System Information
            html.Div([
                html.H3([html.I(className="fas fa-info-circle"), " System Information"]),
                html.Div(id='system-info-display')
            ], className='card', style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top'}),

            # Error Log
            html.Div([
                html.H3([html.I(className="fas fa-exclamation-triangle"), " Status & Errors"]),
                html.Div(id='error-log-display')
            ], className='card',
                style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '10%'})
        ], style={'marginTop': '20px'})
    ], style={'margin': '20px'})


# Callbacks

# Quick Actions Layout
def create_quick_actions_layout():
    return html.Div([
        html.H2([html.I(className="fas fa-bolt", style={'marginRight': '10px'}), "Quick Actions"],
                className='section-title', style={'marginBottom': '2rem'}),
        
        # Emergency Controls
        html.Div([
            html.H3([html.I(className="fas fa-exclamation-triangle", style={'marginRight': '8px'}), "Emergency Controls"],
                    className='section-title'),
            html.Div([
                html.Button([
                    html.I(className="fas fa-stop", style={'marginRight': '8px'}),
                    "EMERGENCY STOP"
                ], id='emergency-stop-btn', className='control-button emergency-button',
                    style={'padding': '1rem 2rem', 'fontSize': '1.1rem'}),
                
                html.Button([
                    html.I(className="fas fa-pause", style={'marginRight': '8px'}),
                    "Pause Operation"
                ], id='pause-operation-btn', className='control-button warning'),
                
                html.Button([
                    html.I(className="fas fa-play", style={'marginRight': '8px'}),
                    "Resume Operation"
                ], id='resume-operation-btn', className='control-button success')
            ], className='button-group')
        ], className='card'),
        
        # Flow Control Section
        html.Div([
            html.Div([
                html.H3([html.I(className="fas fa-tint", style={'marginRight': '8px'}), "Flow Rate Presets"],
                        className='section-title'),
                html.P("Click to start continuous flow at preset rate:", 
                       style={'marginBottom': '1rem', 'color': 'var(--text-secondary)'}),
                html.Div([
                    html.Div(f"{rate} mL/min", 
                             id={'type': 'flow-preset', 'index': i}, 
                             className='quick-preset')
                    for i, rate in enumerate(controller.flow_presets)
                ], style={'marginBottom': '1.5rem'}),
                
                html.Div([
                    html.Label("Custom Flow Rate:", className='input-label'),
                    html.Div([
                        dcc.Input(id='custom-flow-input', type='number', value=1.0, min=0.01, max=50.0, step=0.01,
                                  className='form-input', style={'width': '120px'}),
                        html.Span("mL/min", style={'marginLeft': '8px', 'color': 'var(--text-secondary)'})
                    ], className='input-row', style={'marginBottom': '1rem'}),
                    html.Div([
                        html.Button([html.I(className="fas fa-arrow-up", style={'marginRight': '6px'}), "Start Aspirate"], 
                                   id='start-aspirate-btn', className='control-button success'),
                        html.Button([html.I(className="fas fa-arrow-down", style={'marginRight': '6px'}), "Start Dispense"], 
                                   id='start-dispense-btn', className='control-button info'),
                        html.Button([html.I(className="fas fa-stop", style={'marginRight': '6px'}), "Stop Flow"], 
                                   id='stop-flow-btn', className='control-button danger')
                    ], className='button-group')
                ])
            ], className='card layout-col'),
            
            # Volume Presets
            html.Div([
                html.H3([html.I(className="fas fa-flask", style={'marginRight': '8px'}), "Volume Presets"],
                        className='section-title'),
                html.P("Quick volume operations (aspirate):", 
                       style={'marginBottom': '1rem', 'color': 'var(--text-secondary)'}),
                html.Div([
                    html.Div(f"{vol} μL", 
                             id={'type': 'volume-preset', 'index': i}, 
                             className='quick-preset')
                    for i, vol in enumerate(controller.volume_presets)
                ])
            ], className='card layout-col')
        ], className='layout-row'),
        
        # System Operations
        html.Div([
            html.H3([html.I(className="fas fa-tools", style={'marginRight': '8px'}), "System Operations"],
                    className='section-title'),
            html.Div([
                html.Button([
                    html.I(className="fas fa-fill-drip", style={'marginRight': '8px'}),
                    "Prime System"
                ], id='prime-system-btn', className='control-button info'),
                
                html.Button([
                    html.I(className="fas fa-sync-alt", style={'marginRight': '8px'}),
                    "Purge System"
                ], id='purge-system-btn', className='control-button warning'),
                
                html.Button([
                    html.I(className="fas fa-home", style={'marginRight': '8px'}),
                    "Home Position"
                ], id='home-position-btn', className='control-button'),
                
                html.Button([
                    html.I(className="fas fa-question-circle", style={'marginRight': '8px'}),
                    "Query Status"
                ], id='query-status-quick-btn', className='control-button')
            ], className='button-group')
        ], className='card')
    ], style={'margin': '1.5rem', 'maxWidth': '1400px', 'marginLeft': 'auto', 'marginRight': 'auto'})


# Operation Log Layout
def create_operation_log_layout():
    return html.Div([
        html.H2([html.I(className="fas fa-clipboard-list", style={'marginRight': '10px'}), "Operation Log"],
                className='section-title', style={'marginBottom': '2rem'}),
        
        html.Div([
            html.Div([
                html.Button([
                    html.I(className="fas fa-download", style={'marginRight': '8px'}),
                    "Export CSV"
                ], id='export-log-btn', className='control-button info'),
                
                html.Button([
                    html.I(className="fas fa-trash", style={'marginRight': '8px'}),
                    "Clear Log"
                ], id='clear-log-btn', className='control-button danger'),
                
                dcc.Dropdown(
                    id='log-filter-dropdown',
                    options=[
                        {'label': 'All Messages', 'value': 'all'},
                        {'label': 'Info Only', 'value': 'info'},
                        {'label': 'Warnings Only', 'value': 'warning'},
                        {'label': 'Errors Only', 'value': 'error'}
                    ],
                    value='all',
                    style={'width': '150px', 'marginLeft': '1rem'}
                )
            ], className='button-group', style={'marginBottom': '1.5rem'}),
            
            html.Div(id='operation-log-display', className='operation-log')
        ], className='card')
    ], style={'margin': '1.5rem', 'maxWidth': '1400px', 'marginLeft': 'auto', 'marginRight': 'auto'})


@app.callback(
    Output('tab-content', 'children'),
    Input('main-tabs', 'value')
)
def update_tab_content(active_tab):
    if active_tab == 'dashboard':
        return create_dashboard_layout()
    elif active_tab == 'manual':
        return create_manual_control_layout()
    elif active_tab == 'quick':
        return create_quick_actions_layout()
    elif active_tab == 'method':
        return create_method_editor_layout()
    elif active_tab == 'config':
        return create_configuration_layout()
    elif active_tab == 'log':
        return create_operation_log_layout()
    return html.Div("Select a tab")


@app.callback(
    Output('connection-status', 'children'),
    Input('status-interval', 'n_intervals')
)
def update_connection_status(n):
    if controller.is_connected:
        return html.Span([
            html.I(className="fas fa-circle", style={'color': '#10b981', 'marginRight': '5px'}),
            f"Connected - {controller.status}"
        ], className='status-connected')
    else:
        return html.Span([
            html.I(className="fas fa-circle", style={'color': '#ef4444', 'marginRight': '5px'}),
            f"Disconnected - {controller.status}"
        ], className='status-disconnected')


@app.callback(
    [Output('pressure-display', 'children'),
     Output('flow-display', 'children'),
     Output('volume-display', 'children'),
     Output('pressure-status', 'children'),
     Output('flow-status', 'children'),
     Output('volume-status', 'children'),
     Output('pump-status-display-compact', 'children'),
     Output('pump-position-display', 'children'),
     Output('valve-status-display-compact', 'children'),
     Output('valve-flow-display', 'children'),
     Output('pump-progress', 'style'),
     Output('position-text', 'children'),
     Output('pid-diagram', 'children'),
     Output('operation-status-display', 'children')],
    Input('realtime-interval', 'n_intervals')
)
def update_metrics(n):
    controller.add_data_point()

    if controller.data_buffer['pressure']:
        pressure_val = controller.data_buffer['pressure'][-1]
        flow_val = controller.data_buffer['flow_rate'][-1]
        volume_val = controller.data_buffer['volume'][-1]
        
        pressure = f"{pressure_val:.1f} psi"
        flow = f"{flow_val:.2f} mL/min"
        volume = f"{volume_val:.0f} μL"
        
        # Status indicators
        pressure_status = "ALARM" if pressure_val > controller.pressure_limit else "Normal"
        flow_status = "Active" if abs(flow_val) > 0.1 else "Idle"
        volume_status = f"Total: {volume_val:.0f} μL"
        
        # Pump status
        pump_status = controller.operation_state.upper()
        pump_position_text = f"Pos: {controller.current_position:.0f}"
        
        # Valve status
        valve_status = controller.valve_position.upper()
        valve_flow_status = "Flow Active" if abs(flow_val) > 0.1 else "No Flow"
        
        # Pump position progress
        progress_percent = (controller.current_position / 6000) * 100
        pump_progress_style = {'width': f'{progress_percent}%'}
        position_text = f"Position: {controller.current_position:.0f} / 6000 ({progress_percent:.1f}%)"
        
    else:
        pressure = "0.0 psi"
        flow = "0.0 mL/min"
        volume = "0 μL"
        pressure_status = "Offline"
        flow_status = "Offline"
        volume_status = "Offline"
        pump_status = "OFFLINE"
        pump_position_text = "Pos: 0"
        valve_status = "UNKNOWN"
        valve_flow_status = "No Flow"
        pump_progress_style = {'width': '0%'}
        position_text = "Position: 0 / 6000 (0.0%)"
    
    # P&ID Diagram
    is_flow_active = abs(flow_val if 'flow_val' in locals() else 0) > 0.1
    is_pump_active = controller.operation_state in ['aspirating', 'dispensing']
    
    # Calculate syringe visual state
    syringe_fill_percent = (controller.current_position / 6000) * 100
    plunger_position = f"{syringe_fill_percent}%"
    liquid_height = f"{syringe_fill_percent}%"
    
    pid_diagram = html.Div([
        # Flow path from left to right
        html.Div([
            # Input section
            html.Div([
                html.Div("INLET", style={'fontSize': '0.7rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                html.Div(className=f"pid-valve {'active' if controller.valve_position == 'Input' else ''}", 
                         children="IN"),
            ], className='pid-component'),
            
            # Pipe from inlet to pump
            html.Div(className=f"pid-pipe {'flow-active' if is_flow_active and controller.valve_position == 'Input' else ''}", 
                     style={'width': '60px'}),
            
            # XLP 6000 Syringe Pump
            html.Div([
                html.Div([
                    # Syringe visual
                    html.Div([
                        html.Div(className='pid-syringe-plunger', 
                                style={'top': f"{100 - syringe_fill_percent}%"}),
                        html.Div(className='pid-syringe-liquid', 
                                style={'height': liquid_height})
                    ], className='pid-syringe'),
                    html.Div("SYRINGE", style={'fontSize': '0.7rem', 'fontWeight': '600', 'marginTop': '5px'})
                ]),
                html.Div([
                    html.Div(className=f"pid-pump {'active' if is_pump_active else ''}", 
                             children="XLP 6000"),
                    html.Div("PUMP", style={'fontSize': '0.7rem', 'fontWeight': '600', 'marginTop': '5px'})
                ])
            ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}, 
               className='pid-component'),
            
            # Pipe from pump to outlet valves
            html.Div(className=f"pid-pipe {'flow-active' if is_flow_active and controller.valve_position == 'Output' else ''}", 
                     style={'width': '60px'}),
            
            # Dual outlet valves
            html.Div([
                html.Div([
                    html.Div("OUTLET 1", style={'fontSize': '0.7rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                    html.Div(className=f"pid-valve {'active' if controller.valve_position == 'Output' else ''}", 
                             children="OUT1"),
                ], className='pid-component', style={'marginBottom': '20px'}),
                
                html.Div([
                    html.Div("OUTLET 2", style={'fontSize': '0.7rem', 'fontWeight': '600', 'marginBottom': '5px'}),
                    html.Div(className="pid-valve", children="OUT2"),
                ], className='pid-component'),
            ]),
            
            # Pipes to final outlets
            html.Div([
                html.Div(className=f"pid-pipe {'flow-active' if is_flow_active and controller.valve_position == 'Output' else ''}", 
                         style={'width': '40px', 'marginBottom': '20px'}),
                html.Div(className="pid-pipe", style={'width': '40px'}),
            ], style={'display': 'flex', 'flexDirection': 'column'}),
        ], className='pid-container'),
        
        # Status indicators
        html.Div([
            html.Div(f"Valve: {controller.valve_position}", style={
                'fontSize': '0.8rem', 'fontWeight': '600', 'marginRight': '15px'
            }),
            html.Div(f"Operation: {controller.operation_state.title()}", style={
                'fontSize': '0.8rem', 'fontWeight': '600', 'marginRight': '15px'
            }),
            html.Div(f"Syringe: {syringe_fill_percent:.1f}% Full", style={
                'fontSize': '0.8rem', 'fontWeight': '600'
            })
        ], style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '15px', 'flexWrap': 'wrap'})
    ])
    
    # Operation status
    operation_status = html.Div([
        html.Div([
            html.Span("Status: ", style={'fontWeight': '600'}),
            html.Span(controller.operation_state.title(), style={
                'color': '#059669' if controller.operation_state == 'idle' else '#d97706',
                'fontWeight': '700'
            })
        ], style={'marginBottom': '8px', 'fontSize': '0.875rem'}),
        html.Div([
            html.Span("Flow Mode: ", style={'fontWeight': '600'}),
            html.Span("Continuous" if controller.is_continuous_mode else "Discrete", style={
                'color': '#2563eb' if controller.is_continuous_mode else '#64748b'
            })
        ], style={'marginBottom': '8px', 'fontSize': '0.875rem'}),
        html.Div([
            html.Span("Target Flow: ", style={'fontWeight': '600'}),
            html.Span(f"{controller.target_flow_rate:.2f} mL/min")
        ], style={'fontSize': '0.875rem'}) if controller.target_flow_rate > 0 else html.Div()
    ])

    return (pressure, flow, volume, pressure_status, flow_status, volume_status,
            pump_status, pump_position_text, valve_status, valve_flow_status,
            pump_progress_style, position_text, pid_diagram, operation_status)


@app.callback(
    Output('realtime-chart', 'figure'),
    Input('realtime-interval', 'n_intervals')
)
def update_realtime_chart(n):
    if not controller.data_buffer['time']:
        return go.Figure()

    fig = go.Figure()

    times = list(controller.data_buffer['time'])

    fig.add_trace(go.Scatter(
        x=times,
        y=list(controller.data_buffer['pressure']),
        name='Pressure (psi)',
        line=dict(color='#3b82f6')
    ))

    fig.add_trace(go.Scatter(
        x=times,
        y=list(controller.data_buffer['flow_rate']),
        name='Flow Rate (mL/min)',
        line=dict(color='#10b981'),
        yaxis='y2'
    ))

    fig.update_layout(
        title="Real-time System Monitoring",
        xaxis_title="Time",
        yaxis=dict(title="Pressure (psi)", side="left"),
        yaxis2=dict(title="Flow Rate (mL/min)", side="right", overlaying="y"),
        height=400,
        showlegend=True,
        template="plotly_white"
    )

    return fig


@app.callback(
    [Output('port-dropdown', 'options'),
     Output('port-dropdown', 'value')],
    Input('main-tabs', 'value')  # Trigger when config tab is accessed
)
def update_port_options(active_tab):
    if active_tab == 'config':
        ports = controller.get_available_ports()
        options = [{'label': port, 'value': port} for port in ports]
        value = ports[0] if ports else None
        return options, value
    return [], None


# Manual control callbacks
@app.callback(
    Output('valve-input-btn', 'style'),
    Output('valve-output-btn', 'style'),
    Output('valve-bypass-btn', 'style'),
    Input('valve-input-btn', 'n_clicks'),
    Input('valve-output-btn', 'n_clicks'),
    Input('valve-bypass-btn', 'n_clicks')
)
def update_valve_buttons(input_clicks, output_clicks, bypass_clicks):
    ctx = callback_context
    base_style = {'margin': '5px', 'width': '80px'}
    active_style = {**base_style, 'background': '#10b981'}

    input_style = output_style = bypass_style = base_style

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'valve-input-btn':
            input_style = active_style
            controller.move_valve('Input')
        elif button_id == 'valve-output-btn':
            output_style = active_style
            controller.move_valve('Output')
        elif button_id == 'valve-bypass-btn':
            bypass_style = active_style
            controller.move_valve('Bypass')
    else:
        # Default to bypass active
        bypass_style = active_style

    return input_style, output_style, bypass_style


@app.callback(
    Output('aspirate-btn', 'children'),
    Input('aspirate-btn', 'n_clicks'),
    State('volume-input', 'value')
)
def handle_aspirate(n_clicks, volume):
    if n_clicks and volume:
        controller.aspirate(volume)
        return [html.I(className="fas fa-arrow-up"), f" Aspirated {volume}μL"]
    return [html.I(className="fas fa-arrow-up"), " Aspirate"]


@app.callback(
    Output('dispense-btn', 'children'),
    Input('dispense-btn', 'n_clicks'),
    State('volume-input', 'value')
)
def handle_dispense(n_clicks, volume):
    if n_clicks and volume:
        controller.dispense(volume)
        return [html.I(className="fas fa-arrow-down"), f" Dispensed {volume}μL"]
    return [html.I(className="fas fa-arrow-down"), " Dispense"]


@app.callback(
    Output('move-absolute-btn', 'children'),
    Input('move-absolute-btn', 'n_clicks'),
    State('absolute-position-input', 'value')
)
def handle_absolute_move(n_clicks, position):
    if n_clicks and position is not None:
        controller.move_syringe_absolute(position)
        return f"Moved to {position}"
    return "Move"


# Configuration callbacks
@app.callback(
    Output('connect-btn', 'children'),
    Input('connect-btn', 'n_clicks'),
    State('port-dropdown', 'value'),
    State('baud-dropdown', 'value'),
    State('pump-address-input', 'value')
)
def handle_connect(n_clicks, port, baud, address):
    if n_clicks and port:
        controller.pump_address = address or 1
        if controller.connect(port, baud):
            return [html.I(className="fas fa-check"), " Connected"]
        else:
            return [html.I(className="fas fa-times"), " Connection Failed"]
    return "Connect"


@app.callback(
    Output('disconnect-btn', 'children'),
    Input('disconnect-btn', 'n_clicks')
)
def handle_disconnect(n_clicks):
    if n_clicks:
        controller.disconnect()
        return [html.I(className="fas fa-check"), " Disconnected"]
    return "Disconnect"


@app.callback(
    Output('command-history-display', 'children'),
    Input('realtime-interval', 'n_intervals')
)
def update_command_history(n):
    if not controller.command_history:
        return html.Div("No recent commands", style={'color': 'var(--text-secondary)', 'fontStyle': 'italic'})

    history_items = []
    for cmd in list(controller.command_history)[-6:]:  # Show last 6 commands
        history_items.append(
            html.Div([
                html.Div([
                    html.Code(cmd['command'], style={
                        'fontFamily': 'Fira Code, monospace', 
                        'fontSize': '0.75rem',
                        'background': 'rgba(37, 99, 235, 0.1)',
                        'padding': '2px 6px',
                        'borderRadius': '4px',
                        'color': 'var(--primary-color)'
                    }),
                    html.Small(cmd['timestamp'], style={
                        'color': 'var(--text-secondary)', 
                        'marginLeft': '8px',
                        'fontSize': '0.7rem'
                    })
                ])
            ], style={
                'marginBottom': '6px', 
                'padding': '6px', 
                'background': 'rgba(248, 249, 250, 0.5)', 
                'borderRadius': '4px',
                'border': '1px solid var(--border-color)'
            })
        )

    return history_items


@app.callback(
    Output('pump-status-display', 'children'),
    Input('status-interval', 'n_intervals')
)
def update_pump_status(n):
    status_items = [
        {'label': 'Pump Address', 'value': str(controller.pump_address), 'icon': 'fas fa-hashtag'},
        {'label': 'Syringe Size', 'value': f"{controller.syringe_size} mL", 'icon': 'fas fa-flask'},
        {'label': 'Communication', 'value': f"{controller.baud_rate} baud", 'icon': 'fas fa-wifi'},
        {'label': 'Top Speed', 'value': f"{controller.speed_settings['top_speed']} steps/sec", 'icon': 'fas fa-tachometer-alt'},
        {'label': 'Safety Limit', 'value': f"{controller.pressure_limit} psi", 'icon': 'fas fa-shield-alt'},
    ]
    
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=item['icon'], style={'marginRight': '8px', 'color': 'var(--primary-color)', 'width': '16px'}),
                html.Span(item['label'], style={'fontWeight': '600', 'fontSize': '0.875rem'})
            ], style={'marginBottom': '4px'}),
            html.Div(item['value'], style={'marginLeft': '24px', 'color': 'var(--text-secondary)', 'fontSize': '0.875rem'})
        ], style={'marginBottom': '12px'}) for item in status_items
    ])


# Additional callbacks for new functionality
@app.callback(
    Output('emergency-stop-btn', 'children'),
    Input('emergency-stop-btn', 'n_clicks')
)
def handle_emergency_stop(n_clicks):
    if n_clicks:
        controller.emergency_stop()
        return [html.I(className="fas fa-stop"), " STOPPED"]
    return [html.I(className="fas fa-stop"), " EMERGENCY STOP"]


@app.callback(
    [Output('start-aspirate-btn', 'children'),
     Output('start-dispense-btn', 'children')],
    [Input('start-aspirate-btn', 'n_clicks'),
     Input('start-dispense-btn', 'n_clicks')],
    State('custom-flow-input', 'value')
)
def handle_continuous_flow(aspirate_clicks, dispense_clicks, flow_rate):
    ctx = callback_context
    if ctx.triggered and flow_rate:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'start-aspirate-btn' and aspirate_clicks:
            controller.start_continuous_flow(flow_rate, "aspirate")
            return [html.I(className="fas fa-arrow-up"), f" Aspirating {flow_rate} mL/min"], [html.I(className="fas fa-arrow-down"), " Start Dispense"]
        elif button_id == 'start-dispense-btn' and dispense_clicks:
            controller.start_continuous_flow(flow_rate, "dispense")
            return [html.I(className="fas fa-arrow-up"), " Start Aspirate"], [html.I(className="fas fa-arrow-down"), f" Dispensing {flow_rate} mL/min"]
    
    return [html.I(className="fas fa-arrow-up"), " Start Aspirate"], [html.I(className="fas fa-arrow-down"), " Start Dispense"]


@app.callback(
    Output('stop-flow-btn', 'children'),
    Input('stop-flow-btn', 'n_clicks')
)
def handle_stop_flow(n_clicks):
    if n_clicks:
        controller.stop_continuous_flow()
        return [html.I(className="fas fa-stop"), " Flow Stopped"]
    return [html.I(className="fas fa-stop"), " Stop Flow"]


@app.callback(
    Output('prime-system-btn', 'children'),
    Input('prime-system-btn', 'n_clicks')
)
def handle_prime_system(n_clicks):
    if n_clicks:
        controller.prime_system()
        return [html.I(className="fas fa-check"), " System Primed"]
    return [html.I(className="fas fa-fill-drip"), " Prime System"]


@app.callback(
    Output('purge-system-btn', 'children'),
    Input('purge-system-btn', 'n_clicks')
)
def handle_purge_system(n_clicks):
    if n_clicks:
        controller.purge_system()
        return [html.I(className="fas fa-check"), " System Purged"]
    return [html.I(className="fas fa-sync-alt"), " Purge System"]


@app.callback(
    Output('home-position-btn', 'children'),
    Input('home-position-btn', 'n_clicks')
)
def handle_home_position(n_clicks):
    if n_clicks:
        controller.move_syringe_absolute(0)
        return [html.I(className="fas fa-check"), " At Home"]
    return [html.I(className="fas fa-home"), " Home Position"]


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
