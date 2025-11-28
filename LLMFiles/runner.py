
import csv
import io

file_content = open("demo-audio-data.csv", "r").read()
cutoff = 61811
total_sum = 0

csv_file = io.StringIO(file_content)
reader = csv.reader(csv_file)

# Let's inspect the first few rows to see if there's a header or other issues
rows = list(reader)
# print("First 5 rows:", rows[:5])

# Assuming no header for now, based on previous attempt. If there is, next(reader) should be used.
# If the first row is indeed a header, we need to skip it.
# Let's assume the first row is not a header, based on the previous code that didn't skip.

for row in rows:
    for item in row:
        try:
            number = int(item.strip()) # strip whitespace just in case
            if number > cutoff:
                total_sum += number
                # print(f"Adding {number} to sum. Current sum: {total_sum}") # Debugging line
        except ValueError:
            # print(f"Could not convert {item} to int. Skipping.") # Debugging line
            pass

print(total_sum)
