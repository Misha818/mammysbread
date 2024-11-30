subProducts = [{'ID': 2, 'Name': 'Cookie Mookie', 'Text': 'Weight Meight', 'spssID': 4, 'spssStatus': 1, 'spssRefKey': 5}, {'ID': 2, 'Name': 'Cookie Mookie', 'Text': 'Color Molor', 'spssID': 5, 'spssStatus': 1, 'spssRefKey': 6}, {'ID': 2, 'Name': 'Cookie Mookie', 'Text': 'Taste Maste', 'spssID': 6, 'spssStatus': 1, 'spssRefKey': 8}]

prData = subProducts
print(f'len(subProducts) {len(subProducts)}')
print(f'len(prData) {len(prData)}')
prData.pop(0)
print('--------------')

print(f'len(subProducts) {len(subProducts)}')
print(f'len(prData) {len(prData)}')

PS C:\Users\User\OneDrive\Desktop\IT\E-Market> py test.py
len(subProducts) 3
len(prData) 3
--------------
len(subProducts) 2
len(prData) 2