theory Prefix_Checker_Codegen
  imports Main Sorting_Networks.Checker_Codegen Prefix_Checker
begin

text \<open>Restate the soundness theorem here so that it is checked again in the
theory that actually performs the extraction: the exported constant is the one
this statement is about.\<close>

lemma check_prefix_proof_get_bound_spec:
  assumes \<open>check_prefix_proof_get_bound cert n prefix root_witness = Some b\<close>
  shows \<open>partial_lower_size_bound (fold apply_cmp prefix ` {v. fixed_len_bseq n v}) b\<close>
  using assms by (rule Prefix_Checker.check_prefix_proof_get_bound_spec)

export_code
    check_prefix_proof_get_bound check_proof_get_bound
    integer_of_int int_of_integer integer_of_nat nat_of_integer
    ProofCert ProofStep HuffmanWitnesses SuccessorWitnesses ProofWitness
  in Haskell module_name Verified.PrefixChecker file_prefix "prefixchecker"

end
