import argparse
from functools import reduce
import glob
import multiprocessing
from tqdm import tqdm
import os
import random
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import nltk
import string

nltk.download('punkt')
nltk.download('stopwords')
stopwords = nltk.corpus.stopwords.words('english')
stemmer = nltk.stem.porter.PorterStemmer()

def transform_name(product_name):
    # IMPLEMENT
    products = [
        word.lower().replace("-", "")
        for word in nltk.tokenize.word_tokenize(product_name)
        if word not in stopwords 
        and word not in string.punctuation
    ]
    return " ".join(
        [
            stemmer.stem(product) 
            for product in products
        ]
    )

# Directory for product data
directory = r'/workspace/datasets/product_data/products/'

parser = argparse.ArgumentParser(description='Process some integers.')
general = parser.add_argument_group("general")
general.add_argument("--input", default=directory,  help="The directory containing product data")
general.add_argument("--output", default="/workspace/datasets/fasttext/output.fasttext", help="the file to output to")
general.add_argument("--label", default="id", help="id is default and needed for downsteam use, but name is helpful for debugging")

# Consuming all of the product data, even excluding music and movies,
# takes a few minutes. We can speed that up by taking a representative
# random sample.
general.add_argument("--sample_rate", default=1.0, type=float, help="The rate at which to sample input (default is 1.0)")

# IMPLEMENT: Setting min_products removes infrequent categories and makes the classifier's task easier.
general.add_argument("--min_products", default=0, type=int, help="The minimum number of products per category (default is 0).")

args = parser.parse_args()
output_file = args.output
path = Path(output_file)
output_dir = path.parent
if os.path.isdir(output_dir) == False:
        os.mkdir(output_dir)

if args.input:
    directory = args.input
# IMPLEMENT:  Track the number of items in each category and only output if above the min
min_products = args.min_products
sample_rate = args.sample_rate
names_as_labels = False
if args.label == 'name':
    names_as_labels = True


def _label_filename(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    labels = []
    for child in root:
        if random.random() > sample_rate:
            continue
        # Check to make sure category name is valid and not in music or movies
        if (child.find('name') is not None and child.find('name').text is not None and
            child.find('categoryPath') is not None and len(child.find('categoryPath')) > 0 and
            child.find('categoryPath')[len(child.find('categoryPath')) - 1][0].text is not None and
            child.find('categoryPath')[0][0].text == 'cat00000' and
            child.find('categoryPath')[1][0].text != 'abcat0600000'):
              # Choose last element in categoryPath as the leaf categoryId or name
              if names_as_labels:
                  cat = child.find('categoryPath')[len(child.find('categoryPath')) - 1][1].text.replace(' ', '_')
              else:
                  cat = child.find('categoryPath')[len(child.find('categoryPath')) - 1][0].text
              # Replace newline chars with spaces so fastText doesn't complain
              name = child.find('name').text.replace('\n', ' ')
              labels.append({
                "category": cat, 
                "name": transform_name(name)
               })
    return labels

def merge_lists(left, right):
    if right:
        return left.extend(right)
    else:
        return left 

if __name__ == '__main__':
    files = glob.glob(f'{directory}/*.xml')
    print("Writing results to %s" % output_file)

    with multiprocessing.Pool() as p:
        all_labels = tqdm(p.imap_unordered(_label_filename, files), total=len(files))
        results = []
        for result in all_labels:
            if result:
                results.extend(result)
        df_results = pd.DataFrame(results)
        df_results_summary = df_results['category'].value_counts()
        categories_to_keep = df_results_summary[df_results_summary > min_products].index.tolist()
        print(
            df_results_summary.nlargest(20)
        )
        df_results = df_results.query('category.isin(@categories_to_keep)')     
        print(
            f"Total number of records: {df_results.shape[0]}"
        )   
        with open(output_file, 'w') as output:
            for row in df_results.to_dict(orient="records"):
                output.write(
                    f'__label__{row["category"]} {row["name"]}\n'
                )
