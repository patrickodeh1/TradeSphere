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

    def download_and_process_image(self, category_name, product_id, attempt=0):
        """Download and process image with multiple fallback options"""
        max_attempts = 3
        
        search_terms = {
            'Electronics': 'electronics+technology',
            'Fashion': 'fashion+clothing',
            'Home & Garden': 'furniture+home',
            'Sports & Outdoors': 'sports+fitness',
            'Books & Media': 'books+media',
            'Toys & Games': 'toys+games',
            'Beauty & Health': 'beauty+cosmetics',
            'Automotive': 'car+automotive'
        }
        
        search_term = search_terms.get(category_name, 'product')
        
        # Try different image sources
        image_urls = [
            f'https://source.unsplash.com/800x600/?{search_term}&sig={random.randint(1, 10000)}',
            f'https://picsum.photos/800/600?random={product_id}{attempt}',
            f'https://loremflickr.com/800/600/{search_term.replace("+", ",")}'
        ]
        
        for url in image_urls:
            try:
                response = requests.get(url, timeout=15, allow_redirects=True)
                if response.status_code == 200 and len(response.content) > 1000:  # Ensure valid image
                    # Open and process image
                    img = Image.open(BytesIO(response.content))
                    
                    # Resize to standard size
                    img = img.resize((800, 600), Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Save to BytesIO
                    img_io = BytesIO()
                    img.save(img_io, format='JPEG', quality=85)
                    img_io.seek(0)
                    
                    filename = f'product_{product_id}_{random.randint(1000, 9999)}.jpg'
                    return filename, ContentFile(img_io.read())
                    
            except Exception as e:
                continue
        
        # If all sources fail and we haven't exceeded max attempts, retry
        if attempt < max_attempts:
            time.sleep(2)  # Wait before retry
            return self.download_and_process_image(category_name, product_id, attempt + 1)
        
        return None, None

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Product.objects.all().delete()
            Vendor.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Data cleared!'))

        # Create categories with icons
        categories_data = [
            {'name': 'Electronics', 'description': 'Phones, laptops, and gadgets', 'icon': 'fa-laptop'},
            {'name': 'Fashion', 'description': 'Clothing, shoes, and accessories', 'icon': 'fa-tshirt'},
            {'name': 'Home & Garden', 'description': 'Furniture and home decor', 'icon': 'fa-couch'},
            {'name': 'Sports & Outdoors', 'description': 'Sports equipment and outdoor gear', 'icon': 'fa-football'},
            {'name': 'Books & Media', 'description': 'Books, movies, and music', 'icon': 'fa-book'},
            {'name': 'Toys & Games', 'description': 'Toys and gaming products', 'icon': 'fa-gamepad'},
            {'name': 'Beauty & Health', 'description': 'Beauty and health products', 'icon': 'fa-heart'},
            {'name': 'Automotive', 'description': 'Car parts and accessories', 'icon': 'fa-car'},
        ]

        self.stdout.write('Creating categories...')
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon']
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'  ✓ Created category: {category.name}')

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

            vendor = Vendor.objects.create(
                user=user,
                name=fake.company(),
                location=random.choice(nigerian_cities),
                description=fake.text(max_nb_chars=200),
                contact_email=fake.email(),
                contact_phone=f'+234{random.randint(7000000000, 9099999999)}'
            )
            vendors.append(vendor)
            self.stdout.write(f'  ✓ Created vendor: {vendor.name}')

        # Product templates by category
        product_templates = {
            'Electronics': [
                'Smartphone', 'Laptop', 'Tablet', 'Smartwatch', 'Headphones',
                'Camera', 'Gaming Console', 'Monitor', 'Keyboard', 'Mouse'
            ],
            'Fashion': [
                'T-Shirt', 'Jeans', 'Sneakers', 'Dress', 'Jacket',
                'Handbag', 'Sunglasses', 'Watch', 'Belt', 'Hat'
            ],
            'Home & Garden': [
                'Sofa', 'Dining Table', 'Bed Frame', 'Lamp', 'Rug',
                'Garden Tools', 'Plant Pot', 'Cushions', 'Mirror', 'Curtains'
            ],
            'Sports & Outdoors': [
                'Football', 'Basketball', 'Tennis Racket', 'Bicycle', 'Treadmill',
                'Yoga Mat', 'Dumbbells', 'Camping Tent', 'Hiking Boots', 'Backpack'
            ],
            'Books & Media': [
                'Novel', 'Cookbook', 'Biography', 'Self-Help Book', 'Comic Book',
                'DVD Set', 'Vinyl Record', 'Magazine Subscription', 'E-Reader', 'Art Book'
            ],
            'Toys & Games': [
                'Action Figure', 'Board Game', 'Puzzle', 'Doll', 'LEGO Set',
                'Video Game', 'RC Car', 'Stuffed Animal', 'Building Blocks', 'Card Game'
            ],
            'Beauty & Health': [
                'Skincare Set', 'Perfume', 'Makeup Kit', 'Hair Dryer', 'Face Mask',
                'Vitamins', 'Fitness Tracker', 'Massage Gun', 'Essential Oils', 'Nail Polish'
            ],
            'Automotive': [
                'Car Battery', 'Tire Set', 'Car Cover', 'GPS Navigator', 'Dash Cam',
                'Car Vacuum', 'Jump Starter', 'Floor Mats', 'Air Freshener', 'Tool Kit'
            ]
        }

        # Create products with images
        self.stdout.write('\nCreating products with images...')
        self.stdout.write('(This may take a while as images are being downloaded...)\n')
        
        products_created = 0
        products_skipped = 0
        
        for i in range(options['products']):
            category = random.choice(categories)
            vendor = random.choice(vendors)
            
            # Get product template
            templates = product_templates.get(category.name, ['Product'])
            product_type = random.choice(templates)
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
            
            # Download image BEFORE creating product
            self.stdout.write(f'  Downloading image for product {i+1}/{options["products"]}...', ending='')
            filename, image_content = self.download_and_process_image(category.name, i)
            
            if image_content is None:
                self.stdout.write(self.style.WARNING(f' ✗ SKIPPED (no image): {product_name}'))
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
            product.image.save(filename, image_content, save=True)
            
            products_created += 1
            self.stdout.write(self.style.SUCCESS(f' ✓ {product.name}'))
            
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