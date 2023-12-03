#include <librdkafka/rdkafkacpp.h>
#include <iostream>
#include <vector>
#include "DatabaseHandler.h" // Предполагаемый класс для работы с БД
#include "Tournament.h" // Предполагаемый класс для хранения данных о турнире

class Dispatcher {
public:
    Dispatcher(){
    // Настройки Kafka
    std::string brokers = "localhost";
    std::string errstr;
    RdKafka::Conf* conf = RdKafka::Conf::create(RdKafka::Conf::CONF_GLOBAL);

    conf->set("metadata.broker.list", brokers, errstr);

    consumer = RdKafka::Consumer::create(conf, errstr);
    if (!consumer) {
        std::cerr << "Failed to create consumer: " << errstr << std::endl;
        exit(1);
    }

    RdKafka::TopicConf* topic_conf = RdKafka::TopicConf::create();
    RdKafka::Topic* topic = RdKafka::Topic::create(consumer, "tournament_topic", topic_conf, errstr);

    consumer->start(topic, 0, RdKafka::Topic::OFFSET_BEGINNING);
}
    ~Dispatcher(){
    if (consumer) {
        consumer->close();
        delete consumer;
    }
    RdKafka::wait_destroyed(5000);
}
    
    void start(){
    while (true) {
        RdKafka::Message* msg = consumer->consume(1000);
        if (msg->err() == RdKafka::ERR_NO_ERROR) {
            processMessage(static_cast<const char*>(msg->payload()));
        }
        delete msg;
    }
}
    void processMessage(const std::string& message){
   
}
    
private:
void Dispatcher::createTournament(const Tournament& tournament) {
    // Добавление турнира в БД
    db.insertTournament(tournament);
    // Добавление в список активных турниров
    tournaments.push_back(tournament);
}

void Dispatcher::editTournament(const Tournament& tournament) {
    // Обновление турнира в БД
    db.updateTournament(tournament);
    // Обновление турнира в списке
    for (auto& t : tournaments) {
        if (t.id == tournament.id) {
            t = tournament;
            break;
        }
    }
}

void Dispatcher::startTournament(const Tournament& tournament) {
    // Нахождение подходящего ядра
    Core* core = findSuitableCore();
    // Уведомление ядра о запуске турнира
    core->startTournament(tournament);
    // Если турнир регулярный, создание копии
    if (tournament.isRegular) {
        Tournament newTournament = tournament;
        newTournament.startTime += tournament.interval;
        createTournament(newTournament);
    }
}

void Dispatcher::watchdog() {
    for (const auto& core : cores) {
        // Опрос ядра на предмет корректности работы турниров
        if (!core->isRunningProperly()) {
            // Логика восстановления или перезапуска турниров
        }
    }
}
}

int main() {
    // Инициализация Kafka, базы данных и других ресурсов

    // Создание экземпляров ядра и диспетчера
    Core core;
    Dispatcher dispatcher;

    // Запуск основного цикла обработки сообщений и управления турнирами
    while (true) {
        // Чтение сообщений из Kafka
        auto messages = kafkaConsumer.poll();

        // Обработка сообщений в ядре и диспетчере
        for (const auto& message : messages) {
            if (message["to"] == "jp_core") {
                core.processMessage(message);
            } else if (message["to"] == "dispatcher") {
                dispatcher.processMessage(message);
            }
        }

        // Мониторинг активных турниров и сохранение таблиц лидеров
        core.saveLeaderboards();
        dispatcher.monitorTournaments();

        // Задержка перед следующей итерацией (по необходимости)
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    return 0;
}

