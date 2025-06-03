# mcp_basic_tools_server.py

import subprocess
import shlex
import socket
import requests
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    server_id="basic_pentest_tools_v1",
    title="Basic Network & Command Tools MCP Server", # Updated title
    description="Exposes simple network tools and a bash command executor for an AI agent."
)

@mcp.tool()
def ping_target(target_host: str, count: int = 2) -> str:
    """
    Pings a target host to check for reachability using the system's ping command.
    Assumes a Linux-like environment (e.g., Kali Linux) for 'ping -c'.

    Args:
        target_host: The IP address or hostname to ping.
        count: The number of ping packets to send (default is 2, max is 5).

    Returns:
        String with ping output or error message.
    """
    print(f"[Server Log] Received ping_target request for '{target_host}' with count {count}.")
    try:
        count = int(count)
        if not (1 <= count <= 5): count = 2
    except ValueError: count = 2

    command = ["ping", "-c", str(count), "-W", "3", target_host] # Linux style
    try:
        print(f"[Server Log] Executing: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        output_lines = [f"--- Ping results for {shlex.quote(target_host)} (Count: {count}) ---"]
        if result.stdout: output_lines.extend(["Stdout:", result.stdout.strip()])
        if result.stderr: output_lines.extend(["Stderr:", result.stderr.strip()])
        output_lines.append(f"Ping command exit code: {result.returncode}")
        final_output = "\n".join(output_lines)
        print(f"[Server Log] Ping for '{target_host}' completed. Output length: {len(final_output)}")
        return final_output
    except subprocess.TimeoutExpired: return f"Error: Ping for '{target_host}' timed out."
    except FileNotFoundError: return "Error: 'ping' command not found on server."
    except Exception as e: return f"Ping error for '{target_host}': {str(e)}"

@mcp.tool()
def simple_http_get(url: str) -> str:
    """
    Performs HTTP GET for a URL, returns status, relevant headers, content snippet.

    Args:
        url: URL for GET request (must start http:// or https://).

    Returns:
        String summarizing HTTP response or error.
    """
    print(f"[Server Log] Received simple_http_get for URL: '{url}'.")
    if not (url.startswith("http://") or url.startswith("https://")):
        return "Error: Invalid URL. Must start with http:// or https://"
    headers = {'User-Agent': 'MCP-BasicTools-Client/1.0'}
    try:
        print(f"[Server Log] Executing HTTP GET to: {url}")
        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        content_type = response.headers.get('Content-Type', 'N/A')
        content_snippet = response.text[:500] + ("..." if len(response.text) > 500 else "") if 'text' in content_type.lower() or 'json' in content_type.lower() else "[Binary content]"
        final_output = (
            f"--- HTTP GET Response from {url} ---\n"
            f"Status: {response.status_code} {response.reason}\n"
            f"Content-Type: {content_type}\n"
            f"Content Snippet (first 500 chars):\n{content_snippet}"
        )
        print(f"[Server Log] HTTP GET for '{url}' done. Status: {response.status_code}.")
        return final_output
    except requests.exceptions.Timeout: return f"Error: HTTP GET to '{url}' timed out."
    except requests.exceptions.ConnectionError: return f"Error: Could not connect to '{url}'."
    except requests.exceptions.RequestException as e: return f"HTTP GET error for '{url}': {str(e)}"
    except Exception as e: return f"Unexpected GET error for '{url}': {str(e)}"

@mcp.tool()
def check_port_status(target_host: str, port: int) -> str:
    """
    Checks if a specific TCP port is open on a target host.

    Args:
        target_host: IP address or hostname.
        port: TCP port number (1-65535).

    Returns:
        String indicating port status or error.
    """
    print(f"[Server Log] Received check_port_status for '{target_host}' on port {port}.")
    try:
        port_num = int(port)
        if not (1 <= port_num <= 65535): return f"Error: Invalid port: {port_num}."
    except ValueError: return f"Error: Port '{port}' must be an integer."
    
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result_code = sock.connect_ex((target_host, port_num))
        msg = f"Port {port_num} on '{target_host}' is {'open' if result_code == 0 else 'closed/filtered (code: ' + str(result_code) + ')'}."
        print(f"[Server Log] {msg}")
        return msg
    except socket.timeout: return f"Port {port_num} on '{target_host}' filtered (timeout)."
    except socket.gaierror: return f"Error: Cannot resolve hostname '{target_host}'."
    except Exception as e: return f"Port check error for {port_num} on '{target_host}': {str(e)}"
    finally:
        if sock: sock.close()

# --- NEW TOOL ---
@mcp.tool()
def execute_bash_command(command_string: str) -> str: # Return type is still str, but it will be a JSON string
    """
    Executes a given bash command string on the server (Kali Linux).
    Returns a JSON string with 'stdout', 'stderr', and 'returncode'.
    WARNING: This tool can execute arbitrary commands... (rest of docstring same)
    """
    print(f"[Server Log] Received execute_bash_command request: '{command_string[:100]}{'...' if len(command_string) > 100 else ''}'")

    if not command_string or not command_string.strip():
        return json.dumps({"stdout": "", "stderr": "Error: Empty command string received.", "returncode": -1})

    timeout_seconds = 90 
    try:
        print(f"[Server Log] Executing (shell=True, timeout={timeout_seconds}s): {command_string}")
        result = subprocess.run(
            command_string,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False
        )
        
        response_data = {
            "stdout": result.stdout.strip() if result.stdout else "",
            "stderr": result.stderr.strip() if result.stderr else "",
            "returncode": result.returncode
        }
        print(f"[Server Log] Bash command executed. RC: {result.returncode}. Stdout/Stderr length: {len(response_data['stdout'])}/{len(response_data['stderr'])}")
        return json.dumps(response_data)

    except subprocess.TimeoutExpired:
        err_msg = f"Error: Bash command '{command_string[:50]}...' timed out after {timeout_seconds} seconds."
        print(f"[Server Log] {err_msg}")
        return json.dumps({"stdout": "", "stderr": err_msg, "returncode": -1}) # Using -1 for timeout/script error
    except Exception as e:
        err_msg = f"An unexpected server-side error occurred: {str(e)}"
        print(f"[Server Log] {err_msg}")
        return json.dumps({"stdout": "", "stderr": err_msg, "returncode": -1})

if __name__ == "__main__":
    current_server_id = "basic_pentest_tools_v1" 
    print("Initializing Basic Network & Command Tools MCP Server...")
    
    defined_tool_names = ["ping_target", "simple_http_get", "check_port_status", "execute_bash_command"] # Added new tool
    print(f"Serving tools: {defined_tool_names}")
    print(f"MCP Server ID: {current_server_id}") 
    print("Server is starting with 'stdio' transport.")
    print("An MCP client can now connect and send ListTools or CallTool requests.")
    mcp.run(transport='stdio')
