# Read a monetary value from the user (as a string), convert it to a float, and use f-string formatting to display it rounded to two decimal places and prefixed with a dollar sign.
monetary_value_str = input("Enter a monetary value (e.g., 12.3456): ")
monetary_value = float(monetary_value_str)
formatted_value = f"${monetary_value:.2f}"
print("Formatted monetary value:", formatted_value)
