#ifndef DATABASEHANDLER_H
#define DATABASEHANDLER_H

#include <string>
#include <vector>
#include <mysqlx/xdevapi.h>

struct LeaderboardEntry {
    int64_t player_id;
    int64_t hall_id;
    int points;
    std::string prize;
};

class DatabaseHandler {
public:
    DatabaseHandler(const std::string& host, int port, const std::string& user, const std::string& password, const std::string& database);
    ~DatabaseHandler();

    // Методы для работы с лидерами
    std::vector<LeaderboardEntry> getLeaderboard(int64_t tournament_id);
    void updateLeaderboard(int64_t tournament_id, const std::vector<LeaderboardEntry>& leaderboard);
    void setPrize(int64_t player_id, const std::string& prize);

 
private:
    mysqlx::Session* session;
};

#endif // DATABASEHANDLER_H
