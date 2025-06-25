from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin, urlparse
import sys
from config import BURP_PROXY, SCAN_DEPTH, DRIVER_PATH, SCAN_DELAY, USER_AGENT

# Initialize visited URLs set
visited_urls = set()

def configure_browser():
    """Configure browser to use Burp proxy"""
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=http://' + BURP_PROXY)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--headless=new')  # New headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(f'user-agent={USER_AGENT}')
    return webdriver.Chrome(options=chrome_options)

def get_all_links(url, soup):
    """Extract all unique links from a page"""
    domain = urlparse(url).netloc
    links = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Skip non-web links
        if href.startswith(('javascript:', 'mailto:', 'tel:')):
            continue
            
        full_url = urljoin(url, href)
        parsed_url = urlparse(full_url)
        
        # Filter to same domain and valid paths
        if parsed_url.netloc == domain:
            # Normalize URL by removing fragments
            clean_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            if parsed_url.query:
                clean_url += "?" + parsed_url.query
                
            links.add(clean_url)
    
    return links

def submit_form(driver, form, base_url):
    """Automatically submit forms with test data"""
    try:
        # Build form data
        form_data = {}
        action = form.get('action', '')
        form_url = urljoin(base_url, action)
        method = form.get('method', 'get').lower()
        
        # Find all inputs
        inputs = form.find_all(['input', 'textarea', 'select'])
        for input_field in inputs:
            name = input_field.get('name')
            if name and input_field.get('type') != 'hidden':
                # Use different test data based on field type
                if input_field.get('type') == 'email':
                    form_data[name] = 'test@example.com'
                elif input_field.get('type') == 'password':
                    form_data[name] = 'password123'
                elif input_field.name == 'select':
                    options = input_field.find_all('option')
                    if options:
                        form_data[name] = options[0].get('value', options[0].text)
                elif input_field.get('type') == 'checkbox':
                    form_data[name] = 'on'
                else:
                    form_data[name] = 'test'
        
        # Submit the form
        driver.get(form_url)
        time.sleep(1)  # Wait for form to load
        
        for name, value in form_data.items():
            try:
                element = driver.find_element(By.NAME, name)
                element.clear()
                element.send_keys(value)
            except:
                pass
        
        time.sleep(0.5)
        
        # Try to find submit button
        try:
            submit_button = driver.find_element(By.XPATH, "//form//*[@type='submit']")
            submit_button.click()
        except:
            # If no submit button found, submit the first form
            driver.execute_script("document.forms[0].submit();")
            
        time.sleep(2)
        print(f"Submitted form to {form_url}")
            
    except Exception as e:
        print(f"Error submitting form: {str(e)}")

def scan_page(driver, url, depth=0):
    """Recursive function to scan pages"""
    if depth > SCAN_DEPTH or url in visited_urls:
        return
    
    print(f"📡 Scanning: {url} (Depth: {depth})")
    visited_urls.add(url)
    
    try:
        # Visit the page with delay to avoid overwhelming server
        time.sleep(SCAN_DELAY)
        driver.get(url)
        time.sleep(2)  # Wait for page to load
        
        # Extract page content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find forms and simulate submissions
        forms = soup.find_all('form')
        if forms:
            print(f"🔍 Found {len(forms)} forms on {url}")
            for form in forms:
                submit_form(driver, form, url)
        
        # Recursively scan linked pages
        if depth < SCAN_DEPTH:
            links = get_all_links(url, soup)
            print(f"🔗 Found {len(links)} links on {url}")
            for link in links:
                scan_page(driver, link, depth+1)
                
    except WebDriverException as e:
        print(f"🚨 Browser error scanning {url}: {str(e)}")
    except Exception as e:
        print(f"⚠️ General error scanning {url}: {str(e)}")

def start_scan(target_url):
    """Main function to start the scan"""
    global visited_urls
    visited_urls = set()  # Reset for new scan
    
    # Configure and start browser
    driver = configure_browser()
    print("🌐 Browser configured with Burp Suite proxy")
    
    try:
        print(f"🚀 Starting scan of {target_url}")
        scan_page(driver, target_url)
        print(f"✅ Scan completed! Visited {len(visited_urls)} pages.")
        return list(visited_urls)
    finally:
        driver.quit()
        print("🛑 Browser closed")