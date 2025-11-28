import pandas as pd

df = pd.read_csv('demo-audio-data.csv', header=None)
# The first row is actually data, not a header, so we should consider it as part of the data.
# Let's rename the column to something generic, e.g., 'numbers'
df.columns = ['numbers']

cutoff = 61811

# Filter numbers greater than the cutoff
filtered_numbers = df[df['numbers'] > cutoff]

# Sum the filtered numbers
total_sum = filtered_numbers['numbers'].sum()

print(int(total_sum))