## Deployment Guide(Alma9)

Follow these steps to deploy the Private-Note project on a new Alma9 server:

### 1. Prerequisites

In order to complete this guide, you need a server running Alma9, along with a non-root user with sudo privileges.


### 2. Install Required Packages from the Alma9 Repositories

```bash
sudo dnf update
```
```bash
sudo dnf install python3-devel nginx curl git
```

### 3. Create  Virtual Environment

```bash
python3 -m venv env
```
This will create a directory called env within your project directory. Inside, it will install a local version of Python and a local version of pip to manage packages. You can use this virtual environment structure to install and configure an isolated Python environment for any project that you want to create.

Before installing your project’s Python requirements, you will need to activate the virtual environment. You can do that by typing:
```bash
source env/bin/activate
```

### 4. Install Django and Other Requirements

```bash
pip install django gunicorn pillow
```

### 5. Clone the Project from GitHub

```bash
git clone https://github.com/carlosj1999/Private-Note.git
```

```bash
cd ~/Private-Note
```
### 6. Configure Django Settings

Replace 'your_server_ip_or_domain' with your actual server IP or domain
``` bash
vi pnote4u/settings.py
```

The simplest case: just add the domain name(s) and IP addresses of your Django server:
`ALLOWED_HOSTS = [ 'example.com', '203.0.113.5']`

To respond to 'example.com' and any subdomains, start the domain with a dot:
`ALLOWED_HOSTS = ['.example.com', '203.0.113.5']`

If you want to allow any host (not recommended for production), you can set:
`ALLOWED_HOSTS = ['*']`

```python
ALLOWED_HOSTS = ['your_server_ip_or_domain', 'localhost']
```
Note: Be sure to include `localhost` as one of the options since you will be proxying connections through a local Nginx instance.

### 7. Set Up Django Project

```bash
python manage.py collectstatic
```

```bash
python manage.py makemigrations privnote
```

```bash
python manage.py migrate privnote
```

### 8. Test Gunicorn
The last thing you need to do before leaving your virtual environment is test Gunicorn to make sure that it can serve the application. You can do this by entering the project directory and using gunicorn to load the project’s WSGI module:
```bash
gunicorn --bind 0.0.0.0:8000 pnote4u.wsgi
```
You can go and test the app in your browser by typing `your_ip:8000`.

You should receive an output like this:
```
[2024-09-25 03:30:34 +0000] [3266] [INFO] Starting gunicorn 23.0.0
[2024-09-25 03:30:34 +0000] [3266] [INFO] Listening at: http://0.0.0.0:8000 (3266)
[2024-09-25 03:30:34 +0000] [3266] [INFO] Using worker: sync
[2024-09-25 03:30:34 +0000] [3267] [INFO] Booting worker with pid: 3267
```
When you are finished testing, hit `CTRL-C` in the terminal window to stop Gunicorn.

You can back out of our virtual environment by typing:

$ `deactivate`

### 9. Create Gunicorn Systemd Socket and Service Files

Create and edit `/etc/systemd/system/gunicorn.socket`:

```bash
cat <<EOF | sudo tee /etc/systemd/system/gunicorn.socket
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
EOF
```

Create and edit `/etc/systemd/system/gunicorn.service`:

```bash
cat <<EOF | sudo tee /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=your_username
Group=your_username # Or a valid group like 'nginx'
WorkingDirectory=/path_to_projectdir/Private-Note
ExecStart=/path_to_projectvenv/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock pnote4u.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
```

Notes:
1. Replace `your_username` with the actual username you’re using on the server.
2. Make sure the paths in `WorkingDirectory` and `ExecStart` are correct according to your setup.

### 10. Start and Enable Gunicorn Socket

```bash
sudo systemctl start gunicorn.socket
```
```bash
sudo systemctl enable gunicorn.socket
```

#### 10.1. Allow Gunicorn Access with SELinux Policy Adjustments
If SELinux is enabled it will prevent Gunicorn from running properly, you can modify the SELinux policy to allow Gunicorn to run.

1- First, you need to check what SELinux is blocking to identify the exact issue. Use the audit logs to see what’s being denied:
```bash
sudo cat /var/log/audit/audit.log | grep denied
```
You should receive an output like this:

`type=AVC msg=audit(1728362101.264:824): avc:  denied  { execute } for  pid=34342 comm="(gunicorn)" name="gunicorn" dev="dm-0" ino=34171786 scontext=system_u:system_r:init_t:s0 tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file permissive=1`

2- Use `audit2allow` to generate a custom policy module that will allow the denied access:
```bash
sudo setenforce 0
```
```bash
sudo cat /var/log/audit/audit.log | grep gunicorn | audit2allow -M gunicorn_policy
```
3- Install the policy module you just created:
```bash
sudo semodule -i gunicorn_policy.pp
```
4- Once the module is installed:
```bash
sudo systemctl daemon-reload
```
```bash
sudo setenforce 1
```

Check the status of the process to find out whether it was able to start:
```bash
sudo systemctl status gunicorn.socket
```
You should receive an output like this:
``` bash
Output
● gunicorn.socket - gunicorn socket
     Loaded: loaded (/etc/systemd/system/gunicorn.socket; enabled; vendor preset: enabled)
     Active: active (listening) since Mon 2024-09-25 01:53:25 UTC; 5s ago
   Triggers: ● gunicorn.service
     Listen: /run/gunicorn.sock (Stream)
     CGroup: /system.slice/gunicorn.socket

Sep 25 01:53:25 django systemd[1]: Listening on gunicorn socket.
```

### 10.2. Testing Socket Activation
Currently, if you’ve only started the gunicorn.socket unit, the gunicorn.service will not be active yet since the socket has not yet received any connections. You can check this by typing:
```bash
sudo systemctl status gunicorn
```
```
Output
○ gunicorn.service - gunicorn daemon
     Loaded: loaded (/etc/systemd/system/gunicorn.service; disabled; vendor preset: enabled)
     Active: inactive (dead)
TriggeredBy: ● gunicorn.socket
```

To test the socket activation mechanism, you can send a connection to the socket through curl by typing:
```bash
curl --unix-socket /run/gunicorn.sock localhost
```
You should receive the HTML output from your application in the terminal. This indicates that Gunicorn was started and was able to serve your Django application. You can verify that the Gunicorn service is running by typing:
```bash
sudo systemctl status gunicorn
```
```
Output
● gunicorn.service - gunicorn daemon
     Loaded: loaded (/etc/systemd/system/gunicorn.service; disabled; vendor preset: enabled)
     Active: active (running) since Thu 2024-09-26 02:15:58 UTC; 1min 47s ago
TriggeredBy: ● gunicorn.socket
   Main PID: 4273 (gunicorn)
      Tasks: 4 (limit: 3394)
     Memory: 89.6M
        CPU: 441ms
     CGroup: /system.slice/gunicorn.service
             ├─4273 /home/carlos/env/bin/python3 /home/carlos/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock ip_aggregator.wsgi:application
             ├─4274 /home/carlos/env/bin/python3 /home/carlos/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock ip_aggregator.wsgi:application
             ├─4275 /home/carlos/env/bin/python3 /home/carlos/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock ip_aggregator.wsgi:application
             └─4276 /home/carlos/env/bin/python3 /home/carlos/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock ip_aggregator.wsgi:application
```

### 11. Configure Nginx to Proxy Pass to Gunicorn

Create and edit `/etc/nginx/conf.d/pnote4u.conf`:

```bash
cat <<EOF | sudo tee /etc/nginx/conf.d/pnote4u.conf
server {
    listen 80;
    server_name your_server_ip_or_domain;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path_to_projectdir/Private-Note/privnote;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF
```

Notes:
1. Make sure the paths in `location /static/` and `server_name` are correct according to your setup.

Enable the Nginx configuration:
```bash
sudo ln -s /etc/nginx/sites-available/pnote4u /etc/nginx/sites-enabled
```

### 11.1. Proxy_params File
You need to create or obtain the proxy_params file that Nginx uses for reverse proxy configuration.
```bash
sudo vi /etc/nginx/proxy_params
```
Then add the following typical proxy parameters for reverse proxying:
```bash
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

### 10.2. Allow Nginx Access with SELinux Policy Adjustments
If SELinux is enabled it will prevent Nginx from running properly, you can modify the SELinux policy to allow Nginx to run.

1- First, you need to check what SELinux is blocking to identify the exact issue. Use the audit logs to see what’s being denied:
```bash
sudo cat /var/log/audit/audit.log | grep denied
```
You should receive an output like this:

`type=AVC msg=audit(1728362101.264:824): avc:  denied  { execute } for  pid=34342 comm="(nginx)" name="nginx" dev="dm-0" ino=34171786 scontext=system_u:system_r:init_t:s0 tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file permissive=1`

2- Use `audit2allow` to generate a custom policy module that will allow the denied access:
```bash
sudo setenforce 0
```
```bash
sudo cat /var/log/audit/audit.log | grep denied | audit2allow -M nginx_policy
```
3- Install the policy module you just created:
```bash
sudo semodule -i nginx_policy.pp
```
4- Once the module is installed:
```bash
sudo systemctl daemon-reload
```
```bash
sudo setenforce 1
```

### 11.3. Test Nginx
Test your Nginx configuration for syntax errors by typing:
```bash
sudo nginx -t
```
```bash
sudo systemctl restart nginx
```
Finally, if needed open up your firewall to normal traffic on port 80
```bash
sudo firewall-cmd --permanent --zone=public --add-service=http
```
```bash
sudo firewall-cmd --reload
```

## Troubleshooting
For additional troubleshooting, the logs can help narrow down root causes. Check each of them in turn and look for messages indicating problem areas.

The following logs may be helpful:

Check the Nginx process logs by typing:` journalctl -u nginx`

Check the Nginx access logs by typing:` less /var/log/nginx/access.log`

Check the Nginx error logs by typing:` less /var/log/nginx/error.log`

Check the Gunicorn application logs by typing:` journalctl -u gunicorn`

Check the Gunicorn socket logs by typing:` journalctl -u gunicorn.socket`

#### Nginx Permission Denied Errors:

The primary place to look for more information is in Nginx’s error logs. Generally, this will tell you what conditions caused problems during the proxying event. Follow the Nginx error logs by typing:
```bash
tail -F /var/log/nginx/error.log
```
##### For (13: Permission denied), "GET /static/css/style.css HTTP/1.1":
Ensure that Nginx and Gunicorn have the necessary permissions to access your project files. Adjust permissions cautiously:
```bash
chmod o+rx /path_to_projectdir/Private-Note
```
```bash
chmod -R o+rx /path_to_projectdir/Private-Note/privnote/static
```
```bash
sudo chown -R username:username /path_to_projectdir/Private-Note/privnote/static
```


## Usage

Once deployed, you can access the IP Aggregator application through your server's IP address or domain name.

For local development:

```bash
cd Private-Note
```
```bash
python manage.py runserver
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License
This version is streamlined for clarity, with consistent formatting and concise instructions. Be sure to replace placeholders with your specific information, and add any additional sections that might be relevant to your project.

