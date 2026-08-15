// Stream the frozen validation rows through the exact deployed V1 float32 model.

#include "MericaniiModelV1Weights.hpp"

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

struct Observation {
    float score;
    int final_count;
};

struct SeedResult {
    unsigned int seed;
    unsigned long long rows;
    unsigned long long comparable;
    unsigned long long concordant;
    unsigned long long discordant;
    unsigned long long tied_score;
    double concordance;
    float minimum_score;
    float maximum_score;
    std::map<int, unsigned long long> final_counts;
};

std::vector<std::string> split_tabs(const std::string& line)
{
    std::vector<std::string> fields;
    std::string::size_type start = 0;
    while (true) {
        const std::string::size_type end = line.find('\t', start);
        fields.push_back(line.substr(start, end == std::string::npos ? end : end-start));
        if (end == std::string::npos) break;
        start = end + 1;
    }
    return fields;
}

unsigned int parse_unsigned(const std::string& value, const char* label)
{
    errno = 0;
    char* end = NULL;
    const unsigned long parsed = std::strtoul(value.c_str(), &end, 10);
    if (errno != 0 || end == value.c_str() || *end != '\0' || parsed > 0xffffffffUL) {
        throw std::runtime_error(std::string("invalid ") + label);
    }
    return static_cast<unsigned int>(parsed);
}

int parse_integer(const std::string& value, const char* label)
{
    errno = 0;
    char* end = NULL;
    const long parsed = std::strtol(value.c_str(), &end, 10);
    if (errno != 0 || end == value.c_str() || *end != '\0' || parsed < -2147483647L || parsed > 2147483647L) {
        throw std::runtime_error(std::string("invalid ") + label);
    }
    return static_cast<int>(parsed);
}

float parse_float32(const std::string& value)
{
    errno = 0;
    char* end = NULL;
    const float parsed = std::strtof(value.c_str(), &end);
    if (errno != 0 || end == value.c_str() || *end != '\0' || !std::isfinite(parsed)) {
        throw std::runtime_error("invalid float32 feature");
    }
    return parsed;
}

SeedResult calculate(unsigned int seed, std::vector<Observation>& rows)
{
    std::sort(rows.begin(), rows.end(), [](const Observation& left, const Observation& right) {
        if (left.score != right.score) return left.score < right.score;
        return left.final_count < right.final_count;
    });
    SeedResult result;
    result.seed = seed;
    result.rows = rows.size();
    result.comparable = 0;
    result.concordant = 0;
    result.discordant = 0;
    result.tied_score = 0;
    result.concordance = 0.0;
    result.minimum_score = rows.empty() ? 0.0f : rows.front().score;
    result.maximum_score = rows.empty() ? 0.0f : rows.back().score;
    std::map<int, unsigned long long> prior;
    unsigned long long prior_total = 0;
    std::size_t begin = 0;
    while (begin < rows.size()) {
        std::size_t end = begin + 1;
        while (end < rows.size() && rows[end].score == rows[begin].score) ++end;
        std::map<int, unsigned long long> group;
        for (std::size_t index = begin; index < end; ++index) group[rows[index].final_count]++;
        for (std::map<int, unsigned long long>::const_iterator item = group.begin(); item != group.end(); ++item) {
            unsigned long long prior_less = 0;
            unsigned long long prior_equal = 0;
            for (std::map<int, unsigned long long>::const_iterator seen = prior.begin(); seen != prior.end(); ++seen) {
                if (seen->first < item->first) prior_less += seen->second;
                else if (seen->first == item->first) prior_equal += seen->second;
            }
            const unsigned long long prior_greater = prior_total - prior_less - prior_equal;
            result.concordant += item->second * prior_greater;
            result.discordant += item->second * prior_less;
        }
        const unsigned long long group_total = end - begin;
        unsigned long long equal_final_pairs = 0;
        for (std::map<int, unsigned long long>::const_iterator item = group.begin(); item != group.end(); ++item) {
            equal_final_pairs += item->second * (item->second - 1) / 2;
            prior[item->first] += item->second;
            result.final_counts[item->first] += item->second;
        }
        result.tied_score += group_total * (group_total - 1) / 2 - equal_final_pairs;
        prior_total += group_total;
        begin = end;
    }
    result.comparable = result.concordant + result.discordant + result.tied_score;
    if (result.comparable > 0) {
        result.concordance = (static_cast<double>(result.concordant) + 0.5 * static_cast<double>(result.tied_score)) /
                             static_cast<double>(result.comparable);
    }
    return result;
}

void print_float_hex(float value)
{
    std::cout << '"' << std::hexfloat << value << std::defaultfloat << '"';
}

}  // namespace

int main()
{
    try {
        std::string header;
        if (!std::getline(std::cin, header)) throw std::runtime_error("missing TSV header");
        const std::vector<std::string> header_fields = split_tabs(header);
        if (header_fields.size() != 94 || header_fields[0] != "schema" || header_fields[6] != "f000" ||
            header_fields[90] != "f084" || header_fields[91] != "final_count") {
            throw std::runtime_error("TSV header mismatch");
        }

        std::map<unsigned int, std::vector<Observation> > by_seed;
        std::string line;
        unsigned long long row_count = 0;
        while (std::getline(std::cin, line)) {
            const std::vector<std::string> fields = split_tabs(line);
            if (fields.size() != 94 || fields[0] != "s13-completion-row-v1") {
                throw std::runtime_error("TSV row schema mismatch at row " + std::to_string(row_count));
            }
            const unsigned int seed = parse_unsigned(fields[1], "seed");
            float features[85];
            for (unsigned int index = 0; index < 85; ++index) features[index] = parse_float32(fields[6+index]);
            const float score = MericaniiModelV1::score(features);
            if (!std::isfinite(score)) throw std::runtime_error("non-finite model score");
            by_seed[seed].push_back(Observation{score, parse_integer(fields[91], "final_count")});
            ++row_count;
        }
        if (!std::cin.eof()) throw std::runtime_error("TSV input read failure");

        std::vector<SeedResult> results;
        unsigned long long total_comparable = 0;
        unsigned long long total_concordant = 0;
        unsigned long long total_discordant = 0;
        unsigned long long total_tied_score = 0;
        for (std::map<unsigned int, std::vector<Observation> >::iterator item = by_seed.begin(); item != by_seed.end(); ++item) {
            SeedResult result = calculate(item->first, item->second);
            total_comparable += result.comparable;
            total_concordant += result.concordant;
            total_discordant += result.discordant;
            total_tied_score += result.tied_score;
            results.push_back(result);
        }
        const double micro = total_comparable == 0 ? 0.0 :
            (static_cast<double>(total_concordant) + 0.5 * static_cast<double>(total_tied_score)) /
            static_cast<double>(total_comparable);
        double macro = 0.0;
        unsigned int macro_seeds = 0;
        for (std::size_t index = 0; index < results.size(); ++index) {
            if (results[index].comparable > 0) {
                macro += results[index].concordance;
                ++macro_seeds;
            }
        }
        if (macro_seeds > 0) macro /= macro_seeds;

        std::cout << std::setprecision(17)
                  << "{\n  \"schema_version\": \"s13-validation-score/v1\",\n"
                  << "  \"row_count\": " << row_count << ",\n"
                  << "  \"seed_count\": " << results.size() << ",\n"
                  << "  \"comparable_pairs\": " << total_comparable << ",\n"
                  << "  \"concordant_pairs\": " << total_concordant << ",\n"
                  << "  \"discordant_pairs\": " << total_discordant << ",\n"
                  << "  \"tied_score_pairs\": " << total_tied_score << ",\n"
                  << "  \"micro_concordance\": " << micro << ",\n"
                  << "  \"macro_concordance\": " << macro << ",\n"
                  << "  \"seed_results\": [\n";
        for (std::size_t index = 0; index < results.size(); ++index) {
            const SeedResult& result = results[index];
            if (index > 0) std::cout << ",\n";
            std::cout << "    {\"seed\": " << result.seed
                      << ", \"rows\": " << result.rows
                      << ", \"comparable_pairs\": " << result.comparable
                      << ", \"concordant_pairs\": " << result.concordant
                      << ", \"discordant_pairs\": " << result.discordant
                      << ", \"tied_score_pairs\": " << result.tied_score
                      << ", \"concordance\": " << result.concordance
                      << ", \"minimum_score_hex\": ";
            print_float_hex(result.minimum_score);
            std::cout << ", \"maximum_score_hex\": ";
            print_float_hex(result.maximum_score);
            std::cout << ", \"final_size_distribution\": {";
            bool first = true;
            for (std::map<int, unsigned long long>::const_iterator item = result.final_counts.begin(); item != result.final_counts.end(); ++item) {
                if (!first) std::cout << ", ";
                first = false;
                std::cout << '"' << item->first << "\": " << item->second;
            }
            std::cout << "}}";
        }
        std::cout << "\n  ]\n}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "validation scorer failed: " << error.what() << '\n';
        return 1;
    }
}
