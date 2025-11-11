# 🚀 Railway Deployment Checklist

## ✅ Configuration Complete!

Your Django app is now fully configured to connect to MySQL on Railway. Here's what was set up:

### Files Modified/Created:
- ✅ `config/settings.py` - Database connection configured
- ✅ `requirements.txt` - Added necessary packages
- ✅ `Procfile` - Railway start command
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version specified

---

## 📋 Deploy to Railway - Step by Step

### 1️⃣ Install New Dependencies Locally (Optional but recommended)
```bash
pip install -r requirements.txt
```

### 2️⃣ Push Code to Railway
```bash
git add .
git commit -m "Configure MySQL database and Railway deployment"
git push
```

### 3️⃣ Set Environment Variables in Railway

Go to your Django service in Railway → **Settings** → **Variables**, and add:

#### Required Variables:
```
SECRET_KEY=<generate-a-secure-key>
DEBUG=False
```

**To generate SECRET_KEY**, run locally:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Optional Variables:
```
ALLOWED_HOSTS=your-app-name.up.railway.app
```

**Note:** Railway automatically provides these MySQL variables (no need to add manually):
- `MYSQL_URL`
- `MYSQL_PUBLIC_URL`
- `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`

### 4️⃣ Check Deployment

After pushing, Railway will automatically:
1. Build your application
2. Install dependencies from `requirements.txt`
3. Run migrations (`python manage.py migrate`)
4. Collect static files (`python manage.py collectstatic`)
5. Start the server with Gunicorn

### 5️⃣ Create Superuser (Optional)

To access Django admin, use Railway CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link project
railway login
railway link

# Create superuser
railway run python manage.py createsuperuser
```

Or use the Railway dashboard console under your service.

---

## 🔍 Verify Database Connection

### Check in Railway Logs:
1. Go to your Django service
2. Click on "Deployments"
3. Look for:
   ```
   Operations to perform:
     Apply all migrations...
   Running migrations:
     ...
   ```

### Test Locally with Railway MySQL:
If you want to test locally with the hosted database:

1. Get `MYSQL_PUBLIC_URL` from Railway MySQL service variables
2. Add to your local `.env` file:
   ```
   DATABASE_URL=<paste-MYSQL_PUBLIC_URL-here>
   SECRET_KEY=<your-secret-key>
   DEBUG=True
   ```
3. Run:
   ```bash
   python3 manage.py migrate
   python3 manage.py runserver
   ```

---

## 🎯 What Happens Now?

When you deploy to Railway, your app will:

1. ✅ **Automatically connect to MySQL** using Railway's environment variables
2. ✅ **Run migrations** on startup
3. ✅ **Serve static files** with Whitenoise
4. ✅ **Handle CORS** for your frontend
5. ✅ **Use Gunicorn** for production-ready serving
6. ✅ **Auto-restart** on failure (up to 10 times)

---

## 🛠️ Troubleshooting

### Issue: "DisallowedHost" Error
**Solution:** Add your Railway domain to environment variables:
```
ALLOWED_HOSTS=your-app.railway.app,*.railway.app
```

### Issue: "Database connection failed"
**Solution:** 
- Verify MySQL service is running in Railway
- Check that both services are in the same project
- Railway automatically injects MySQL variables - no manual setup needed

### Issue: "Static files not loading"
**Solution:** Already configured with Whitenoise! Just ensure:
```bash
python manage.py collectstatic --noinput
```
is in your start command (already added).

### Issue: "502 Bad Gateway"
**Solution:**
- Check if the app is binding to `0.0.0.0:$PORT` (already configured)
- Check deploy logs for Python errors
- Verify all dependencies are in `requirements.txt`

---

## 📊 Monitor Your App

### View Logs:
```bash
railway logs
```

### Access Django Admin:
```
https://your-app-name.railway.app/admin/
```

### Check Database:
Railway MySQL service → Variables → Copy `MYSQL_PUBLIC_URL` → Use with any MySQL client

---

## 🎉 You're Ready to Deploy!

Just push your code and Railway will handle the rest:
```bash
git add .
git commit -m "Ready for Railway deployment"
git push
```

Your Django app will automatically connect to the hosted MySQL database! 🚀

