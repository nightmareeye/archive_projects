#include "DatabaseHandler.h"
#include "Logger.h"
#include <stdexcept>

DatabaseHandler::DatabaseHandler(const std::string& host, int port, const std::string& user, const std::string& password, const std::string& database) {
    try {
        session = new mysqlx::Session(host, port, user, password, database);
    } catch (const std::exception& e) {
        Logger::logError("Database Connection", 0, "", {{"error", e.what()}});
        throw;
    }
}

DatabaseHandler::~DatabaseHandler() {
    delete session;
}

std::vector<LeaderboardEntry> DatabaseHandler::getLeaderboard(int64_t tournament_id) {
    std::vector<LeaderboardEntry> leaderboard;

    try {
        std::string query = "SELECT player_id, hall_id, points, prize FROM leaderboard WHERE tournament_id = ?";
        auto result = session->sql(query).bind(tournament_id).execute();

        for (auto row : result.fetchAll()) {
            LeaderboardEntry entry;
            entry.player_id = row[0];
            entry.hall_id = row[1];
            entry.points = row[2];
            entry.prize = row[3];
            leaderboard.push_back(entry);
        }

    } catch (const std::exception& e) {
        Logger::logError("Get Leaderboard", tournament_id, "", {{"error", e.what()}});
        throw;
    }

    return leaderboard;
}

void DatabaseHandler::updateLeaderboard(int64_t tournament_id, const std::vector<LeaderboardEntry>& leaderboard) {
    try {
        std::string query = "INSERT INTO leaderboard (tournament_id, player_id, hall_id, points) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE points = ?";
        auto stmt = session->sql(query);

        for (const LeaderboardEntry& entry : leaderboard) {
            stmt.bind(tournament_id, entry.player_id, entry.hall_id, entry.points, entry.points).execute();
        }

    } catch (const std::exception& e) {
        Logger::logError("Update Leaderboard", tournament_id, "", {{"error", e.what()}});
        throw;
    }
}

void DatabaseHandler::setPrize(int64_t player_id, const std::string& prize) {
    try {
        std::string query = "UPDATE leaderboard SET prize = ? WHERE player_id = ?";
        session->sql(query).bind(prize, player_id).execute();

    } catch (const std::exception& e) {
        Logger::logError("Set Prize", 0, std::to_string(player_id), {{"error", e.what()}});
        throw;
    }
}
