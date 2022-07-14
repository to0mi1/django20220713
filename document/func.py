import os

from argon2 import PasswordHasher
from pandas import DataFrame


def hash_text(text: str):
    ph = PasswordHasher()
    hashed = ph.hash('aaa')
    return os.getpid(), text, hashed


def hash_text_df(df: DataFrame, shared_list=None):
    result_df = df.copy()
    result_df.assign(Hashed='')
    ph = PasswordHasher()
    for i, row in df.iterrows():
        plain_test = ''.join(row[6:9].values)
        if shared_list is not None:
            shared_list.append(plain_test)
        result_df.at[i, 'Hashed'] = ph.hash(plain_test)
    return result_df
