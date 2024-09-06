# Private Note

PrivNote is a secure, Django-based web application for sharing confidential notes. Users can create notes that self-destruct after a certain time or after being viewed once, ensuring that sensitive information is only accessible to the intended recipient.

## Features

- Create private, self-destructing notes.
- Set expiration durations or one-time view options for each note.
- Share private links to notes.
- Integrated security for note privacy and link protection.
- Built-in input validation to ensure note integrity.

## Deployment Guide(Ubuntu 22.04)

Follow these steps to deploy the Private-Note project on a new Ubuntu server:

### 1. Initial Server Setup

1. Set up a new Ubuntu server (22.04 or later).
2. Create a non-root user with sudo privileges.
3. Set up a firewall (UFW).

### 2. Install Required Packages

```bash
sudo apt update
sudo apt install python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl
```

### 3. Create PostgreSQL Database and User

```bash
sudo -u postgres psql
```

In the PostgreSQL prompt:

```sql
CREATE DATABASE ip_aggregator;
CREATE USER ip_aggregator_user WITH PASSWORD 'your_secure_password';
ALTER ROLE PrivNote_user SET client_encoding TO 'utf8';
ALTER ROLE PrivNote_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE PrivNote_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE PrivNote TO PrivNote_user;
\q
```

### 4. Create a Project Directory and Virtual Environment

```bash
mkdir ~/PrivNote
cd ~/PrivNote
python3 -m venv env
source env/bin/activate
```

### 5. Install Django and Other Requirements

```bash
pip install django gunicorn psycopg2-binary
```

### 6. Clone the Project from GitHub

```bash
git clone https://github.com/your_username/Private-Note.git .
```

### 7. Configure Django Settings

Edit `~/PrivNote/myproject/settings.py`:

```python
ALLOWED_HOSTS = ['your_server_ip_or_domain', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'PrivNote',
        'USER': 'PrivNote_user',
        'PASSWORD': 'your_secure_password',
        'HOST': 'localhost',
        'PORT': '',
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
```

### 8. Set Up Django Project

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### 9. Test Gunicorn

```bash
gunicorn --bind 0.0.0.0:8000 myproject.wsgi
```

### 10. Create Gunicorn Systemd Socket and Service Files

Create and edit `/etc/systemd/system/gunicorn.socket`:

```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

Create and edit `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=your_username
Group=www-data
WorkingDirectory=/home/your_username/PrivNote
ExecStart=/home/your_username/PrivNote/env/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          myproject.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 11. Start and Enable Gunicorn Socket

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```

### 12. Configure Nginx

Create and edit `/etc/nginx/sites-available/PrivNote`:

```nginx
server {
    listen 80;
    server_name your_server_ip_or_domain;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/your_username/PrivNote;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Enable the Nginx configuration:

```bash
sudo ln -s /etc/nginx/sites-available/PrivNote /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 13. Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
```

## Usage

Once deployed, you can access the Private-Note application through your server's IP address or domain name.

For local development:

```bash
cd PrivNote
python manage.py runserver
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License
This version is streamlined for clarity, with consistent formatting and concise instructions. Be sure to replace placeholders with your specific information, and add any additional sections that might be relevant to your project.
