#pragma once
#include "maidionis/model.h"
#include "maidionis/storage.h"
namespace maidionis {
struct TrainingConfig {
  int64_t seed=42,epochs=6,batch_size=16,patience=100;
  double learning_rate=.02,weight_decay=.001,max_grad_norm=1;
  std::string selection_scope="train_diagnostic";
  Json json() const;
  void validate() const;
};
struct TrainingResult {ModelPtr final_model,best_model;Json state;std::string checkpoint_digest;double gradient_l1=0;};
class DatasetHandle {
 public:
  const std::vector<Json>& training_rows() const {return train_;}
  const std::vector<Json>& development_rows() const {return dev_;}
  const std::string& manifest_digest() const {return manifest_digest_;}
 private:
  DatasetHandle()=default;
  friend DatasetHandle training_data(const std::filesystem::path&,const std::string&,const NumericalComposition&);
  friend TrainingResult train(const NumericalComposition&,const DatasetHandle&,const TrainingConfig&,const std::filesystem::path&,bool,int64_t,Fault);
  std::vector<Json> train_,dev_;std::string manifest_digest_;
};
DatasetHandle training_data(const std::filesystem::path&,const std::string& trusted_digest,const NumericalComposition&);
TrainingResult train(const NumericalComposition&,const DatasetHandle&,const TrainingConfig&,const std::filesystem::path& checkpoint_root,
                     bool resume=false,int64_t epochs_this_call=0,Fault={});
}
