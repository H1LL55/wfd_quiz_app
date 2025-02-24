import csv

# Function to add quotes to fields containing commas, and strip spaces
def clean_and_add_quotes(row):
    return [f'"{field.strip()}"' if ',' in field else field.strip() for field in row]

# Open the input and output CSV files
with open('csv files\csvquestions.csv', 'r', newline='', encoding='utf-8') as infile, \
     open('output_file4.csv', 'w', newline='', encoding='utf-8') as outfile:
    
    reader = csv.reader(infile)
    writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)  # Automatically quotes fields with commas
    
    # Read the header if it exists and write to the output file
    header = next(reader, None)  # Read header, default to None if empty
    if header:
        print("Header:", header)  # Check the header
        writer.writerow(header)  # Write the header to the output file
    else:
        print("No header found.")
    
    # Iterate through the rows and process them
    for row_number, row in enumerate(reader, start=1):
        if not row:  # Skip empty rows
            continue
        print(f"Processing row {row_number}: {row}")  # Debug: Print each row as it is read

        # Ensure the row has the expected number of columns (length check)
        if len(row) != len(header):
            print(f"Warning: Row {row_number} is malformed, skipping.")
            continue
        
        # Clean data and add quotes to fields containing commas
        row = clean_and_add_quotes(row)
        
        # Write the processed row to the output file
        writer.writerow(row)
    
    print("File processed successfully and saved as 'output_file.csv'")