# marketplace/management/commands/populate_db.py
from django.core.management.base import BaseCommand
from marketplace.models import Vendor, Product, Category, ProductReview
from django.contrib.auth.models import User
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Populate the database with fake data'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create or get the admin user
        user, created = User.objects.get_or_create(username='admin')
        if created:
            user.set_password('admin')  # Set password using set_password to hash it
            user.save()

        # Clear existing data
        Vendor.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        # Create categories
        categories = []
        for _ in range(5):  # Adjust the number of categories as needed
            category = Category.objects.create(
                name=fake.word().capitalize(),
                description=fake.text(max_nb_chars=200)
            )
            categories.append(category)

        # Create vendors and their products
        for _ in range(10):  # Adjust the number of vendors as needed
            vendor = Vendor.objects.create(
                name=fake.company(),
                location=fake.city(),
                user=user  # Provide the user instance
            )

            # Create products for each vendor
            for _ in range(random.randint(1, 5)):  # Each vendor has 1 to 5 products
                Product.objects.create(
                    vendor=vendor,
                    category=random.choice(categories),  # Randomly assign a category
                    name=fake.word().capitalize(),
                    description=fake.text(max_nb_chars=300),
                    price=round(random.uniform(10.0, 100.0), 2),  # Random price
                    image='path/to/image.jpg'  # Placeholder for an image
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated the database'))
