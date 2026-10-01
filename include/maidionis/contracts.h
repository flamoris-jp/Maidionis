#pragma once
#include <nlohmann/json.hpp>
#include <filesystem>
#include <functional>
#include <map>
#include <string>

namespace maidionis {
using Json=nlohmann::json;
Json parse_json(const std::string&, size_t max_bytes=65536);
std::string canonical(const Json&);
std::string sha256(const std::string&);
std::string read_file(const std::filesystem::path&, size_t max_bytes);
void validate_schema(const Json&,const Json&);
Json schema(const std::string&);
void validate_record(const std::string&,const Json&);
void safe_path(const std::string&);
class Registry {
 public:
  const Json& descriptor() const { return descriptor_; }
  const std::string& build_digest() const { return build_; }
  void payload(const std::string&,const Json&) const;
  void request(const Json&) const;
  void sample(const Json&) const;
  void result(const Json&,const Json&,const std::string&) const;
 private:
  friend class RegistryBuilder;
  Json descriptor_; std::string build_;
  std::map<std::string,std::pair<Json,Json>> schemas_;
};
class RegistryBuilder {
 public:
  explicit RegistryBuilder(std::string build);
  void add_schema(const Json&,const Json&);
  void add_operation(const Json&,const Json&,std::function<void(const Json&)>);
  Registry freeze(const Json&);
 private:
  bool frozen_=false; Registry registry_;
  std::map<std::string,std::pair<Json,std::function<void(const Json&)>>> operations_;
};
}
