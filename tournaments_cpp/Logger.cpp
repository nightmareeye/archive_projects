#include "Logger.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>

void Logger::logTrace(const std::string& event, int64_t t_id, const std::string& player, const nlohmann::json& details) {
    log("trace", event, t_id, player, details);
}

void Logger::logError(const std::string& event, int64_t t_id, const std::string& player, const nlohmann::json& details) {
    log("error", event, t_id, player, details);
}

void Logger::log(const std::string& level, const std::string& event, int64_t t_id, const std::string& player, const nlohmann::json& details) {
    auto now = std::chrono::system_clock::now();
    std::time_t now_c = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;

    std::stringstream dateStream, timeStream;
    dateStream << std::put_time(std::localtime(&now_c), "%d.%m.%Y");
    timeStream << std::put_time(std::localtime(&now_c), "%T") << "." << std::setw(3) << std::setfill('0') << ms.count();

    nlohmann::json logObject;
    logObject["date"] = dateStream.str();
    logObject["time"] = timeStream.str();
    logObject["level"] = level;
    logObject["event"] = event;
    logObject["t_id"] = t_id;
    logObject["player"] = player;
    logObject["log"] = details;

    std::cout << logObject.dump() << std::endl;
}
