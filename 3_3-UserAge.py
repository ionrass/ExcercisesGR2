# Use comparison and logical operators (and, or, not) to check if a user's age is between 18 and 65, inclusive, but not exactly 30.
age = int(input("Enter your age: "))
is_between_18_and_65 = 18 <= age <= 65
is_not_30 = age != 30
print("Is the user's age between 18 and 65, inclusive, but not exactly 30?", is_between_18_and_65 and is_not_30)