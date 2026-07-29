import urllib.request
import urllib.parse
import re
import csv
import json
from bs4 import BeautifulSoup

def search_part(part_number):
    """
    Searches for the part number on PartCatalog.com and returns the product page URL.
    """
    search_url = f"https://www.partcatalog.com/search?q={urllib.parse.quote(part_number)}"
    req = urllib.request.Request(
        search_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all links containing /products/ and the part number
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if '/products/' in href and part_number in href:
                    # Construct full URL
                    if href.startswith('/'):
                        return f"https://www.partcatalog.com{href.split('?')[0]}"
                    return href.split('?')[0]
    except Exception as e:
        print(f"Error searching part {part_number}: {e}")
    return None

def scrape_product_page(product_url):
    """
    Scrapes the title, specifications, vehicle compatibility list, and interchange numbers
    from the PartCatalog product page.
    """
    req = urllib.request.Request(
        product_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. Scrape Title
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else ""
            
            # 2. Scrape Specifications (Table 0)
            specs = {}
            # Locate specifications table (usually the first table on the page)
            tables = soup.find_all('table')
            if tables:
                for row in tables[0].find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == 2:
                        key = cells[0].text.strip()
                        val = cells[1].text.strip()
                        specs[key] = val
                        
            # 3. Scrape Compatibility (Table 1)
            compatibility = []
            if len(tables) > 1:
                headers = []
                for row_idx, row in enumerate(tables[1].find_all('tr')):
                    if row_idx == 0:
                        headers = [cell.text.strip() for cell in row.find_all(['th', 'td'])]
                    else:
                        cells = [cell.text.strip() for cell in row.find_all('td')]
                        if len(cells) == len(headers):
                            compatibility.append(dict(zip(headers, cells)))
            
            # 4. Scrape Interchange Numbers
            interchange_numbers = []
            interchange_container = soup.find('div', class_='pv2-interchange-grid')
            if interchange_container:
                chips = interchange_container.find_all('span', class_='pv2-interchange-chip')
                interchange_numbers = [chip.text.strip() for chip in chips]
            else:
                # Fallback to json-ld search
                json_ld_script = soup.find('script', type='application/ld+json')
                if json_ld_script:
                    try:
                        data = json.loads(json_ld_script.string)
                        if isinstance(data, dict):
                            # Try to find Interchange Numbers in additionalProperty
                            for prop in data.get('additionalProperty', []):
                                if prop.get('name') == 'Interchange Numbers':
                                    interchange_numbers = [n.strip() for n in prop.get('value', '').split(',') if n.strip()]
                    except Exception:
                        pass

            return {
                'url': product_url,
                'title': title,
                'specifications': specs,
                'compatibility': compatibility,
                'interchange_numbers': interchange_numbers
            }
            
    except Exception as e:
        print(f"Error scraping product page {product_url}: {e}")
    return None

def process_part(part_number):
    print(f"Searching for part: {part_number}...")
    url = search_part(part_number)
    if not url:
        print(f"Could not find product page for part number: {part_number}")
        return None
    
    print(f"Found product page: {url}")
    print("Scraping details...")
    data = scrape_product_page(url)
    return data

if __name__ == "__main__":
    # Example run for Dorman 76916
    part = "76916"
    result = process_part(part)
    if result:
        print("\n--- RESULTS ---")
        print("Title:", result['title'])
        print("Interchange Numbers:", result['interchange_numbers'])
        print("Specifications:")
        for k, v in result['specifications'].items():
            print(f"  {k}: {v}")
        print(f"Compatibility (Fits {len(result['compatibility'])} vehicles):")
        for fit in result['compatibility'][:5]:
            print(f"  {fit.get('Year')} {fit.get('Make')} {fit.get('Model')} - {fit.get('Notes')}")
        if len(result['compatibility']) > 5:
            print(f"  ... and {len(result['compatibility']) - 5} more vehicles")
