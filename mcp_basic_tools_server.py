# mcp_basic_tools_server.py

import subprocess
import shlex # For robust argument splitting if we were building complex shell commands
from typing import List # For type hinting, though not strictly used by return types here
import requests # For the simple_http_get tool
from mcp.server.fastmcp import FastMCP # The MCP server framework

# Initialize FastMCP server
mcp = FastMCP(
    server_id="basic_pentest_tools_v1", # A unique ID for this server
    title="Basic Network Tools MCP Server",
    description="Exposes simple network tools like ping and HTTP GET for an AI agent."
)

@mcp.tool()
def ping_target(target_host: str, count: int = 2) -> str:
    """
    Pings a target host to check for reachability using the system's ping command.
    This implementation assumes a Linux-like environment (e.g., Kali Linux) for the 'ping -c' command.

    Args:
        target_host: The IP address or hostname to ping.
        count: The number of ping packets to send (default is 2, max is 5).

    Returns:
        A string containing the output (stdout and stderr) of the ping command,
        or an error message if the ping fails or an issue occurs.
    """
    print(f"[Server Log] Received ping_target request for '{target_host}' with count {count}.")

    # Validate and sanitize count
    try:
        count = int(count)
        if not (1 <= count <= 5): # Ensure count is within a safe range
            print(f"[Server Log] Invalid ping count {count}. Setting to default 2.")
            count = 2
    except ValueError:
        print(f"[Server Log] Non-integer ping count provided. Setting to default 2.")
        count = 2

    # Basic security consideration: Avoid direct command injection.
    # While subprocess with a list of args (shell=False) is safer,
    # validating target_host against known patterns (IP, valid hostname chars)
    # would be a good practice in a more robust system.
    # For this educational example, we proceed with caution.
    command = ["ping", "-c", str(count), "-W", "3", target_host] # -W 3 for a 3-second timeout for each ping reply

    try:
        print(f"[Server Log] Executing: {' '.join(command)}")
        # Timeout for the whole subprocess call to prevent indefinite hanging
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        
        output_lines = []
        output_lines.append(f"--- Ping results for {shlex.quote(target_host)} (Count: {count}) ---") # Use shlex.quote for safe display
        if result.stdout:
            output_lines.append("Stdout:")
            output_lines.append(result.stdout.strip())
        if result.stderr:
            output_lines.append("Stderr:")
            output_lines.append(result.stderr.strip())
        
        if result.returncode != 0:
            output_lines.append(f"Ping command exited with error code: {result.returncode}")
        else:
            output_lines.append(f"Ping command completed successfully (return code: {result.returncode})")
            
        final_output = "\n".join(output_lines)
        print(f"[Server Log] Ping for '{target_host}' completed. Output length: {len(final_output)}")
        return final_output

    except subprocess.TimeoutExpired:
        err_msg = f"Error: Ping command for '{target_host}' timed out after 15 seconds."
        print(f"[Server Log] {err_msg}")
        return err_msg
    except FileNotFoundError:
        err_msg = "Error: 'ping' command not found on the server. Is it installed and in PATH?"
        print(f"[Server Log] {err_msg}")
        return err_msg
    except Exception as e:
        err_msg = f"An unexpected error occurred while pinging '{target_host}': {str(e)}"
        print(f"[Server Log] {err_msg}")
        return err_msg

@mcp.tool()
def simple_http_get(url: str) -> str:
    """
    Performs a simple HTTP GET request to the specified URL and returns status,
    relevant headers, and a snippet of the content.

    Args:
        url: The URL to send the GET request to (must start with http:// or https://).

    Returns:
        A string summarizing the HTTP response or an error message.
    """
    print(f"[Server Log] Received simple_http_get request for URL: '{url}'.")

    if not (url.startswith("http://") or url.startswith("https://")):
        err_msg = "Error: Invalid URL. Must start with http:// or https://"
        print(f"[Server Log] {err_msg} (URL was: {url})")
        return err_msg

    custom_headers = {
        'User-Agent': 'MCP-BasicTools-Client/1.0 (Kali VM)', # Identify our client
        'Accept': '*/*' # Be flexible
    }

    try:
        print(f"[Server Log] Executing HTTP GET to: {url}")
        # Timeout for the request, verify=True by default for HTTPS
        response = requests.get(url, timeout=10, headers=custom_headers, allow_redirects=True)
        
        # Process response
        content_type = response.headers.get('Content-Type', 'N/A')
        content_length = response.headers.get('Content-Length', 'N/A (or chunked)')
        
        # Get a snippet of the text content, careful about large non-text responses
        content_snippet = ""
        if 'text' in content_type.lower() or 'json' in content_type.lower() or 'xml' in content_type.lower():
            content_snippet = response.text[:500] # Get first 500 chars for text-based content
            if len(response.text) > 500:
                content_snippet += "\n... (content truncated)"
        elif response.content: # For binary data, just indicate its presence and length
            content_snippet = f"[Binary content of length {len(response.content)} bytes received]"
        else:
            content_snippet = "[No content body]"
            
        final_output = (
            f"--- HTTP GET Response from {url} ---\n"
            f"Status Code: {response.status_code} {response.reason}\n"
            f"Content-Type: {content_type}\n"
            f"Content-Length: {content_length}\n"
            f"--- Response Content (Snippet) ---\n{content_snippet}"
        )
        print(f"[Server Log] HTTP GET for '{url}' completed. Status: {response.status_code}. Output length: {len(final_output)}")
        return final_output
                
    except requests.exceptions.Timeout:
        err_msg = f"Error: HTTP GET request to '{url}' timed out after 10 seconds."
        print(f"[Server Log] {err_msg}")
        return err_msg
    except requests.exceptions.ConnectionError:
        err_msg = f"Error: Could not connect to '{url}'. Verify the URL, network connectivity, and DNS resolution on the server."
        print(f"[Server Log] {err_msg}")
        return err_msg
    except requests.exceptions.TooManyRedirects:
        err_msg = f"Error: Too many redirects encountered for URL '{url}'."
        print(f"[Server Log] {err_msg}")
        return err_msg
    except requests.exceptions.RequestException as e: # Catch other requests-related errors
        err_msg = f"An error occurred during the HTTP GET request to '{url}': {str(e)}"
        print(f"[Server Log] {err_msg}")
        return err_msg
    except Exception as e: # Catch any other unexpected error
        err_msg = f"An unexpected server-side error occurred during HTTP GET to '{url}': {str(e)}"
        print(f"[Server Log] {err_msg}")
        return err_msg

if __name__ == "__main__":
    # The server_id we used when initializing FastMCP
    current_server_id = "basic_pentest_tools_v1" 
    
    print("Initializing Basic Network Tools MCP Server...")
    
    # For the startup message, explicitly list the tools defined in this script.
    # The actual tool list for clients is exposed via the MCP ListToolsRequest.
    defined_tool_names = ["ping_target", "simple_http_get"]
    print(f"Serving tools: {defined_tool_names}")
    
    # Print the server_id used during initialization
    print(f"MCP Server ID: {current_server_id}") 
    
    print("Server is starting with 'stdio' transport.")
    print("An MCP client can now connect and send ListTools or CallTool requests.")
    mcp.run(transport='stdio')