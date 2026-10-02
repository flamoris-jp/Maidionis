#pragma once
#include "maidionis/training.h"
#include <functional>
namespace maidionis {
Json expected_tensor_inventory(const ModelConfig&);
std::string evaluated_component_digest(const Files&);
struct ValidationContext {
  std::string expected_digest;
  bool trusted_provenance=false;
  std::string purpose="offline_evaluation";
  size_t snapshot_budget=0;
};
class ValidatedBundle {
 public:
  const Json& manifest() const {return manifest_;}
  const Json& registration() const {return registration_;}
  const std::string& digest() const {return digest_;}
  size_t parameter_bytes() const {return parameter_bytes_;}
 private:
  friend ValidatedBundle validate_bundle(const std::filesystem::path&,const NumericalComposition&,const ValidationContext&);
  friend struct BundleAccess;
  Json manifest_,registration_;Files files_;std::string digest_;size_t parameter_bytes_=0;
};
ValidatedBundle validate_bundle(const std::filesystem::path&,const NumericalComposition&,const ValidationContext&);
struct OfflineContext {
  std::string operation_id,profile;
  size_t process_address_space_budget=0,persistent_budget=0,peak_transient_budget=0;
  std::function<bool()> current;
  Fault fault;
};
// The caller owns the isolated process. A holder never transfers to Runtime here.
struct LoadedBundle {ModelPtr model;Json receipt;};
LoadedBundle materialize_model(const ValidatedBundle&,const NumericalComposition&,const OfflineContext&);
}
