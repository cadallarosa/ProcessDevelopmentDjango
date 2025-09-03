"""
DASGIP CSV File Parser
Extracts metadata and time-series data from DASGIP bioreactor export files
"""

import csv
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any
import pandas as pd
from io import StringIO


class DasgipParser:
    """Parser for DASGIP bioreactor export CSV files"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.info = {}
        self.core_info = {}
        self.project_info = []
        self.track_info = []
        self.data_rows = []
        self.units = {}  # Dictionary to store unit-specific data
        
    def parse(self):
        """Main parsing method that orchestrates all parsing steps"""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
        # Split content into sections
        sections = self._split_sections(content)
        
        # Parse each section
        if '[Info]' in sections:
            self.info = self._parse_info_section(sections['[Info]'])
            
        if '[CoreInfo]' in sections:
            self.core_info = self._parse_core_info_section(sections['[CoreInfo]'])
            
        if '[ProjectInfo]' in sections:
            self.project_info = self._parse_project_info_section(sections['[ProjectInfo]'])
            
        if '[TrackInfo]' in sections:
            self.track_info = self._parse_track_info_section(sections['[TrackInfo]'])
            
        # Parse data rows
        if 'data' in sections:
            self.data_rows = self._parse_data_section(sections['data'])
            
        # Organize data by units
        self._organize_by_units()
        
        return self.get_parsed_data()
    
    def _split_sections(self, content: str) -> Dict[str, str]:
        """Split the CSV content into sections based on headers"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Check for section headers
            if line.startswith('[') and line.endswith(']'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                    
                current_section = line
                current_content = []
            elif current_section:
                current_content.append(line)
            elif not current_section and line:
                # Data section (no header)
                if 'data' not in sections:
                    sections['data'] = []
                sections.setdefault('data', []).append(line)
                
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
            
        # Join data lines if they exist
        if 'data' in sections and isinstance(sections['data'], list):
            sections['data'] = '\n'.join(sections['data'])
            
        return sections
    
    def _parse_info_section(self, content: str) -> Dict[str, str]:
        """Parse the [Info] section"""
        info = {}
        reader = csv.reader(StringIO(content), delimiter=';')
        
        for row in reader:
            if row and len(row) >= 2:
                if row[0] == 'Product':
                    # Header row, skip
                    continue
                elif len(row) >= 7:
                    # Info row with multiple fields
                    info['product'] = row[0]
                    info['version'] = row[1]
                    info['host'] = row[2]
                    info['timestamp'] = row[3]
                    info['author'] = row[4]
                    info['connection'] = row[5]
                    info['application'] = row[6]
                else:
                    # Version info rows
                    info[row[0]] = row[1] if len(row) > 1 else ''
                    
        return info
    
    def _parse_core_info_section(self, content: str) -> Dict[str, str]:
        """Parse the [CoreInfo] section"""
        core_info = {}
        reader = csv.reader(StringIO(content), delimiter=';')
        
        for row in reader:
            if row and len(row) >= 2:
                if row[0] == 'Product':
                    continue
                core_info[row[0]] = row[1] if len(row) > 1 else ''
                
        return core_info
    
    def _parse_project_info_section(self, content: str) -> List[Dict[str, Any]]:
        """Parse the [ProjectInfo] section to extract project and unit information"""
        projects = []
        reader = csv.DictReader(StringIO(content), delimiter=';')
        
        for row in reader:
            project = {}
            for key, value in row.items():
                if value:
                    project[key] = value
            projects.append(project)
            
        return projects
    
    def _parse_track_info_section(self, content: str) -> List[Dict[str, Any]]:
        """Parse the [TrackInfo] section to extract parameter definitions"""
        tracks = []
        reader = csv.DictReader(StringIO(content), delimiter=';')
        
        for row in reader:
            track = {}
            for key, value in row.items():
                if value:
                    track[key] = value
            tracks.append(track)
            
        return tracks
    
    def _parse_data_section(self, content: str) -> List[List[str]]:
        """Parse the data section containing time-series values"""
        data = []
        reader = csv.reader(StringIO(content), delimiter=';')
        
        for row in reader:
            if row and any(cell.strip() for cell in row):
                data.append(row)
                
        return data
    
    def _organize_by_units(self):
        """Organize parsed data by bioreactor units"""
        # Extract unit information from project info
        unit_projects = {}
        
        for project in self.project_info:
            # Look for unit number in parameters
            unit_no = None
            for param_key in project.keys():
                if param_key.startswith('Parameter'):
                    param_value = project[param_key]
                    if 'UnitNo=' in param_value:
                        match = re.search(r'UnitNo=(\d+)', param_value)
                        if match:
                            unit_no = int(match.group(1))
                            break
                            
            if unit_no:
                unit_projects[project['ProjName']] = {
                    'unit_number': unit_no,
                    'project': project,
                    'tracks': [],
                    'data_columns': []
                }
        
        # Assign tracks to units
        for track in self.track_info:
            if 'Module' in track:
                module_name = track['Module']
                # Find which unit this track belongs to
                for proj_name, unit_info in unit_projects.items():
                    if module_name and proj_name in module_name:
                        unit_info['tracks'].append(track)
                        
        # Map data columns to units based on track order
        if self.data_rows:
            # First row should be timestamps
            header_row = self.data_rows[0] if self.data_rows else []
            
            # Create column mapping
            col_index = 0
            for track in self.track_info:
                if 'Timestamp' not in track.get('ProjName', '') and 'Duration' not in track.get('ProjName', ''):
                    if 'Module' in track:
                        module_name = track['Module']
                        for proj_name, unit_info in unit_projects.items():
                            if module_name and proj_name in module_name:
                                unit_info['data_columns'].append(col_index)
                col_index += 1
                
        self.units = unit_projects
        
    def get_parsed_data(self) -> Dict[str, Any]:
        """Return the parsed data in a structured format"""
        return {
            'info': self.info,
            'core_info': self.core_info,
            'project_info': self.project_info,
            'track_info': self.track_info,
            'units': self.units,
            'data_rows': self.data_rows[:10] if self.data_rows else [],  # Return sample of data rows
            'total_data_rows': len(self.data_rows)
        }
    
    def get_experiment_info(self) -> Dict[str, Any]:
        """Extract experiment-level information"""
        # Find the main project (not a module)
        main_project = None
        for project in self.project_info:
            if 'dgcMain' in project.get('ProjName', ''):
                main_project = project
                break
                
        if not main_project and self.project_info:
            main_project = self.project_info[0]
        
        # Handle case where no project info found
        if not main_project:
            main_project = {}
            
        exp_info = {
            'project_name': main_project.get('ProjName', 'Unknown'),
            'full_name': main_project.get('FullName', ''),
            'location_name': main_project.get('LocName', ''),
            'comment': main_project.get('LocComment', ''),
            'state': main_project.get('State', ''),
            'version': main_project.get('Version', ''),
            'start_timestamp': self._parse_timestamp(main_project.get('StartTimestamp', '')),
            'stop_timestamp': self._parse_timestamp(main_project.get('StopTimestamp', '')),
            'guid': main_project.get('Guid', ''),
            'host': self.info.get('host', ''),
            'dasware_version': self.core_info.get('Product', ''),
            'database_version': self.core_info.get('Database', '')
        }
        
        return exp_info
    
    def get_units_info(self) -> List[Dict[str, Any]]:
        """Extract information about all bioreactor units"""
        units_info = []
        
        for proj_name, unit_data in self.units.items():
            project = unit_data['project']
            unit_info = {
                'unit_number': unit_data['unit_number'],
                'setup_name': project.get('LocName', ''),
                'location_name': project.get('LocNamePar', ''),
                'module_name': project.get('ProjName', ''),
                'start_timestamp': self._parse_timestamp(project.get('StartTimestamp', '')),
                'stop_timestamp': self._parse_timestamp(project.get('StopTimestamp', '')),
                'guid': project.get('Guid', ''),
                'tracks': unit_data['tracks'],
                'data_column_indices': unit_data['data_columns']
            }
            units_info.append(unit_info)
            
        return sorted(units_info, key=lambda x: x['unit_number'])
    
    def get_unit_data(self, unit_number: int) -> pd.DataFrame:
        """Get time-series data for a specific unit as a pandas DataFrame"""
        # Find unit info
        unit_info = None
        for unit in self.get_units_info():
            if unit['unit_number'] == unit_number:
                unit_info = unit
                break
                
        if not unit_info:
            return pd.DataFrame()
            
        # Extract data for this unit
        tracks = unit_info['tracks']
        
        # Create column names from tracks
        columns = ['timestamp', 'duration']
        for track in tracks:
            if 'Timestamp' not in track.get('ProjName', '') and 'Duration' not in track.get('ProjName', ''):
                param_name = track.get('LocName', '').split('.')[-1] if '.' in track.get('LocName', '') else track.get('LocName', '')
                columns.append(param_name)
                
        # Extract data rows
        data = []
        for row in self.data_rows:
            if len(row) > 2:  # Ensure row has data
                try:
                    # Parse timestamp and duration from first two columns
                    timestamp = row[0] if row[0] else None
                    duration = row[1] if len(row) > 1 and row[1] else None
                    
                    # Get data values for this unit's tracks
                    unit_row = [timestamp, duration]
                    
                    # Map column indices to get correct data
                    col_offset = 2  # Start after timestamp and duration
                    for track in tracks:
                        if 'Timestamp' not in track.get('ProjName', '') and 'Duration' not in track.get('ProjName', ''):
                            # Find column index for this track
                            track_name = track.get('ProjName', '')
                            col_index = self._find_track_column_index(track_name)
                            if col_index >= 0 and col_index < len(row):
                                unit_row.append(row[col_index])
                            else:
                                unit_row.append(None)
                                
                    if timestamp:  # Only add rows with valid timestamp
                        data.append(unit_row)
                except Exception:
                    continue
                    
        # Create DataFrame
        if data:
            df = pd.DataFrame(data, columns=columns)
            # Convert timestamp column to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            # Convert duration to float
            df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
            # Convert other columns to float
            for col in columns[2:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        else:
            return pd.DataFrame(columns=columns)
    
    def _find_track_column_index(self, track_name: str) -> int:
        """Find the column index for a given track name"""
        for i, track in enumerate(self.track_info):
            if track.get('ProjName', '') == track_name:
                return i
        return -1
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
            
        try:
            # Try different timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y %H:%M:%S.%f'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
                    
            # If no format matches, return None
            return None
        except Exception:
            return None