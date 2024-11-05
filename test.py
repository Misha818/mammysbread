page = int(input('Page '))
PAGINATION = 3
selectFrom = (page - 1) * PAGINATION
selectTo = selectFrom + PAGINATION

print(f"From {selectFrom} To {selectTo}")