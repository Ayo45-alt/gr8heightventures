import os
import sys
import glob
import re
import shutil
from django.utils.text import slugify
from PIL import Image
import numpy as np

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greatkart.settings')
import django
django.setup()

from category.models import Category
from store.models import Product, Variation

def run_import():
    print("=== STARTING REFINED KEMI'S BOUTIQUE CATALOG IMPORT ===")
    
    # 1. Setup Categories
    categories_data = [
        {'name': 'Shoes', 'slug': 'shoes', 'desc': 'Curated luxury heels, sandals, flats, boots, and sneakers.'},
        {'name': 'Dresses', 'slug': 'dresses', 'desc': 'Elegant evening gowns, cocktail dresses, and everyday styles.'},
        {'name': 'Tops & Blouses', 'slug': 'tops', 'desc': 'Chic blouses, tops, and knitwear.'},
        {'name': 'Trousers & Pants', 'slug': 'trousers', 'desc': 'Tailored trousers, suiting pants, and denim.'},
        {'name': 'Jackets & Outerwear', 'slug': 'jackets', 'desc': 'Tailored blazers, jackets, and outerwear.'},
    ]
    
    cats = {}
    for cdata in categories_data:
        cat, created = Category.objects.get_or_create(
            slug=cdata['slug'],
            defaults={'category_name': cdata['name'], 'description': cdata['desc']}
        )
        if cat.category_name != cdata['name']:
            cat.category_name = cdata['name']
            cat.description = cdata['desc']
            cat.save()
        cats[cdata['slug']] = cat

    # Clear old products
    Product.objects.all().delete()
    print("Cleared existing products from database.")

    products_dest_dir = os.path.join('media', 'photos', 'products')
    os.makedirs(products_dest_dir, exist_ok=True)

    clothes_dir = 'C:/Users/USER/Desktop/sample_studio_matches/clothes'
    shoes_dir = 'C:/Users/USER/Desktop/sample_studio_matches/shoes'
    review_files = sorted(glob.glob('C:/Users/USER/.gemini/antigravity/brain/3b8d05c7-ecdb-4dab-9ffb-cb333b4de9ea/batch*_review.md'))

    # 2. Parse and Import Clothes
    clothes_count = 0
    for rf in review_files:
        with open(rf, encoding='utf-8') as fp:
            text = fp.read()
        sections = re.split(r'\n(?=##\s+)', text)
        for s in sections:
            m = re.search(r'##\s+(?:Item\s+|(?:\d+\.\s+Item\s+))([^\n:]+):\s*([^\n]+)', s)
            if not m:
                continue
            item_id = m.group(1).strip()
            title = m.group(2).strip()
            
            price_m = re.search(r'\*\*Price\*\*:\s*₦?([\d,]+)', s)
            price = int(price_m.group(1).replace(',', '')) if price_m else 24000
            
            size_m = re.search(r'\*\*Size\*\*:\s*([^\n|]+)', s)
            size = size_m.group(1).strip() if size_m else 'Free Size'
            
            brand_m = re.search(r'\*\*Brand\*\*:\s*([^\n|]+)', s)
            brand = brand_m.group(1).strip() if brand_m else ''
            
            desc_m = re.search(r'\*\*(?:Style\s*/\s*)?Description\*\*:\s*([^\n]+)', s)
            desc = desc_m.group(1).strip() if desc_m else f"{brand} boutique piece in {title}."

            # Determine category based on title first
            t_title = title.lower()
            if any(w in t_title for w in ['pant', 'trouser', 'jean', 'legging', 'culotte', 'capri', 'skirt', 'shorts', 'jogger']):
                cat = cats['trousers']
            elif any(w in t_title for w in ['jacket', 'bomber', 'blazer', 'coat']):
                cat = cats['jackets']
            elif 'dress' in t_title:
                cat = cats['dresses']
            else:
                cat = cats['tops']

            # Find matching image file
            found_img = None
            if os.path.exists(clothes_dir):
                for f in os.listdir(clothes_dir):
                    if (f.lower().startswith(f"clothes_{item_id.lower()}_") and ('angle_1' in f.lower() or 'front' in f.lower())) or \
                       (f.lower().startswith(f"item{item_id.lower()}_studio_front")):
                        found_img = os.path.join(clothes_dir, f)
                        break
                    elif f.lower().startswith(f"clothes_{item_id.lower()}_"):
                        found_img = os.path.join(clothes_dir, f)

            if not found_img:
                cand_imgs = glob.glob(f'C:/Users/USER/.gemini/antigravity/brain/3b8d05c7-ecdb-4dab-9ffb-cb333b4de9ea/review_images/**/item{item_id}*_front*.jpg', recursive=True)
                if cand_imgs:
                    found_img = cand_imgs[0]

            if not found_img:
                cands = glob.glob(f'{clothes_dir}/*{item_id}*')
                if cands:
                    found_img = cands[0]

            if not found_img:
                continue

            # Clean product name properly (remove unwanted symbols, keep spaces clean)
            clean_title = re.sub(r'^[^\w]+', '', title)
            clean_title = clean_title.replace('—', ' - ').replace('–', ' - ').replace('', '')
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            # Remove redundant item prefixes if any
            clean_title = re.sub(r'^\d+\.\s*', '', clean_title)
            if len(clean_title) > 65:
                clean_title = clean_title[:62] + '...'

            prod_slug = slugify(f"kemi-{item_id}-{clean_title[:30]}")
            ext = os.path.splitext(found_img)[1]
            dest_filename = f"{prod_slug}{ext}"
            dest_path = os.path.join(products_dest_dir, dest_filename)
            shutil.copy2(found_img, dest_path)

            prod = Product.objects.create(
                product_name=clean_title,
                slug=prod_slug,
                description=desc[:490],
                price=price,
                images=f"photos/products/{dest_filename}",
                stock=1,
                is_available=True,
                category=cat
            )
            
            # Add size variation (boutique single piece)
            if size:
                clean_size = size.strip()
                if '/' in clean_size:
                    parts = [p.strip() for p in clean_size.split('/') if p.strip()]
                    if len(parts) == 2:
                        clean_size = f"{parts[0]} ({parts[1]})"
                Variation.objects.create(
                    product=prod,
                    variation_category='size',
                    variation_value=clean_size[:50],
                    is_active=True
                )
            clothes_count += 1

    print(f"Imported {clothes_count} clean clothing products.")

    # 3. Import Shoes with smart image scoring
    shoes_count = 0
    if os.path.exists(shoes_dir):
        shoe_files = os.listdir(shoes_dir)
        shoes_groups = {}
        for f in shoe_files:
            m = re.match(r'^(S\d+)_(.+)\.(jpg|png|webp|jpeg)$', f, re.IGNORECASE)
            if m:
                sid = m.group(1)
                if sid not in shoes_groups:
                    shoes_groups[sid] = []
                shoes_groups[sid].append(f)

        shoe_prices = {
            'heels': 26000,
            'wedge': 24000,
            'boot': 35000,
            'sneaker': 30000,
            'sandal': 22000,
            'pump': 25000,
            'slipper': 18000,
            'default': 25000
        }

        for sid in sorted(shoes_groups.keys(), key=lambda s: int(s[1:])):
            cand_files = shoes_groups[sid]
            # score images
            scored = []
            for cf in cand_files:
                p = os.path.join(shoes_dir, cf)
                try:
                    im = Image.open(p).convert('RGB')
                    arr = np.array(im)
                    corners = [arr[0,0], arr[0,-1], arr[-1,0], arr[-1,-1]]
                    avg_corner = np.mean(corners)
                    bonus = 25 if 'pair' in cf.lower() else (15 if 'catalog' in cf.lower() else 0)
                    scored.append((avg_corner + bonus, cf))
                except Exception:
                    pass
            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0][1] if scored else cand_files[0]

            clean_name = re.sub(r'_(Pair\d*|Side|Top|Back|Catalog|Angle|Shop|Detail|Sole)$', '', best.rsplit('.', 1)[0], flags=re.IGNORECASE)
            clean_name = re.sub(r'^S\d+_', '', clean_name).replace('_', ' ').strip()
            clean_name = re.sub(r'\s+', ' ', clean_name)

            cn_lower = clean_name.lower()
            p_price = shoe_prices['default']
            for stype, pr in shoe_prices.items():
                if stype in cn_lower:
                    p_price = pr
                    break

            prod_slug = slugify(f"kemi-{sid}-{clean_name[:30]}")
            ext = os.path.splitext(best)[1]
            dest_filename = f"{prod_slug}{ext}"
            src_path = os.path.join(shoes_dir, best)
            dest_path = os.path.join(products_dest_dir, dest_filename)
            shutil.copy2(src_path, dest_path)

            prod = Product.objects.create(
                product_name=clean_name,
                slug=prod_slug,
                description=f"Authentic designer {clean_name} from Kemi's boutique collection. Hand-selected for luxury and comfort.",
                price=p_price,
                images=f"photos/products/{dest_filename}",
            stock=1,
            is_available=True,
            category=cats['shoes']
        )

        shoe_sizes = {
            's1': '38 (UK 5 / US 7.5)', 's2': '41 (UK 8 / US 10)', 's3': '39 (UK 6 / US 8.5)',
            's4': '38 (UK 5 / US 7.5)', 's5': '37 (UK 4 / US 6.5)', 's6': '39 (UK 6 / US 8.5)',
            's7': '38 (UK 5 / US 7.5)', 's8': '39 (UK 6 / US 8.5)', 's9': '40 (UK 7 / US 9)',
            's10': '38 (UK 5 / US 7.5)', 's11': '39 (UK 6 / US 8.5)', 's12': '39 (UK 6 / US 8.5)',
            's13': '38 (UK 5 / US 7.5)', 's14': '38 (UK 5 / US 7.5)', 's15': '39 (UK 6 / US 8.5)',
            's16': '38 (UK 5 / US 7.5)', 's17': '39 (UK 6 / US 8.5)', 's18': '40.5 (UK 7.5 / US 9.5)',
            's19': '39 (UK 6 / US 8.5)', 's20': '41 (UK 8 / US 10)', 's21': '39 (UK 6 / US 8.5)',
            's22': '39 (UK 6 / US 8)', 's23': '40 (UK 7 / US 9)', 's24': '39 (UK 6 / US 8.5)',
            's25': '40 (UK 7 / US 9)', 's26': '39 (UK 6 / US 8.5)', 's27': '38 (UK 5 / US 7.5)',
            's28': '36 (UK 3.5 / US 5.5)', 's29': '38.5 (UK 5.5 / US 5.5)', 's30': '39 (UK 6 / US 8.5)',
            's31': '38 (UK 5 / US 7.5)', 's32': '42 (UK 8 / US 9)',
        }
        sz_val = shoe_sizes.get(sid.lower(), '38 (UK 5 / US 7.5)')
        Variation.objects.create(
            product=prod,
            variation_category='size',
            variation_value=sz_val,
            is_active=True
        )
        shoes_count += 1

    print(f"Imported {shoes_count} clean shoe products.")
    print("=== FINAL PRODUCT BREAKDOWN ===")
    for c in Category.objects.all():
        print(f" - {c.category_name}: {c.product_set.count()} products")

if __name__ == '__main__':
    run_import()
