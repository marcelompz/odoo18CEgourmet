import re
import sys

def remove_attrs(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Remove attrs attributes
    pattern = r'\s+attrs="{[^}]*}"'
    content = re.sub(pattern, '', content)

    with open(filename, 'w') as f:
        f.write(content)

    print(f"Removed attrs from {filename}")

def tree_to_list(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Replace tree with list
    content = content.replace('<tree ', '<list ')
    content = content.replace('</tree>', '</list>')
    # Also replace standalone tree tags (without attributes)
    content = content.replace('<tree>', '<list>')
    content = content.replace('</tree>', '</list>')

    with open(filename, 'w') as f:
        f.write(content)

    print(f"Changed tree to list in {filename}")

# Process files
remove_attrs('views/cleanup_log_views.xml')
remove_attrs('views/cleanup_config_views.xml')
remove_attrs('wizard/cleanup_wizard_views.xml')
remove_attrs('wizard/cleanup_pos_tax_wizard_views.xml')

tree_to_list('views/cleanup_log_views.xml')
tree_to_list('views/cleanup_config_views.xml')
tree_to_list('wizard/cleanup_pos_tax_wizard_views.xml')