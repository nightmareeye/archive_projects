config = {
    "APIToken": "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",  # OpenAI Токен
    #"BotToken": "6493344068:AAG3odOw-2L6P2TeQ7b-KmAwYNDA6CekWwo",  # Токен самого бота
    "BotToken": "6572146217:AAEQHLUtE9FvMnmNJnKZqMnN1sN6MNUO6Ss",  # Токен самого бота
    "DialogsDir": "dialogs/",  # Директория для хранения контекста пользователя
    "LangsDir": "langs/",  # Директория с файлами языков
    "AdminList": [657162940, 5252948559, 531025167],  # Список админов
    "UpdateTime": "01",
    "GPTModel": "gpt-3.5-turbo"
}

tones = {
    "neutral_tone": "Нейтральный",
    "optimistic_tone": "Оптимистичный",
    "friendly_tone": "Дружелюбный",
    "playful_tone": "Шутливый",
    "sympathetic_tone": "Сочувствующий",
    "assertive_tone": "Напористый",
    "formal_tone": "Формальный"
}
lens = {
    "short_paragraph": "1 короткий абзац",
    "middle_paragraph": "1000 символов",
    "big_paragraph": "2000 символов"
}
    
#-1001224122704
sub_chat_id = '@byMPProff'
channel_url = 'https://t.me/byMPProff'

preset_assistant = "You are a helpful assistant!"
preset = """I want you to present yourself as an e-commerce SEO expert who writes compelling product descriptions for users who want to make a purchase online. I'm going to provide the name of one product. Make sure that each of the unique content sections is marked with an informative and attractive subtitle describing the main focus of the content section. The main goal of these teams is to develop a new, informative and fascinating resume/product description, rich in keywords, with a volume of less than the specified length. The purpose of the product description is to promote the product among users who want to buy it. Use emotional words that are defined by a given tone and creative reasons to show why the user should buy the product I'm telling you about.Also include a bulleted list of keywords with a broad match that were used to write the product description. Write a convincing and professional-sounding title and description that will include the same wording as the text of the description of the new product.  Don't repeat my hint. Don't remind me what I asked you to do. Don't apologize. Don't refer to yourself."""