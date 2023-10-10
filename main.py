from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler
import string
import numpy as np

from tensorflow import keras
import tensorflow as tf


with open('rus.txt') as f:
    text = f.read()

import string
import re
import tqdm

def preprocess_text(text):
    text=re.sub("'",'',text)
    text=''.join(char for char in text if char not in string.punctuation)
    text=re.sub("[0-9]",'',text)
    return text.lower()

maxlen_phrase_encoder = 0
maxlen_phrase_decoder = 0

def return_sentences(text,num_lines=70000):
    global maxlen_phrase_encoder, maxlen_phrase_decoder
    text_lines=text.split('\n')
    english_texts,russian_texts=[],[]
    english_words,russian_words=set(),set()
    for text_line in range(min(len(text_lines),num_lines)):
        preprocessed_text_line=preprocess_text(text_lines[text_line])
        tab_split_text=preprocessed_text_line.split('\t')
        english_text,russian_text=tab_split_text[0],'<sos> '+tab_split_text[1]+' <eos>'
        english_texts.append(english_text)
        maxlen_phrase_encoder = max(maxlen_phrase_encoder, len(english_text))
        russian_texts.append(russian_text)
        maxlen_phrase_decoder = max(maxlen_phrase_decoder, len(russian_text))
        for english_word in english_text.split():
            if english_word not in english_words:
                english_words.add(english_word)
        for russian_word in russian_text.split():
            if russian_word not in russian_words:
                russian_words.add(russian_word)
    english_words=sorted(list(english_words))
    russian_words=sorted(list(russian_words))
    return english_texts,russian_texts,english_words,russian_words

english_texts,russian_texts,english_words,russian_words = return_sentences(text)
english_words.append(' ')
russian_words.append(' ')


russian_word_to_key = {word:number for number, word in enumerate(russian_words)}
english_word_to_key = {word:number for number, word in enumerate(english_words)}

russian_key_to_word = {number:word for number, word in enumerate(russian_words)}
english_key_to_word = {number:word for number, word in enumerate(english_words)}

model = keras.models.load_model('model')
encoder_model = keras.models.load_model('encoder')
decoder_model = keras.models.load_model('decoder')



def generate_text(text):
    translation = ""
    states_value = encoder_model(text)
    target = np.zeros((1, 1))
    target[0, 0] = russian_word_to_key['<sos>']
    stop_condition = False
    while not stop_condition:
        output_token, hidden_state, cell_state = decoder_model([target] + states_value)
        char_index = np.argmax(output_token[0, -1, :])
        char = russian_key_to_word[[char_index]]
        if char == '<eos>' or len(translation) >= maxlen_phrase_decoder:
            stop_condition = True
            continue
        translation += ' ' + char
        states_value = [hidden_state, cell_state]
        target[0, 0] = russian_word_to_key[char]
    return translation



TOKEN = '5882106674:AAHBer7rOWkQWvmKbaERJKbN-rAn9wIrwBs'


def translate(update, context):
    text = update.message.text
    text = ''.join([i for i in text if i not in string.punctuation])
    text = text.lower()
    update.message.reply_text(text)


def start(update, context):
    update.message.reply_text('Hello! I am Simple Translator bot. I can translate from English to Russian. Just write me someting.')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    text_handler = MessageHandler(Filters.text, translate)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(text_handler)
    updater.start_polling()
    updater.idle()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()


