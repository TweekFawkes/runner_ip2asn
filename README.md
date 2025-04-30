# runner_ip2asn

A simple Python script to look up the Autonomous System Number (ASN) and related BGP information for a given IP address using the Team Cymru WHOIS service.

## Usage

```bash
python app.py <IP_ADDRESS>
```

**Example:**

```bash
python app.py 8.8.8.8
```

This will output the WHOIS information provided by Team Cymru, including:

*   AS Number
*   IP Address
*   BGP Prefix
*   Country Code (CC)
*   Registry
*   Allocation Date
*   AS Name

The script connects to `whois.cymru.com` on port 43. It includes basic error handling for network issues and timeouts. It returns an exit code of `0` if information (including an ASN) is successfully retrieved, and `1` otherwise.