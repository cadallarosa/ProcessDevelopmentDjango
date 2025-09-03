"""
DASGIP CSV File Parser V2 - Improved parsing for actual file format
"""

import csv
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from io import StringIO


class DasgipParserV2:
    """Improved parser for DASGIP bioreactor export CSV files"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_lines = []
        self.info_section = {}
        self.core_info = {}
        self.project_info = []
        self.track_info = []
        self.data_section_start = 0
        self.units_data = {}
        
    def parse(self):
        """Main parsing method"""
        # Read file with proper encoding
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as file:
            self.raw_lines = file.readlines()
        
        # Find section boundaries
        sections = self._identify_sections()
        
        # Parse each section
        if 'info' in sections:
            self._parse_info_section(sections['info'])
        
        if 'core_info' in sections:
            self._parse_core_info(sections['core_info'])
            
        if 'project_info' in sections:
            self._parse_project_info(sections['project_info'])
            
        if 'track_info' in sections:
            self._parse_track_info(sections['track_info'])
            
        if 'data' in sections:
            self.data_section_start = sections['data'][0]
            
        # Organize units
        self._organize_units()
        
        return self.get_parsed_data()
    
    def _identify_sections(self) -> Dict[str, Tuple[int, int]]:
        """Identify line ranges for each section"""
        sections = {}
        current_section = None
        start_line = 0
        
        for i, line in enumerate(self.raw_lines):
            line_stripped = line.strip()
            
            if line_stripped in ['"[Info]"', '[Info]']:
                if current_section:
                    sections[current_section] = (start_line, i-1)
                current_section = 'info'
                start_line = i + 1
                
            elif line_stripped in ['"[CoreInfo]"', '[CoreInfo]']:
                if current_section:
                    sections[current_section] = (start_line, i-1)
                current_section = 'core_info'
                start_line = i + 1
                
            elif line_stripped in ['"[ProjectInfo]"', '[ProjectInfo]']:
                if current_section:
                    sections[current_section] = (start_line, i-1)
                current_section = 'project_info'
                start_line = i + 1
                
            elif line_stripped in ['"[TrackInfo]"', '[TrackInfo]']:
                if current_section:
                    sections[current_section] = (start_line, i-1)
                current_section = 'track_info'
                start_line = i + 1
                
            elif current_section == 'track_info' and line_stripped and not line_stripped.startswith('"'):
                # Data section starts after track info when we see actual data
                # Check if this looks like a data row (starts with a date)
                if re.match(r'\d{4}-\d{2}-\d{2}', line_stripped):
                    sections[current_section] = (start_line, i-1)
                    sections['data'] = (i, len(self.raw_lines)-1)
                    break
        
        # Handle last section
        if current_section and current_section not in sections:
            sections[current_section] = (start_line, len(self.raw_lines)-1)
            
        return sections
    
    def _parse_info_section(self, line_range: Tuple[int, int]):
        """Parse the [Info] section"""
        start, end = line_range
        
        # First line should be headers
        if start <= end:
            # Parse the main info line
            for i in range(start, min(end + 1, len(self.raw_lines))):
                line = self.raw_lines[i].strip()
                if not line:
                    continue
                    
                parts = line.split(';')
                if len(parts) >= 7 and parts[0] == '"FngArchiv"':
                    # Main info line
                    self.info_section = {
                        'product': parts[0].strip('"'),
                        'version': parts[1].strip('"'),
                        'host': parts[2].strip('"'),
                        'timestamp': parts[3].strip('"'),
                        'author': parts[4].strip('"') if len(parts) > 4 else '',
                        'connection': parts[5].strip('"') if len(parts) > 5 else '',
                        'application': parts[6].strip('"') if len(parts) > 6 else ''
                    }
                    break
    
    def _parse_core_info(self, line_range: Tuple[int, int]):
        """Parse the [CoreInfo] section"""
        start, end = line_range
        
        for i in range(start, min(end + 1, len(self.raw_lines))):
            line = self.raw_lines[i].strip()
            if not line or line.startswith('"Product"'):
                continue
                
            parts = line.split(';')
            if len(parts) >= 2:
                key = parts[0].strip('"')
                value = parts[1].strip('"') if len(parts) > 1 else ''
                self.core_info[key] = value
    
    def _parse_project_info(self, line_range: Tuple[int, int]):
        """Parse the [ProjectInfo] section"""
        start, end = line_range
        
        # First line should be headers
        if start <= end:
            header_line = self.raw_lines[start].strip()
            headers = [h.strip('"') for h in header_line.split(';')]
            
            # Parse data rows
            for i in range(start + 1, min(end + 1, len(self.raw_lines))):
                line = self.raw_lines[i].strip()
                if not line:
                    continue
                    
                values = [v.strip('"') for v in line.split(';')]
                if len(values) >= len(headers):
                    project = dict(zip(headers, values))
                    self.project_info.append(project)
    
    def _parse_track_info(self, line_range: Tuple[int, int]):
        """Parse the [TrackInfo] section"""
        start, end = line_range
        
        # First line should be headers
        if start <= end:
            header_line = self.raw_lines[start].strip()
            headers = [h.strip('"') for h in header_line.split(';')]
            
            # Parse data rows
            for i in range(start + 1, min(end + 1, len(self.raw_lines))):
                line = self.raw_lines[i].strip()
                if not line:
                    continue
                    
                values = [v.strip('"') for v in line.split(';')]
                if len(values) >= len(headers):
                    track = dict(zip(headers, values[:len(headers)]))
                    self.track_info.append(track)
    
    def _organize_units(self):
        """Organize data by bioreactor units"""
        # Find units from project info
        units = {}
        
        for project in self.project_info:
            # Check if this is a unit module
            proj_name = project.get('ProjName', '')
            
            # Look for unit number in parameters
            unit_no = None
            for i in range(1, 21):  # Check Parameter1 through Parameter20
                param_key = f'Parameter{i}'
                if param_key in project:
                    param_value = project[param_key]
                    if 'UnitNo=' in param_value:
                        match = re.search(r'UnitNo=(\d+)', param_value)
                        if match:
                            unit_no = int(match.group(1))
                            break
            
            if unit_no:
                units[unit_no] = {
                    'project': project,
                    'tracks': [],
                    'module_name': proj_name
                }
        
        # Assign tracks to units
        for track in self.track_info:
            module = track.get('Module', '')
            
            # Find which unit this track belongs to
            for unit_no, unit_data in units.items():
                if unit_data['module_name'] in module:
                    unit_data['tracks'].append(track)
        
        self.units_data = units
    
    def get_parsed_data(self) -> Dict[str, Any]:
        """Return parsed data summary"""
        return {
            'info': self.info_section,
            'core_info': self.core_info,
            'project_info': self.project_info,
            'track_info': self.track_info,
            'units': self.units_data,
            'data_start_line': self.data_section_start,
            'total_lines': len(self.raw_lines)
        }
    
    def get_experiment_info(self) -> Dict[str, Any]:
        """Extract experiment-level information"""
        # Find main project
        main_project = None
        for project in self.project_info:
            if 'dgcMain' in project.get('ProjName', ''):
                main_project = project
                break
        
        if not main_project and self.project_info:
            # Use first project if no main found
            main_project = self.project_info[0]
        
        if not main_project:
            main_project = {}
        
        return {
            'project_name': main_project.get('ProjName', 'Unknown'),
            'full_name': main_project.get('FullName', ''),
            'location_name': main_project.get('LocName', ''),
            'comment': main_project.get('LocComment', ''),
            'version': main_project.get('Version', ''),
            'start_timestamp': self._parse_datetime(main_project.get('StartTimestamp', '')),
            'stop_timestamp': self._parse_datetime(main_project.get('StopTimestamp', '')),
            'host': self.info_section.get('host', ''),
            'guid': main_project.get('Guid', '')
        }
    
    def get_units_info(self) -> List[Dict[str, Any]]:
        """Get information about all units"""
        units_list = []
        
        for unit_no, unit_data in self.units_data.items():
            project = unit_data['project']
            units_list.append({
                'unit_number': unit_no,
                'setup_name': project.get('LocName', f'Unit {unit_no}'),
                'location_name': project.get('LocNamePar', ''),
                'start_timestamp': self._parse_datetime(project.get('StartTimestamp', '')),
                'stop_timestamp': self._parse_datetime(project.get('StopTimestamp', '')),
                'guid': project.get('Guid', ''),
                'tracks_count': len(unit_data['tracks'])
            })
        
        return sorted(units_list, key=lambda x: x['unit_number'])
    
    def get_unit_data_df(self, unit_number: int, sample_size: Optional[int] = None) -> pd.DataFrame:
        """Get time-series data for a specific unit as DataFrame"""
        if unit_number not in self.units_data:
            return pd.DataFrame()
        
        unit_tracks = self.units_data[unit_number]['tracks']
        
        # Build column mapping
        columns = []
        column_indices = []
        
        # First columns are always timestamp and duration
        columns.extend(['timestamp', 'duration'])
        
        # Find column index for each track
        for i, track in enumerate(self.track_info):
            track_name = track.get('ProjName', '')
            
            # Check if this track belongs to our unit
            for unit_track in unit_tracks:
                if unit_track.get('ProjName', '') == track_name:
                    # Extract parameter name
                    loc_name = track.get('LocName', '')
                    if '.' in loc_name:
                        param_name = loc_name.split('.')[-1]
                    else:
                        param_name = loc_name
                    
                    columns.append(param_name)
                    column_indices.append(i)
                    break
        
        # Read data section
        data_rows = []
        
        if self.data_section_start > 0:
            end_line = self.data_section_start + (sample_size if sample_size else len(self.raw_lines))
            
            for i in range(self.data_section_start, min(end_line, len(self.raw_lines))):
                line = self.raw_lines[i].strip()
                if not line:
                    continue
                
                # Parse CSV line
                values = line.split(';')
                
                # Extract timestamp and duration (first 2 columns)
                if len(values) >= 2:
                    row = [values[0].strip('"'), values[1].strip('"')]
                    
                    # Extract values for this unit's tracks
                    for col_idx in column_indices:
                        if col_idx + 2 < len(values):  # +2 for timestamp and duration
                            row.append(values[col_idx + 2].strip('"'))
                        else:
                            row.append('')
                    
                    data_rows.append(row)
        
        # Create DataFrame
        if data_rows:
            df = pd.DataFrame(data_rows, columns=columns)
            
            # Convert data types
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
            
            # Convert numeric columns
            for col in columns[2:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        
        return pd.DataFrame(columns=columns)
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime string"""
        if not dt_str:
            return None
        
        try:
            # Remove quotes if present
            dt_str = dt_str.strip('"')
            
            # Try common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None