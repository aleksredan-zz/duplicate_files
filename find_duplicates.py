"""
The script for finding duplicated files in the given paths.

Aleksander Tadeusz Dominiczak (atdo@equinor.com, github:aleksredan)
"""
import os, sys
import numpy as np
import pandas as pd
import hashlib 

def read_paths()->list:
    paths = []
    i = 0
    number=int(input('Enter number of folders to look up for duplicates:'))
    while i < number:
        temp = input('Add folder path for duplicate screening:')
        if not os.path.exists(temp) or not os.path.isdir(temp):
            print('Thats not correct path')
            if get_bool('Do you want to add another path (1) or skip (0):'):
                continue
            else:
                i += 1
                continue
        paths.append(temp)
        i += 1
    return paths

def get_bool(prompt: str)->bool:
    while True:
        try:
           return {'1':True,'0':False}[input(prompt)]
        except KeyError:
           print('Invalid input please enter True or False!')

def create_path_size_df(path: str, silent=False)->pd.DataFrame:
    temp_list = []
    print(f'Screening files in {path}:')
    for dir_name, _, file_list in os.walk(path):
        for file_name in file_list:
            full_path = os.path.join(dir_name, file_name)
            if os.path.isfile(full_path) and not file_name.startswith('~'):
                size = os.path.getsize(full_path)
                temp_list.append((full_path, size))
                if not silent:
                    print(f'{size}\t\t{file_name}')
    labels = ['path','size']
    df = pd.DataFrame.from_records(temp_list, columns=labels)
    return df

def check_same(df: pd.DataFrame, column: str):
    length = len(df.index)
    duplicate_counter: int = 0
    df['duplicate'] = np.nan
    df['delete_row'] = np.nan
    df = df.sort_values(by=[column])
    df = df.reset_index(drop=True)
    df.loc[0,'duplicate'] = duplicate_counter
    for i in range(length-1):
        if df.loc[i+1, column]==df.loc[i, column]:
            df.loc[i+1, 'duplicate'] = duplicate_counter
        else:
            count = df[df.duplicate == df.loc[i,'duplicate']].shape[0]
            if count == 1:
                df.loc[i,'delete_row'] = 1
            duplicate_counter += 1
            df.loc[i+1, 'duplicate'] = duplicate_counter
    if df[column][df.index[-1]] != df[column][df.index[-2]]:
        df.loc[df.index[-1],'delete_row'] = 1
    df = df[df['delete_row'] != 1]
    df = df.reset_index(drop=True)
    df = df.drop(['delete_row'], axis=1)
    print(df)
    return df

def check_same_filesizes(df: pd.DataFrame):
    df = check_same(df, 'size')
    return df


def check_same_hashes(df: pd.DataFrame):
    for i in range(len(df.index)):
        df.loc[i,'hash'] = file_hash(df.loc[i,'path'])
    df = check_same(df,'hash')
    df = df.drop(['hash'], axis=1)
    return df 

def file_hash(path: str, blocksize = 65536):
    try :
        f = open(path, 'rb')
        hasher = hashlib.md5()
        buffer = f.read(blocksize)
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = f.read(blocksize)
        f.close()
        file_hash = hasher.hexdigest()
    except OSError:
        file_hash = '0'
    return file_hash

def find_duplicates(paths: list)-> pd.DataFrame: 
    df = pd.DataFrame()
    for path in paths:
        df_temp = create_path_size_df(path,silent=True)
        df = pd.concat([df, df_temp])
    total_files = len(df.index)
    df.to_csv('paths_for_duplicates.csv')
    print(f'Total of {total_files} files found during screening of provided paths.')
    df = check_same_filesizes(df)
    first_check = len(df.index)
    df.to_csv('sizes_compared.csv')
    print(f'{first_check/total_files*100}% of analised files was preselected for hash checking.')
    df = check_same_hashes(df)
    second_check = len(df.index)
    print(f'{second_check/total_files*100}% of analised files are duplicates (have the same hash, even if the name is different). It\'s {second_check/first_check*100}% of checked hashes.')
    df = sort_duplicate_results(df)
    return df

def sort_duplicate_results(df: pd.DataFrame, big_to_small: bool=True)-> pd.DataFrame:
    if big_to_small:
        ascending = [False,True]
    else:
        ascending = [True,True]
    df = df.sort_values(by=['size', 'duplicate'], ascending=ascending)
    df = df.reset_index(drop=True)
    return df

def main():
    paths = read_paths()
    data = find_duplicates(paths)
    data.to_csv('duplicates.csv')

main()