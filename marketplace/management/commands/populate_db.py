from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from marketplace.models import Vendor, Product, Category, User, UserProfile
from faker import Faker
import random
import requests
from io import BytesIO
from PIL import Image
import time

class Command(BaseCommand):
    help = 'Populate the database with fake data including images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vendors',
            type=int,
            default=10,
            help='Number of vendors to create'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=50,
            help='Number of products to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def download_and_process_image(self, search_term, image_id, width=800, height=600, attempt=0):
        """Download and process image with multiple fallback options"""
        max_attempts = 3
        
        # Try different image sources
        image_urls = [
            f'https://source.unsplash.com/{width}x{height}/?{search_term}&sig={random.randint(1, 10000)}',
            f'https://picsum.photos/{width}/{height}?random={image_id}{attempt}',
            f'https://loremflickr.com/{width}/{height}/{search_term.replace("+", ",")}'
        ]
        
        for url in image_urls:
            try:
                response = requests.get(url, timeout=15, allow_redirects=True)
                if response.status_code == 200 and len(response.content) > 1000:  # Ensure valid image
                    # Open and process image
                    img = Image.open(BytesIO(response.content))
                    
                    # Resize to standard size
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Save to BytesIO
                    img_io = BytesIO()
                    img.save(img_io, format='JPEG', quality=85)
                    img_io.seek(0)
                    
                    return ContentFile(img_io.read())
                    
            except Exception as e:
                continue
        
        # If all sources fail and we haven't exceeded max attempts, retry
        if attempt < max_attempts:
            time.sleep(2)  # Wait before retry
            return self.download_and_process_image(search_term, image_id, width, height, attempt + 1)
        
        return None

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Product.objects.all().delete()
            Vendor.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Data cleared!'))

        # Create categories with images
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Phones, laptops, and tech gadgets',
                'search': 'electronics+technology+gadgets'
            },
            {
                'name': 'Fashion',
                'description': 'Clothing, shoes, and accessories',
                'search': 'fashion+clothing+style'
            },
            {
                'name': 'Home & Garden',
                'description': 'Furniture and home decor',
                'search': 'furniture+home+interior'
            },
            {
                'name': 'Sports & Outdoors',
                'description': 'Sports equipment and outdoor gear',
                'search': 'sports+fitness+outdoor'
            },
            {
                'name': 'Books & Media',
                'description': 'Books, movies, and music',
                'search': 'books+library+reading'
            },
            {
                'name': 'Toys & Games',
                'description': 'Toys and gaming products',
                'search': 'toys+games+play'
            },
            {
                'name': 'Beauty & Health',
                'description': 'Beauty and health products',
                'search': 'beauty+cosmetics+skincare'
            },
            {
                'name': 'Automotive',
                'description': 'Car parts and accessories',
                'search': 'car+automotive+vehicle'
            },
        ]

        self.stdout.write('Creating categories with images...')
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description']
                }
            )
            
            # Add image to category if it doesn't have one
            if created or not category.image:
                self.stdout.write(f'  Downloading image for {category.name}...', ending='')
                image_content = self.download_and_process_image(
                    cat_data['search'], 
                    category.id,
                    width=1200,
                    height=800
                )
                
                if image_content:
                    filename = f'category_{category.id}_{random.randint(1000, 9999)}.jpg'
                    category.image.save(filename, image_content, save=True)
                    self.stdout.write(self.style.SUCCESS(f' ✓ Created: {category.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f' ⚠ No image: {category.name}'))
            else:
                self.stdout.write(f'  ✓ Already exists: {category.name}')
            
            categories.append(category)

        # Nigerian cities for vendors
        nigerian_cities = [
            'Lagos', 'Abuja', 'Port Harcourt', 'Ibadan', 'Kano',
            'Benin City', 'Enugu', 'Kaduna', 'Jos', 'Warri'
        ]

        # Create vendors
        self.stdout.write('\nCreating vendors...')
        vendors = []
        for i in range(options['vendors']):
            username = fake.user_name() + str(random.randint(1000, 9999))
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )

            # Generate unique vendor name and slug
            vendor_name = fake.company()
            from django.utils.text import slugify
            base_slug = slugify(vendor_name)
            slug = base_slug
            counter = 1
            
            # Ensure unique slug
            while Vendor.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            vendor = Vendor.objects.create(
                user=user,
                name=vendor_name,
                slug=slug,
                location=random.choice(nigerian_cities),
                description=fake.text(max_nb_chars=200),
                contact_email=fake.email(),
                contact_phone=f'+234{random.randint(7000000000, 9099999999)}'
            )
            vendors.append(vendor)
            self.stdout.write(f'  ✓ Created vendor: {vendor.name}')

        # Product templates by category with specific search terms
        product_templates = {
            'Electronics': {
                'products': [
                    ('Smartphone', 'smartphone+mobile'),
                    ('Laptop', 'laptop+computer'),
                    ('Tablet', 'tablet+ipad'),
                    ('Smartwatch', 'smartwatch+wearable'),
                    ('Headphones', 'headphones+audio'),
                    ('Camera', 'camera+photography'),
                    ('Gaming Console', 'gaming+console'),
                    ('Monitor', 'monitor+display'),
                    ('Keyboard', 'keyboard+mechanical'),
                    ('Mouse', 'mouse+gaming')
                ]
            },
            'Fashion': {
                'products': [
                    ('T-Shirt', 'tshirt+fashion'),
                    ('Jeans', 'jeans+denim'),
                    ('Sneakers', 'sneakers+shoes'),
                    ('Dress', 'dress+fashion'),
                    ('Jacket', 'jacket+coat'),
                    ('Handbag', 'handbag+purse'),
                    ('Sunglasses', 'sunglasses+eyewear'),
                    ('Watch', 'watch+timepiece'),
                    ('Belt', 'belt+leather'),
                    ('Hat', 'hat+cap')
                ]
            },
            'Home & Garden': {
                'products': [
                    ('Sofa', 'sofa+couch'),
                    ('Dining Table', 'dining+table'),
                    ('Bed Frame', 'bed+frame'),
                    ('Lamp', 'lamp+lighting'),
                    ('Rug', 'rug+carpet'),
                    ('Garden Tools', 'garden+tools'),
                    ('Plant Pot', 'plant+pot'),
                    ('Cushions', 'cushion+pillow'),
                    ('Mirror', 'mirror+decor'),
                    ('Curtains', 'curtains+drapes')
                ]
            },
            'Sports & Outdoors': {
                'products': [
                    ('Football', 'football+soccer'),
                    ('Basketball', 'basketball+ball'),
                    ('Tennis Racket', 'tennis+racket'),
                    ('Bicycle', 'bicycle+bike'),
                    ('Treadmill', 'treadmill+fitness'),
                    ('Yoga Mat', 'yoga+mat'),
                    ('Dumbbells', 'dumbbells+weights'),
                    ('Camping Tent', 'camping+tent'),
                    ('Hiking Boots', 'hiking+boots'),
                    ('Backpack', 'backpack+outdoor')
                ]
            },
            'Books & Media': {
                'products': [
                    ('Novel', 'novel+book'),
                    ('Cookbook', 'cookbook+recipe'),
                    ('Biography', 'biography+book'),
                    ('Self-Help Book', 'selfhelp+book'),
                    ('Comic Book', 'comic+book'),
                    ('DVD Set', 'dvd+movie'),
                    ('Vinyl Record', 'vinyl+record'),
                    ('Magazine Subscription', 'magazine+reading'),
                    ('E-Reader', 'ereader+kindle'),
                    ('Art Book', 'artbook+illustration')
                ]
            },
            'Toys & Games': {
                'products': [
                    ('Action Figure', 'action+figure'),
                    ('Board Game', 'boardgame+game'),
                    ('Puzzle', 'puzzle+jigsaw'),
                    ('Doll', 'doll+toy'),
                    ('LEGO Set', 'lego+blocks'),
                    ('Video Game', 'videogame+gaming'),
                    ('RC Car', 'rc+car'),
                    ('Stuffed Animal', 'stuffed+animal'),
                    ('Building Blocks', 'building+blocks'),
                    ('Card Game', 'card+game')
                ]
            },
            'Beauty & Health': {
                'products': [
                    ('Skincare Set', 'skincare+cosmetics'),
                    ('Perfume', 'perfume+fragrance'),
                    ('Makeup Kit', 'makeup+cosmetics'),
                    ('Hair Dryer', 'hairdryer+beauty'),
                    ('Face Mask', 'facemask+skincare'),
                    ('Vitamins', 'vitamins+supplements'),
                    ('Fitness Tracker', 'fitness+tracker'),
                    ('Massage Gun', 'massage+gun'),
                    ('Essential Oils', 'essential+oils'),
                    ('Nail Polish', 'nailpolish+beauty')
                ]
            },
            'Automotive': {
                'products': [
                    ('Car Battery', 'car+battery'),
                    ('Tire Set', 'tire+wheel'),
                    ('Car Cover', 'car+cover'),
                    ('GPS Navigator', 'gps+navigation'),
                    ('Dash Cam', 'dashcam+camera'),
                    ('Car Vacuum', 'car+vacuum'),
                    ('Jump Starter', 'jump+starter'),
                    ('Floor Mats', 'car+mats'),
                    ('Air Freshener', 'car+freshener'),
                    ('Tool Kit', 'tool+kit')
                ]
            }
        }

        # Create products with images
        self.stdout.write('\nCreating products with images...')
        self.stdout.write('(This may take a while as images are being downloaded...)\n')
        
        products_created = 0
        products_skipped = 0
        
        for i in range(options['products']):
            category = random.choice(categories)
            vendor = random.choice(vendors)
            
            # Get product template with search term
            templates = product_templates.get(category.name, {}).get('products', [('Product', 'product')])
            product_type, search_term = random.choice(templates)
            brand = fake.company().split()[0]
            
            # Generate realistic product name
            product_name = f"{brand} {product_type}"
            
            # Generate price (in Naira)
            base_price = random.randint(5000, 500000)
            price = round(base_price, -2)  # Round to nearest 100
            
            # Sometimes add a discount
            compare_at_price = None
            if random.random() > 0.6:  # 40% chance of discount
                compare_at_price = price + random.randint(5000, 50000)
            
            # Download image BEFORE creating product using specific search term
            self.stdout.write(f'  [{i+1}/{options["products"]}] Downloading image for {product_name}...', ending='')
            image_content = self.download_and_process_image(search_term, i)
            
            if image_content is None:
                self.stdout.write(self.style.WARNING(f' ✗ SKIPPED'))
                products_skipped += 1
                continue  # Skip this product if no image available
            
            # Create product with image
            product = Product.objects.create(
                vendor=vendor,
                category=category,
                name=product_name,
                description=fake.text(max_nb_chars=300),
                price=price,
                compare_at_price=compare_at_price,
                stock=random.randint(0, 100),
                is_featured=random.random() > 0.7,  # 30% featured
                is_active=True
            )
            
            # Save the image
            filename = f'product_{product.id}_{random.randint(1000, 9999)}.jpg'
            product.image.save(filename, image_content, save=True)
            
            products_created += 1
            self.stdout.write(self.style.SUCCESS(f' ✓'))
            
            # Small delay to avoid rate limiting
            if i % 5 == 0 and i > 0:
                time.sleep(1)
                self.stdout.write(f'\n  Progress: {products_created} created, {products_skipped} skipped\n')

        # Create some customer accounts
        self.stdout.write('\nCreating customer accounts...')
        for i in range(5):
            username = fake.user_name() + str(random.randint(1000, 9999))
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            
            # Update profile with shipping info
            profile = user.profile
            profile.phone = f'+234{random.randint(7000000000, 9099999999)}'
            profile.shipping_address = fake.street_address()
            profile.shipping_city = random.choice(nigerian_cities)
            profile.shipping_state = random.choice(['Lagos', 'Oyo', 'Rivers', 'Abuja FCT', 'Kano'])
            profile.shipping_postal_code = fake.postcode()
            profile.shipping_country = 'Nigeria'
            profile.bio = fake.text(max_nb_chars=100)
            profile.save()
            
            self.stdout.write(f'  ✓ Created customer: {user.username}')

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('\n✓ Database population complete!\n'))
        self.stdout.write(f'  Categories: {Category.objects.count()}')
        self.stdout.write(f'  Categories with images: {Category.objects.exclude(image="").count()}')
        self.stdout.write(f'  Vendors: {Vendor.objects.count()}')
        self.stdout.write(f'  Products: {Product.objects.count()}')
        self.stdout.write(f'  Products with images: {Product.objects.exclude(image="").count()}')
        self.stdout.write(f'  Products skipped: {products_skipped}')
        self.stdout.write(f'  Users: {User.objects.count()}')
        self.stdout.write('\n' + '='*50)
        
        self.stdout.write('\nLogin credentials for testing:')
        self.stdout.write('  Username: Any vendor/customer username from above')
        self.stdout.write('  Password: password123')
        self.stdout.write('\nOr create a superuser with: python manage.py createsuperuser\n')