# Railway MySQL Connection Setup Guide

## ✅ Database Configuration (Already Done!)
Your `settings.py` is configured to automatically read Railway's MySQL environment variables.

## 🔗 Connecting to Your Hosted Database

### Step 1: Verify Railway MySQL Service
1. Go to your Railway project dashboard
2. You should see two services:
   - Your Django app service
   - MySQL database service

### Step 2: Link Services (If Not Already Done)
Railway automatically provides these variables when MySQL is added:
- `MYSQL_URL` - Internal connection URL
- `MYSQL_PUBLIC_URL` - External connection URL  
- `MYSQLHOST` - Database host
- `MYSQLPORT` - Database port (usually 3306)
- `MYSQLUSER` - Database user (usually root)
- `MYSQLPASSWORD` - Database password
- `MYSQLDATABASE` - Database name

**Your Django app will automatically use these variables!**

### Step 3: Deploy Your Code
```bash
git add .
git commit -m "Configure MySQL connection for Railway"
git push
```

### Step 4: Run Migrations on Railway
After deployment, you need to create the database tables:

#### Option A: Using Railway CLI
```bash
# Install Railway CLI if not installed
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Run migrations
railway run python manage.py migrate

# Create superuser (optional)
railway run python manage.py createsuperuser
```

#### Option B: Using Railway Dashboard
1. Go to your Django service in Railway
2. Click on the "Settings" tab
3. Scroll to "Deploy Logs"
4. You can add a custom start command or use the console to run:
```bash
python manage.py migrate
```

### Step 5: Set Additional Required Variables
In your Django service settings on Railway, add these variables:

```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.up.railway.app
```

To generate a secure SECRET_KEY, run locally:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 6: Configure Start Command
In Railway, set your start command (Settings → Deploy):
```bash
python manage.py migrate && gunicorn config.wsgi:application
```

You'll need to add `gunicorn` to your requirements.txt:
```
gunicorn==21.2.0
```

## 🧪 Test Connection Locally (Optional)
If you want to test the connection to your Railway MySQL from local:

1. Get your `MYSQL_PUBLIC_URL` from Railway (visible in the MySQL service variables)
2. Create a `.env` file locally:
```
DATABASE_URL=mysql://user:password@host:port/database
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

3. Test connection:
```bash
python manage.py dbshell
```

## 🔍 Troubleshooting

### Connection Refused Error
- Make sure MySQL service is running in Railway
- Check if both services are in the same project
- Verify environment variables are set

### Migration Errors
- Ensure migrations are run on Railway after deployment
- Check deploy logs for errors

### 502/503 Errors
- Check if `ALLOWED_HOSTS` includes your Railway domain
- Verify your app is listening on `0.0.0.0:$PORT`

## 📝 Important Notes
1. Railway automatically provisions MySQL with all necessary variables
2. Your Django app reads these variables automatically (no manual entry needed)
3. MySQL internal URL (`MYSQL_URL`) is faster than public URL
4. Database credentials are auto-generated and secure
5. Railway handles SSL/TLS connections automatically

## ✨ Your Connection is Ready!
The database configuration in `settings.py` will automatically:
- Use `MYSQL_URL` or `DATABASE_URL` if available
- Fall back to individual variables (`MYSQLHOST`, etc.)
- Work with both Railway and local development

