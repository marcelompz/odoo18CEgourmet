# Odoo 18 CE - Provecchio Deployment (Gourmet)

**Odoo 18 CE deployment for Provecchio (Paraguay) with full localization support, automation scripts, and custom import tools.**

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- SSH key added to GitHub
- Access to repository `git@github.com:marcelompz/odoo18CEgourmet.git`

### Automatic Installation

```bash
# 1. Clone repository
git clone git@github.com:marcelompz/odoo18CEgourmet.git odoo18_provecchio
cd odoo18_provecchio

# 2. Start Docker containers (starts postgres, web, and runs automated initialization)
docker compose up -d

# 3. Wait for initialization to complete
docker logs -f odoo_init_db_18
```

### Access Credentials

- **URL:** http://localhost:9038
- **Database:** `prod`
- **Email:** `soporte@crossnexion.com`
- **Password:** `Cross1983_`

---

## ⚙️ Automated Initialization Container (`odoo_init_db_18`)

The service `init` defined in `docker-compose.yml` runs a lightweight, temporary container (`odoo_init_db_18`) that manages database provisioning.

### Purpose and Workflow:
1. **Database Healthcheck Loop:** Waits for the PostgreSQL database (`db5771`) to be fully online and accepting connections.
2. **Auto-creation:** Verifies if the database `prod` exists. If not, it creates it automatically.
3. **Core Installation:** Installs Odoo's base tables (`base`, `web`, `mail`) using the command line.
4. **Admin Security Reset:** Programmatically resets the `admin` (`__system__`) password to `Cross1983_`.
5. **Localization Configuration:** Updates the main company's country to Paraguay and currency to Guaraníes (PYG).
6. **Paraguay Localization Installation:** Automatically installs the `l10n_py` Odoo 18 module and its python dependencies (`tu-ruc-python-client`).
7. **Lock Mechanism:** Generates a lock file at `/tmp/init_completed` inside the database volume to prevent running again on container restarts.

### Is it worth keeping?
**Absolutely yes.** In Odoo, starting a fresh environment usually requires manual steps through the web UI (creating databases, choosing country/currency, installing modules one by one, resetting default passwords). Having this initialization container guarantees a **100% automated, one-command deployment** suitable for CI/CD pipelines, local testing, and staging environments.

---

## 📄 Analysis of Scripts in Project

The project contains several scripts to automate imports and test setups. Here is a breakdown of their structure and purpose:

### 1. `addons/import_products_direct.py`
- **Path:** `addons/import_products_direct.py`
- **Mechanism:** Direct Odoo ORM execution. It loads Odoo's registry for database `prod`, opens a cursor, and reads `addons/materia_prima_fixed.csv` (348 raw materials).
- **Target:** Imports ingredients and raw materials, automatically creating categories and setting units.
- **Odoo 18 Adaptation:** In Odoo 18, the storable and consumable types are merged into `'consu'` (Goods). This script sets `type = 'consu'` and `is_storable = True` to enable stock tracking.
- **Verdict:** **Highly recommended** for loading raw materials quickly without browser timeouts.

### 2. `addons/import_comidas_direct.py`
- **Path:** `addons/import_comidas_direct.py`
- **Mechanism:** Direct Odoo ORM execution. Reads `addons/comida.csv` (132 finished dishes).
- **Target:** Imports finished POS dishes. It maps columns to set sales prices, marks them as `available_in_pos = True`, and activates the `is_pos_bom = True` checkbox (allowing ingredients recipes to be configured).
- **Verdict:** **Required** to load the menu/plates in bulk before linking ingredients.

### 3. `addons/import_recipes_direct.py`
- **Path:** `addons/import_recipes_direct.py`
- **Mechanism:** Instantiates Odoo's custom `excel.recipe.import.wizard` model via the ORM. It loads `addons/plantilla_importacion.xlsx` as binary base64 and executes the wizard's action programmatically.
- **Target:** Automatically imports recipes into two categories:
  - **MRP BoMs (Manufacturing):** Associated with production subproducts (e.g. *PAN DE LA CASA BLANCO*, *FOCACCIA*).
  - **POS BoMs (Point of Sale):** Associated with dishes (e.g. *HUEVOS BENEDICTINOS CON JAMÓN DE PAVO*).
- **Verdict:** Perfect as a test command to check if recipes import cleanly in a new database.

### 4. `setup_spa_final.py` & `setup_spa_data.py`
- **Path:** Root level (`setup_spa_final.py` / `setup_spa_data.py`)
- **Mechanism:** Web API RPC connections (JSON-RPC). They authenticate as `soporte@crossnexion.com` over HTTP and invoke Odoo models remotely.
- **Target:** Configures test contacts, POS settings, and dummy partners.
- **Verdict:** Useful for sandbox validation and automated UI test environments.

---

## 📂 Directory Structure

```
odoo18_provecchio/
├── docker-compose.yml              # Multi-container Docker setup (web, db, init)
├── Dockerfile                      # Rebuilt Odoo 18 image containing pandas, openpyxl>=3.1.5, pyopenssl
├── requirements.txt                # Python package list
├── .env                            # Environment variables (ports, hostnames, passwords)
├── config/
│   └── odoo.conf                   # Odoo server configuration
├── addons/                         # Custom modules & import data
│   ├── excel_recipe_import/       # Wizard to import recipes from Excel
│   ├── product_mass_import/       # Bulk product import UI
│   ├── pos_product_bom/           # POS ingredients and POS BOM
│   ├── *data files*                # comida.csv, materia_prima_fixed.csv, plantilla_importacion.xlsx
│   └── *import scripts*            # import_products_direct.py, import_comidas_direct.py, import_recipes_direct.py
├── init_prod_db.sh                 # Database initialization script (called by odoo_init_db_18)
└── README.md                       # This documentation file
```
