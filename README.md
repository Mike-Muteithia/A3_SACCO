# A3_SACCO
# Akiba Sacco — Core Financial Management System

A server-side rendered (SSR) core banking and financial accounting portal built for Kenyan Savings and Credit Cooperative Organizations (SACCOs). Engineered with **Python 3.12+**, **Flask 3.0.3**, **SQLAlchemy**, and **PostgreSQL/SQLite**, running on **Gunicorn** behind a Linux systemd service daemon.

---

## 1. System Overview & Architecture

Akiba Sacco manages the end-to-end financial lifecycle of SACCO operations: member onboarding, savings deposits, share capital tracking, credit facility applications, automated annuity amortization, and general ledger auditing.

### Architecture Highlights
- **Server-Side Rendered (SSR):** High-performance Jinja2 templating with zero client-side SPA framework bloat.
- **Strict Decimal Precision:** All monetary evaluations run on Python `decimal.Decimal` with explicit banker's rounding (`ROUND_HALF_UP`) quantized to two decimal places (`Decimal('0.01')`), eliminating IEEE 754 floating-point drift.
- **Pessimistic Concurrency Control:** Row-level pessimistic locking (`SELECT ... FOR UPDATE`) prevents race conditions and balance discrepancies during concurrent deposits, withdrawals, and loan settlements.
- **Multi-Worker WSGI Daemon:** Gunicorn running threaded workers (`gthread`) managed by Ubuntu `systemd` with structured log rotation writing to `/var/log/akiba_sacco/`.

---

## 2. Core Financial Mechanics & Business Rules

### Savings & Liquidity Pool
- A member's net unencumbered savings balance is computed dynamically as:
  $$\text{Total Savings} = \sum \text{Savings Deposits} - \sum \text{Withdrawals}$$
- Withdrawals enforce row-level locking on the `Member` record before evaluation to guarantee that unencumbered capital is never overdrawn.

### Credit Facilities & Loan Amortization
- **3x Collateralization Limit:** Loan eligibility is strictly capped at $3\times$ the applicant's current net savings pool balance.
- **Amortization Formula:** Monthly repayment installments ($M$) follow the standard equal-installment annuity formula over principal $P$, monthly interest rate $r$, and duration $n$:
  $$M = P \cdot \frac{r(1 + r)^n}{(1 + r)^n - 1}$$
- Calculated using `Decimal` arithmetic. If interest is zero ($r = 0$), the formula falls back to $M = P / n$.
- Total liability over the loan term is $M \cdot n$. Remaining balance updates dynamically against recorded repayments.

---

## 3. Role-Based Access Control (RBAC) Matrix

The platform implements Segregation of Duties (SoD) through normalized many-to-many permissions:

| Role | Permissions Assigned | Primary Responsibilities |
|---|---|---|
| **Member** | `OWN_READ` | Access personal dashboard and personal financial statements only. |
| **Teller** | `PROFILE_READ`, `TX_CREATE` | Over-the-counter cash operations (Savings, Withdrawals, Share Capital). |
| **LoanOfficer** | `PROFILE_READ`, `LOAN_APPROVE_STD` | Verify credit eligibility; approve standard loans up to KES 500,000. |
| **Manager** | `PROFILE_READ`, `LOAN_APPROVE_STD`, `LOAN_APPROVE_LARGE`, `REPORT_READ_ALL` | Tiered loan approvals (> KES 500,000), General Ledger audits, portfolio export. |
| **SystemAdmin** | `PROFILE_READ`, `PROFILE_DELETE`, `USER_MANAGE`, `SYSTEM_CONFIG` | User provisioning, RBAC mapping, member archiving, audit trail inspection. |

---

## 4. Security Hardening & Validations

- **CSRF Protection:** Global `CSRFProtect` enforced across all form submissions, including inline deletion and loan approval action buttons.
- **IDOR Elimination:** Financial statements (`/reports/statement/<id>`) verify account ownership for members and require explicit `REPORT_READ_ALL` privileges for staff.
- **Static Multi-Worker Secret Key:** Fails fast in production if `SECRET_KEY` is undefined; local development uses a persistent key to prevent multi-worker session dropping.
- **Kenyan Format Validators:**
  - **National ID:** Enforces 7–8 digit numeric Kenyan identification format (`^[1-9]\d{6,7}$`).
  - **Mobile Phone (MSISDN):** Validates Safaricom/Airtel formats (`07XXXXXXXX`, `01XXXXXXXX`, or `+2547XXXXXXXX`).
- **HTTP Security Flags:** Session cookies configured with `HttpOnly=True` and `SameSite=Lax`.

---

## 5. Visual Identity & UI/UX Design System

The frontend implements a custom financial theme tailored for a Kenyan banking institution:
- **Color Palette:** Deep Forest Green (`#0F5132`), Dark Slate (`#1A252C`), Warm Gold (`#D4AF37`), and Neutral Slate canvases (`#F4F6F8`).
- **Typography:** Plus Jakarta Sans (`300`–`800` weight).
- **Executive Stat Panels:** Trend badges, glassmorphic metric cards, and responsive elevation shadows.
- **Mobile Drawer:** Offcanvas navigation drawer ensuring touch usability on tablet and mobile screens.
- **Safety Confirmations:** Native JavaScript `confirm()` alerts replaced with accessible Bootstrap modal dialogs for all destructive actions.

---

## 6. Local Setup & Deployment (WSL 2 / Ubuntu 24.04 LTS)

### Prerequisites
- Ubuntu 24.04 LTS on WSL 2
- Python 3.12+
- SQLite (default local) or PostgreSQL

### Setup Steps

1. **Clone the Repository & Navigate to Source:**
   ```bash
   cd ~/IST1025/A3_SACCO/sacco_management

2. **Set Up Python 3.12 Virtual Environment:**
  ```bash
  python3.12 -m venv ../.venv
  source ../.venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt

3. **Configure Environment Variables (.env):**
  ```bash
  cat << EOF > .env
  FLASK_ENV=development
  SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  SQLALCHEMY_DATABASE_URI=sqlite:///akiba_sacco.db
  GUNICORN_BIND=0.0.0.0:8000
  EOF

4. **Initialize Log Directory:**
  ```bash
  sudo mkdir -p /var/log/akiba_sacco
  sudo chown -R $USER:$USER /var/log/akiba_sacco
  sudo chmod -R 755 /var/log/akiba_sacco

5. **Run Migrations & Seed Initial Records:**
  ```bash
  flask db upgrade
  python seed.py

6. **Start Gunicorn as a Managed Systemd Service:**
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now akiba_sacco
  sudo systemctl status akiba_sacco --no-pager

7. **Local Development (Interactive):**
  ```bash
  gunicorn --config gunicorn.conf.py "app:create_app()"

8. **Production Service (Daemon):**
  ```bash
  sudo systemctl enable --now akiba_sacco

---

## 7. UI/UX Upgrades
The Jinja2 frontend has been enhanced with modern interactivity while maintaining its lightweight Server-Side Rendered (SSR) footprint:
- **Interactive DataTables:** The member directory uses DataTables.js for instant client-side column sorting without triggering a page reload.
- **Form Ergonomics:** A custom Jinja2 macro (`_macros.html`) intercepts Flask-WTF validation failures (e.g., regex mismatch on National IDs) and dynamically renders native Bootstrap `is-invalid` classes with inline red warnings.
- **Capital Visualization:** The Executive Dashboard integrates Chart.js to render a responsive doughnut chart, visualizing the ratio of the Unencumbered Savings Pool against the Active Loan Portfolio.

---

## 8. DevSecOps & Production Deployment
The environment transitions from a local Flask development server to a highly available, self-healing architecture:
- **Systemd Daemonization:** Gunicorn runs as a dedicated Linux background service (`akiba_sacco.service`), ensuring automatic startup on boot and instant process recovery upon failure.
- **Nginx Reverse Proxy:** Nginx intercepts public traffic on port 80, serves `static/style.css` instantaneously from memory, and proxies dynamic requests to Gunicorn on port 8000 while enforcing `X-Frame-Options` and `X-XSS-Protection` headers.
- **Automated Disaster Recovery (Cron):** A scheduled bash script (`backup_db.sh`) runs via `cron` at 2:00 AM daily. It safely duplicates the active SQLite database, applies gzip compression to minimize disk footprint, and autonomously deletes archives older than 30 days to prevent storage exhaustion.
