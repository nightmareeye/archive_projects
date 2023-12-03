#ifndef TOURNAMENT_H
#define TOURNAMENT_H

#include <string>
#include <vector>
#include <chrono>

enum class ScoreAlgorithm {
    GROW_BETTER,
    BREAK_THE_BANK,
    SPIN_TO_WIN
};

enum class PrizeType {
    FIXED,
    DYNAMIC
};

enum class PrizeReward {
    CREDITS,
    COUPONS
};

class Tournament {
public:
    int64_t hallId; // ИД зала
    std::string name; // Название турнира
    ScoreAlgorithm scoreAlgorithm; // Алгоритм начисления очков
    bool requiresRegistration; // Требуется ли регистрация
    int64_t repeatInterval; // Повторяемость в минутах (0 - нет повторяемости)
    std::chrono::system_clock::time_point startTime; // Время начала
    int durationHours; // Продолжительность в часах
    int offsetMinutes; // Смещение по времени при создании нового
    int minRank; // Минимальный ранг участника
    std::vector<std::string> games; // Набор игр участвующих в турнире
    PrizeType prizeType; // Тип призового фонда
    PrizeReward prizeReward; // Тип приза
    
    // Конструктор и другие методы по необходимости
};

#endif // TOURNAMENT_H
