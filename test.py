data = [
  {
    "quantityID": 1,
    "quantity": 10,
    "maxQuantity": None,
    "ptID": 12
  },
  {
    "quantityID": 2,
    "quantity": 5,
    "maxQuantity": None,
    "ptID": 12
  },
  {
    "quantityID": 3,
    "quantity": 15,
    "maxQuantity": None,
    "ptID": 12
  }
]

Q = 19

bufferQuantities = {}
flag = True
while flag:
    for row in data:
        print(Q)
        if flag != True:
            break
        if row['quantity'] >= Q:
            # sql Update `quantity`
            bufferQuantities[row['quantityID']] = Q
            flag = False
        if row['quantity'] < Q:
            # sql Update `quantity`
            Q = Q - row['quantity']
            bufferQuantities[row['quantityID']] = row['quantity']

print(bufferQuantities)

        

# def boffer_q(qID, q, Q):
