🚀 PIXLUME BACKEND DEPLOYMENT GUIDE (AWS EC2)
🔐 1. LOGIN TO SERVER

From your system CMD / PowerShell:

ssh -i "F:\Pixlume\aws-key\Pixlume-Key.pem" ubuntu@YOUR_PUBLIC_IP

Example:

ssh -i "F:\Pixlume\aws-key\Pixlume-Key.pem" ubuntu@13.206.97.212

📁 2. GO TO PROJECT
cd ~/Pixlume-backend
🔄 3. PULL LATEST CODE
git pull origin main
🐍 4. ACTIVATE VIRTUAL ENV
source venv/bin/activate
📦 5. INSTALL NEW DEPENDENCIES (if any)
pip install -r requirements.txt
🗄️ 6. RUN DATABASE MIGRATIONS
alembic upgrade head
⚠️ If migration fails:
alembic stamp head
🔁 7. RESTART BACKEND SERVER
✅ If using systemd (RECOMMENDED)
sudo systemctl restart pixlume

Check:

sudo systemctl status pixlume

❌ If NOT using systemd (manual)
pkill -f uvicorn

uvicorn app.main:app --host 0.0.0.0 --port 8000

🌐 8. RESTART NGINX (only if config changed)
sudo systemctl restart nginx

🧪 9. TEST BACKEND
curl <http://127.0.0.1:8000/docs>

or browser:

<https://api.pixlume.online/docs>
🎯 10. VERIFY FROM FRONTEND

Open:

<https://pixlume.online>

Check:

images loading
login working
🔍 DEBUG COMMANDS (VERY IMPORTANT)
🔴 Check backend logs
sudo journalctl -u pixlume -n 50
🔴 Check nginx errors
sudo tail -f /var/log/nginx/error.log
🔴 Check running process
ps aux | grep uvicorn
🧠 OPTIONAL (AUTO START ON REBOOT)
sudo systemctl enable pixlume

⚡ QUICK DEPLOY (SHORT VERSION)
ssh -i key.pem ubuntu@IP
cd ~/Pixlume-backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart pixlume
🚨 COMMON ISSUES + FIX
❌ 502 Error
sudo systemctl restart pixlume
❌ DB error
alembic upgrade head
❌ SSL error
sudo certbot --nginx -d api.pixlume.online
❌ Permission error (SSH key)

Use PowerShell:

icacls key.pem /inheritance:r
🎯 FINAL ARCHITECTURE
Frontend → Vercel → pixlume.online
Backend → EC2 + FastAPI → api.pixlume.online
Reverse Proxy → Nginx
DB → PostgreSQL
