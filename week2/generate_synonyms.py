from argparse import ArgumentParser
import os
from pathlib import Path
import fasttext

MODEL_DIRECTORY_DEFAULT = '/workspace/datasets/fasttext/title_model_normalized.bin'
FILEPATH_DEFAULT = '/workspace/datasets/fasttext/top_words.txt'
OUTPUT_DEFAULT = '/workspace/datasets/fasttext/synonyms.csv'

parser = ArgumentParser("Ingest model path and threshold for NN")
parser.add_argument(
    "--model-path",
    default=MODEL_DIRECTORY_DEFAULT,
    type=str
)
parser.add_argument(
    "--threshold",
    default=0.8,
    type=float
)
parser.add_argument(
    "--file-path",
    default=FILEPATH_DEFAULT,
    type=str
)
parser.add_argument(
    "--output",
    default=OUTPUT_DEFAULT,
    type=str
)
args = parser.parse_args()
MODEL_DIRECTORY = Path(args.model_path)
THRESHOLD = args.threshold
FILEPATH = Path(args.file_path)
OUTPUT_FILENAME = Path(args.output)

model = fasttext.load_model(MODEL_DIRECTORY)

def main():
    with open(FILEPATH, 'r') as f:
        words = f.readlines()
        
    results = []
    for word in words:
        scores_synonyms = model.get_nearest_neighbors(word)
        synonyms = " ".join(
            [
                ss[1]
                for ss in scores_synonyms
                if ss[0] > THRESHOLD 
            ]
        )
        results.append(
            {
                'word': word,
                "synonyms": synonyms 
            }
        )

    df_results = pd.DataFrame(results)
    df_results.to_csv(
        OUTPUT_FILENAME,
        header=False
    )

if __name__ == '__main__':
    main()
