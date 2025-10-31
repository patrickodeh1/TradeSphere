# TradeSphere - Modern Marketplace Platform

TradeSphere is a modern, location-based marketplace platform designed to connect buyers and sellers in their local areas. Built with Django, it features a complete e-commerce experience with cart management, secure checkout, and Paystack payment integration.

## ✨ Features

### For Customers
- **Browse & Search**: Discover products with advanced search and filtering
- **Shopping Cart**: Add multiple items and manage quantities
- **Secure Checkout**: Complete checkout with shipping address management
- **Paystack Integration**: Safe and secure payment processing
- **Order Tracking**: View order history and track shipments
- **Wishlist**: Save products for later
- **Product Reviews**: Rate and review purchased products
- **User Profile**: Manage personal information and shipping addresses

### For Vendors
- **Vendor Dashboard**: Manage products and view sales
- **Product Management**: Upload and edit product listings
- **Inventory Control**: Track stock levels
- **Order Management**: View and process customer orders

### Technical Features
- **Responsive Design**: Optimized for mobile, tablet, and desktop
- **Modern UI**: Clean, contemporary interface with smooth animations
- **Secure Authentication**: User registration and login system
- **Image Uploads**: Product and profile picture management
- **RESTful Architecture**: Clean URL structure
- **Database Models**: Robust relational data structure

## 🛠 Technologies Used

- **Backend**: Django 5.0.6
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: HTML5, CSS3, JavaScript
- **Payment**: Paystack API
- **Icons**: Font Awesome 6.4.0
- **Image Processing**: Pillow
- **Configuration**: Python Decouple

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone https://github.com/patrickodeh1/TradeSphere.git
cd TradeSphere
```

### Step 2: Create Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```
SECRET_KEY=your-django-secret-key
DEBUG=True
PAYSTACK_PUBLIC_KEY=your-paystack-public-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key
```

**Get Paystack Keys:**
1. Sign up at [Paystack](https://paystack.com/)
2. Navigate to Settings > API Keys & Webhooks
3. Copy your Test Public Key and Test Secret Key
4. Add them to your `.env` file

### Step 5: Database Migration
```bash
# Delete old migrations (if upgrading from old version)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 7: Collect Static Files (Production)
```bash
python manage.py collectstatic
```

### Step 8: Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## 🔧 Database Schema Updates

The updated models include:

### New Models
- `Cart` - Shopping cart for each user
- `CartItem` - Items in the cart
- `OrderItem` - Individual items in orders

### Updated Models
- `UserProfile` - Added shipping address fields and phone
- `Product` - Added stock, compare_at_price, is_featured, is_active
- `Order` - Complete rewrite with shipping info and payment tracking

### Migration Notes
If you have existing data, backup your database before migrating:
```bash
python manage.py dumpdata > backup.json
```

## 🎨 Customization

### Styling
- Main CSS: `static/css/style.css`
- Color scheme defined in CSS variables
- Responsive breakpoints at 768px

### Payment Configuration
- Test mode by default
- Switch to live keys in production
- Amount automatically converted to kobo (Naira * 100)

## 📱 Usage

### For Customers
1. **Register**: Create an account as a Customer
2. **Browse**: Explore products by category or search
3. **Add to Cart**: Click "Add to Cart" on products
4. **Checkout**: Enter shipping information
5. **Pay**: Complete payment via Paystack
6. **Track**: View order status in "My Orders"

### For Vendors
1. **Register**: Create an account as a Vendor
2. **Dashboard**: Access vendor dashboard
3. **Upload Products**: Add product details, images, pricing
4. **Manage**: Edit products and stock levels
5. **Process Orders**: View and fulfill customer orders

## 🔐 Security Notes

- Never commit `.env` file
- Use strong SECRET_KEY in production
- Set `DEBUG=False` in production
- Use HTTPS in production
- Regularly update dependencies
- Implement rate limiting for API endpoints

## 🚀 Deployment

### Heroku Deployment
```bash
# Install Heroku CLI
# Create Heroku app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set PAYSTACK_PUBLIC_KEY=your-key
heroku config:set PAYSTACK_SECRET_KEY=your-key

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use PostgreSQL database
- [ ] Set up static file serving (WhiteNoise or CDN)
- [ ] Configure media file storage (AWS S3 or similar)
- [ ] Set up SSL certificate
- [ ] Configure email backend
- [ ] Set up error logging (Sentry)
- [ ] Implement backup strategy
- [ ] Set up monitoring

## 📁 Project Structure

```
TradeSphere/
├── TradeSphere/          # Project settings
│   ├── settings.py       # Main settings
│   ├── urls.py           # Root URL configuration
│   └── wsgi.py           # WSGI configuration
├── marketplace/          # Main app
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── forms.py          # Form classes
│   ├── urls.py           # App URL patterns
│   └── admin.py          # Admin configuration
├── templates/            # HTML templates
│   └── marketplace/      # App templates
├── static/               # Static files
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript
│   └── images/           # Images
├── media/                # User uploads
│   ├── products/         # Product images
│   └── profile_pics/     # Profile pictures
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

## 🐛 Troubleshooting

### Common Issues

**Migration Errors**
```bash
# Reset database (development only)
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

**Static Files Not Loading**
```bash
python manage.py collectstatic --clear
```

**Paystack Integration Issues**
- Verify API keys are correct
- Ensure amount is in kobo (multiply by 100)
- Check callback URL is accessible
- Test with Paystack test cards

**Cart Not Working**
- Ensure user is authenticated
- Check Cart model is created for user
- Verify signals are working

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

**Patrick Odeh**
- GitHub: [@patrickodeh1](https://github.com/patrickodeh1)
- Email: patrickodeh1@gmail.com

## 🙏 Acknowledgments

Special thanks to **ALX** for providing the knowledge, resources, and support that made this project possible. The skills acquired during my time at ALX have been instrumental in developing TradeSphere.

## 📞 Support

For support, email patrickodeh1@gmail.com or open an issue on GitHub.

---

**Note**: This is an MVP (Minimum Viable Product) designed for demonstration and learning purposes. For production use, implement additional security measures, testing, and scalability considerations.