# Odoo 18 CE - Provecchio Deployment (Gourmet)

**Odoo 18 CE deployment for Provecchio (Paraguay) with full localization support and custom import modules.**

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

# 2. Start Docker containers (this starts postgres and odoo, plus the init container)
docker compose up -d

# 3. Wait for initialization to complete
docker logs -f odoo_init_db_18
```

### Access

- **URL:** http://localhost:9038
- **Database:** `prod`
- **Email:** `soporte@crossnexion.com`
- **Password:** `Cross1983_`

## 📁 Project Structure

```
odoo18_provecchio/
├── docker-compose.yml       # Docker configuration
├── .env                     # Environment variables
├── config/
│   └── odoo.conf           # Odoo configuration
├── addons/                  # Custom modules (excel_recipe_import, product_mass_import, pos_product_bom, etc.)
├── init_prod_db.sh         # Database initialization script (configured for Odoo 18)
└── README.md                # This file
```
