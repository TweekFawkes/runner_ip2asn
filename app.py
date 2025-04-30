import argparse
import socket
import sys

### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ###

def get_cymru_whois_info(ip_address):
    """
    Queries Team Cymru's WHOIS service (port 43) for information about an IP address.

    Args:
        ip_address: The IP address string to query.

    Returns:
        A dictionary containing the parsed WHOIS information, or None if an error occurs.
        Example keys: 'AS', 'IP', 'BGP Prefix', 'CC', 'Registry', 'Allocated', 'AS Name'
    """
    server = "whois.cymru.com"
    port = 43
    timeout_seconds = 10 # Connection and read timeout

    try:
        # Use socket context manager for automatic closing
        with socket.create_connection((server, port), timeout=timeout_seconds) as sock:
            sock.settimeout(timeout_seconds) # Set timeout for recv as well
            # Send query using bulk format with verbose flag
            query = f"begin\nverbose\n{ip_address}\nend\n".encode('utf-8')
            sock.sendall(query)

            # Receive response
            response_bytes = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_bytes += chunk
                except socket.timeout:
                    print(f"[!] Error: Timeout receiving data from {server}:{port}", file=sys.stderr)
                    return None
                except socket.error as e:
                    # Handle potential connection reset or other errors during recv
                    print(f"[!] Error: Socket error receiving data from {server}:{port}: {e}", file=sys.stderr)
                    return None


            response_str = response_bytes.decode('utf-8')
            lines = response_str.strip().splitlines()

            # Basic validation and parsing
            # Expect at least 2 lines: Bulk mode info and data line
            if len(lines) < 2:
                print(f"[!] Error: Received unexpected response format from {server} (lines={len(lines)}). Expected at least 2 lines.", file=sys.stderr)
                print(f"""Full response:
{response_str}""", file=sys.stderr)
                return None

            # Define expected headers based on Cymru format
            # AS | IP | BGP Prefix | CC | Registry | Allocated | AS Name
            expected_headers = ['AS', 'IP', 'BGP Prefix', 'CC', 'Registry', 'Allocated', 'AS Name']

            # The second line should be the data line
            data_line = lines[1]

            # Clean up and split data
            data = [d.strip() for d in data_line.split('|')]

            if len(expected_headers) != len(data):
                print(f"[!] Error: Expected header ({len(expected_headers)}) and data ({len(data)}) field count mismatch.", file=sys.stderr)
                print(f"Expected Headers: {' | '.join(expected_headers)}", file=sys.stderr)
                print(f"Data Line:      {data_line}", file=sys.stderr)
                return None

            # Create result dictionary
            result = dict(zip(expected_headers, data))

            # Check if the returned IP matches the queried IP (basic sanity check)
            # Allow for cases where the query IP doesn't directly appear (e.g., for ASN queries, though we don't do that here)
            # or if the IP key is missing for some reason.
            if 'IP' in result and result['IP'] != ip_address:
                 print(f"[!] Warning: Queried IP {ip_address} but response IP is {result.get('IP')}", file=sys.stderr)
                 # Continue processing, but warn the user.

            # Check for empty ASN, which indicates an unallocated or bogon IP
            if 'AS' not in result or not result['AS'] or result['AS'].lower() == 'na':
                print(f"[!] Info: IP {ip_address} appears to be unallocated or is a Bogon (No ASN found).", file=sys.stderr)
                # Return the partial info we might have received
                # return None # Option: return None if no ASN

            return result

    except socket.timeout:
        print(f"[!] Error: Timeout connecting to {server}:{port}", file=sys.stderr)
        return None
    except socket.gaierror as e:
        print(f"[!] Error: Could not resolve hostname {server}: {e}", file=sys.stderr)
        return None
    except socket.error as e:
        print(f"[!] Error: Socket error connecting or communicating with {server}:{port}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[!] Error: Unexpected error during WHOIS lookup: {e}", file=sys.stderr)
        return None

### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ###

def main():
    parser = argparse.ArgumentParser(description="Lookup IP Address ASN and BGP info using Team Cymru's WHOIS service.")
    # Use a positional argument for the IP address
    parser.add_argument('ip_address', help='IP Address to Get Information For')
    args = parser.parse_args()

    ip_address = args.ip_address

    # Basic IP format validation (optional but recommended)
    # Add more robust validation if needed (e.g., using ipaddress module)
    if '.' not in ip_address and ':' not in ip_address:
         print(f"[!] Error: '{ip_address}' does not look like a valid IPv4 or IPv6 address.", file=sys.stderr)
         return 1

    print(f"[*] Querying Team Cymru WHOIS for IP: {ip_address}...")
    whois_info = get_cymru_whois_info(ip_address)

    if whois_info:
        print("\n--- Team Cymru WHOIS Information ---")
        # Determine max key length for alignment, handle empty dict case
        max_key_len = 0
        if whois_info:
             try:
                 max_key_len = max(len(key) for key in whois_info.keys()) if whois_info else 0
             except ValueError: # Handle case where whois_info might be empty dict
                 max_key_len = 0


        for key, value in whois_info.items():
            # Simple aligned print
             print(f"{key:<{max_key_len}} : {value if value else 'N/A'}") # Display 'N/A' for empty values
        print("------------------------------------\n")
        # Check if essential info like ASN is present before declaring full success
        if 'AS' in whois_info and whois_info['AS'] and whois_info['AS'].lower() != 'na':
            return 0 # Success
        else:
            # Considered partial success / info only if ASN missing
            return 1 # Indicate potential issue / missing data
    else:
        print(f"[!] Failed to retrieve WHOIS information for {ip_address}.")
        return 1 # Failure

### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ### --- ###

if __name__ == "__main__":
    # Use sys.exit() to ensure the exit code is propagated correctly
    sys.exit(main())