#include "maidionis/contracts.h"
#include <iostream>
int main(int argc,char** argv) {
  try {
    if(argc!=3)throw std::invalid_argument("usage: maidionis_contract_check schema-name file");
    auto value=maidionis::parse_json(maidionis::read_file(argv[2],4*1024*1024),4*1024*1024);
    maidionis::validate_record(argv[1],value);std::cout<<maidionis::canonical(value);return 0;
  }catch(const std::exception&){std::cerr<<"contract rejected\n";return 1;}
}
