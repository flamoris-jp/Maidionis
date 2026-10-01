#include "maidionis/storage.h"
#include <fcntl.h>
#include <unistd.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <linux/fs.h>
#include <cerrno>
#include <set>
#include <ctime>

namespace maidionis {
std::string utc_now(){std::time_t now=std::time(nullptr);std::tm value;::gmtime_r(&now,&value);char text[32];std::strftime(text,sizeof text,"%Y-%m-%dT%H:%M:%SZ",&value);return text;}
namespace {
void fail(bool bad,const char* message){if(bad)throw std::runtime_error(message);}
void point(Fault f,const char* name){if(f)f(name);}
void sync_dir(const std::filesystem::path& p){int fd=::open(p.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW);fail(fd<0,"directory open failure");int r=::fsync(fd);::close(fd);fail(r!=0,"directory fsync failure");}
void no_links(const std::filesystem::path& p){auto full=std::filesystem::absolute(p);std::filesystem::path cur;for(const auto& part:full){cur/=part;fail(std::filesystem::is_symlink(cur),"symlink path");}}
std::string unique(){return ".stage-"+std::to_string(::getpid())+"-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());}
}
WriterLock::WriterLock(const std::filesystem::path& p){std::filesystem::create_directories(p.parent_path());no_links(p);fd_=::open(p.c_str(),O_CREAT|O_RDWR|O_NOFOLLOW,0600);if(fd_<0||::flock(fd_,LOCK_EX|LOCK_NB)!=0){if(fd_>=0)::close(fd_);fd_=-1;throw std::runtime_error("writer lock unavailable");}}
WriterLock::~WriterLock(){if(fd_>=0)::close(fd_);}
std::string immutable_read(const std::filesystem::path& p,size_t cap) {
  no_links(p);int fd=::open(p.c_str(),O_RDONLY|O_NOFOLLOW);fail(fd<0,"file open failure");
  try {struct stat before,after;fail(::fstat(fd,&before)!=0||!S_ISREG(before.st_mode)||before.st_size<0||uint64_t(before.st_size)>cap,"file bound");
    std::string raw;raw.reserve(before.st_size);char buffer[8192];ssize_t n;
    while((n=::read(fd,buffer,sizeof buffer))>0){fail(size_t(n)>cap-raw.size(),"file bound");raw.append(buffer,n);}fail(n<0,"file read failure");
    fail(::fstat(fd,&after)!=0||before.st_size!=after.st_size||before.st_mtim.tv_sec!=after.st_mtim.tv_sec||before.st_mtim.tv_nsec!=after.st_mtim.tv_nsec||raw.size()!=size_t(before.st_size),"mutable source");
    ::close(fd);return raw;
  }catch(...){::close(fd);throw;}
}
void durable_write(const std::filesystem::path& p,const std::string& bytes,Fault f) {
  no_links(p);point(f,"write");int fd=::open(p.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);fail(fd<0,"write conflict");
  try {size_t done=0;while(done<bytes.size()){auto n=::write(fd,bytes.data()+done,bytes.size()-done);fail(n<=0,"write failure");done+=n;}point(f,"fsync");fail(::fsync(fd)!=0,"file fsync failure");fail(::close(fd)!=0,"file close failure");fd=-1;}
  catch(...){if(fd>=0)::close(fd);throw;}
}
void atomic_pointer(const std::filesystem::path& p,const std::string& bytes,Fault f) {
  no_links(p);auto tmp=p.parent_path()/unique();durable_write(tmp,bytes,f);
  try{point(f,"pointer");fail(::rename(tmp.c_str(),p.c_str())!=0,"pointer rename failure");sync_dir(p.parent_path());}
  catch(...){std::filesystem::remove(tmp);throw;}
}
void publish_tree(const std::filesystem::path& final,const Files& files,Fault f) {
  no_links(final);std::filesystem::create_directories(final.parent_path());auto stage=final.parent_path()/unique();std::filesystem::create_directory(stage);
  try{
    for(const auto& [path,bytes]:files){safe_path(path);auto p=stage/path;std::filesystem::create_directories(p.parent_path());durable_write(p,bytes,f);}
    for(const auto& [path,bytes]:files)fail(immutable_read(stage/path,bytes.size())!=bytes,"staging verification");
    for(auto it=std::filesystem::recursive_directory_iterator(stage);it!=std::filesystem::recursive_directory_iterator();++it)if(it->is_directory())sync_dir(it->path());
    point(f,"directory_fsync");sync_dir(stage);point(f,"rename");
    fail(::syscall(SYS_renameat2,AT_FDCWD,stage.c_str(),AT_FDCWD,final.c_str(),RENAME_NOREPLACE)!=0,"publication conflict");sync_dir(final.parent_path());
  }catch(...){std::filesystem::remove_all(stage);throw;}
}
Json inventory(const Files& files){Json out=Json::array();for(const auto& [p,b]:files){safe_path(p);out.push_back({{"path",p},{"sha256",sha256(b)},{"bytes",b.size()}});}return out;}
Files verified_snapshot(const std::filesystem::path& root,const Json& entries,size_t total_cap,size_t member_cap) {
  no_links(root);fail(!entries.is_array()||entries.size()>1000,"inventory limit");Files files;size_t total=0;
  for(const auto& entry:entries){validate_schema(entry,Json{{"type","object"},{"required",{"path","sha256","bytes"}},
      {"additionalProperties",false},{"properties",{{"path",{{"type","string"}}},{"sha256",{{"type","string"},{"pattern","^[a-f0-9]{64}$"}}},{"bytes",{{"type","integer"},{"minimum",0}}}}}});
    const auto path=entry["path"].get<std::string>();safe_path(path);const auto size=entry["bytes"].get<uint64_t>();
    fail(size>member_cap||size>total_cap-total||files.contains(path),"inventory bound or duplicate");
    auto raw=immutable_read(root/path,size);fail(raw.size()!=size||sha256(raw)!=entry["sha256"].get<std::string>(),"inventory digest");total+=size;files.emplace(path,std::move(raw));
  }
  std::set<std::string> seen;
  for(const auto& e:std::filesystem::recursive_directory_iterator(root)){fail(e.is_symlink(),"symlink member");if(e.is_directory())continue;fail(!e.is_regular_file(),"nonregular member");auto p=std::filesystem::relative(e.path(),root).generic_string();if(p!="manifest.json")seen.insert(p);}
  std::set<std::string> expected;for(const auto& [p,b]:files)expected.insert(p);fail(expected!=seen,"extra or missing inventory file");return files;
}
}
