#include "maidionis/storage.h"
#include <iostream>
#include <unistd.h>
using namespace maidionis;
void check(bool x){if(!x)throw std::runtime_error("storage test assertion");}
int main(){auto root=std::filesystem::temp_directory_path()/("maidionis-storage-"+std::to_string(::getpid()));try {
  std::filesystem::create_directory(root);WriterLock lock(root/"writer.lock");
  bool blocked=false;try{WriterLock other(root/"writer.lock");}catch(const std::exception&){blocked=true;}check(blocked);
  Files files={{"state.json","first\n"}};files["manifest.json"]=canonical(inventory(files));publish_tree(root/"good",files);
  atomic_pointer(root/"latest.json","good\n");
  for(const auto& stage:{"write","fsync","directory_fsync","rename"}) {
    bool failed=false;try{publish_tree(root/(std::string("fault-")+stage),files,[stage](const std::string& point){if(point==stage)throw std::runtime_error("injected fault");});}catch(const std::exception&){failed=true;}
    check(failed);check(immutable_read(root/"latest.json",100)=="good\n");check(!std::filesystem::exists(root/(std::string("fault-")+stage)));
  }
  bool failed=false;try{atomic_pointer(root/"latest.json","new\n",[](const std::string& s){if(s=="pointer")throw std::runtime_error("injected pointer fault");});}catch(const std::exception&){failed=true;}check(failed);check(immutable_read(root/"latest.json",100)=="good\n");
  auto entries=inventory(Files{{"state.json","first\n"}});check(verified_snapshot(root/"good",entries,100,100).at("state.json")=="first\n");
  durable_write(root/"good"/"extra","x");failed=false;try{verified_snapshot(root/"good",entries,100,100);}catch(const std::exception&){failed=true;}check(failed);
  std::filesystem::remove_all(root);std::cout<<"durability fault checks passed\n";return 0;
}catch(const std::exception& e){std::filesystem::remove_all(root);std::cerr<<e.what()<<"\n";return 1;}}
