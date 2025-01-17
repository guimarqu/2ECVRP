import os
import json
import re
import glob

def clean_ansi(text):
    # Remove ANSI color codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def parse_input_data(content):
    # Clean ANSI codes
    content = clean_ansi(content)
    
    # Initialize the data structure
    data = {
        "first_level_vehicles": {},
        "second_level_vehicles": {},
        "customers": [],
        "satellites": [],
        "cdcs": []
    }
    
    # Find the section with vehicle information
    vehicle_match = re.search(r'\|K\| = (\d+)\s+Q1 = (\d+)\s+cost = (\d+).*?\|L\| = (\d+)\s+Q2 = (\d+)\s+cost = (\d+)', content, re.DOTALL)
    if not vehicle_match:
        print("Could not find vehicle information")
        return None
    
    # Parse vehicle information
    data["first_level_vehicles"] = {
        "fleet_size": int(vehicle_match.group(1)),
        "capacity": int(vehicle_match.group(2)),
        "cost": int(vehicle_match.group(3))
    }
    data["second_level_vehicles"] = {
        "fleet_size": int(vehicle_match.group(4)),
        "capacity": int(vehicle_match.group(5)),
        "cost": int(vehicle_match.group(6))
    }
    
    # Find all customer entries
    customer_pattern = r'Customer (\d+)\s+x = (-?\d+)\s+y = (-?\d+)\s+demand = (\d+)\s+tw = \[(\d+), (\d+)\]\s+st = (\d+)'
    for match in re.finditer(customer_pattern, content):
        customer = {
            "id": int(match.group(1)),
            "x": int(match.group(2)),
            "y": int(match.group(3)),
            "demand": int(match.group(4)),
            "time_window": [int(match.group(5)), int(match.group(6))],
            "service_time": int(match.group(7))
        }
        data["customers"].append(customer)
    
    # Find all satellite entries
    satellite_pattern = r'Satellite (\d+)\s+x = (-?\d+)\s+y = (-?\d+)\s+tw = \[(\d+), (\d+)\]\s+st = (\d+)'
    for match in re.finditer(satellite_pattern, content):
        satellite = {
            "id": int(match.group(1)),
            "x": int(match.group(2)),
            "y": int(match.group(3)),
            "time_window": [int(match.group(4)), int(match.group(5))],
            "service_time": int(match.group(6))
        }
        data["satellites"].append(satellite)
    
    # Find all CDC entries
    cdc_pattern = r'CDC (\d+)\s+x = (-?\d+)\s+y = (-?\d+)\s+tw = \[(\d+), (\d+)\]\s+st = (\d+)'
    for match in re.finditer(cdc_pattern, content):
        cdc = {
            "id": int(match.group(1)),
            "x": int(match.group(2)),
            "y": int(match.group(3)),
            "time_window": [int(match.group(4)), int(match.group(5))],
            "service_time": int(match.group(6))
        }
        data["cdcs"].append(cdc)
    
    # Verify we found at least some data
    if not data["customers"] or not data["satellites"] or not data["cdcs"]:
        print("Missing required data:")
        print(f"Customers: {len(data['customers'])}")
        print(f"Satellites: {len(data['satellites'])}")
        print(f"CDCs: {len(data['cdcs'])}")
        return None
    
    return data

def process_input_files():
    # Find all jobs-input directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Base directory: {base_dir}")
    
    found_dirs = False
    for root, dirs, files in os.walk(base_dir):
        if os.path.basename(root) == 'jobs-input':
            found_dirs = True
            print(f"\nProcessing directory: {root}")
            # Create a corresponding instances directory at the same level as jobs-input
            instances_dir = os.path.join(os.path.dirname(root), 'instances')
            os.makedirs(instances_dir, exist_ok=True)
            print(f"Created instances directory: {instances_dir}")
            
            # Process each file in jobs-input
            for file in files:
                input_file_path = os.path.join(root, file)
                print(f"\nProcessing file: {input_file_path}")
                
                # Read the input file
                with open(input_file_path, 'r') as f:
                    content = f.read()
                
                # Parse the data
                data = parse_input_data(content)
                
                if data:
                    # Create output JSON file
                    output_filename = os.path.splitext(file)[0] + '.json'
                    output_file_path = os.path.join(instances_dir, output_filename)
                    
                    with open(output_file_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"Created JSON file: {output_file_path}")
                else:
                    print("Failed to parse input data")
    
    if not found_dirs:
        print("No jobs-input directories found!")

if __name__ == "__main__":
    process_input_files()
