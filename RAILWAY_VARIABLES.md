# Railway Environment Variables Guide

## 🔴 REQUIRED - Variables You MUST Add Manually

Add these in Railway Dashboard → Your Django Service → **Settings** → **Variables**:

### 1. SECRET_KEY (Required)
```
SECRET_KEY=django-insecure-your-generated-secret-key-here
```

**How to generate:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. DEBUG (Required)
```
DEBUG=False
```
⚠️ **NEVER** set `DEBUG=True` in production!

---

## 🟡 RECOMMENDED - Optional but Highly Recommended

### 3. ALLOWED_HOSTS (Recommended)
```
ALLOWED_HOSTS=your-app-name.railway.app,*.railway.app
```
**Note:** Your app automatically detects Railway domain, but you can add this for extra domains.

---

## 🟢 AUTOMATIC - Railway Provides These (NO NEED TO ADD)

Railway **automatically** injects these when you add MySQL service:

### MySQL Connection Variables:
- ✅ `MYSQL_URL` - Internal connection URL
- ✅ `MYSQL_PUBLIC_URL` - Public connection URL
- ✅ `MYSQLHOST` - Database host
- ✅ `MYSQLPORT` - Database port (3306)
- ✅ `MYSQLUSER` - Database user (usually root)
- ✅ `MYSQLPASSWORD` - Database password
- ✅ `MYSQLDATABASE` - Database name

### Railway System Variables:
- ✅ `PORT` - Port your app should listen on
- ✅ `RAILWAY_PUBLIC_DOMAIN` - Your app's public domain
- ✅ `RAILWAY_ENVIRONMENT` - Deployment environment

**Your Django app is already configured to use all these automatically!**

---

## 📧 OPTIONAL - Email Configuration (if needed)

If you want to send emails (for password reset, etc.):

```
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-mailtrap-username
EMAIL_HOST_PASSWORD=your-mailtrap-password
EMAIL_FROM=noreply@sademiy.com
```

---

## 📝 Quick Setup Checklist

### In Railway Dashboard:

1. **Navigate to Variables:**
   - Open your Django service
   - Click "Settings" tab
   - Scroll to "Variables" section
   - Click "New Variable"

2. **Add Required Variables:**
   ```
   SECRET_KEY=<paste-generated-key-here>
   DEBUG=False
   ```

3. **Save and Redeploy:**
   - Railway will automatically redeploy with new variables

---

## 🎯 Summary

### What YOU need to add:
1. ✅ `SECRET_KEY` (generate it first!)
2. ✅ `DEBUG=False`

### What Railway adds automatically:
- All MySQL connection variables (9 variables)
- Railway system variables (PORT, domain, etc.)

### That's it! 🎉

Your app will automatically connect to the hosted MySQL database once you add `SECRET_KEY` and push your code.

