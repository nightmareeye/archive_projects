from fastapi import FastAPI
import pika

app = FastAPI()
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

def print_doc_sales():
    





@app.post("/generate_doc")
async def generate_doc(doc_type: str, org_name: str):
    # Генерация документа
    doc = generate_document(doc_type, org_name)
    
    # Отправка задачи на генерацию документа в RabbitMQ
    channel = connection.channel()
    channel.queue_declare(queue='doc_generation')
    channel.basic_publish(exchange='', routing_key=doc_type+' '+org_name, body=doc)
    return {"message": "Document generation task added to queue"}

@app.get("/doc_history")
async def doc_history():
    # Получение истории задач на генерацию документов
    history = get_doc_history()
    
    return {"history": history}

def generate_document(doc_type: str, org_name: str):
    # Генерация документа с учетом типа документа и организации
    if doc_type == "check":
        if org_name == "org1":
            return "<html><body><h1>Check for org1</h1></body></html>"
        else:
            return "<html><body><h1>Check for org2</h1></body></html>"
    elif doc_type == "bill":
        if org_name == "org1":
            return "<html><body><h1>Bill for org1</h1></body></html>"
        else:
            return "<html><body><h1>Bill for org2</h1></body></html>"
    elif doc_type == "act":
        if org_name == "org1":
            return "<html><body><h1>Act for org1</h1></body></html>"
        else:
            return "<html><body><h1>Act for org2</h1></body></html>"
    elif doc_type == "invoice":
        if org_name == "org1":
            return "<html><body><h1>Invoice for org1</h1></body></html>"
        else:
            return "<html><body><h1>Invoice for org2</h1></body></html>"
    else:
        return None

def get_doc_history():
    # Получение истории задач на генерацию документов
    history = []
    channel = connection.channel()
    channel.queue_declare(queue='doc_generation')
    
    # Получение сообщений из очереди
    for method_frame, properties, body in channel.consume('doc_generation'):
        # Добавление содержимого сообщения в историю
        history.append(body.decode())
        
        # Отправка подтверждения о получении сообщения в очереди
        channel.basic_ack(method_frame.delivery_tag)
        
        # Остановка получения сообщений после получения всех доступных
        if not method_frame.delivery_tag:
            break
    
    # Закрытие соединения и канала с RabbitMQ
    channel.cancel()
    
    return history