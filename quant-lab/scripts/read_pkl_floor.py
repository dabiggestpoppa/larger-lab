import pickle, os, json

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Read pkl and print ALL fields for FLOOR mode of our pairs
with open(os.path.join(reports, '_matrix_data.pkl'), 'rb') as f:
    data = pickle.load(f)

target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

for p in target_pairs:
    d = data.get(p, {})
    floor = d.get('FLOOR', {})
    if floor:
        print(f'{p} FLOOR:')
        for k, v in floor.items():
            print(f'  {k}: {v}')
    else:
        print(f'{p}: NO FLOOR')
    print()
