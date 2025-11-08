# Ask the user for their name and preferred greeting (e.g., "Hello,", "Welcome,") and use f-strings to combine the input into a custom message.
name = input("Enter your name: ")
greeting = input("Enter your preferred greeting (e.g., 'Hello,', 'Welcome,'): ")
custom_message = f"{greeting} {name}!"
print(custom_message)