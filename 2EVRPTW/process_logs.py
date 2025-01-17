import os
import glob
import json
import re

def parse_solution_checker_output(lines):
    # Initialize the result dictionary
    result = {
        "nb_first_level_routes": 0,
        "nb_second_level_routes": 0,
        "nb_urban_trucks": 0,
        "nb_city_freighters": 0,
        "first_level_routes": [],
        "second_level_routes": []
    }
    
    # Find all solution checker sections
    solution_checker_starts = []
    for i, line in enumerate(lines):
        if "Solution Checker" in line:
            solution_checker_starts.append(i)
    
    if not solution_checker_starts:
        return None
        
    # Use the last occurrence
    start_idx = solution_checker_starts[-1]
    
    # Extract solution value
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        if "Cost of the solution is" in line:
            # Remove ANSI escape codes and get the value
            value_str = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)  # Remove all ANSI escape codes
            value_str = value_str.split("Cost of the solution is")[-1].strip()
            try:
                result["solution_value"] = float(value_str)
            except ValueError:
                continue  # If we can't parse the value, try next line
            break
    
    # Find route sections
    first_level_start = None
    second_level_start = None
    
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)  # Remove ANSI escape codes
        if "FIRST LEVEL ROUTES" in line:
            first_level_start = i
        elif "SECOND LEVEL ROUTES" in line:
            second_level_start = i
            break
    
    if not all([first_level_start, second_level_start]):
        return None
    
    # Parse first level routes
    i = first_level_start + 1
    while i < second_level_start:
        line = lines[i].strip()
        if not line:
            break
            
        # Remove ANSI escape codes
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
            
        # Extract route information
        nodes = re.findall(r'(\d+)', line)  # Get all numbers
        times = re.findall(r't=([0-9.]+)', line)
        demands = re.findall(r'd=([0-9.]+)', line)
        capacity = re.search(r'Q=(\d+)', line)
        
        if nodes:
            route = {
                "path": []
            }
            
            for j in range(len(nodes)):
                node_info = {
                    "node": int(nodes[j]),
                    "time": float(times[j]) if j < len(times) else 0.0,
                    "demand": float(demands[j]) if j < len(demands) else 0.0
                }
                route["path"].append(node_info)
            
            if capacity:
                route["capacity"] = int(capacity.group(1))
            
            result["first_level_routes"].append(route)
            result["nb_first_level_routes"] += 1
        i += 1
    
    # Parse second level routes
    i = second_level_start + 1
    while i < len(lines):
        line = lines[i].strip()
        if not line or "Cost of the solution" in line:
            break
            
        # Remove ANSI escape codes
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
            
        # Extract route information
        nodes = re.findall(r'(\d+)', line)  # Get all numbers
        times = re.findall(r't=([0-9.]+)', line)
        loads = re.findall(r'l=([0-9.]+)', line)
        dist_cost = re.search(r'distcost = ([0-9.]+)', line)
        
        if nodes:
            route = {
                "dist_cost": float(dist_cost.group(1)) if dist_cost else 0.0,
                "path": []
            }
            
            for j in range(len(nodes)):
                node_info = {
                    "node": int(nodes[j]),
                    "time": float(times[j]) if j < len(times) else 0.0,
                    "load": float(loads[j]) if j < len(loads) else 0.0
                }
                route["path"].append(node_info)
            
            result["second_level_routes"].append(route)
            result["nb_second_level_routes"] += 1
        i += 1
    
    # Return result if we found any routes
    if result["first_level_routes"] or result["second_level_routes"]:
        return result
    
    return None

def process_log_file(log_file_path):
    # Get the directory and filename
    dir_path = os.path.dirname(log_file_path)
    base_dir = os.path.dirname(dir_path)
    filename = os.path.basename(log_file_path)
    
    # Create input, output and solutions directories if they don't exist
    input_dir = os.path.join(base_dir, 'jobs-input')
    output_dir = os.path.join(base_dir, 'jobs-output')
    solutions_dir = os.path.join(base_dir, 'solutions')
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(solutions_dir, exist_ok=True)
    
    # Read the file content
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
    
    # Extract first 500 lines for input
    first_lines = lines[:500]
    with open(os.path.join(input_dir, filename), 'w') as f:
        f.writelines(first_lines)
    
    # Extract last 500 lines for output and parse solution
    last_lines = lines[-500:] if len(lines) > 500 else lines
    with open(os.path.join(output_dir, filename), 'w') as f:
        f.writelines(last_lines)
    
    # Parse solution and save as JSON if solution exists
    solution = parse_solution_checker_output(last_lines)
    if solution:
        json_path = os.path.join(solutions_dir, f"{filename}.json")
        with open(json_path, 'w') as f:
            json.dump(solution, f, indent=2)
        print(f"Generated JSON: {json_path}")
    else:
        # Record files without solutions in errors.csv
        error_file = os.path.join(base_dir, f"errors_{filename.split('_')[-1].split('.')[0]}.csv")
        with open(error_file, 'a') as f:
            f.write(f"{filename}\n")
        print(f"No solution found for: {filename}")

def main():
    # Get all jobs-logs directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for jobs_logs_dir in glob.glob(os.path.join(base_dir, '**/jobs-logs'), recursive=True):
        # Process each log file in the directory
        for log_file in glob.glob(os.path.join(jobs_logs_dir, '*')):
            if os.path.isfile(log_file):
                try:
                    process_log_file(log_file)
                    print(f"Processed: {log_file}")
                except Exception as e:
                    print(f"Error processing {log_file}: {str(e)}")

if __name__ == "__main__":
    main()
