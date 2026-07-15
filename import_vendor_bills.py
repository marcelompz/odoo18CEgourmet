#!/usr/bin/env python3
"""
Import posted vendor bills from prod_bkup_2026-04-03 to prod_fixed_2026-04-04
"""
import psycopg2
import json

# Database connection params
DB_PARAMS = {
    'host': 'db_odoo_5771',
    'user': 'odoo',
    'password': 'odoo',
}

SOURDE_DB = 'prod_fixed_2026-04-04'
TARGET_DB = 'prod_fixed_2026-04-05'

def get_source_data():
    """Extract posted vendor bills from source database"""
    conn = psycopg2.connect(dbname=SOURCE_DB, **DB_PARAMS)
    cur = conn.cursor()
    
    # Get all posted vendor bills
    cur.execute("""
        SELECT id, name, ref, partner_id, invoice_date, date, 
               amount_total, amount_tax, amount_untaxed, journal_id,
               narration, payment_reference, fiscal_position_id,
               move_type, state, auto_post, to_check, reversed_entry_id,
               tax_lock_date, invoice_origin, incoterm_id, delivery_date,
               currency_id, company_id
        FROM account_move 
        WHERE move_type = 'in_invoice' AND state = 'posted'
        ORDER BY id
    """)
    moves = cur.fetchall()
    move_cols = [desc[0] for desc in cur.description]
    
    # Get all move lines for these moves
    move_ids = [m[0] for m in moves]
    cur.execute("""
        SELECT aml.id, aml.move_id, aml.account_id, aml.name, aml.debit, aml.credit,
               aml.quantity, aml.price_unit, aml.product_id, aml.tax_line_id,
               aml.purchase_line_id, aml.partner_id, aml.currency_id, aml.company_id,
               aml.amount_currency, aml.tax_base_amount, aml.tax_tag_invert,
               aml.tax_exigible, aml.tax_group_id, aml.tax_repartition_line_id,
               aml.tax_audit, aml.maturity_date, aml.date, aml.display_type,
               aml.sequence, aml.parent_state
        FROM account_move_line aml
        WHERE aml.move_id = ANY(%s)
        ORDER BY aml.move_id, aml.sequence, aml.id
    """, (move_ids,))
    lines = cur.fetchall()
    line_cols = [desc[0] for desc in cur.description]
    
    # Get purchase order line IDs referenced
    po_line_ids = [l[10] for l in lines if l[10] is not None]
    if po_line_ids:
        cur.execute("""
            SELECT pol.id, pol.order_id, po.name as po_name
            FROM purchase_order_line pol
            JOIN purchase_order po ON pol.order_id = po.id
            WHERE pol.id = ANY(%s)
        """, (po_line_ids,))
        po_lines = {row[0]: {'order_id': row[1], 'po_name': row[2]} for row in cur.fetchall()}
    else:
        po_lines = {}
    
    cur.close()
    conn.close()
    
    return {
        'moves': moves,
        'move_cols': move_cols,
        'lines': lines,
        'line_cols': line_cols,
        'po_lines': po_lines,
    }

def import_to_target(data):
    """Import vendor bills into target database"""
    conn = psycopg2.connect(dbname=TARGET_DB, **DB_PARAMS)
    cur = conn.cursor()
    
    # Get current max IDs
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM account_move")
    max_move_id = cur.fetchone()[0]
    
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM account_move_line")
    max_line_id = cur.fetchone()[0]
    
    print(f"Target max move_id: {max_move_id}, max line_id: {max_line_id}")
    
    # Create ID mapping: source_id -> target_id
    move_id_map = {}
    line_id_map = {}
    
    new_move_id = max_move_id + 1
    new_line_id = max_line_id + 1
    
    # Map move IDs
    for move in data['moves']:
        src_id = move[0]
        move_id_map[src_id] = new_move_id
        new_move_id += 1
    
    # Map line IDs
    for line in data['lines']:
        src_id = line[0]
        line_id_map[src_id] = new_line_id
        new_line_id += 1
    
    # Check if referenced PO lines exist in target
    existing_po_lines = set()
    po_line_ids = list(data['po_lines'].keys())
    if po_line_ids:
        cur.execute("""
            SELECT id FROM purchase_order_line WHERE id = ANY(%s)
        """, (po_line_ids,))
        existing_po_lines = {row[0] for row in cur.fetchall()}
        print(f"PO lines in source: {len(po_line_ids)}, existing in target: {len(existing_po_lines)}")
    
    # Insert moves
    moves_inserted = 0
    for move in data['moves']:
        src_id = move[0]
        target_id = move_id_map[src_id]
        
        # Build insert for account_move
        # Columns: id, name, ref, partner_id, invoice_date, date, amount_total, amount_tax,
        #          amount_untaxed, journal_id, narration, payment_reference, fiscal_position_id,
        #          move_type, state, auto_post, to_check, reversed_entry_id, tax_lock_date,
        #          invoice_origin, incoterm_id, delivery_date, currency_id, company_id
        try:
            cur.execute("""
                INSERT INTO account_move (
                    id, name, ref, partner_id, invoice_date, date, amount_total, amount_tax,
                    amount_untaxed, journal_id, narration, payment_reference, fiscal_position_id,
                    move_type, state, auto_post, to_check, reversed_entry_id, tax_lock_date,
                    invoice_origin, incoterm_id, delivery_date, currency_id, company_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                target_id, move[1], move[2], move[3], move[4], move[5],
                move[6], move[7], move[8], move[9], move[10], move[11], move[12],
                move[13], move[14], move[15], move[16], move[17], move[18],
                move[19], move[20], move[21], move[22], move[23]
            ))
            moves_inserted += 1
        except Exception as e:
            print(f"Error inserting move {src_id} ({move[1]}): {e}")
            conn.rollback()
            continue
    
    print(f"Inserted {moves_inserted} moves")
    
    # Insert move lines
    lines_inserted = 0
    lines_skipped_po = 0
    for line in data['lines']:
        src_id = line[0]
        target_id = line_id_map[src_id]
        src_move_id = line[1]
        target_move_id = move_id_map.get(src_move_id)
        
        if not target_move_id:
            print(f"Skipping line {src_id}: parent move {src_move_id} not mapped")
            continue
        
        po_line_id = line[10]
        # If PO line doesn't exist in target, set to NULL
        if po_line_id is not None and po_line_id not in existing_po_lines:
            po_line_id = None
            lines_skipped_po += 1
        
        try:
            cur.execute("""
                INSERT INTO account_move_line (
                    id, move_id, account_id, name, debit, credit,
                    quantity, price_unit, product_id, tax_line_id,
                    purchase_line_id, partner_id, currency_id, company_id,
                    amount_currency, tax_base_amount, tax_tag_invert,
                    tax_exigible, tax_group_id, tax_repartition_line_id,
                    tax_audit, maturity_date, date, display_type,
                    sequence, parent_state
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                target_id, target_move_id, line[2], line[3], line[4], line[5],
                line[6], line[7], line[8], line[9], po_line_id, line[11], line[12], line[13],
                line[14], line[15], line[16], line[17], line[18], line[19],
                line[20], line[21], line[22], line[23], line[24], line[25]
            ))
            lines_inserted += 1
        except Exception as e:
            print(f"Error inserting line {src_id} for move {src_move_id}: {e}")
            conn.rollback()
            continue
    
    print(f"Inserted {lines_inserted} move lines ({lines_skipped_po} had missing PO lines)")
    
    # Update sequences
    cur.execute(f"SELECT setval('account_move_id_seq', {new_move_id})")
    cur.execute(f"SELECT setval('account_move_line_id_seq', {new_line_id})")
    
    conn.commit()
    print("Migration complete!")
    
    # Verify
    cur.execute("""
        SELECT COUNT(*) FROM account_move 
        WHERE move_type = 'in_invoice' AND state = 'posted'
    """)
    print(f"Total posted vendor bills in target: {cur.fetchone()[0]}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    print("Extracting vendor bills from source database...")
    data = get_source_data()
    print(f"Found {len(data['moves'])} posted vendor bills with {len(data['lines'])} move lines")
    
    print("\nImporting to target database...")
    import_to_target(data)
