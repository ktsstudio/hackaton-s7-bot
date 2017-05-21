import os
from lxml import etree
import pandas as pd


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
def main():
    etree.register_namespace('sphinx', "http://www.company.com")  # some name
    root = etree.Element('{http://www.company.com}docset')
    schema = etree.Element('{http://www.company.com}schema')
    schema.append(etree.Element('{http://www.company.com}field', attrib={
        'name': 'title'
    }))
    schema.append(etree.Element('{http://www.company.com}field', attrib={
        'name': 'text'
    }))
    schema.append(etree.Element('{http://www.company.com}attr', attrib={
        'name': 'title',
        'type': 'string'
    }))
    schema.append(etree.Element('{http://www.company.com}attr', attrib={
        'name': 'text',
        'type': 'string'
    }))
    root.append(schema)

    df = pd.read_csv(os.path.join(CURRENT_DIR, './faq.csv'),
                     names=['category', 'title', 'text'])

    for row_id, row in df.iterrows():
        doc = etree.Element('{http://www.company.com}document', attrib={
            'id': str(row_id + 1)
        })

        title = etree.Element('title')
        text = etree.Element('text')
        title.text = row['title']
        text.text = row['text']
        doc.append(title)
        doc.append(text)

        root.append(doc)

    print('<?xml version="1.0" encoding="utf-8"?>')
    print(etree.tostring(root, pretty_print=True, encoding='utf-8').decode('utf-8'))


if __name__ == '__main__':
    main()
