import json
from textblob import TextBlob
from loguru import logger

logger = logger.opt(colors=True)


# Из того, что я прочитал в Интернете,
# оценка полярности представляет собой плавающую величину в диапазоне [-1,0, 1,0],
# где 0 означает нейтральное отношение, +1 очень положительное отношение и -1 очень негативное отношение.
# Субъективность — это число с плавающей запятой в диапазоне [0,0, 1,0],
# где 0,0 — очень объективно, а 1,0 — очень субъективно.

def take_text(channel_title):
    with open(f'../data/{channel_title}.json', 'r', encoding='utf8') as file:
        data = json.load(file)
    return data


def save_in_json(channel_title, data):
    logger.debug("Сохранение в json формат")
    with open(f'../data/{channel_title}.json', 'w', encoding='utf8') as outfile:
        json.dump(data, outfile, ensure_ascii=False, sort_keys=True, indent=4)


class Sentiment_textblob:
    """Определение тональности с помощью textblob"""

    def __init__(self):
        pass

    def write_sentiment(self, data):
        for i in range(len(data)):
            text_message = data[i]['message']
            data[i].update(Sentiment_textblob.sentiment_analysis(text_message))
            if len(data[i]['comments']) > 0:
                for k in range(len(data[i]['comments'])):
                    comment_message = data[i]['comments'][k]['message']
                    data[i]['comments'][k].update(Sentiment_textblob.sentiment_analysis(comment_message))
        return data

    @staticmethod
    def sentiment_analysis(text):
        blob = TextBlob(text)
        sentiment_analysis = {}
        sentiment = blob.sentiment
        if sentiment[0] < -0.4:
            sentiment_analysis = {"sentiment": "Очень негативное"}
        elif -0.8 >= sentiment[0] >= -0.4:
            sentiment_analysis = {"sentiment": "Негативное"}
        elif 0.2 >= sentiment[0] > -0.8:
            sentiment_analysis = {"sentiment": "Нейтральное"}
        elif 0.6 >= sentiment[0] > 0.2:
            sentiment_analysis = {"sentiment": "Положительное"}
        elif 1 >= sentiment[0] > 0.6:
            sentiment_analysis = {"sentiment": "Очень положительное"}
        else:
            logger.error(f"Выход за предполагаемые границы [-1;1] {sentiment[0]}")
        if 1 >= sentiment[1] > 0.5:
            sentiment_analysis.update({"subjectivity": "Субъективно"})
        elif 0.5 >= sentiment[1] >= 0:
            sentiment_analysis.update({"subjectivity": "Объективно"})
        else:
            logger.error(f"Выход за предполагаемые границы [0;1] {sentiment[1]}")
        return sentiment_analysis


# class Sentiment_SpaCy:
#     """Определение тональности с помощью SpaCy"""
#
#     def __init__(self):
#         self.nlp = spacy.load('ru_core_news_sm')
#
#     def get_sentiment(self, text):
#         doc = self.nlp(text)
#         sentiment = 0
#         token_list = [token for token in doc]
#         logger.info(f"слова {token_list}")
#         filtered_tokens = [token for token in doc if not token.is_stop]
#         logger.info(f"удалены стоп слова {filtered_tokens}")
#
#         for i in range(len(filtered_tokens)):
#             logger.info(f"{filtered_tokens[i].vector}")
#
#
#     # def get_sentiment(self, text):
#     #     doc = self.nlp(text)
#     #     sentiment = 0
#     #     for token in doc:
#     #         if token.sentiment:
#     #             sentiment += token.sentiment.polarity
#     #     return sentiment
#
#     def write_sentiment(self, data):
#         for i in range(len(data)):
#             text_message = data[i]['message']
#             data[i].update(Sentiment_SpaCy.sentiment_analysis(text_message))
#             if len(data[i]['comments']) > 0:
#                 for k in range(len(data[i]['comments'])):
#                     comment_message = data[i]['comments'][k]['message']
#                     data[i]['comments'][k].update(Sentiment_SpaCy.sentiment_analysis(comment_message))
#         return data


def main():
    # input_string = "Этот фильм был просто ужасен"
    # analyzer = Sentiment_SpaCy()
    # sentiment_score = analyzer.get_sentiment(input_string)
    # print("Sentiment score:", sentiment_score)
    b = Sentiment_textblob()
    data = take_text("DevFM")
    print(b.write_sentiment(data))


if __name__ == "__main__":
    main()
