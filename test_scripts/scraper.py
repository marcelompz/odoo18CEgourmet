import urllib.request
from bs4 import BeautifulSoup
import csv
import os
import re
import time
import ssl

base_url = "https://www.electropar.com.py/categorias/ferreteria-en-general-4?page="
headers = {'User-Agent': 'Mozilla/5.0'}
images_dir = "/opt/odoo/odoo8084/electropar_images"
csv_file_path = "/opt/odoo/odoo8084/electropar_products.csv"

# Ensure the images directory exists
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

def clean_filename(name):
    # Remove invalid characters for filenames
    return re.sub(r'[^A-Za-z0-9_\-\.]', '_', name)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Name', 'Price', 'Category', 'POS_Category', 'Image_URL', 'Local_Image_Path'])
    
    page = 1
    total_count = 0
    category_name = "FERRETERÍA EN GENERAL"
    
    while True:
        print(f"Scraping page {page}...", flush=True)
        url = f"{base_url}{page}"
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
                html = response.read().decode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')
                
                if page == 1 and soup.title:
                    title_text = soup.title.text
                    if '|' in title_text:
                        category_name = title_text.split('|')[0].strip()
                
                products = soup.find_all('div', class_='product-item')
                if not products:
                    print("No more products found. Ending pagination.", flush=True)
                    break
                    
                page_count = 0
                for p in products:
                    title_el = p.find('h3', class_='product-item__title')
                    name = title_el.text.strip() if title_el else ''
                    
                    price_el = p.find('div', class_='product-item__price')
                    price = price_el.text.strip() if price_el else ''
                    if not price:
                        price_el = p.find('span', class_='product-row__price-value')
                        price = price_el.text.strip() if price_el else ''
                        
                    img_el = p.find('img', class_='product-item__thumbnail')
                    if not img_el:
                        img_el = p.find('img', class_='product-row__thumbnail')
                    img_url = img_el.get('src') if img_el else ''
                    
                    if name:
                        local_image_path = ""
                        if img_url:
                            if img_url.startswith('/'):
                                img_url = "https://www.electropar.com.py" + img_url
                                
                            try:
                                ext = os.path.splitext(img_url.split('?')[0])[1]
                                if not ext:
                                    ext = '.jpg'
                                safe_name = clean_filename(name) + ext
                                local_image_path = os.path.join(images_dir, safe_name)
                                
                                if not os.path.exists(local_image_path):
                                    img_req = urllib.request.Request(img_url, headers=headers)
                                    with urllib.request.urlopen(img_req, timeout=15, context=ctx) as img_res, open(local_image_path, 'wb') as f:
                                        f.write(img_res.read())
                                        print(f"  Downloaded image for: {name}", flush=True)
                                else:
                                    # print(f"  Image already exists for: {name}", flush=True)
                                    pass
                            except Exception as img_e:
                                print(f"  Error downloading image for {name}: {img_e}", flush=True)
                        
                        writer.writerow([name, price, category_name, category_name, img_url, local_image_path])
                        page_count += 1
                        total_count += 1
                
                print(f"  -> Extracted {page_count} products from page {page}.", flush=True)
                page += 1
                time.sleep(1) 
                
        except Exception as e:
            print(f"Error fetching page {page}: {e}", flush=True)
            break

print(f"Successfully scraped a total of {total_count} products and saved to {csv_file_path}", flush=True)
