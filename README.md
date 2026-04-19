# 🏢 CWSRBS – Co-Working Space Resource Booking System
**Systems Analysis & Design – Regent College London**

---

## ⚡ What This App Does

A fully working web application that demonstrates all concepts from your portfolio:
- Member registration & login (JWT authentication)
- Browse co-working resources (hot desks, offices, meeting rooms, event space)
- Real-time availability checking before booking
- Create, view, and cancel bookings with automatic cost calculation
- Admin panel: manage resources, view all bookings, revenue reports
- SQLite database with all ERD entities (Users, Resources, Bookings, Payments)

---

## 🖥️ STEP-BY-STEP DEPLOYMENT GUIDE

### Prerequisites – What You Need Installed

| Tool | Why needed | Check if installed |
|------|-----------|-------------------|
| Python 3.8+ | Runs the backend server | Open terminal: `python --version` |
| pip | Installs Python packages | `pip --version` |
| A web browser | Runs the frontend | Chrome / Firefox / Edge |

---

### STEP 1 – Download & Extract the Project

1. Download the zip file and extract it anywhere on your computer
2. You will see a folder called **`cwsrbs`**
3. Open your terminal (Windows: press `Win+R`, type `cmd`, press Enter)
4. Navigate into the folder:

```bash
cd path\to\cwsrbs
# Example on Windows: cd C:\Users\YourName\Downloads\cwsrbs
# Example on Mac/Linux: cd ~/Downloads/cwsrbs
```

---

### STEP 2 – Install Python Dependencies

Run this single command to install all required packages:

```bash
pip install flask flask-cors flask-jwt-extended bcrypt
```

✅ You should see: `Successfully installed flask flask-cors flask-jwt-extended bcrypt`

> **If you get a permissions error on Mac/Linux:**
> ```bash
> pip3 install flask flask-cors flask-jwt-extended bcrypt
> ```
> Or add `--user`:
> ```bash
> pip install --user flask flask-cors flask-jwt-extended bcrypt
> ```

---

### STEP 3 – Start the Server

```bash
python app.py
```

You will see this in your terminal:

```
✅ Database initialised at cwsrbs.db
🚀 CWSRBS running at http://localhost:5000
   Admin login:  admin@cwsrbs.com / admin123
   Demo member:  jane@demo.com / member123

 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

### STEP 4 – Open the App in Your Browser

Open your browser and go to:

```
http://localhost:5000
```

The login screen will appear. 🎉

---

## 🔐 Demo Accounts

| Role | Email | Password | What you can do |
|------|-------|----------|----------------|
| **Member** | `jane@demo.com` | `member123` | Browse resources, make/cancel bookings |
| **Admin** | `admin@cwsrbs.com` | `admin123` | Everything + admin panel, reports, manage resources |

---

## 🎯 How to Demo to Your Teacher (Script)

### Demonstration 1 – Member Flow
1. Login as `jane@demo.com / member123`
2. Click **"Resources"** → show all resource types (desks, offices, meeting rooms)
3. Use the **filter buttons** to show only Meeting Rooms
4. Use the **search box** to find "Boardroom"
5. Click a resource card → booking modal appears
6. Set a start/end time → watch the **cost calculate automatically**
7. Click **"Confirm & Pay"** → booking confirmed
8. Go to **"My Bookings"** → see the booking with status, cost, details
9. Click **"Cancel"** → booking changes to cancelled

### Demonstration 2 – Admin Flow
1. Logout → login as `admin@cwsrbs.com / admin123`
2. Click **"Admin Panel"** in the nav bar
3. Show the **stats cards** (total bookings, revenue, members)
4. Show the **Top Resources chart**
5. Click **"All Bookings"** tab → see all member bookings in a table
6. Click **"Manage Resources"** tab → show deactivate button
7. Click **"+ Add Resource"** → fill in the form → save
8. Go back to Resources page → new resource appears immediately
9. Click **"Members"** tab → see all registered users

### Demonstration 3 – Register a New Member
1. Logout → click **"Register"** tab
2. Fill in name, email, new password → Submit
3. Automatically logged in → explore the system as a new member

---

## 📁 Project Structure

```
cwsrbs/
│
├── app.py              ← Flask backend server (API + routing)
├── cwsrbs.db           ← SQLite database (auto-created on first run)
├── requirements.txt    ← Python dependencies
│
└── public/
    └── index.html      ← Complete frontend (HTML + CSS + JavaScript)
```

---

## 🗄️ Database Tables (matches your ERD)

| Table | Purpose |
|-------|---------|
| `users` | Registered members and admins |
| `resource_types` | Categories: Desk, Office, Meeting Room, Event Space |
| `resources` | Individual bookable resources |
| `bookings` | All booking records with status |
| `payments` | Payment records linked to bookings |

---

## 🔌 API Endpoints (matches your DFD)

| Method | Endpoint | Who | Purpose |
|--------|----------|-----|---------|
| POST | `/api/auth/register` | Anyone | Register new member |
| POST | `/api/auth/login` | Anyone | Login |
| GET | `/api/resources` | Anyone | List all available resources |
| GET | `/api/resources/availability` | Anyone | Check if slot is free |
| GET | `/api/bookings` | Member | My bookings |
| POST | `/api/bookings` | Member | Create booking |
| DELETE | `/api/bookings/:id` | Member | Cancel booking |
| GET | `/api/admin/all-bookings` | Admin | All bookings |
| GET | `/api/admin/reports` | Admin | Revenue & stats |
| POST | `/api/admin/resources` | Admin | Add resource |
| DELETE | `/api/admin/resources/:id` | Admin | Deactivate resource |

---

## ❓ Troubleshooting

**"Port already in use"**
```bash
# Change port in app.py last line to e.g. 5001:
app.run(debug=True, port=5001)
# Then go to http://localhost:5001
```

**"ModuleNotFoundError: flask"**
```bash
pip install flask flask-cors flask-jwt-extended bcrypt
```

**Reset the database (clear all data)**
```bash
# Delete the database file and restart
del cwsrbs.db        # Windows
rm cwsrbs.db         # Mac/Linux
python app.py        # Re-creates with fresh seed data
```

**Browser shows old version**
Press `Ctrl+Shift+R` (hard refresh) in your browser.

---

## 🛑 Stopping the Server

Press `Ctrl+C` in the terminal window where the server is running.
