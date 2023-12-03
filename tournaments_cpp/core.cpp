#include <librdkafka/rdkafkacpp.h>
#include <iostream>
#include "Tournament.h"
#include "Leaderboard.h" // Предполагаемый класс для таблицы лидеров

struct PlayerData {
    std::string player;
    int64_t bet;
    int64_t win;
    std::string game;
    // Дополнительные поля по необходимости
};


class Core {
public:
    Core();
    ~Core();
    
    void start();
    void processMessage(const std::string& message){
    if (message["to"] == "jp_core" && message["type"] == "spin") {
        PlayerData playerData{
            message["data"]["bet_data"]["player"],
            message["data"]["bet_data"]["bet"],
            message["data"]["bet_data"]["win"],
            message["data"]["bet_data"]["game"]
        };
        
        int64_t tournamentId = ...; // Получение ID турнира из сообщения (если это возможно)

        // Обновление данных в активном турнире
        updateTournamentData(tournamentId, playerData){
    for (auto& t : activeTournaments) {
        if (t.id == tournamentId && !t.paused) {
            // Обновление таблицы лидеров
            // Здесь нужен код для обновления таблицы лидеров с учетом данных игрока
            // ...

            // Отправка таблицы лидеров в Kafka, если есть изменения
            sendLeaderboardToKafka(t.leaderboard);
        }
    }
}
    }
}

Leaderboard Core::getLeaderboard(int64_t tournamentId) const {
    for (const auto& t : activeTournaments) {
        if (t.id == tournamentId) {
            return t.leaderboard;
        }
    }
    return {}; // Возвращаем пустую таблицу, если турнир не найден
}    
private:
    void startTournament(const Tournament& tournament){
    // Добавление турнира в активные турниры
    activeTournaments.push_back(tournament);
    // Остальная логика запуска турнира (например, инициализация таблицы лидеров)
}
    void pauseTournament(const Tournament& tournament) {
    // Установка флага паузы для соответствующего турнира
    for (auto& t : activeTournaments) {
        if (t.id == tournament.id) {
            t.paused = true;
            break;
        }
    }
}
    void resumeTournament(const Tournament& tournament){
    // Снятие флага паузы для соответствующего турнира
    for (auto& t : activeTournaments) {
        if (t.id == tournament.id) {
            t.paused = false;
            break;
        }
    }
}
    void endTournament(const Tournament& tournament){
    // Завершение турнира и сохранение финальных результатов
    // ...

    // Удаление турнира из активных
    activeTournaments.erase(std::remove_if(activeTournaments.begin(), activeTournaments.end(),
        [&tournament](const Tournament& t) { return t.id == tournament.id; }), activeTournaments.end());
}
    void saveLeaderboard(const Leaderboard& leaderboard){
    for (const auto& t : activeTournaments) {
        // Сохранение таблицы лидеров в БД
        db.saveLeaderboard(t.id, t.leaderboard);
    }
}
    
    RdKafka::Consumer* consumer;
    std::vector<Tournament> activeTournaments;
};

