"""
DASGIP CSV File Parser - Final Version
Handles multiple data sections for multiple units
"""

import csv
import re
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class DasgipFinalParser:
    """Final parser that handles multiple data sections for multiple units"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.units = []
        self.tracks = []
        self.project_info = []
        self.info_section = {}
        self.data_sections = {}  # unit_number -> {'header_line': int, 'columns': list}
        
    def parse(self):
        """Parse the file and extract all units and their data"""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
        
        # Find all data sections
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Look for data header lines with unit information
            if 'Timestamp' in line_stripped and 'Duration' in line_stripped and 'Unit ' in line_stripped:
                # Extract unit number from the first Unit column
                columns = [col.strip('"') for col in line_stripped.split(';')]
                
                # Find the first Unit column to determine which unit this section is for
                unit_no = None
                for col in columns:
                    if col.startswith('Unit '):
                        match = re.match(r'Unit (\d+)\.', col)
                        if match:
                            unit_no = int(match.group(1))
                            break
                
                if unit_no:
                    self.data_sections[unit_no] = {
                        'header_line': i,
                        'columns': columns
                    }
        
        # Extract units and parameters from all data sections
        for unit_no, section_info in self.data_sections.items():
            self._extract_unit_data(unit_no, section_info['columns'])
        
        # Parse basic project info
        self._parse_basic_project_info(lines)
        
        return len(self.units) > 0
    
    def _extract_unit_data(self, unit_no: int, columns: List[str]):
        """Extract unit and parameter information from data columns"""
        
        # Get actual timestamps from data
        start_time, stop_time = self._get_unit_time_range(unit_no)
        
        # Create unit record
        self.units.append({
            'unit_number': unit_no,
            'setup_name': f'Setup {unit_no}',
            'location_name': '',
            'start_timestamp': start_time,
            'stop_timestamp': stop_time,
            'guid': '',
            'module_name': f'Unit_{unit_no}'
        })
        
        # Extract parameters from columns
        for col in columns:
            # Skip timestamp and duration
            if col in ['Timestamp', 'Duration']:
                continue
            
            # Look for "Unit X.ParameterName" pattern
            match = re.match(rf'Unit {unit_no}\.(.+)', col)
            if match:
                param_full = match.group(1)
                
                # Extract parameter name and unit
                # Format: "DO1.PV [%DO]" or "pH1.PV [pH]"
                unit_match = re.match(r'(.+?)\s*\[(.+?)\]', param_full)
                if unit_match:
                    param_name = unit_match.group(1)
                    unit_measure = unit_match.group(2)
                else:
                    param_name = param_full
                    unit_measure = ''
                
                # Map to our desired parameters
                mapped_param = self._map_parameter_name(param_name)
                if mapped_param:
                    track_info = {
                        'unit_number': unit_no,
                        'parameter_name': mapped_param['name'],
                        'parameter_label': mapped_param['label'],
                        'location_name': col,
                        'unit_of_measurement': mapped_param['unit'],
                        'original_column': col
                    }
                    self.tracks.append(track_info)
    
    def _get_unit_time_range(self, unit_no: int):
        """Get actual start and stop timestamps from unit data"""
        from datetime import datetime
        import pandas as pd
        
        # Default timestamps if no data found
        default_time = datetime.now()
        
        if unit_no not in self.data_sections:
            return default_time, default_time
        
        section_info = self.data_sections[unit_no]
        header_line = section_info['header_line']
        
        try:
            # Read first and last data lines for this unit
            start_line = header_line + 1
            
            # Find the end of this unit's data
            end_line = len(self.lines)
            for other_unit, other_section in self.data_sections.items():
                if other_unit != unit_no and other_section['header_line'] > header_line:
                    end_line = min(end_line, other_section['header_line'])
            
            # Get first valid timestamp
            start_timestamp = None
            for i in range(start_line, min(start_line + 100, end_line)):
                if i >= len(self.lines):
                    break
                line = self.lines[i].strip()
                if not line or line.startswith('"Timestamp'):
                    continue
                values = line.split(';')
                if len(values) > 0:
                    timestamp_str = values[0].strip('"')
                    if timestamp_str and timestamp_str != 'Timestamp':
                        try:
                            start_timestamp = pd.to_datetime(timestamp_str)
                            break
                        except:
                            continue
            
            # Get last valid timestamp
            stop_timestamp = None
            for i in range(max(end_line - 100, start_line), end_line):
                if i >= len(self.lines):
                    break
                line = self.lines[i].strip()
                if not line or line.startswith('"Timestamp'):
                    continue
                values = line.split(';')
                if len(values) > 0:
                    timestamp_str = values[0].strip('"')
                    if timestamp_str and timestamp_str != 'Timestamp':
                        try:
                            stop_timestamp = pd.to_datetime(timestamp_str)
                        except:
                            continue
            
            # Return found timestamps or defaults
            if start_timestamp and stop_timestamp:
                return start_timestamp, stop_timestamp
            elif start_timestamp:
                return start_timestamp, start_timestamp
            else:
                return default_time, default_time
                
        except Exception as e:
            print(f"Error getting time range for unit {unit_no}: {e}")
            return default_time, default_time
    
    def _parse_basic_project_info(self, lines):
        """Parse basic project information"""
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if line_stripped in ['"[ProjectInfo]"', '[ProjectInfo]']:
                # Found project info section - parse main project
                for j in range(i + 1, min(i + 10, len(lines))):
                    proj_line = lines[j].strip()
                    if proj_line and not proj_line.startswith('"['):
                        parts = proj_line.split(';')
                        if len(parts) > 0:
                            proj_name = parts[0].strip('"')
                            if proj_name and not proj_name.startswith('Module'):
                                self.project_info.append({'ProjName': proj_name})
                        break
                break
    
    def _map_parameter_name(self, param_name: str) -> Optional[Dict]:
        """Map DASGIP parameter names to our standardized names"""
        
        parameter_mappings = {
            # Dissolved Oxygen
            'DO1.Out': {'name': 'do_out', 'label': 'DO Controller Output', 'unit': '%'},
            'DO1.PV': {'name': 'do_pv', 'label': 'DO Process Value', 'unit': '% DO'},
            'DO1.SP': {'name': 'do_sp', 'label': 'DO Setpoint', 'unit': '% DO'},
            
            # pH
            'pH1.Out': {'name': 'ph_out', 'label': 'pH Controller Output', 'unit': '%'},
            'pH1.PV': {'name': 'ph_pv', 'label': 'pH Process Value', 'unit': 'pH'},
            'pH1.SP': {'name': 'ph_sp', 'label': 'pH Setpoint', 'unit': 'pH'},
            
            # Temperature
            'T1.Out': {'name': 'temp_out', 'label': 'Temperature Controller Output', 'unit': '%'},
            'T1.PV': {'name': 'temp_pv', 'label': 'Temperature Process Value', 'unit': '°C'},
            'T1.SP': {'name': 'temp_sp', 'label': 'Temperature Setpoint', 'unit': '°C'},
            
            # Agitation Speed
            'N1.PV': {'name': 'rpm_pv', 'label': 'Agitation Speed Process Value', 'unit': 'RPM'},
            'N1.SP': {'name': 'rpm_sp', 'label': 'Agitation Speed Setpoint', 'unit': 'RPM'},
            
            # Volume
            'V1.VPV': {'name': 'volume_pv', 'label': 'Reactor Volume', 'unit': 'mL'},
            
            # Air Flow
            'FAir1.PV': {'name': 'air_flow_pv', 'label': 'Air Flow Process Value', 'unit': 'sL/h'},
            'FAir1.SP': {'name': 'air_flow_sp', 'label': 'Air Flow Setpoint', 'unit': 'sL/h'},
            
            # Feed A Flow
            'FA1.PV': {'name': 'feed_a_pv', 'label': 'Feed A Flow Process Value', 'unit': 'mL/h'},
            'FA1.SP': {'name': 'feed_a_sp', 'label': 'Feed A Flow Setpoint', 'unit': 'mL/h'},
            
            # Feed B Flow
            'FB1.PV': {'name': 'feed_b_pv', 'label': 'Feed B Flow Process Value', 'unit': 'mL/h'},
            'FB1.SP': {'name': 'feed_b_sp', 'label': 'Feed B Flow Setpoint', 'unit': 'mL/h'},
            
            # O2 Concentration
            'XO21.PV': {'name': 'o2_conc_pv', 'label': 'O2 Concentration Process Value', 'unit': '%'},
            'XO21.SP': {'name': 'o2_conc_sp', 'label': 'O2 Concentration Setpoint', 'unit': '%'},
            
            # CO2 Concentration
            'XCO21.PV': {'name': 'co2_conc_pv', 'label': 'CO2 Concentration Process Value', 'unit': '%'},
            'XCO21.SP': {'name': 'co2_conc_sp', 'label': 'CO2 Concentration Setpoint', 'unit': '%'},
        }
        
        # Direct mapping first
        if param_name in parameter_mappings:
            return parameter_mappings[param_name]
        
        # Try different unit numbers (DO2, DO3, etc. -> DO1)
        for unit_num in range(1, 9):
            if re.search(rf'{unit_num}\.', param_name):
                # Replace unit number with 1 and try mapping
                base_param = re.sub(rf'{unit_num}\.', '1.', param_name)
                if base_param in parameter_mappings:
                    return parameter_mappings[base_param]
        
        return None
    
    def get_experiment_info(self) -> Dict:
        """Get basic experiment information"""
        project_name = 'Unknown'
        host = 'Unknown'
        
        # Try to get project name
        if self.project_info:
            project_name = self.project_info[0].get('ProjName', 'Unknown')
        
        # Extract host from filename
        if self.file_path:
            import os
            filename = os.path.basename(self.file_path)
            if 'CTPCNK808814' in filename:
                host = 'CTPCNK808814'
        
        return {
            'project_name': project_name,
            'host': host,
            'units_count': len(self.units),
            'tracks_count': len(self.tracks)
        }
    
    def get_units_info(self) -> List[Dict]:
        """Get all units information"""
        return sorted(self.units, key=lambda x: x['unit_number'])
    
    def get_unit_tracks(self, unit_number: int) -> List[Dict]:
        """Get tracks for a specific unit"""
        return [track for track in self.tracks if track['unit_number'] == unit_number]
    
    def get_sample_data(self, unit_number: int, max_rows: int = 100) -> pd.DataFrame:
        """Get sample data for a specific unit"""
        unit_tracks = self.get_unit_tracks(unit_number)
        if not unit_tracks or unit_number not in self.data_sections:
            return pd.DataFrame()
        
        section_info = self.data_sections[unit_number]
        header_line = section_info['header_line']
        columns_list = section_info['columns']
        
        # Create column mapping
        columns = ['timestamp', 'duration']
        col_indices = {'timestamp': 0, 'duration': 1}  # Timestamp and Duration are first
        
        # Map our parameter names to column indices
        for track in unit_tracks:
            columns.append(track['parameter_name'])
            # Find the column index in data_columns
            try:
                col_index = columns_list.index(track['original_column'])
                col_indices[track['parameter_name']] = col_index
            except ValueError:
                continue
        
        # Read data for this specific unit
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
            
            data_rows = []
            start_line = header_line + 1  # Skip header
            
            # Find the end of this unit's data (next unit header or end of file)
            end_line = len(lines)
            for other_unit, other_section in self.data_sections.items():
                if other_unit != unit_number and other_section['header_line'] > header_line:
                    end_line = min(end_line, other_section['header_line'])
            
            # Limit to max_rows if specified
            if max_rows:
                end_line = min(start_line + max_rows, end_line)
            
            for i in range(start_line, end_line):
                if i >= len(lines):
                    break
                    
                line = lines[i].strip()
                if not line or line.startswith('"Timestamp'):
                    continue
                
                values = line.split(';')
                row_data = {}
                
                # Get all values we're interested in
                for col_name, col_idx in col_indices.items():
                    if col_idx < len(values):
                        row_data[col_name] = values[col_idx].strip('"')
                    else:
                        row_data[col_name] = ''
                
                # Only add rows with valid timestamp
                if row_data.get('timestamp') and row_data['timestamp'] not in ['', 'Timestamp']:
                    data_rows.append([row_data.get(col, '') for col in columns])
            
            # Create DataFrame
            if data_rows:
                df = pd.DataFrame(data_rows, columns=columns)
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
                
                # Convert parameter columns to numeric
                for col in columns[2:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
            
        except Exception as e:
            print(f"Error reading data for unit {unit_number}: {e}")
        
        return pd.DataFrame(columns=columns)