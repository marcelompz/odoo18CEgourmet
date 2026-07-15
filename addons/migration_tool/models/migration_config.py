# -*- coding: utf-8 -*-
import os
import logging
import subprocess
import json
import requests
import shutil
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MigrationConfig(models.Model):
    _name = 'migration.config'
    _description = 'Migration Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, default='Default')
    
    # Deployment type
    deployment_type = fields.Selection([
        ('docker', 'Docker Compose'),
        ('bare_metal', 'Bare Metal / Local'),
    ], string='Deployment Type', default='docker', required=True)
    
    # Docker settings
    db_container = fields.Char(string='DB Container')
    odoo_container = fields.Char(string='Odoo Container')
    
    # Bare metal settings
    db_host = fields.Char(string='DB Host', default='localhost')
    db_port = fields.Integer(string='DB Port', default=5432)
    db_user = fields.Char(string='DB User', default='odoo')
    db_password = fields.Char(string='DB Password', password=True)
    psql_path = fields.Char(string='psql Path', default='psql')
    pg_dump_path = fields.Char(string='pg_dump Path', default='pg_dump')
    createdb_path = fields.Char(string='createdb Path', default='createdb')
    dropdb_path = fields.Char(string='dropdb Path', default='dropdb')
    
    # Source DB
    source_db = fields.Char(string='Source Database', required=True)
    source_url = fields.Char(string='Source URL', default='http://localhost:8069')
    source_user = fields.Char(string='Source User')
    source_password = fields.Char(string='Source Password', password=True)
    
    # Target DB
    target_db = fields.Char(string='Target Database')
    target_url = fields.Char(string='Target URL')
    target_user = fields.Char(string='Target User')
    target_password = fields.Char(string='Target Password', password=True)
    
    # Export settings
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    export_path = fields.Char(string='Export Path', default='/tmp/migration_exports')
    
    active = fields.Boolean(default=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-detect containers on creation"""
        for vals in vals_list:
            if not vals.get('deployment_type'):
                vals['deployment_type'] = self._detect_deployment_type()
            if vals.get('deployment_type') == 'docker':
                if not vals.get('db_container'):
                    vals['db_container'] = self._detect_db_container()
                if not vals.get('odoo_container'):
                    vals['odoo_container'] = self._detect_odoo_container()
            # Auto-fill DB name
            if not vals.get('source_db'):
                vals['source_db'] = self._detect_current_db()
            # Auto-detect bare metal paths
            if vals.get('deployment_type') == 'bare_metal':
                for tool in ['psql_path', 'pg_dump_path', 'createdb_path', 'dropdb_path']:
                    if not vals.get(tool):
                        tool_name = tool.replace('_path', '')
                        vals[tool] = shutil.which(tool_name) or tool_name
        return super().create(vals_list)
    
    @api.model
    def _detect_deployment_type(self):
        """Detect if running in Docker or bare metal"""
        # Check for .dockerenv file
        if os.path.exists('/.dockerenv'):
            return 'docker'
        # Check if running inside a container
        try:
            with open('/proc/1/cgroup', 'r') as f:
                if 'docker' in f.read():
                    return 'docker'
        except:
            pass
        return 'bare_metal'
    
    @api.model
    def _detect_db_container(self):
        """Detect DB container from Odoo config HOST env var"""
        host = os.environ.get('HOST', '')
        if host:
            return host
        try:
            r = subprocess.run(
                ['docker', 'ps', '--filter', 'name=postgres', '--format', '{{.Names}}'],
                capture_output=True, text=True
            )
            containers = [c for c in r.stdout.strip().split('\n') if c]
            return containers[0] if containers else 'db_odoo'
        except:
            return 'db_odoo'
    
    @api.model
    def _detect_odoo_container(self):
        """Detect Odoo container from hostname"""
        hostname = os.environ.get('HOSTNAME', '')
        if hostname:
            return hostname
        try:
            r = subprocess.run(
                ['docker', 'ps', '--filter', 'name=odoo', '--format', '{{.Names}}'],
                capture_output=True, text=True
            )
            containers = [c for c in r.stdout.strip().split('\n') if c]
            return containers[0] if containers else 'odoo_web'
        except:
            return 'odoo_web'
    
    @api.model
    def _detect_current_db(self):
        """Detect current database name from Odoo config"""
        return os.environ.get('PGDATABASE', '') or self.env.cr.dbname
    
    # ====== Docker Methods ======
    
    def _get_docker_cmd(self):
        """Get docker exec command"""
        return ['docker', 'exec', self.db_container]
    
    def _run_docker_psql(self, db, query, stdin_data=None):
        """Run a psql command via Docker"""
        cmd = self._get_docker_cmd() + ['psql', '-U', 'odoo', '-d', db, '-c', query]
        r = subprocess.run(cmd, capture_output=True, text=True, input=stdin_data)
        return r
    
    def _run_docker_psql_pipe(self, src_db, src_query, dst_db, dst_cmd):
        """Export from one DB and import to another via Docker"""
        export_cmd = self._get_docker_cmd() + ['psql', '-U', 'odoo', '-d', src_db, '-c', src_query]
        import_cmd = ['docker', 'exec', self.db_container, 'psql', '-U', 'odoo', '-d', dst_db, '-c', dst_cmd]
        
        p1 = subprocess.Popen(export_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p2 = subprocess.run(import_cmd, stdin=p1.stdout, capture_output=True, text=True)
        p1.wait()
        return p2
    
    # ====== Bare Metal Methods ======
    
    def _get_psql_env(self):
        """Get environment for psql commands"""
        env = os.environ.copy()
        if self.db_password:
            env['PGPASSWORD'] = self.db_password
        return env
    
    def _run_bare_psql(self, db, query, stdin_data=None):
        """Run a psql command directly"""
        cmd = [
            self.psql_path,
            '-h', self.db_host,
            '-p', str(self.db_port),
            '-U', self.db_user,
            '-d', db,
            '-c', query,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, env=self._get_psql_env(), input=stdin_data)
        return r
    
    def _run_bare_psql_pipe(self, src_db, src_query, dst_db, dst_cmd):
        """Export from one DB and import to another directly"""
        export_cmd = [
            self.psql_path,
            '-h', self.db_host, '-p', str(self.db_port),
            '-U', self.db_user, '-d', src_db, '-c', src_query,
        ]
        import_cmd = [
            self.psql_path,
            '-h', self.db_host, '-p', str(self.db_port),
            '-U', self.db_user, '-d', dst_db, '-c', dst_cmd,
        ]
        
        p1 = subprocess.Popen(export_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            env=self._get_psql_env())
        p2 = subprocess.run(import_cmd, stdin=p1.stdout, capture_output=True, text=True,
                          env=self._get_psql_env())
        p1.wait()
        return p2
    
    def _run_bare_createdb(self, db, template):
        """Create database with template"""
        cmd = [
            self.createdb_path,
            '-h', self.db_host, '-p', str(self.db_port),
            '-U', self.db_user,
            '-T', template,
            db,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, env=self._get_psql_env())
        return r
    
    def _run_bare_dropdb(self, db):
        """Drop database"""
        cmd = [
            self.dropdb_path,
            '-h', self.db_host, '-p', str(self.db_port),
            '-U', self.db_user,
            '--if-exists',
            db,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, env=self._get_psql_env())
        return r
    
    def _run_bare_pg_dump(self, db, query):
        """Run pg_dump via psql"""
        # For bare metal, we use psql to run COPY commands
        return self._run_bare_psql(db, query)
    
    # ====== Unified Methods ======
    
    def _run_psql(self, db, query, stdin_data=None):
        """Run psql command (unified for both deployment types)"""
        if self.deployment_type == 'docker':
            return self._run_docker_psql(db, query, stdin_data)
        else:
            return self._run_bare_psql(db, query, stdin_data)
    
    def _run_psql_pipe(self, src_db, src_query, dst_db, dst_cmd):
        """Export from source and import to destination (unified)"""
        if self.deployment_type == 'docker':
            return self._run_docker_psql_pipe(src_db, src_query, dst_db, dst_cmd)
        else:
            return self._run_bare_psql_pipe(src_db, src_query, dst_db, dst_cmd)
    
    def copy_table(self, table, src_db, dst_db, where_clause=None):
        """Copy a table from source to destination"""
        where = f"WHERE {where_clause}" if where_clause else ""
        export_sql = f"COPY (SELECT * FROM {table} {where}) TO STDOUT WITH CSV;"
        import_sql = f"SET session_replication_role = 'replica'; COPY {table} FROM STDIN WITH CSV;"
        return self._run_psql_pipe(src_db, export_sql, dst_db, import_sql)
    
    def clone_and_clean_db(self, source_db, target_db):
        """Clone source DB and clean all transactional data"""
        log_lines = []
        
        def log(msg):
            log_lines.append(msg)
            _logger.info(msg)
        
        log(f"🔄 Cloning {source_db} → {target_db} ({self.deployment_type})")
        
        if self.deployment_type == 'docker':
            # Kill connections
            self._run_psql('postgres', f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid) 
                FROM pg_stat_activity 
                WHERE datname = '{target_db}' AND pid <> pg_backend_pid();
            """)
            self._run_psql('postgres', f"DROP DATABASE IF EXISTS {target_db};")
            self._run_psql('postgres', f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid) 
                FROM pg_stat_activity 
                WHERE datname = '{source_db}' AND pid <> pg_backend_pid();
            """)
            
            import time
            time.sleep(2)
            
            # Clone
            r = self._run_psql('postgres', f"CREATE DATABASE {target_db} TEMPLATE {source_db};")
            if r.returncode != 0:
                raise UserError(f"❌ Failed to clone: {r.stderr}")
            log("✅ Database cloned")
            
        else:
            # Bare metal: drop, kill connections, clone
            self._run_bare_dropdb(target_db)
            # Kill connections
            self._run_bare_psql('postgres', f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid) 
                FROM pg_stat_activity 
                WHERE datname = '{source_db}' AND pid <> pg_backend_pid();
            """)
            
            import time
            time.sleep(2)
            
            r = self._run_bare_createdb(target_db, source_db)
            if r.returncode != 0:
                raise UserError(f"❌ Failed to clone: {r.stderr}")
            log("✅ Database cloned")
        
        # Clean transactional data
        clean_sql = """
        SET session_replication_role = 'replica';
        DELETE FROM pos_payment;
        DELETE FROM pos_order_line;
        DELETE FROM pos_order;
        DELETE FROM pos_session;
        DELETE FROM account_bank_statement_line;
        DELETE FROM account_bank_statement;
        DELETE FROM account_payment;
        DELETE FROM stock_move_line;
        DELETE FROM stock_valuation_layer;
        DELETE FROM stock_move;
        DELETE FROM stock_picking;
        DELETE FROM stock_quant;
        DELETE FROM sale_order_line;
        DELETE FROM sale_order;
        DELETE FROM purchase_order_line;
        DELETE FROM purchase_order;
        DELETE FROM account_move_line;
        DELETE FROM account_move;
        DELETE FROM account_analytic_line;
        DELETE FROM fleet_vehicle_log_services;
        DELETE FROM payment_transaction;
        DELETE FROM sms_sms;
        DELETE FROM lot_validation_log;
        SET session_replication_role = 'origin';
        """
        self._run_psql(target_db, clean_sql)
        log("✅ Transactional data cleaned")
        
        return '\n'.join(log_lines)
    
    def copy_all_transactional(self, source_db, target_db):
        """Copy all transactional data from source to target"""
        log_lines = []
        tables = [
            'pos_session', 'pos_order', 'pos_order_line', 'pos_payment',
            'purchase_order', 'purchase_order_line',
            'stock_picking', 'stock_move', 'stock_move_line', 
            'stock_quant', 'stock_valuation_layer',
        ]
        
        for table in tables:
            self.copy_table(table, source_db, target_db)
            log_lines.append(f"✅ {table}")
        
        # Recalculate PO amounts
        self._run_psql(target_db, """
            UPDATE purchase_order po
            SET amount_untaxed = COALESCE(sub.untaxed, 0),
                amount_tax = COALESCE(sub.tax, 0),
                amount_total = COALESCE(sub.untaxed, 0) + COALESCE(sub.tax, 0)
            FROM (
                SELECT pol.order_id, 
                    SUM(pol.price_subtotal) as untaxed, 
                    SUM(pol.price_tax) as tax
                FROM purchase_order_line pol 
                GROUP BY pol.order_id
            ) sub 
            WHERE po.id = sub.order_id;
        """)
        log_lines.append("✅ PO amounts recalculated")
        
        return '\n'.join(log_lines)
    
    def fix_icons(self, target_db):
        """Clear web assets and mark modules for upgrade"""
        self._run_psql(target_db, "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';")
        self._run_psql(target_db, "UPDATE ir_module_module SET state = 'to upgrade' WHERE state = 'installed';")
        return "✅ Assets cleared. Restart Odoo and reload page."
