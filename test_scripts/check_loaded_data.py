import sys

session = env['pos.session'].search([], limit=1)
if session:
    loaded_data = session.load_pos_data()
    for key in loaded_data.keys():
        print(f"Key: {key}")
        if not isinstance(loaded_data[key], list) and not isinstance(loaded_data[key], dict):
            print(f"  Type: {type(loaded_data[key])}")
        else:
            print(f"  Type: {type(loaded_data[key])} - Len: {len(loaded_data[key])}")
            if key == 'pos.session':
                print(f"  Keys in pos.session: {loaded_data[key].keys()}")
            if key == 'pos.config':
                print(f"  Keys in pos.config: {loaded_data[key].keys()}")
