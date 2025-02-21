import glob
import json
import os
import re
import sys


def remove_ansi_codes(text):
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", text)


def parse_log(file_path):
    """
    Reads the last section of the log file and extracts key metrics from logs.
    Extracted metrics:
      - First level routes as list of dict with keys: route, used, cost
      - Second level routes as list of dict with keys: route, used, cost
      - Vehicles used as a dict with keys 'urban_trucks' and 'city_freighters'
      - Final solution cost
      - Summary table header and values as a dictionary
    """
    result = {}
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Could not read file {file_path}: {e}")
        return None

    text = "".join(lines)
    # Remove ANSI escape sequences
    text = remove_ansi_codes(text)

    # Extract first level routes using regex
    # Matches lines like: "> 1st lev tour visiting [205, 215] used 1.0 time(s) (cost = 68.0294054067798)."
    pattern_first = r">\s*1st lev tour visiting\s*\[([^\]]+)\]\s*used\s*([\d\.]+)\s*time\(s\)\s*\(cost\s*=\s*([-\d\.]+)\)"
    first_matches = re.findall(pattern_first, text)
    first_routes = []
    for match in first_matches:
        route_str, used_str, cost_str = match
        # Convert route string to list of integers
        route = [int(x.strip()) for x in route_str.split(",") if x.strip().isdigit()]
        try:
            used_val = int(float(used_str))
            cost_val = float(cost_str)
        except ValueError:
            used_val = used_str
            cost_val = cost_str
        first_routes.append({"route": route, "used": used_val, "cost": cost_val})
    result["first_level_routes"] = first_routes if first_routes else None

    # Extract second level routes
    # Matches lines like: "> 2nd lev tour [200, 22, 10, ...] used 1.0 time(s) (cost = 22.181175003465135)."
    pattern_second = r">\s*2nd lev tour\s*\[([^\]]+)\]\s*used\s*([\d\.]+)\s*time\(s\)\s*\(cost\s*=\s*([-\d\.]+)\)"
    second_matches = re.findall(pattern_second, text)
    second_routes = []
    for match in second_matches:
        route_str, used_str, cost_str = match
        route = [int(x.strip()) for x in route_str.split(",") if x.strip().isdigit()]
        try:
            used_val = int(float(used_str))
            cost_val = float(cost_str)
        except ValueError:
            used_val = used_str
            cost_val = cost_str
        second_routes.append({"route": route, "used": used_val, "cost": cost_val})
    result["second_level_routes"] = second_routes if second_routes else None

    # Extract vehicles used as dictionary
    # Matches lines like: ">  5.0  urban trucks used (out of 9) -- setup_cost = 0."
    pattern_veh = r">\s*([\d\.]+)\s*(urban trucks|city freighters) used"
    veh_matches = re.findall(pattern_veh, text)
    vehicles = {}
    for val, vtype in veh_matches:
        try:
            vehicles[vtype.replace(" ", "_")] = int(float(val))
        except ValueError:
            vehicles[vtype.replace(" ", "_")] = val
    result["vehicles_used"] = vehicles if vehicles else None

    # Extract final solution cost
    solution_match = re.search(
        r"Cost of the solution\s*:\s*([-\d\.]+)", text, re.IGNORECASE
    )
    if solution_match:
        try:
            result["final_solution_value"] = float(solution_match.group(1))
        except ValueError:
            result["final_solution_value"] = solution_match.group(1).strip()
    else:
        result["final_solution_value"] = None

    # Extract summary table header and its corresponding values, and convert to a dictionary
    summary_match = re.search(r"^(Instance,.*)$\n^(.*)$", text, re.MULTILINE)
    if summary_match:
        header_line = summary_match.group(1)
        value_line = summary_match.group(2)
        headers = [h.strip() for h in header_line.split(",")]
        values = [v.strip() for v in value_line.split(",")]
        summary_dict = {}
        for h, v in zip(headers, values):
            try:
                conv = float(v)
                if conv.is_integer():
                    summary_dict[h] = int(conv)
                else:
                    summary_dict[h] = conv
            except ValueError:
                summary_dict[h] = v
        result["summary"] = summary_dict
    else:
        result["summary"] = None

    # Extract execution time from log
    # Matches lines like: "Elapsed (wall clock) time (h:mm:ss or m:ss): 60:01:40"
    exec_match = re.search(
        r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([\d:]+)", text
    )
    if exec_match:
        raw_time = exec_match.group(1).strip()
        # Convert to total seconds if possible
        parts = raw_time.split(":")
        try:
            if len(parts) == 3:
                hours, minutes, seconds = parts
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                total_seconds = int(minutes) * 60 + float(seconds)
            else:
                total_seconds = None
        except ValueError:
            total_seconds = None
        result["execution_time"] = {"raw": raw_time, "seconds": total_seconds}
    else:
        result["execution_time"] = None

    # Instance identifier
    result["instance"] = os.path.basename(file_path)

    return result


def main():
    search_pattern = os.path.join("jobs-logs_*", "*.sh")
    log_files = glob.glob(search_pattern)
    if not log_files:
        print(f"No log files found with pattern: {search_pattern}")
        sys.exit(1)

    results = []
    for file_path in log_files:
        data = parse_log(file_path)
        if data:
            results.append(data)
        else:
            print(f"Skipping file {file_path} due to read/parse error")

    output_file = "solution_summary.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        print(
            f"Extracted data for {len(results)} log files. Output saved to {output_file}"
        )
    except Exception as e:
        print(f"Failed to write output file: {e}")


if __name__ == "__main__":
    main()
