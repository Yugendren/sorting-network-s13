theory Prefix_Checker
  imports Main Sorting_Networks.Sorting_Network Sorting_Networks.Checker
begin

text \<open>
  A verified checker for PREFIX-ROOTED certificates (the v2p container,
  docs/certificate-format-v2.md sec.9).

  Nothing in Checker.thy is modified. Every proof rule, every step, and the
  whole step DAG are checked by @{const check_proof}, unchanged. What this
  theory adds is a different way of DISCHARGING THE ROOT.

  Checker.thy's top-level @{thm check_proof_get_bound_spec} takes the last
  step's set and widens it to the full n-cube via @{thm bound_mono_subset},
  concluding @{const lower_size_bound}. That widening is the ONLY place the
  full cube is baked in: @{const step_checked} -- and therefore everything
  @{const check_proof} establishes -- is already a statement about an
  arbitrary set, namely @{const pls_bound} of that step's own vectors.

  So a prefix root needs no new proof rule. We

    * compute \<open>X_P\<close>, the image of the full n-cube under the comparator
      sequence \<open>P\<close>, inside the verified code (so a caller cannot lie about
      it -- this is check P3 of sec.9.4, discharged by construction rather
      than by comparing against a stored copy);
    * discharge the root with @{const get_bound}, Checker.thy's own witness
      rule, which is exactly check P5 of sec.9.4; and
    * conclude a bound on \<open>X_P\<close> rather than on the cube.

  The headline result is \<open>prefix_network_size_bound\<close> at the end of this
  theory: any comparator network that begins with \<open>P\<close> and sorts every
  n-channel input has at least \<open>length P + b\<close> comparators.

  COMPARATOR CONVENTION. @{const apply_cmp} sends the FIRST component of the
  pair to the minimum and the second to the maximum. The v2p prefix section
  stores pairs in the engine's opposite convention (first component receives
  the maximum, sec.9.3). The decoder must swap; this theory proves a
  statement about whatever list it is handed, so getting the swap wrong
  yields a true theorem about the wrong prefix. That obligation lives in the
  unverified glue, exactly like the rest of decoding.
\<close>

section \<open>The full cube as a vect trie\<close>

fun all_vects :: \<open>nat \<Rightarrow> bool list list\<close> where
  \<open>all_vects 0 = [[]]\<close> |
  \<open>all_vects (Suc n) = map ((#) False) (all_vects n) @ map ((#) True) (all_vects n)\<close>

lemma set_all_vects: \<open>set (all_vects n) = {xs. length xs = n}\<close>
proof (induction n)
  case 0
  show ?case by simp
next
  case (Suc n)
  have \<open>{xs. length xs = Suc n} =
      ((#) False) ` {xs. length xs = n} \<union> ((#) True) ` {xs. length xs = n}\<close>
    by (rule set_eqI; auto simp add: length_Suc_conv; metis (full_types) image_eqI mem_Collect_eq)
  thus ?case
    using Suc by simp
qed

definition all_vects_vt :: \<open>nat \<Rightarrow> vect_trie\<close> where
  \<open>all_vects_vt n = vt_list (all_vects n)\<close>

lemma set_vt_all_vects_vt: \<open>set_vt (all_vects_vt n) = {xs. length xs = n}\<close>
  unfolding all_vects_vt_def set_vt_list
  by (rule set_all_vects)

lemma list_to_vect_all_vects_vt:
  \<open>list_to_vect ` set_vt (all_vects_vt n) = {v. fixed_len_bseq n v}\<close>
proof (rule set_eqI; rule iffI)
  fix v assume \<open>v \<in> list_to_vect ` set_vt (all_vects_vt n)\<close>
  thus \<open>v \<in> {v. fixed_len_bseq n v}\<close>
    using fixed_len_bseq_list_to_vect set_vt_all_vects_vt by auto
next
  fix v assume asm: \<open>v \<in> {v. fixed_len_bseq n v}\<close>
  define xs where \<open>xs = map v [0..<n]\<close>
  have len: \<open>length xs = n\<close>
    by (simp add: xs_def)
  have \<open>list_to_vect xs = v\<close>
  proof (rule ext)
    fix i
    show \<open>list_to_vect xs i = v i\<close>
      using asm len
      unfolding list_to_vect_as_nth fixed_len_bseq_def xs_def
      by (cases \<open>i < n\<close>; simp)
  qed
  thus \<open>v \<in> list_to_vect ` set_vt (all_vects_vt n)\<close>
    using len set_vt_all_vects_vt by blast
qed

section \<open>Applying a comparator sequence to a vect trie\<close>

text \<open>This is the same idiom @{const check_successors} already uses to build a
successor set, lifted to a list of comparators and with no redundancy test.\<close>

definition apply_cmp_vt :: \<open>cmp \<Rightarrow> vect_trie \<Rightarrow> vect_trie\<close> where
  \<open>apply_cmp_vt c A = vt_list (map (apply_cmp_list c) (list_vt A))\<close>

definition apply_cmps_vt :: \<open>cmp list \<Rightarrow> vect_trie \<Rightarrow> vect_trie\<close> where
  \<open>apply_cmps_vt cs A = fold apply_cmp_vt cs A\<close>

lemma apply_cmps_vt_Nil[simp]: \<open>apply_cmps_vt [] A = A\<close>
  by (simp add: apply_cmps_vt_def)

lemma apply_cmps_vt_Cons: \<open>apply_cmps_vt (c # cs) A = apply_cmps_vt cs (apply_cmp_vt c A)\<close>
  by (simp add: apply_cmps_vt_def)

lemma set_vt_apply_cmp_vt: \<open>set_vt (apply_cmp_vt c A) = apply_cmp_list c ` set_vt A\<close>
  by (simp add: apply_cmp_vt_def set_vt_list set_list_vt)

lemma apply_cmp_vt_width:
  assumes \<open>set_vt A \<subseteq> {xs. length xs = n}\<close>
  shows \<open>set_vt (apply_cmp_vt c A) \<subseteq> {xs. length xs = n}\<close>
  using assms
  by (auto simp add: set_vt_apply_cmp_vt length_apply_cmp_list)

lemma apply_cmps_vt_width:
  assumes \<open>set_vt A \<subseteq> {xs. length xs = n}\<close>
  shows \<open>set_vt (apply_cmps_vt cs A) \<subseteq> {xs. length xs = n}\<close>
  using assms
proof (induction cs arbitrary: A)
  case Nil
  thus ?case by simp
next
  case (Cons c cs)
  show ?case
    unfolding apply_cmps_vt_Cons
    by (rule Cons.IH; rule apply_cmp_vt_width; rule Cons.prems)
qed

lemma list_to_vect_apply_cmp_vt:
  assumes \<open>set_vt A \<subseteq> {xs. length xs = n}\<close> \<open>fst c < n\<close> \<open>snd c < n\<close>
  shows \<open>list_to_vect ` set_vt (apply_cmp_vt c A) = apply_cmp c ` list_to_vect ` set_vt A\<close>
  using apply_cmp_as_apply_cmp_list'[OF assms]
  unfolding apply_cmp_vt_def
  by simp

lemma list_to_vect_apply_cmps_vt:
  assumes \<open>set_vt A \<subseteq> {xs. length xs = n}\<close>
    \<open>list_all (\<lambda>c. fst c < n \<and> snd c < n) cs\<close>
  shows \<open>list_to_vect ` set_vt (apply_cmps_vt cs A) = fold apply_cmp cs ` (list_to_vect ` set_vt A)\<close>
  using assms
proof (induction cs arbitrary: A)
  case Nil
  thus ?case by simp
next
  case (Cons c cs)
  have c_bounds: \<open>fst c < n\<close> \<open>snd c < n\<close>
    using Cons.prems(2) by auto
  have width': \<open>set_vt (apply_cmp_vt c A) \<subseteq> {xs. length xs = n}\<close>
    by (rule apply_cmp_vt_width; rule Cons.prems(1))
  have \<open>list_to_vect ` set_vt (apply_cmps_vt (c # cs) A) =
      fold apply_cmp cs ` (list_to_vect ` set_vt (apply_cmp_vt c A))\<close>
    unfolding apply_cmps_vt_Cons
    by (rule Cons.IH[OF width']; insert Cons.prems(2); simp)
  also have \<open>\<dots> = fold apply_cmp cs ` (apply_cmp c ` list_to_vect ` set_vt A)\<close>
    using list_to_vect_apply_cmp_vt[OF Cons.prems(1) c_bounds] by simp
  also have \<open>\<dots> = fold apply_cmp (c # cs) ` (list_to_vect ` set_vt A)\<close>
    by (simp add: image_image)
  finally show ?case.
qed

section \<open>The prefix-rooted checker\<close>

text \<open>@{const check_proof} is Checker.thy's, unchanged. The root is discharged
by @{const get_bound}, Checker.thy's, unchanged. \<open>prefix\<close> is in
@{const apply_cmp} convention (first component receives the minimum).\<close>

definition check_prefix_proof_get_bound ::
  \<open>proof_cert \<Rightarrow> nat \<Rightarrow> cmp list \<Rightarrow> proof_witness option \<Rightarrow> nat option\<close> where
  \<open>check_prefix_proof_get_bound cert n prefix root_witness = (
    if check_proof cert \<and> list_all (\<lambda>c. fst c < n \<and> snd c < n) prefix
    then
      get_bound (cert_step cert) (cert_length cert) root_witness n
        (apply_cmps_vt prefix (all_vects_vt n))
    else None
  )\<close>

theorem check_prefix_proof_get_bound_spec:
  assumes \<open>check_prefix_proof_get_bound cert n prefix root_witness = Some b\<close>
  shows \<open>partial_lower_size_bound (fold apply_cmp prefix ` {v. fixed_len_bseq n v}) b\<close>
proof -
  define X where \<open>X = apply_cmps_vt prefix (all_vects_vt n)\<close>

  have checked: \<open>check_proof cert\<close>
    and prefix_bounds: \<open>list_all (\<lambda>c. fst c < n \<and> snd c < n) prefix\<close>
    using assms unfolding check_prefix_proof_get_bound_def
    by (meson option.distinct(1))+

  have root: \<open>get_bound (cert_step cert) (cert_length cert) root_witness n X = Some b\<close>
    using assms checked prefix_bounds
    unfolding check_prefix_proof_get_bound_def X_def
    by simp

  have cube_width: \<open>set_vt (all_vects_vt n) \<subseteq> {xs. length xs = n}\<close>
    by (simp add: set_vt_all_vects_vt)

  have X_width: \<open>set_vt X \<subseteq> {xs. length xs = n}\<close>
    unfolding X_def
    by (rule apply_cmps_vt_width[OF cube_width])

  have steps: \<open>\<And>step. 0 \<le> step \<and> step < cert_length cert \<Longrightarrow> step_checked (cert_step cert step)\<close>
    using checked check_proof_spec by blast

  have bound: \<open>pls_bound (list_to_vect ` set_vt X) b\<close>
    by (rule get_bound_bound[OF steps X_width root])

  have image: \<open>list_to_vect ` set_vt X = fold apply_cmp prefix ` {v. fixed_len_bseq n v}\<close>
    unfolding X_def
    using list_to_vect_apply_cmps_vt[OF cube_width prefix_bounds] list_to_vect_all_vects_vt
    by simp

  have widths: \<open>\<And>v. v \<in> list_to_vect ` set_vt X \<Longrightarrow> fixed_len_bseq n v\<close>
    using X_width fixed_len_bseq_list_to_vect by blast

  show ?thesis
    using pls_bound_implies_lower_size_bound[OF widths bound] image
    by simp
qed

text \<open>The statement of sec.9.1: completing \<open>P\<close> into a sorting network costs at
least \<open>b\<close> further comparators, so any n-channel sorting network beginning with
\<open>P\<close> has at least \<open>length P + b\<close> comparators.\<close>

corollary prefix_network_size_bound:
  assumes \<open>check_prefix_proof_get_bound cert n prefix root_witness = Some b\<close>
    and \<open>\<And>x. fixed_len_bseq n x \<Longrightarrow> mono (fold apply_cmp (prefix @ cn) x)\<close>
  shows \<open>length (prefix @ cn) \<ge> length prefix + b\<close>
proof -
  have sorts: \<open>\<forall>y \<in> fold apply_cmp prefix ` {v. fixed_len_bseq n v}. mono (fold apply_cmp cn y)\<close>
    using assms(2) by auto
  have \<open>length cn \<ge> b\<close>
    using check_prefix_proof_get_bound_spec[OF assms(1)] sorts
    unfolding partial_lower_size_bound_def
    by blast
  thus ?thesis
    by simp
qed

end
