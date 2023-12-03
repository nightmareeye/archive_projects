#ifndef LOGGER_H
#define LOGGER_H

#include <string>
#include <nlohmann/json.hpp> 

class Logger {
public:
    static void logTrace(const std::string& event, int64_t t_id, const std::string& player, const nlohmann::json& details);
    static void logError(const std::string& event, int64_t t_id, const std::string& player, const nlohmann::json& details);

private:
    static void log(const std::string& level, const std::string& event, int64_t t_id, const std::string& player, const nlohmann::json& details);
};

#endif // LOGGER_H
