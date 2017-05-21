import csv
import os

import bs4
import pandas as pd
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    df = pd.read_csv(os.path.join(CURRENT_DIR, 'faq.csv'),
                     names=['category', 'title', 'text'])
    d = df.drop_duplicates(['title'])
    d.to_csv(os.path.join(CURRENT_DIR, 'faq.csv'))


if __name__ == '__main__':
    main()
