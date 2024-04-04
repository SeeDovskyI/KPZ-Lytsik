import pandas as pd
from datetime import datetime
import os

filename = 'filename.csv'

# Проверка наличия файла и чтение, если он существует
if os.path.isfile(filename):
    df = pd.read_csv(filename)
else:
    df = pd.DataFrame(columns=['year', 'month', 'day', 'hour', 'minute', 'second'])

now = datetime.now()

new_row = now.strftime('%Y %m %d %H %M %S').split()
df.loc[len(df)] = new_row

df.to_csv(filename, index=False)

print(df)
