#!/usr/bin/env python3
"""
Test client for the MarkItDown API.
This script demonstrates how to use the API to convert a document to Markdown.
"""

import argparse
import requests
import sys
import json


def convert_file(file_path, api_url, enable_plugins=False, use_docintel=False, docintel_endpoint=None):
    """
    Convert a file to Markdown using the MarkItDown API.
    
    Args:
        file_path (str): Path to the file to convert
        api_url (str): URL of the MarkItDown API
        enable_plugins (bool): Whether to enable plugins
        use_docintel (bool): Whether to use Azure Document Intelligence
        docintel_endpoint (str): Azure Document Intelligence endpoint
    
    Returns:
        dict: API response containing the Markdown content and metadata
    """
    # Prepare options
    options = {
        "enable_plugins": str(enable_plugins).lower(),
        "use_docintel": str(use_docintel).lower(),
    }
    
    if docintel_endpoint:
        options["docintel_endpoint"] = docintel_endpoint
    
    # Upload the file
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{api_url}/convert", files=files, data=options)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}", file=sys.stderr)
        sys.exit(1)
    
    # Return the response
    return response.json()


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Convert a file to Markdown using the MarkItDown API")
    parser.add_argument("file", help="Path to the file to convert")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL of the MarkItDown API")
    parser.add_argument("--enable-plugins", action="store_true", help="Enable plugins")
    parser.add_argument("--use-docintel", action="store_true", help="Use Azure Document Intelligence")
    parser.add_argument("--docintel-endpoint", help="Azure Document Intelligence endpoint")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output the full JSON response")
    
    args = parser.parse_args()
    
    # Convert the file
    result = convert_file(
        args.file,
        args.api_url,
        args.enable_plugins,
        args.use_docintel,
        args.docintel_endpoint
    )
    
    # Output the result
    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = result["markdown_content"]
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main() 