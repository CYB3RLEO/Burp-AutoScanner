from scanner import start_scan
from report_generator import generate_html_report
import sys
import os
import time
import re
from urllib.parse import urlparse
from config import OUTPUT_DIR

def validate_url(url):
    """Ensure URL has proper format"""
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = 'http://' + url
    
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
        return url
    except:
        raise ValueError("Invalid URL format")

def main():
    print("""
    🛡️ Burp Suite Automated Scanner 🛡️
    ==================================
    """)
    
    # Get target URL from command line or user input
    if len(sys.argv) > 1:
        target_url = ' '.join(sys.argv[1:])
    else:
        target_url = input("Enter target URL to scan: ")
    
    try:
        target_url = validate_url(target_url)
        print(f"✅ Validated URL: {target_url}")
    except ValueError as e:
        print(f"❌ Invalid URL: {str(e)}")
        print("Please enter a valid URL (e.g., http://example.com or example.com)")
        return
    
    print("\n⚠️ IMPORTANT PREPARATION:")
    print("1. Open Burp Suite Community Edition")
    print("2. Go to Proxy → Options")
    print("3. Ensure proxy is running on 127.0.0.1:8080")
    print("4. Turn 'Intercept' OFF")
    print("5. Ensure logging is enabled in Dashboard")
    print("\nStarting scan in 10 seconds...")
    
    # Countdown to allow Burp configuration
    for i in range(10, 0, -1):
        print(f"{i}...", end=' ', flush=True)
        time.sleep(1)
    print("\n")
    
    # Run scan
    try:
        visited_urls = start_scan(target_url)
    except Exception as e:
        print(f"🔥 Scan failed: {str(e)}")
        return
    
    # Generate report
    try:
        report_path = generate_html_report(target_url, visited_urls)
    except Exception as e:
        print(f"🔥 Report generation failed: {str(e)}")
        return
    
    # Final instructions
    print("\n✅ SCAN COMPLETE! NEXT STEPS:")
    print(f"1. Review Burp Suite's HTTP history for findings")
    print(f"2. Open scan report: file://{os.path.abspath(report_path)}")
    print("3. Manually export findings from Burp Suite (Target → Site Map → Save)")
    print("\n🔥 Tip: For vulnerability details, examine Burp's 'Dashboard' and 'Target' tabs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Scan aborted by user")
    except Exception as e:
        print(f"🔥 Critical error: {str(e)}")