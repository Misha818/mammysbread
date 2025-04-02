import re
amount = '545'

invalid = False
if not amount:
    invalid = True
num = amount.count(',') + amount.count('.')

print(bool(re.match(r'^[0-9.,]+$', amount)))

if num > 1 or invalid == True or bool(re.match(r'^[0-9.,]+$', amount)) == False:
    print('Invalid number')
else:
    print('The number is valid!')



# num = amount.count(',') + amount.count('.')
# if num > 1:
#     print('Invalid number')
    


# if bool(re.match(r'^[0-9.,]+$', amount)):
#     print('amount is digital')
# else:
#     print('amount is NOT digital')
