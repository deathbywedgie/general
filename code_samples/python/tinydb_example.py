from tinydb import TinyDB, Query


# Initialize TinyDB with a JSON storage file
# args and kwargs defined here are passed to JSON later
root_db = TinyDB('db.json', indent=2)

# db.default_table_name = "something_else"

db = root_db.table("table1")


# Insert data into the database
db.insert({'name': 'John', 'age': 22, 'location': 'New York'})
db.insert({'name': 'Jane', 'age': 28, 'location': 'Chicago'})
db.insert({'name': 'Doe', 'age': 32, 'location': 'San Francisco'})

# Query the database
User = Query()
result = db.search(User.age > 25)

# Print results
print(result)  # Output: [{'name': 'Jane', 'age': 28, 'location': 'Chicago'}, {'name': 'Doe', 'age': 32, 'location': 'San Francisco'}]

# Update a record
db.update({'age': 29}, User.name == 'Jane')

# Print the updated record
print(db.search(User.name == 'Jane'))  # Output: [{'name': 'Jane', 'age': 29, 'location': 'Chicago'}]

# Remove a record
db.remove(User.name == 'Doe')

# Print remaining records
print(db.all())  # Output: [{'name': 'John', 'age': 22, 'location': 'New York'}, {'name': 'Jane', 'age': 29, 'location': 'Chicago'}]

# Close the database
root_db.close()
