import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords')
nltk.download('punkt_tab')
stop_words = set(stopwords.words('english')) 
lemmatizer = WordNetLemmatizer()

def preprocess(text):

    # lowercase and stop removal


    tokens = word_tokenize(text.lower())
    
    filterdTokens = []
    for t in tokens:
        if t not in stop_words and t.isalpha():
            filterdTokens.append(t)
    tokens = filterdTokens

    # stemmer
    lemma = []
    for t in tokens:
        lemma.append(lemmatizer.lemmatize(t))
    tokens = lemma

    return tokens
