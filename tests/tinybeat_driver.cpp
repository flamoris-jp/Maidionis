#include "tinybeat_composition.h"
#include "maidionis/training.h"
#include <iostream>
using namespace maidionis;
int main(int argc,char** argv){try {
  if(argc!=8||std::string(argv[1])!="train")throw std::invalid_argument("usage: tinybeat_driver train dataset digest checkpoint-root output epochs-this-call resume");
  auto c=tinybeat_composition(argv[2]);auto data=training_data(argv[2],argv[3],c.registry);TrainingConfig config;
  auto initial=make_seeded_model(c.model_config,config.seed);auto initial_bytes=save_model_bytes(initial);
  auto result=train(c,data,config,argv[4],std::string(argv[7])=="1",std::stoll(argv[6]));
  Files files={{"final.pt",save_model_bytes(result.final_model)},{"best.pt",save_model_bytes(result.best_model)},
    {"state.json",canonical(result.state)},{"model.config.json",canonical(c.model_config.json())},{"training.json",canonical(Json{{"config",config.json()},{"state",result.state},
    {"checkpoint_digest",result.checkpoint_digest},{"dataset_digest",data.manifest_digest},{"environment_digest",sha256(numerical_environment())}})}};
  Json summary={{"state",result.state},{"gradient_l1",result.gradient_l1},{"parameters_changed",initial_bytes!=files["final.pt"]},{"environment_digest",sha256(numerical_environment())},
    {"final_sha256",sha256(files["final.pt"])},{"best_sha256",sha256(files["best.pt"])}};
  result.final_model->eval();result.best_model->eval();Json final_logits=Json::array(),best_logits=Json::array();
  torch::NoGradGuard no;
  for(const auto& row:data.train){auto batch=c.encode({row});auto a=result.final_model->forward(batch).flatten(),b=result.best_model->forward(batch).flatten();
    final_logits.push_back({a[0].item<float>(),a[1].item<float>()});best_logits.push_back({b[0].item<float>(),b[1].item<float>()});}
  summary["final_logits"]=final_logits;summary["best_logits"]=best_logits;files["summary.json"]=canonical(summary);publish_tree(argv[5],files);std::cout<<canonical(summary);return 0;
}catch(const std::exception& e){std::cerr<<"native operation rejected: "<<e.what()<<"\n";return 1;}}
