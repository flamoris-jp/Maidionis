#pragma once
#include "maidionis/contracts.h"
#include <map>
#include <functional>
namespace maidionis {
using Files=std::map<std::string,std::string>;
using Fault=std::function<void(const std::string&)>;
class WriterLock {
 public: explicit WriterLock(const std::filesystem::path&); ~WriterLock();
  WriterLock(const WriterLock&)=delete;WriterLock& operator=(const WriterLock&)=delete;
 private:int fd_=-1;
};
void durable_write(const std::filesystem::path&,const std::string&,Fault={});
void atomic_pointer(const std::filesystem::path&,const std::string&,Fault={});
void publish_tree(const std::filesystem::path&,const Files&,Fault={});
Json inventory(const Files&);
Files verified_snapshot(const std::filesystem::path&,const Json&,size_t total_cap,size_t member_cap);
std::string immutable_read(const std::filesystem::path&,size_t);
std::string utc_now();
}
