import requests
from bs4 import BeautifulSoup
import json
import sys

def fetch_html(url, session, headers=None):
    """
    Fetches the HTML content from the given URL using the provided session.
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.screener.in/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch page with status code: {response.status_code}")
        return None

def extract_company_ids(soup):
    """
    Extracts the company ID and warehouse ID from the HTML page.
    """
    # Look for the div with id 'company-info'
    company_info_div = soup.find('div', id='company-info')
    if company_info_div:
        company_id = company_info_div.get('data-company-id')
        warehouse_id = company_info_div.get('data-warehouse-id')
        return company_id, warehouse_id
    else:
        print("Company ID and Warehouse ID not found in 'company-info' div.")
        return None, None

def extract_company_info(soup):
    """
    Extracts the company info part.
    """
    company_info = {}
    # Company Name
    name_tag = soup.find('h1', class_='margin-0')
    if name_tag:
        company_info['Company Name'] = name_tag.get_text(strip=True)
    else:
        company_info['Company Name'] = None

    # Stock Price
    price_tag = soup.find('span', text='Current Price')
    if price_tag:
        price_value_tag = price_tag.find_next('span', class_='number')
        if price_value_tag:
            company_info['Current Price'] = price_value_tag.get_text(strip=True)
        else:
            company_info['Current Price'] = None
    else:
        company_info['Current Price'] = None

    # Other Ratios
    ratios_list = soup.find('ul', id='top-ratios')
    if ratios_list:
        for li in ratios_list.find_all('li'):
            ratio_name_tag = li.find('span', class_='name')
            ratio_value_tag = li.find('span', class_='number')
            if ratio_name_tag and ratio_value_tag:
                ratio_name = ratio_name_tag.get_text(strip=True)
                ratio_value = ratio_value_tag.get_text(strip=True)
                company_info[ratio_name] = ratio_value
            else:
                continue
    else:
        print("No ratios found in company info.")
    return company_info

def extract_table_data(soup, section_id):
    section = soup.find('section', id=section_id)
    if not section:
        return None

    table = section.find('table')
    if not table:
        return None

    headers = []
    data_rows = []

    # Extract table headers
    thead = table.find('thead')
    if thead:
        header_cells = thead.find_all('th')
        headers = [cell.get_text(strip=True) for cell in header_cells]

    # Extract table body rows
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        for row in rows:
            # Skip rows that are notes or have different structure
            if 'class' in row.attrs and ('notes' in row['class'] or 'sub' in row['class']):
                continue
            cells = row.find_all(['th', 'td'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            data_rows.append(row_data)

    # Combine headers and data
    table_data = []
    for row in data_rows:
        # Create a dictionary for each row
        if len(row) == len(headers):
            row_dict = dict(zip(headers, row))
            table_data.append(row_dict)
        else:
            # Handle rows with missing cells
            pass  # You can add logic here to handle irregular rows

    return table_data

def extract_shareholding(soup, section_id):
    section = soup.find('section', id=section_id)
    if not section:
        return None

    # Find the active tab (Quarterly or Yearly)
    active_tab = section.find('div', id='quarterly-shp') or section.find('div', id='yearly-shp')
    if not active_tab:
        return None

    table = active_tab.find('table')
    if not table:
        return None

    headers = []
    data_rows = []

    # Extract table headers
    thead = table.find('thead')
    if thead:
        header_cells = thead.find_all('th')
        headers = [cell.get_text(strip=True) for cell in header_cells]

    # Extract table body rows
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all(['th', 'td'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            data_rows.append(row_data)

    # Combine headers and data
    shareholding_data = []
    for row in data_rows:
        if len(row) == len(headers):
            row_dict = dict(zip(headers, row))
            shareholding_data.append(row_dict)
        else:
            pass  # Handle as needed

    return shareholding_data

def extract_peer_comparison_from_html(soup):
    """
    Extracts the peer comparison data from the provided HTML soup.
    """
    table = soup.find('table')
    if not table:
        print("No Peer Comparison table found.")
        return None

    headers = []
    data_rows = []

    # Extract table headers
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        if rows:
            header_row = rows[0]
            header_cells = header_row.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_cells]
            # Remove the header row from data rows
            data_rows = rows[1:]
        else:
            print("No rows found in the peer comparison table.")
            return None
    else:
        print("No tbody found in the peer comparison table.")
        return None

    # Now extract the data rows
    peer_comparison_data = []
    for row in data_rows:
        if 'data-row-company-id' in row.attrs:
            cells = row.find_all(['th', 'td'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if len(row_data) == len(headers):
                row_dict = dict(zip(headers, row_data))
                peer_comparison_data.append(row_dict)
            else:
                # Handle rows with missing cells
                pass  # You can add logic here to handle irregular rows
        else:
            continue  # Skip rows that are not data rows

    return peer_comparison_data

# Main execution
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script_name.py STOCK_SYMBOL")
        sys.exit(1)

    stock_symbol = sys.argv[1].upper()

    # Initialize a session
    session = requests.Session()

    # URL of the company page
    company_url = f'https://www.screener.in/company/{stock_symbol}/'

    # Fetch the HTML content
    html_content = fetch_html(company_url, session)
    if not html_content:
        sys.exit("Failed to retrieve the company page.")

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')  # Use 'html.parser' if 'lxml' is not available

    # Extract company ID and warehouse ID
    company_id, warehouse_id = extract_company_ids(soup)
    if not company_id or not warehouse_id:
        sys.exit("Failed to extract company ID or Warehouse ID.")

    # Initialize a dictionary to store all data
    all_data = {}

    # Extract company info
    company_info = extract_company_info(soup)
    all_data['company_info'] = company_info

    # Sections to extract
    sections = ['quarters', 'profit-loss', 'balance-sheet', 'cash-flow', 'ratios']

    for section_id in sections:
        data = extract_table_data(soup, section_id)
        if data:
            all_data[section_id] = data
        else:
            print(f"No data found for section: {section_id}")

    # Extract shareholding pattern
    shareholding_data = extract_shareholding(soup, 'shareholding')
    if shareholding_data:
        all_data['shareholding'] = shareholding_data
    else:
        print("No data found for shareholding section.")

    # Now, fetch peers data via the API using warehouse_id
    peers_api_url = f'https://www.screener.in/api/company/{warehouse_id}/peers/'

    # Set headers for the API request
    api_headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': company_url,
        'X-Requested-With': 'XMLHttpRequest',
    }

    # Fetch the peers data
    response = session.get(peers_api_url, headers=api_headers)
    if response.status_code == 200:
        peers_html_content = response.text
        # Parse the peers_html_content with BeautifulSoup
        peers_soup = BeautifulSoup(peers_html_content, 'lxml')
        # Extract peers data
        peer_comparison_data = extract_peer_comparison_from_html(peers_soup)
        if peer_comparison_data:
            all_data['peer_comparison'] = peer_comparison_data
        else:
            print("No data found for peer comparison section.")
    else:
        print(f"Failed to fetch peers data with status code: {response.status_code}")

    # Save to JSON file named with stock symbol
    json_file_name = f'{stock_symbol}.json'
    with open(json_file_name, 'w', encoding='utf-8') as json_file:
        # print(all_data)
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)

    print(f"Data extraction complete. Check '{json_file_name}' for the output.")
