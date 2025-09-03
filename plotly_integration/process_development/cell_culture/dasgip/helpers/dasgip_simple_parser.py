"""
Simplified DASGIP CSV Parser - Focus on working implementation
"""

import csv
import re
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class DasgipSimpleParser:
    """Simple parser for DASGIP bioreactor export CSV files"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.sections = {}
        self.units = []
        self.tracks = []
        self.project_info = []
        self.info_section = {}
        
    def parse(self):
        """Parse the file and extract key information"""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
        
        # Find section boundaries
        section_starts = {}
        for i, line in enumerate(lines):
            line_clean = line.strip().strip('"')
            if line_clean in ['[Info]', '[CoreInfo]', '[ProjectInfo]', '[TrackInfo]']:
                section_starts[line_clean.strip('[]')] = i
        
        # Parse project info to find units
        if 'ProjectInfo' in section_starts:
            start = section_starts['ProjectInfo']
            # Find header line
            header_line = None
            data_lines = []
            
            for i in range(start + 1, len(lines)):
                line = lines[i].strip()
                if not line:
                    continue
                if line.startswith('"[TrackInfo]"'):
                    break
                    
                if header_line is None and 'ProjName' in line:
                    header_line = line
                elif header_line is not None:
                    data_lines.append(line)
            
            
            if header_line and data_lines:
                headers = [h.strip('"') for h in header_line.split(';')]
                
                for j, data_line in enumerate(data_lines):
                    values = [v.strip('"') for v in data_line.split(';')]
                    
                    # Pad values to match header length
                    while len(values) < len(headers):
                        values.append('')
                    
                    row_dict = dict(zip(headers, values))
                    
                    # Look for unit number in parameters
                    unit_no = None
                    for i in range(1, 21):
                        param_key = f'Parameter{i}'
                        if param_key in row_dict and row_dict[param_key]:
                            if 'UnitNo=' in row_dict[param_key]:
                                match = re.search(r'UnitNo=(\d+)', row_dict[param_key])
                                if match:
                                    unit_no = int(match.group(1))
                                    break
                    
                    if unit_no:
                        self.units.append({
                            'unit_number': unit_no,
                            'setup_name': row_dict.get('LocName', f'Unit {unit_no}'),
                            'location_name': row_dict.get('LocNamePar', ''),
                            'start_timestamp': self._parse_datetime(row_dict.get('StartTimestamp', '')),
                            'stop_timestamp': self._parse_datetime(row_dict.get('StopTimestamp', '')),
                            'guid': row_dict.get('Guid', ''),
                            'module_name': row_dict.get('ProjName', '')
                        })
        
        # Parse track info
        if 'TrackInfo' in section_starts:
            start = section_starts['TrackInfo']
            header_line = None
            data_lines = []
            
            for i in range(start + 1, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('"['):
                    if line.startswith('"['):  # Next section
                        break
                    continue
                
                # Look for actual data start (timestamp format)
                if re.match(r'\d{4}-\d{2}-\d{2}', line):
                    # This is where data starts
                    self.data_start_line = i
                    break
                    
                if header_line is None and 'ProjName' in line:
                    header_line = line
                elif header_line is not None:
                    data_lines.append(line)
            
            if header_line and data_lines:
                headers = [h.strip('"') for h in header_line.split(';')]
                
                for data_line in data_lines:
                    values = [v.strip('"') for v in data_line.split(';')]
                    if len(values) >= len(headers):
                        row_dict = dict(zip(headers, values))
                        
                        # Skip timestamp/duration tracks
                        if 'Timestamp' in row_dict.get('ProjName', '') or 'Duration' in row_dict.get('ProjName', ''):
                            continue
                        
                        # Find which unit this track belongs to
                        module_name = row_dict.get('Module', '')
                        unit_no = None
                        for unit in self.units:
                            if unit['module_name'] in module_name:
                                unit_no = unit['unit_number']
                                break
                        
                        if unit_no:
                            # Extract parameter name and check if it's one we want to store
                            loc_name = row_dict.get('LocName', '')
                            param_name = loc_name.split('.')[-1] if '.' in loc_name else loc_name
                            
                            # Map to our desired parameters
                            mapped_param = self._map_parameter_name(loc_name, unit_no)
                            
                            if mapped_param:  # Only store parameters we're interested in
                                self.tracks.append({
                                    'unit_number': unit_no,
                                    'parameter_name': mapped_param['name'],
                                    'parameter_label': mapped_param['label'],
                                    'location_name': loc_name,
                                    'description': row_dict.get('LocComment', ''),
                                    'unit_of_measurement': mapped_param['unit'],
                                    'module': module_name,
                                    'track_index': len(self.tracks),
                                    'original_column': loc_name
                                })
        
        return True
    
    def _map_parameter_name(self, location_name: str, unit_number: int) -> Optional[Dict]:
        """Map DASGIP location names to our standardized parameter names"""
        
        # Define the parameter mappings based on DASGIP naming convention
        # The location_name typically looks like "Unit X.ParameterName.Type"
        parameter_mappings = {
            # Dissolved Oxygen
            'DO.PV': {'name': 'do_pv', 'label': 'DO Process Value', 'unit': '% DO'},
            'DO.SP': {'name': 'do_sp', 'label': 'DO Setpoint', 'unit': '% DO'},
            'DO.Out': {'name': 'do_out', 'label': 'DO Controller Output', 'unit': '%'},
            
            # pH
            'pH.PV': {'name': 'ph_pv', 'label': 'pH Process Value', 'unit': 'pH'},
            'pH.SP': {'name': 'ph_sp', 'label': 'pH Setpoint', 'unit': 'pH'},
            'pH.Out': {'name': 'ph_out', 'label': 'pH Controller Output', 'unit': '%'},
            
            # Temperature
            'T.PV': {'name': 'temp_pv', 'label': 'Temperature Process Value', 'unit': '°C'},
            'T.SP': {'name': 'temp_sp', 'label': 'Temperature Setpoint', 'unit': '°C'},
            'T.Out': {'name': 'temp_out', 'label': 'Temperature Controller Output', 'unit': '%'},
            
            # Agitation Speed
            'N.PV': {'name': 'rpm_pv', 'label': 'Agitation Speed Process Value', 'unit': 'RPM'},
            'N.SP': {'name': 'rpm_sp', 'label': 'Agitation Speed Setpoint', 'unit': 'RPM'},
            
            # Volume
            'V.VPV': {'name': 'volume_pv', 'label': 'Reactor Volume', 'unit': 'mL'},
            
            # Air Flow
            'FAir.PV': {'name': 'air_flow_pv', 'label': 'Air Flow Process Value', 'unit': 'sL/h'},
            'FAir.SP': {'name': 'air_flow_sp', 'label': 'Air Flow Setpoint', 'unit': 'sL/h'},
            
            # Feed A Flow
            'FA.PV': {'name': 'feed_a_pv', 'label': 'Feed A Flow Process Value', 'unit': 'mL/h'},
            'FA.SP': {'name': 'feed_a_sp', 'label': 'Feed A Flow Setpoint', 'unit': 'mL/h'},
            
            # Feed B Flow
            'FB.PV': {'name': 'feed_b_pv', 'label': 'Feed B Flow Process Value', 'unit': 'mL/h'},
            'FB.SP': {'name': 'feed_b_sp', 'label': 'Feed B Flow Setpoint', 'unit': 'mL/h'},
            
            # O2 Concentration
            'XO2.PV': {'name': 'o2_conc_pv', 'label': 'O2 Concentration Process Value', 'unit': '%'},
            'XO2.SP': {'name': 'o2_conc_sp', 'label': 'O2 Concentration Setpoint', 'unit': '%'},
            
            # CO2 Concentration
            'XCO2.PV': {'name': 'co2_conc_pv', 'label': 'CO2 Concentration Process Value', 'unit': '%'},
            'XCO2.SP': {'name': 'co2_conc_sp', 'label': 'CO2 Concentration Setpoint', 'unit': '%'},
        }
        
        # Extract the parameter part from location name
        # Format is typically "Unit X.ParameterName" or "Unit X.ParamName.SubType"
        if '.' in location_name:
            parts = location_name.split('.')
            if len(parts) >= 2:
                # Try different combinations
                param_part = '.'.join(parts[1:])  # Everything after "Unit X"
                
                # Check direct match first
                if param_part in parameter_mappings:
                    return parameter_mappings[param_part]
                
                # Try last two parts (for cases like "Unit 1.pH1.PV" -> "pH.PV")
                if len(parts) >= 3:
                    # Remove the unit number from parameter name (pH1 -> pH)
                    param_name = ''.join(c for c in parts[-2] if not c.isdigit())
                    param_type = parts[-1]
                    combined = f"{param_name}.{param_type}"
                    
                    if combined in parameter_mappings:
                        return parameter_mappings[combined]
        
        return None
    
    def get_experiment_info(self) -> Dict:
        """Get basic experiment information"""
        # Try to extract project name from actual data
        project_name = 'Unknown'
        host = 'Unknown'
        
        # Look in project info for main project
        for project in self.project_info:
            proj_name = project.get('ProjName', '')
            if proj_name and not proj_name.startswith('Module'):
                project_name = proj_name
                break
        
        # Try to get host from info section or filename
        if hasattr(self, 'info_section') and 'host' in self.info_section:
            host = self.info_section['host']
        elif hasattr(self, 'file_path'):
            # Extract from filename
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
        """Get sample data for a unit"""
        unit_tracks = self.get_unit_tracks(unit_number)
        if not unit_tracks:
            return pd.DataFrame()
        
        # Create column mapping
        columns = ['timestamp', 'duration']
        column_mapping = {}  # Maps parameter name to original column name
        
        for track in unit_tracks:
            columns.append(track['parameter_name'])
            column_mapping[track['parameter_name']] = track['original_column']
        
        # Read some data lines
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
            
            # Find data start (look for timestamp pattern)
            data_start = None
            for i, line in enumerate(lines):
                if re.match(r'\d{4}-\d{2}-\d{2}', line.strip()):
                    data_start = i
                    break
            
            if data_start is None:
                return pd.DataFrame(columns=columns)
            
            # Read sample data
            data_rows = []
            for i in range(data_start, min(data_start + max_rows, len(lines))):
                line = lines[i].strip()
                if not line:
                    continue
                
                values = line.split(';')
                if len(values) >= 2:
                    # Get timestamp and duration
                    row_data = [values[0].strip('"'), values[1].strip('"')]
                    
                    # Add track values (this is simplified - would need proper column mapping)
                    for j, track in enumerate(unit_tracks):
                        if j + 2 < len(values):
                            row_data.append(values[j + 2].strip('"'))
                        else:
                            row_data.append('')
                    
                    data_rows.append(row_data)
            
            # Create DataFrame
            if data_rows:
                df = pd.DataFrame(data_rows, columns=columns)
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
                
                # Convert numeric columns
                for col in columns[2:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
            
        except Exception as e:
            print(f"Error reading data: {e}")
        
        return pd.DataFrame(columns=columns)
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime string"""
        if not dt_str or dt_str == '':
            return None
        
        try:
            dt_str = dt_str.strip('"')
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None