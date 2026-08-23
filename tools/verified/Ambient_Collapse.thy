(*  Title:      Ambient_Collapse.thy
    Author:     S(13) mechanization campaign, 2026-08-23

    A machine-checked formalisation of the abstract "graded ambient search"
    class of docs/level-law-general.md 1.1-1.3, and of

      Part I   (Ambient Collapse),
      Part II  (Chain Collapse),
      the Corollary of 1.5 (polynomial census cutoff),

    together with two concrete interpretations that discharge every locale
    assumption, so the hypotheses are demonstrably satisfiable and the
    theorems are non-vacuous.

    This theory is SELF-CONTAINED (imports Main only).  It touches none of the
    frozen theories: Checker.thy, Huffman.thy, Sorting_Network.thy,
    Sorting_Network_Bound.thy, Checker_Codegen.thy, Prefix_Checker.thy.

    NOTHING here is a formalisation of the sortnetopt engine.  See
    docs/mechanized-collapse.md for the exact statement of what is and is not
    mechanized.

    No sorry.  No oops.
*)

theory Ambient_Collapse
  imports Main
begin

section \<open>Graded walks\<close>

text \<open>
  A walk in a relation \<open>E\<close> whose edges are weighted by \<open>G\<close>, carrying the total
  weight.  \<open>pathg E G s t g\<close>: there is a walk from \<open>s\<close> to \<open>t\<close> of total grade
  exactly \<open>g\<close>.  Since the census is defined by an inequality on the graded
  distance, and the graded distance is the least \<open>g\<close> for which a walk exists,
  "\<open>d(s,t) \<le> B\<close>" is the same as "\<open>\<exists>g \<le> B. pathg E G s t g\<close>", which is how the
  census is defined below.  This avoids any partiality in the distance.
\<close>

inductive pathg :: "('s \<Rightarrow> 's \<Rightarrow> bool) \<Rightarrow> ('s \<Rightarrow> 's \<Rightarrow> nat) \<Rightarrow> 's \<Rightarrow> 's \<Rightarrow> nat \<Rightarrow> bool"
  for E :: "'s \<Rightarrow> 's \<Rightarrow> bool" and G :: "'s \<Rightarrow> 's \<Rightarrow> nat"
  where
    pg_refl: "pathg E G s s 0"
  | pg_snoc: "pathg E G s t g \<Longrightarrow> E t u \<Longrightarrow> pathg E G s u (g + G t u)"

text \<open>A walk all of whose states satisfy a predicate \<open>B\<close> (used for the
  width-confinement of hypothesis H4).\<close>

inductive pathgB ::
  "('s \<Rightarrow> 's \<Rightarrow> bool) \<Rightarrow> ('s \<Rightarrow> 's \<Rightarrow> nat) \<Rightarrow> ('s \<Rightarrow> bool) \<Rightarrow> 's \<Rightarrow> 's \<Rightarrow> nat \<Rightarrow> bool"
  for E :: "'s \<Rightarrow> 's \<Rightarrow> bool" and G :: "'s \<Rightarrow> 's \<Rightarrow> nat" and B :: "'s \<Rightarrow> bool"
  where
    pb_refl: "B s \<Longrightarrow> pathgB E G B s s 0"
  | pb_snoc: "pathgB E G B s t g \<Longrightarrow> E t u \<Longrightarrow> B u \<Longrightarrow> pathgB E G B s u (g + G t u)"

lemma pathg_trans:
  assumes "pathg E G a b g1" and "pathg E G b c g2"
  shows "pathg E G a c (g1 + g2)"
  using assms(2) assms(1)
proof (induction rule: pathg.induct)
  case (pg_refl s)
  then show ?case by simp
next
  case (pg_snoc s t g u)
  from pg_snoc.IH pg_snoc.prems have "pathg E G a t (g1 + g)" by simp
  from pathg.pg_snoc[OF this pg_snoc.hyps(2)]
  have "pathg E G a u ((g1 + g) + G t u)" .
  then show ?case by (simp add: add.assoc)
qed

lemma pathgB_ends: "pathgB E G B s t g \<Longrightarrow> B s \<and> B t"
  by (induction rule: pathgB.induct) auto

lemma pathgB_pathg: "pathgB E G B s t g \<Longrightarrow> pathg E G s t g"
  by (induction rule: pathgB.induct) (auto intro: pathg.intros)

lemma pathgB_weaken:
  assumes "pathgB E G B s t g" and "\<And>x. B x \<Longrightarrow> B' x"
  shows "pathgB E G B' s t g"
  using assms(1)
proof (induction rule: pathgB.induct)
  case (pb_refl s)
  then show ?case using assms(2) by (simp add: pathgB.pb_refl)
next
  case (pb_snoc s t g u)
  from assms(2)[OF pb_snoc.hyps(3)] have "B' u" .
  from pathgB.pb_snoc[OF pb_snoc.IH pb_snoc.hyps(2) this] show ?case .
qed

lemma pathgB_trans:
  assumes "pathgB E G B a b g1" and "pathgB E G B b c g2"
  shows "pathgB E G B a c (g1 + g2)"
  using assms(2) assms(1)
proof (induction rule: pathgB.induct)
  case (pb_refl s)
  then show ?case by simp
next
  case (pb_snoc s t g u)
  from pb_snoc.IH pb_snoc.prems have "pathgB E G B a t (g1 + g)" by simp
  from pathgB.pb_snoc[OF this pb_snoc.hyps(2) pb_snoc.hyps(3)]
  have "pathgB E G B a u ((g1 + g) + G t u)" .
  then show ?case by (simp add: add.assoc)
qed


section \<open>The abstract class: graded ambient search\<close>

text \<open>
  docs/level-law-general.md 1.1.  A graded ambient search is
  \<open>(S, w, \<rightarrow>, \<gamma>, {root_n})\<close>.

  Two of the six hypotheses are discharged STRUCTURALLY by the signature and
  cannot be violated by any interpretation:

  \<^item> H0 (ambient-free naming).  The states inhabit ONE type \<^typ>\<open>'s\<close> that does
    not mention the ambient.  A state therefore has one and the same name at
    every ambient, by construction.  Equivalently: canonicalisation is already
    applied, and it quotients away the unused dimensions.

  \<^item> H2 (ambient-free grading).  \<open>grade\<close> has type \<^typ>\<open>'s \<Rightarrow> 's \<Rightarrow> nat\<close>: it takes
    no ambient argument.

  The remaining four are locale assumptions.
\<close>

locale graded_ambient_search =
  fixes width :: "'s \<Rightarrow> nat"
    and edge  :: "nat \<Rightarrow> 's \<Rightarrow> 's \<Rightarrow> bool"
    and grade :: "'s \<Rightarrow> 's \<Rightarrow> nat"
    and root  :: "nat \<Rightarrow> 's"
    and C     :: "nat \<Rightarrow> nat"
  assumes H1: "\<lbrakk> width s \<le> m; m \<le> n \<rbrakk> \<Longrightarrow>
                 {t. edge n s t \<and> width t \<le> m} = {t. edge m s t}"
      \<comment> \<open>H1, ambient freedom, stratified: raising the ambient may only add
          transitions to WIDER states.\<close>
    and H3_width: "width (root m) \<le> m"
    and H3_mono:  "m \<le> n \<Longrightarrow> C m \<le> C n"
    and H3_tower: "m \<le> n \<Longrightarrow> pathg (edge n) grade (root n) (root m) (C n - C m)"
      \<comment> \<open>H3, root tower, in the uniform form that covers the non-degenerate
          case (\<open>root n \<rightarrow> root (n-1)\<close> with grade \<open>\<delta> n\<close>, \<open>C n = sum of \<delta>\<close>) and the
          degenerate case (\<open>root n = root 0\<close>, \<open>C = 0\<close>) at once.\<close>
    and H4: "\<lbrakk> m \<le> n; width s \<le> m; pathg (edge n) grade (root n) s g \<rbrakk> \<Longrightarrow>
               \<exists>g'. pathgB (edge n) grade (\<lambda>t. width t \<le> m) (root m) s g'
                    \<and> (C n - C m) + g' \<le> g"
      \<comment> \<open>H4, width convexity / no high-width detour: every ambient-\<open>n\<close> walk to a
          state of width \<open>\<le> m\<close> can be replaced, at no greater grade, by the root
          tower down to \<open>root m\<close> followed by a walk confined to width \<open>\<le> m\<close>.
          This is exactly the geodesic-confinement step of the informal proof.\<close>
begin

subsection \<open>Immediate consequences of H1\<close>

lemma H1_down: "\<lbrakk> width s \<le> m; m \<le> n; edge n s t; width t \<le> m \<rbrakk> \<Longrightarrow> edge m s t"
  using H1 by blast

lemma H1_up: "\<lbrakk> width s \<le> m; m \<le> n; edge m s t \<rbrakk> \<Longrightarrow> edge n s t"
  using H1 by blast

lemma H1_bound: "\<lbrakk> width s \<le> m; edge m s t \<rbrakk> \<Longrightarrow> width t \<le> m"
  using H1[of s m m] by blast

subsection \<open>Transport of walks between ambients\<close>

lemma path_up:
  assumes "pathg (edge m) grade a b g" and "width a \<le> m" and "m \<le> n"
  shows "pathg (edge n) grade a b g \<and> width b \<le> m"
  using assms(1,2)
proof (induction rule: pathg.induct)
  case (pg_refl s)
  then show ?case by (simp add: pathg.pg_refl)
next
  case (pg_snoc s t g u)
  from pg_snoc.IH pg_snoc.prems have IH: "pathg (edge n) grade s t g" "width t \<le> m"
    by simp_all
  from H1_bound[OF IH(2) pg_snoc.hyps(2)] have wu: "width u \<le> m" .
  from H1_up[OF IH(2) \<open>m \<le> n\<close> pg_snoc.hyps(2)] have "edge n t u" .
  from pathg.pg_snoc[OF IH(1) this] wu show ?case by simp
qed

lemma pathB_down:
  assumes "pathgB (edge n) grade (\<lambda>t. width t \<le> m) a b g" and "m \<le> n"
  shows "pathg (edge m) grade a b g"
  using assms(1)
proof (induction rule: pathgB.induct)
  case (pb_refl s)
  then show ?case by (simp add: pathg.pg_refl)
next
  case (pb_snoc s t g u)
  from pathgB_ends[OF pb_snoc.hyps(1)] have wt: "width t \<le> m" by simp
  from H1_down[OF wt \<open>m \<le> n\<close> pb_snoc.hyps(2) pb_snoc.hyps(3)] have "edge m t u" .
  from pathg.pg_snoc[OF pb_snoc.IH this] show ?case .
qed

subsection \<open>The census\<close>

definition Reach :: "nat \<Rightarrow> nat \<Rightarrow> 's set" where
  "Reach n l = {s. \<exists>g. pathg (edge n) grade (root n) s g \<and> g \<le> C n + l}"

lemma ReachI: "\<lbrakk> pathg (edge n) grade (root n) s g; g \<le> C n + l \<rbrakk> \<Longrightarrow> s \<in> Reach n l"
  by (auto simp: Reach_def)

lemma ReachE:
  assumes "s \<in> Reach n l"
  obtains g where "pathg (edge n) grade (root n) s g" "g \<le> C n + l"
  using assms by (auto simp: Reach_def)

lemma Reach_width: "s \<in> Reach n l \<Longrightarrow> width s \<le> n"
proof -
  assume "s \<in> Reach n l"
  then obtain g where p: "pathg (edge n) grade (root n) s g" by (auto simp: Reach_def)
  from path_up[OF p H3_width order.refl] show "width s \<le> n" by simp
qed

lemma Reach_root: "root n \<in> Reach n l"
  by (rule ReachI[of n "root n" 0]) (auto simp: pathg.pg_refl)

lemma Reach_mono_level: "l \<le> l' \<Longrightarrow> Reach n l \<subseteq> Reach n l'"
  by (auto simp: Reach_def)


subsection \<open>Part I: Ambient Collapse\<close>

theorem ambient_collapse:
  assumes mn: "m \<le> n"
  shows "Reach n l \<inter> {s. width s \<le> m} = Reach m l"
proof (rule set_eqI, rule iffI)
  fix s assume "s \<in> Reach n l \<inter> {s. width s \<le> m}"
  then have sR: "s \<in> Reach n l" and sw: "width s \<le> m" by auto
  from sR obtain g where p: "pathg (edge n) grade (root n) s g" and gb: "g \<le> C n + l"
    by (rule ReachE)
  from H4[OF mn sw p] obtain g' where
    pB: "pathgB (edge n) grade (\<lambda>t. width t \<le> m) (root m) s g'"
    and gg: "(C n - C m) + g' \<le> g" by blast
  from pathB_down[OF pB mn] have pm: "pathg (edge m) grade (root m) s g'" .
  have "C m \<le> C n" using H3_mono[OF mn] .
  then have "C n = C m + (C n - C m)" by simp
  with gg gb have "(C n - C m) + g' \<le> C m + (C n - C m) + l" by simp
  then have "g' \<le> C m + l" by simp
  with pm show "s \<in> Reach m l" by (rule ReachI)
next
  fix s assume sm: "s \<in> Reach m l"
  then have sw: "width s \<le> m" by (rule Reach_width)
  from sm obtain g where p: "pathg (edge m) grade (root m) s g" and gb: "g \<le> C m + l"
    by (rule ReachE)
  from path_up[OF p H3_width mn] have pn: "pathg (edge n) grade (root m) s g" by simp
  from pathg_trans[OF H3_tower[OF mn] pn]
  have "pathg (edge n) grade (root n) s ((C n - C m) + g)" .
  moreover have "(C n - C m) + g \<le> C n + l"
    using gb H3_mono[OF mn] by simp
  ultimately have "s \<in> Reach n l" by (rule ReachI)
  with sw show "s \<in> Reach n l \<inter> {s. width s \<le> m}" by simp
qed

text \<open>Equality of LEVELS on every shared state (the second clause of Part I).\<close>

definition level :: "nat \<Rightarrow> 's \<Rightarrow> nat" where
  "level n s = (LEAST l. s \<in> Reach n l)"

corollary level_agree:
  assumes "m \<le> n" and "width s \<le> m"
  shows "level n s = level m s"
proof -
  have "(\<lambda>l. s \<in> Reach n l) = (\<lambda>l. s \<in> Reach m l)"
  proof (rule ext)
    fix l
    from ambient_collapse[OF assms(1), of l] assms(2)
    show "(s \<in> Reach n l) = (s \<in> Reach m l)" by blast
  qed
  then show ?thesis by (simp add: level_def)
qed

subsection \<open>The strata carry no dependence on the ambient\<close>

definition stratum :: "nat \<Rightarrow> nat \<Rightarrow> 's set" where
  "stratum v l = {s \<in> Reach v l. width s = v}"

lemma stratum_sub_Reach:
  assumes "v \<le> n" shows "stratum v l \<subseteq> Reach n l"
  using ambient_collapse[OF assms, of l] by (auto simp: stratum_def)

theorem census_stratified: "Reach n l = (\<Union>v\<le>n. stratum v l)"
proof (rule set_eqI, rule iffI)
  fix s assume s: "s \<in> Reach n l"
  then have w: "width s \<le> n" by (rule Reach_width)
  from ambient_collapse[OF w, of l] s have "s \<in> Reach (width s) l" by auto
  then have "s \<in> stratum (width s) l" by (simp add: stratum_def)
  with w show "s \<in> (\<Union>v\<le>n. stratum v l)" by auto
next
  fix s assume "s \<in> (\<Union>v\<le>n. stratum v l)"
  then obtain v where "v \<le> n" "s \<in> stratum v l" by auto
  with stratum_sub_Reach show "s \<in> Reach n l" by blast
qed

lemma stratum_width: "s \<in> stratum v l \<Longrightarrow> width s = v"
  by (simp add: stratum_def)

lemma stratum_disjoint: "v \<noteq> v' \<Longrightarrow> stratum v l \<inter> stratum v' l = {}"
  by (auto simp: stratum_def)

lemma Reach_Suc: "Reach (Suc n) l = Reach n l \<union> stratum (Suc n) l"
proof -
  have "Reach (Suc n) l = (\<Union>v\<le>Suc n. stratum v l)" by (rule census_stratified)
  also have "\<dots> = (\<Union>v\<le>n. stratum v l) \<union> stratum (Suc n) l"
    by (auto simp: le_Suc_eq)
  also have "\<dots> = Reach n l \<union> stratum (Suc n) l"
    by (simp add: census_stratified)
  finally show ?thesis .
qed

lemma Reach_finite:
  assumes "\<And>v. finite (stratum v l)"
  shows "finite (Reach n l)"
  by (subst census_stratified) (auto simp: assms)

end


section \<open>Part II: Chain Collapse (the gated tail)\<close>

text \<open>
  H5 is stated as a property of the SMALL search: at ambient \<open>v\<close> itself, above
  the threshold, the only level-\<open>l\<close> state of full width \<open>v\<close> is the chain root
  \<open>root v\<close>.  Part I is what lifts this to every larger ambient.  This is
  strictly weaker than assuming the shape of \<open>Reach n l\<close> for large \<open>n\<close>.
\<close>

locale gated_ambient_search = graded_ambient_search +
  fixes nmin :: "nat \<Rightarrow> nat"
  assumes H5: "nmin l < v \<Longrightarrow> stratum v l = {root v}"
begin

lemma root_width_above: "nmin l < v \<Longrightarrow> width (root v) = v"
  using H5[of l v] by (auto simp: stratum_def)

theorem chain_collapse:
  assumes mn: "nmin l \<le> n"
  shows "Reach n l = Reach (nmin l) l \<union> root ` {v. nmin l < v \<and> v \<le> n}"
proof -
  have split: "{..n} = {..nmin l} \<union> {v. nmin l < v \<and> v \<le> n}"
    using mn by auto
  have "Reach n l = (\<Union>v\<le>n. stratum v l)" by (rule census_stratified)
  also have "\<dots> = (\<Union>v\<le>nmin l. stratum v l) \<union> (\<Union>v\<in>{v. nmin l < v \<and> v \<le> n}. stratum v l)"
    by (subst split) (rule UN_Un)
  also have "(\<Union>v\<le>nmin l. stratum v l) = Reach (nmin l) l"
    by (simp add: census_stratified)
  also have "(\<Union>v\<in>{v. nmin l < v \<and> v \<le> n}. stratum v l) = root ` {v. nmin l < v \<and> v \<le> n}"
    using H5 by auto
  finally show ?thesis .
qed

lemma tail_disjoint:
  "Reach (nmin l) l \<inter> root ` {v. nmin l < v \<and> v \<le> n} = {}"
proof -
  have "root v \<notin> Reach (nmin l) l" if "nmin l < v" for v
  proof
    assume "root v \<in> Reach (nmin l) l"
    then have "width (root v) \<le> nmin l" by (rule Reach_width)
    with root_width_above[OF that] that show False by simp
  qed
  then show ?thesis by auto
qed

lemma tail_inj: "inj_on root {v. nmin l < v \<and> v \<le> n}"
  by (rule inj_onI) (metis mem_Collect_eq root_width_above)

theorem chain_collapse_card:
  assumes mn: "nmin l \<le> n" and fin: "finite (Reach (nmin l) l)"
  shows "card (Reach n l) = card (Reach (nmin l) l) + (n - nmin l)"
proof -
  have f2: "finite (root ` {v. nmin l < v \<and> v \<le> n})" by simp
  have "card (Reach n l)
        = card (Reach (nmin l) l) + card (root ` {v. nmin l < v \<and> v \<le> n})"
    by (subst chain_collapse[OF mn], rule card_Un_disjoint[OF fin f2 tail_disjoint])
  also have "card (root ` {v. nmin l < v \<and> v \<le> n}) = card {v. nmin l < v \<and> v \<le> n}"
    by (rule card_image[OF tail_inj])
  also have "{v. nmin l < v \<and> v \<le> n} = {nmin l <.. n}" by auto
  also have "card {nmin l <.. n} = n - nmin l" by simp
  finally show ?thesis .
qed

end


section \<open>The growth law\<close>

text \<open>
  The forward-difference calculus.  "\<open>f\<close> agrees with a polynomial of degree
  \<open>\<le> d\<close> from \<open>v0\<close> on" is equivalent to "the \<open>(d+1)\<close>-st forward difference of
  \<open>f\<close> vanishes from \<open>v0\<close> on", and we prove the direction we need CONSTRUCTIVELY,
  by exhibiting the Newton expansion in the binomial basis.  The binomial basis
  is a genuine polynomial basis: \<open>(t choose j)\<close> is a polynomial in \<open>t\<close> of degree
  exactly \<open>j\<close> with leading coefficient \<open>1/j!\<close>.
\<close>

definition fdiff :: "(nat \<Rightarrow> int) \<Rightarrow> nat \<Rightarrow> int" where
  "fdiff f n = f (Suc n) - f n"

lemma sum_binomial_lower: "(\<Sum>u<t. int (u choose j)) = int (t choose Suc j)"
  by (induction t) simp_all

lemma telescope_fdiff: "f (v0 + t) = f v0 + (\<Sum>u<t. fdiff f (v0 + u))"
  by (induction t) (simp_all add: fdiff_def)

lemma fdiff_shift: "(fdiff ^^ k) (\<lambda>n. f (Suc n)) n = (fdiff ^^ k) f (Suc n)"
proof (induction k arbitrary: n)
  case 0 then show ?case by simp
next
  case (Suc k)
  have "(fdiff ^^ Suc k) (\<lambda>n. f (Suc n)) n
        = fdiff ((fdiff ^^ k) (\<lambda>n. f (Suc n))) n"
    by (simp add: funpow_swap1)
  also have "\<dots> = (fdiff ^^ k) (\<lambda>n. f (Suc n)) (Suc n) - (fdiff ^^ k) (\<lambda>n. f (Suc n)) n"
    by (simp add: fdiff_def)
  also have "\<dots> = (fdiff ^^ k) f (Suc (Suc n)) - (fdiff ^^ k) f (Suc n)"
    by (simp add: Suc.IH)
  also have "\<dots> = fdiff ((fdiff ^^ k) f) (Suc n)" by (simp add: fdiff_def)
  also have "\<dots> = (fdiff ^^ Suc k) f (Suc n)" by (simp add: funpow_swap1)
  finally show ?case .
qed

text \<open>Newton's forward-difference expansion: a vanishing \<open>(d+1)\<close>-st difference
  from \<open>v0\<close> on forces \<open>f\<close> to agree, from \<open>v0\<close> on, with an integer combination of
  binomial coefficients of order \<open>\<le> d\<close> --- i.e. with a polynomial of degree
  \<open>\<le> d\<close>.\<close>

lemma newton_expansion:
  fixes f :: "nat \<Rightarrow> int"
  assumes "\<And>n. v0 \<le> n \<Longrightarrow> (fdiff ^^ Suc d) f n = 0"
  shows "\<exists>c. \<forall>t. f (v0 + t) = (\<Sum>j\<le>d. c j * int (t choose j))"
  using assms
proof (induction d arbitrary: f)
  case 0
  have "f (v0 + t) = f v0" for t
  proof -
    have z: "(\<Sum>u<t. fdiff f (v0 + u)) = 0"
    proof (rule sum.neutral, rule ballI)
      fix u assume "u \<in> {..<t}"
      have "(fdiff ^^ Suc 0) f (v0 + u) = 0" using "0"[of "v0 + u"] by simp
      then show "fdiff f (v0 + u) = 0" by simp
    qed
    have "f (v0 + t) = f v0 + (\<Sum>u<t. fdiff f (v0 + u))" by (rule telescope_fdiff)
    with z show ?thesis by simp
  qed
  then show ?case by (intro exI[of _ "\<lambda>_. f v0"]) simp
next
  case (Suc d)
  define g where "g = fdiff f"
  have gvan: "(fdiff ^^ Suc d) g n = 0" if "v0 \<le> n" for n
  proof -
    have "(fdiff ^^ Suc d) g n = (fdiff ^^ Suc (Suc d)) f n"
      by (simp add: g_def funpow_swap1)
    with Suc.prems[OF that] show ?thesis by simp
  qed
  from Suc.IH[OF gvan] obtain c
    where cEq: "\<And>t. g (v0 + t) = (\<Sum>j\<le>d. c j * int (t choose j))" by blast
  define c' where "c' = (\<lambda>j. if j = 0 then f v0 else (if j - 1 \<le> d then c (j - 1) else 0))"
  have "f (v0 + t) = (\<Sum>j\<le>Suc d. c' j * int (t choose j))" for t
  proof -
    have t1: "f (v0 + t) = f v0 + (\<Sum>u<t. g (v0 + u))"
      unfolding g_def by (rule telescope_fdiff)
    have "(\<Sum>u<t. g (v0 + u)) = (\<Sum>u<t. \<Sum>j\<le>d. c j * int (u choose j))"
      by (simp add: cEq)
    also have "\<dots> = (\<Sum>j\<le>d. \<Sum>u<t. c j * int (u choose j))"
      by (rule sum.swap)
    also have "\<dots> = (\<Sum>j\<le>d. c j * (\<Sum>u<t. int (u choose j)))"
      by (simp add: sum_distrib_left)
    also have "\<dots> = (\<Sum>j\<le>d. c j * int (t choose Suc j))"
      by (simp add: sum_binomial_lower)
    finally have t2: "(\<Sum>u<t. g (v0 + u)) = (\<Sum>j\<le>d. c j * int (t choose Suc j))" .
    have "(\<Sum>j\<le>Suc d. c' j * int (t choose j))
          = c' 0 * int (t choose 0) + (\<Sum>j\<le>d. c' (Suc j) * int (t choose Suc j))"
      by (rule sum.atMost_Suc_shift)
    also have "\<dots> = f v0 + (\<Sum>j\<le>d. c j * int (t choose Suc j))"
      by (simp add: c'_def)
    finally show ?thesis using t1 t2 by simp
  qed
  then show ?case by blast
qed

context graded_ambient_search
begin

definition census :: "nat \<Rightarrow> nat \<Rightarrow> int" where
  "census n l = int (card (Reach n l))"

definition strat_size :: "nat \<Rightarrow> nat \<Rightarrow> int" where
  "strat_size v l = int (card (stratum v l))"

lemma census_step:
  assumes fin: "\<And>v. finite (stratum v l)"
  shows "fdiff (\<lambda>n. census n l) n = strat_size (Suc n) l"
proof -
  have d: "Reach n l \<inter> stratum (Suc n) l = {}"
  proof (rule ccontr)
    assume "Reach n l \<inter> stratum (Suc n) l \<noteq> {}"
    then obtain x where x1: "x \<in> Reach n l" and x2: "x \<in> stratum (Suc n) l" by blast
    from x1 have "width x \<le> n" by (rule Reach_width)
    moreover from x2 have "width x = Suc n" by (simp add: stratum_def)
    ultimately show False by simp
  qed
  have "card (Reach (Suc n) l) = card (Reach n l) + card (stratum (Suc n) l)"
    by (subst Reach_Suc, rule card_Un_disjoint[OF Reach_finite[OF fin] fin d])
  then show ?thesis by (simp add: fdiff_def census_def strat_size_def)
qed

text \<open>
  The Corollary of docs/level-law-general.md 1.5, mechanized:
  if the width strata agree with a polynomial of degree \<open>\<le> d\<close> from \<open>v0\<close> on,
  then the census agrees with a polynomial of degree \<open>\<le> d+1\<close> in the ambient
  from \<open>v0\<close> on.  Everything is stated in the vanishing-forward-difference form,
  which is the diagnostic the campaign actually uses, and then converted into
  an explicit polynomial by @{thm newton_expansion}.
\<close>

theorem census_growth_law:
  assumes fin: "\<And>v. finite (stratum v l)"
    and van: "\<And>v. v0 \<le> v \<Longrightarrow> (fdiff ^^ Suc d) (\<lambda>v. strat_size v l) v = 0"
  shows "\<exists>c. \<forall>t. census (v0 + t) l = (\<Sum>j\<le>Suc d. c j * int (t choose j))"
proof (rule newton_expansion)
  fix n assume vn: "v0 \<le> n"
  have "fdiff (\<lambda>n. census n l) = (\<lambda>n. strat_size (Suc n) l)"
    by (rule ext) (rule census_step[OF fin])
  then have "(fdiff ^^ Suc (Suc d)) (\<lambda>n. census n l) n
             = (fdiff ^^ Suc d) (\<lambda>n. strat_size (Suc n) l) n"
    by (simp add: funpow_swap1)
  also have "\<dots> = (fdiff ^^ Suc d) (\<lambda>v. strat_size v l) (Suc n)"
    by (rule fdiff_shift)
  also have "\<dots> = 0" using van vn by simp
  finally show "(fdiff ^^ Suc (Suc d)) (\<lambda>n. census n l) n = 0" .
qed

end

context gated_ambient_search
begin

text \<open>The T-trivial regime is the degree-0 case: the census is eventually
  AFFINE in the ambient, with slope exactly one.  This is the growth law of
  Part II / Theorem 12.\<close>

theorem census_affine:
  assumes fin: "\<And>v. finite (stratum v l)" and mn: "nmin l \<le> n"
  shows "fdiff (\<lambda>n. census n l) n = 1"
proof -
  have "strat_size (Suc n) l = 1"
    using H5[of l "Suc n"] mn by (simp add: strat_size_def)
  with census_step[OF fin] show ?thesis by simp
qed

corollary census_second_difference_vanishes:
  assumes fin: "\<And>v. finite (stratum v l)" and mn: "nmin l \<le> n"
  shows "(fdiff ^^ 2) (\<lambda>n. census n l) n = 0"
proof -
  have "(fdiff ^^ 2) (\<lambda>n. census n l) n
        = fdiff (\<lambda>n. census n l) (Suc n) - fdiff (\<lambda>n. census n l) n"
    by (simp add: fdiff_def numeral_2_eq_2)
  also have "\<dots> = 1 - 1"
    using census_affine[OF fin mn] census_affine[OF fin, of "Suc n"] mn by simp
  finally show ?thesis by simp
qed

end


section \<open>Interpretation 1: words --- a degenerate tower, non-monotone width,
  and a genuinely ambient-dependent transition relation\<close>

text \<open>
  States are finite words over \<open>\<nat>\<close>; the ambient \<open>n\<close> is the alphabet size; the
  width of a word is the least alphabet that contains it.  There are two kinds
  of move, each of grade one: APPEND a letter \<open>a < n\<close>, and DROP the last letter.
  The root is the empty word and the tower is degenerate (\<open>C = 0\<close>).

  This interpretation is deliberately chosen so that H4 has CONTENT: the width
  is neither monotone up nor monotone down along an edge (append raises it,
  drop can lower it), so a large-ambient search really does have routes
  unavailable at a smaller ambient.  H4 --- "no high-width detour is ever a
  shortcut" --- is here a THEOREM, not a triviality.
\<close>

primrec wwidth :: "nat list \<Rightarrow> nat" where
  "wwidth [] = 0"
| "wwidth (x # xs) = max (Suc x) (wwidth xs)"

definition wgrade :: "nat list \<Rightarrow> nat list \<Rightarrow> nat" where
  "wgrade xs ys = 1"

definition wroot :: "nat \<Rightarrow> nat list" where
  "wroot n = []"

definition wC :: "nat \<Rightarrow> nat" where
  "wC n = 0"

definition wedge :: "nat \<Rightarrow> nat list \<Rightarrow> nat list \<Rightarrow> bool" where
  "wedge n xs ys \<longleftrightarrow> (\<exists>a<n. ys = xs @ [a]) \<or> (xs \<noteq> [] \<and> ys = butlast xs)"

lemma wwidth_le_iff: "wwidth xs \<le> m \<longleftrightarrow> set xs \<subseteq> {..<m}"
  by (induction xs) auto

lemma wwidth_snoc_iff: "wwidth (xs @ [a]) \<le> m \<longleftrightarrow> wwidth xs \<le> m \<and> a < m"
  by (auto simp: wwidth_le_iff)

lemma wwidth_self: "set xs \<subseteq> {..<wwidth xs}"
  using wwidth_le_iff[of xs "wwidth xs"] by simp

lemma wwidth_butlast: "wwidth (butlast xs) \<le> wwidth xs"
proof -
  have "set (butlast xs) \<subseteq> set xs" by (auto dest: in_set_butlastD)
  with wwidth_self have "set (butlast xs) \<subseteq> {..<wwidth xs}" by blast
  then show ?thesis by (simp add: wwidth_le_iff)
qed

text \<open>H1 for this domain: raising the alphabet adds exactly the moves that
  append a letter outside the smaller alphabet, and those all land on WIDER
  states.\<close>

lemma wedge_H1:
  assumes wm: "wwidth xs \<le> m" and mn: "m \<le> n"
  shows "{ys. wedge n xs ys \<and> wwidth ys \<le> m} = {ys. wedge m xs ys}"
  using wm mn
  by (auto simp: wedge_def wwidth_snoc_iff wwidth_le_iff dest: in_set_butlastD)

text \<open>Every walk changes the length by exactly one and costs exactly one, so no
  walk can reach a word of length \<open>k\<close> in fewer than \<open>k\<close> moves --- however far it
  climbs in between.  This is the fact that makes H4 true here.\<close>

lemma wpath_props:
  assumes "pathg (wedge n) wgrade xs0 ys g"
  shows "set ys \<subseteq> set xs0 \<union> {..<n} \<and> length ys \<le> length xs0 + g"
  using assms
proof (induction rule: pathg.induct)
  case (pg_refl s)
  show ?case by simp
next
  case (pg_snoc s t g u)
  from pg_snoc.IH have t1: "set t \<subseteq> set s \<union> {..<n}"
    and t2: "length t \<le> length s + g" by simp_all
  have gr: "wgrade t u = 1" by (simp add: wgrade_def)
  from pg_snoc.hyps(2) show ?case
  proof (unfold wedge_def, elim disjE exE conjE)
    fix a assume "a < n" and u: "u = t @ [a]"
    with t1 t2 gr show ?case by auto
  next
    assume "t \<noteq> []" and u: "u = butlast t"
    with t1 t2 gr show ?case by (auto dest: in_set_butlastD)
  qed
qed

lemma wpath_props0:
  assumes "pathg (wedge n) wgrade [] ys g"
  shows "set ys \<subseteq> {..<n}" and "length ys \<le> g"
  using wpath_props[OF assms] by simp_all

text \<open>Conversely the direct append walk realises the length as its grade and
  never leaves the width of its endpoint.\<close>

lemma wpath_direct:
  assumes "set ys \<subseteq> {..<n}" and "wwidth ys \<le> m" and "m \<le> n"
  shows "pathgB (wedge n) wgrade (\<lambda>t. wwidth t \<le> m) [] ys (length ys)"
  using assms
proof (induction ys rule: rev_induct)
  case Nil
  have "pathgB (wedge n) wgrade (\<lambda>t. wwidth t \<le> m) [] [] 0"
    by (rule pathgB.pb_refl) simp
  then show ?case by simp
next
  case (snoc a ys)
  from snoc.prems(1) have sy: "set ys \<subseteq> {..<n}" and a: "a < n" by auto
  have wa: "wwidth (ys @ [a]) \<le> m" using snoc.prems(2) .
  have wy: "wwidth ys \<le> m" using wa by (simp add: wwidth_snoc_iff)
  from snoc.IH[OF sy wy snoc.prems(3)]
  have p: "pathgB (wedge n) wgrade (\<lambda>t. wwidth t \<le> m) [] ys (length ys)" .
  have e: "wedge n ys (ys @ [a])" using a by (auto simp: wedge_def)
  have g1: "wgrade ys (ys @ [a]) = 1" by (simp add: wgrade_def)
  from pathgB.pb_snoc[OF p e wa]
  have "pathgB (wedge n) wgrade (\<lambda>t. wwidth t \<le> m) [] (ys @ [a])
          (length ys + wgrade ys (ys @ [a]))" .
  then show ?case by (simp add: g1)
qed

interpretation Words: graded_ambient_search wwidth wedge wgrade wroot wC
proof
  fix s :: "nat list" and m n :: nat
  assume "wwidth s \<le> m" and "m \<le> n"
  then show "{t. wedge n s t \<and> wwidth t \<le> m} = {t. wedge m s t}" by (rule wedge_H1)
next
  fix m :: nat
  show "wwidth (wroot m) \<le> m" by (simp add: wroot_def)
next
  fix m n :: nat
  assume "m \<le> n"
  show "wC m \<le> wC n" by (simp add: wC_def)
next
  fix m n :: nat
  assume "m \<le> n"
  have "pathg (wedge n) wgrade [] [] 0" by (rule pathg.pg_refl)
  then show "pathg (wedge n) wgrade (wroot n) (wroot m) (wC n - wC m)"
    by (simp add: wroot_def wC_def)
next
  fix m n :: nat and s :: "nat list" and g :: nat
  assume mn: "m \<le> n" and ws: "wwidth s \<le> m"
    and p: "pathg (wedge n) wgrade (wroot n) s g"
  from p have p0: "pathg (wedge n) wgrade [] s g" by (simp add: wroot_def)
  from wpath_props0[OF p0] have sn: "set s \<subseteq> {..<n}" and lg: "length s \<le> g" by simp_all
  from wpath_direct[OF sn ws mn]
  have "pathgB (wedge n) wgrade (\<lambda>t. wwidth t \<le> m) [] s (length s)" .
  then have pb: "pathgB (wedge n) wgrade (\<lambda>t. wwidth t \<le> m) (wroot m) s (length s)"
    by (simp add: wroot_def)
  from pb lg
  show "\<exists>g'. pathgB (wedge n) wgrade (\<lambda>t. wwidth t \<le> m) (wroot m) s g'
             \<and> (wC n - wC m) + g' \<le> g"
    by (auto simp: wC_def)
qed

text \<open>The census is exactly the set of words of length at most the level over an
  alphabet of size the ambient.  Every claim below is therefore checkable by
  hand.\<close>

lemma Words_Reach: "Words.Reach n l = {xs. set xs \<subseteq> {..<n} \<and> length xs \<le> l}"
proof (rule set_eqI, rule iffI)
  fix xs assume "xs \<in> Words.Reach n l"
  then obtain g where p: "pathg (wedge n) wgrade (wroot n) xs g" and gb: "g \<le> wC n + l"
    by (auto simp: Words.Reach_def)
  from p have p0: "pathg (wedge n) wgrade [] xs g" by (simp add: wroot_def)
  from wpath_props0[OF p0] gb show "xs \<in> {xs. set xs \<subseteq> {..<n} \<and> length xs \<le> l}"
    by (auto simp: wC_def)
next
  fix xs assume "xs \<in> {xs. set xs \<subseteq> {..<n} \<and> length xs \<le> l}"
  then have sx: "set xs \<subseteq> {..<n}" and lx: "length xs \<le> l" by auto
  from sx have wx: "wwidth xs \<le> n" by (simp add: wwidth_le_iff)
  from pathgB_pathg[OF wpath_direct[OF sx wx order.refl]]
  have "pathg (wedge n) wgrade [] xs (length xs)" .
  then have "pathg (wedge n) wgrade (wroot n) xs (length xs)" by (simp add: wroot_def)
  with lx show "xs \<in> Words.Reach n l" by (auto simp: Words.Reach_def wC_def)
qed

text \<open>H4 has real content here: the width can both rise and fall along an edge.\<close>

lemma Words_width_can_rise: "wedge 3 [] [2] \<and> wwidth [] < wwidth [2]"
  by (simp add: wedge_def)

lemma Words_width_can_fall: "wedge 3 [2] [] \<and> wwidth [] < wwidth [2]"
  by (simp add: wedge_def)

text \<open>Non-vacuity: the census is non-empty and genuinely depends on the ambient,
  so Part I is not a statement about empty sets.\<close>

lemma Words_nonvacuous_1: "[] \<in> Words.Reach n l"
  unfolding Words_Reach by simp

lemma Words_nonvacuous_2: "[2] \<in> Words.Reach 3 (Suc 0)"
  unfolding Words_Reach by simp

lemma Words_nonvacuous_3: "[2] \<notin> Words.Reach 2 (Suc 0)"
  unfolding Words_Reach by simp

lemma Words_nonvacuous_4: "Words.Reach 2 (Suc 0) \<subset> Words.Reach 3 (Suc 0)"
proof -
  have "Words.Reach 2 (Suc 0) \<subseteq> Words.Reach 3 (Suc 0)"
    unfolding Words_Reach by auto
  with Words_nonvacuous_2 Words_nonvacuous_3 show ?thesis by blast
qed

text \<open>Part I, specialised.  This is a real identity between two different
  computations, not a triviality: the ambient-3 census is strictly larger than
  the ambient-2 census, yet they agree exactly below width 2.\<close>

corollary Words_collapse:
  "m \<le> n \<Longrightarrow> Words.Reach n l \<inter> {s. wwidth s \<le> m} = Words.Reach m l"
  by (rule Words.ambient_collapse)

text \<open>The strata are finite, and the census obeys the growth law: the width-\<open>v\<close>
  stratum is the set of words of length \<open>\<le> l\<close> whose largest letter is \<open>v-1\<close>.\<close>

lemma Words_stratum_finite: "finite (Words.stratum v l)"
proof -
  have "Words.stratum v l \<subseteq> {xs. set xs \<subseteq> {..<v} \<and> length xs \<le> l}"
    by (auto simp: Words.stratum_def Words_Reach)
  moreover have "finite {xs. set xs \<subseteq> {..<v} \<and> length xs \<le> l}"
    by (rule finite_subset[OF _ finite_lists_length_le[of "{..<v}" l]]) auto
  ultimately show ?thesis by (rule finite_subset)
qed

text \<open>The growth law, instantiated: whenever the width strata of the word
  search agree with a polynomial of degree \<open>\<le> d\<close> from \<open>v0\<close> on, its census agrees
  with a polynomial of degree \<open>\<le> d+1\<close> in the ambient from \<open>v0\<close> on.\<close>

corollary Words_growth_law:
  assumes "\<And>v. v0 \<le> v \<Longrightarrow> (fdiff ^^ Suc d) (\<lambda>v. Words.strat_size v l) v = 0"
  shows "\<exists>c. \<forall>t. Words.census (v0 + t) l = (\<Sum>j\<le>Suc d. c j * int (t choose j))"
  by (rule Words.census_growth_law[OF Words_stratum_finite assms])


section \<open>Interpretation 2: a gated root tower --- Part II is satisfiable\<close>

text \<open>
  The abstract skeleton of the sorting-network instance.  There is a chain of
  roots \<open>Tow n \<rightarrow> Tow (n-1) \<rightarrow> \<dots>\<close>, each step of grade \<open>\<delta> k\<close>, so the free chain is
  \<open>C n = \<Sum>\<^bsub>k\<le>n\<^esub> \<delta> k\<close>.  Every \<open>Tow k\<close> additionally has ONE off-chain successor
  \<open>Off k\<close> of the same width, reachable only at grade \<open>C k + D k + 1\<close> --- the
  abstract mirror of the Huffman ceiling of ambient-reduction.md Theorem D,
  which gates the successor branch at the root until the level exceeds
  \<open>D (k)\<close>.  With \<open>D\<close> monotone and unbounded, \<open>nmin l = (LEAST k. l \<le> D k)\<close> and
  H5 holds.

  This is a MODEL of the hypotheses with the same chain structure as the
  sorting-network search.  It is NOT a formalisation of that search.
\<close>

datatype tstate = Tow nat | Off nat

primrec twidth :: "tstate \<Rightarrow> nat" where
  "twidth (Tow k) = k"
| "twidth (Off k) = k"

locale tower_data =
  fixes delta :: "nat \<Rightarrow> nat" and D :: "nat \<Rightarrow> nat"
  assumes D_mono: "mono D"
    and D_unbounded: "\<exists>k. l \<le> D k"
begin

definition CC :: "nat \<Rightarrow> nat" where "CC n = (\<Sum>k\<le>n. delta k)"

definition gate :: "nat \<Rightarrow> nat" where "gate k = CC k + D k + 1"

fun tgrade :: "tstate \<Rightarrow> tstate \<Rightarrow> nat" where
  "tgrade (Tow k) (Tow j) = (if j = k - 1 then delta k else 0)"
| "tgrade (Tow k) (Off j) = gate k"
| "tgrade (Off k) _ = 0"

definition tedge :: "tstate \<Rightarrow> tstate \<Rightarrow> bool" where
  "tedge s t \<longleftrightarrow> (\<exists>k. s = Tow (Suc k) \<and> t = Tow k) \<or> (\<exists>k. s = Tow k \<and> t = Off k)"

definition tnmin :: "nat \<Rightarrow> nat" where "tnmin l = (LEAST k. l \<le> D k)"

lemma CC_mono: "m \<le> n \<Longrightarrow> CC m \<le> CC n"
  by (simp add: CC_def sum_mono2)

lemma CC_Suc: "CC (Suc k) = CC k + delta (Suc k)"
  by (simp add: CC_def)

lemma tedge_width: "tedge s t \<Longrightarrow> twidth t \<le> twidth s"
  by (auto simp: tedge_def)

lemma tedge_H1:
  assumes wm: "twidth s \<le> m" and mn: "m \<le> n"
  shows "{t. tedge s t \<and> twidth t \<le> m} = {t. tedge s t}"
proof -
  have "twidth t \<le> m" if "tedge s t" for t
    using tedge_width[OF that] wm by simp
  then show ?thesis by auto
qed

lemma ttower: "m \<le> n \<Longrightarrow> pathg tedge tgrade (Tow n) (Tow m) (CC n - CC m)"
proof (induction n)
  case 0 then show ?case by (simp add: pathg.pg_refl)
next
  case (Suc n)
  show ?case
  proof (cases "m = Suc n")
    case True then show ?thesis by (simp add: pathg.pg_refl)
  next
    case False
    with Suc.prems have mn: "m \<le> n" by simp
    have e: "tedge (Tow (Suc n)) (Tow n)" by (auto simp: tedge_def)
    have g: "tgrade (Tow (Suc n)) (Tow n) = delta (Suc n)" by simp
    from pathg.pg_snoc[OF pathg.pg_refl[of tedge tgrade "Tow (Suc n)"] e]
    have "pathg tedge tgrade (Tow (Suc n)) (Tow n) (delta (Suc n))" by (simp add: g)
    from pathg_trans[OF this Suc.IH[OF mn]]
    have "pathg tedge tgrade (Tow (Suc n)) (Tow m) (delta (Suc n) + (CC n - CC m))" .
    moreover have "delta (Suc n) + (CC n - CC m) = CC (Suc n) - CC m"
      using CC_mono[OF mn] by (simp add: CC_Suc)
    ultimately show ?thesis by simp
  qed
qed

text \<open>The complete description of the reachable set from \<open>Tow n\<close>.\<close>

lemma tpath_shape_gen:
  assumes "pathg tedge tgrade r s g" and "r = Tow n"
  shows "(\<exists>j\<le>n. s = Tow j \<and> g = CC n - CC j)
         \<or> (\<exists>j\<le>n. s = Off j \<and> g = (CC n - CC j) + gate j)"
  using assms
proof (induction rule: pathg.induct)
  case (pg_refl s)
  then show ?case by auto
next
  case (pg_snoc s t g u)
  from pg_snoc.IH[OF pg_snoc.prems] show ?case
  proof (elim disjE exE conjE)
    fix j assume j: "j \<le> n" and t: "t = Tow j" and gv: "g = CC n - CC j"
    have te: "tedge (Tow j) u" using pg_snoc.hyps(2) t by simp
    show ?case
    proof (cases u)
      case (Tow k)
      with te have jk: "j = Suc k" by (auto simp: tedge_def)
      then have kn: "k \<le> n" using j by simp
      have tg: "tgrade t u = delta j" using t Tow jk by simp
      have "CC j = CC k + delta j" using jk by (simp add: CC_Suc)
      then have "(CC n - CC j) + delta j = CC n - CC k"
        using CC_mono[OF kn] CC_mono[OF j] by simp
      then have "g + tgrade t u = CC n - CC k" using gv tg by simp
      with Tow kn show ?thesis by auto
    next
      case (Off k)
      with te have jk: "j = k" by (auto simp: tedge_def)
      have tg: "tgrade t u = gate j" using t Off by simp
      then have "g + tgrade t u = (CC n - CC j) + gate j" using gv by simp
      with Off jk j show ?thesis by auto
    qed
  next
    fix j assume "j \<le> n" and "t = Off j"
    with pg_snoc.hyps(2) show ?case by (auto simp: tedge_def)
  qed
qed

lemma tpath_shape:
  assumes "pathg tedge tgrade (Tow n) s g"
  shows "(\<exists>j\<le>n. s = Tow j \<and> g = CC n - CC j)
         \<or> (\<exists>j\<le>n. s = Off j \<and> g = (CC n - CC j) + gate j)"
  by (rule tpath_shape_gen[OF assms refl])

lemma tstep: "tedge (Tow (Suc k)) (Tow k)"
  by (auto simp: tedge_def)

lemma tower_conf:
  "j \<le> m \<Longrightarrow> pathgB tedge tgrade (\<lambda>t. twidth t \<le> m) (Tow m) (Tow j) (CC m - CC j)"
proof (induction m)
  case 0
  then have "j = 0" by simp
  then show ?case by (simp add: pathgB.pb_refl)
next
  case (Suc m)
  show ?case
  proof (cases "j = Suc m")
    case True
    then show ?thesis by (simp add: pathgB.pb_refl)
  next
    case False
    with Suc.prems have jm: "j \<le> m" by simp
    have wk: "pathgB tedge tgrade (\<lambda>t. twidth t \<le> Suc m) (Tow m) (Tow j) (CC m - CC j)"
      by (rule pathgB_weaken[OF Suc.IH[OF jm]]) simp
    have r: "pathgB tedge tgrade (\<lambda>t. twidth t \<le> Suc m) (Tow (Suc m)) (Tow (Suc m)) 0"
      by (rule pathgB.pb_refl) simp
    have "pathgB tedge tgrade (\<lambda>t. twidth t \<le> Suc m) (Tow (Suc m)) (Tow m)
            (0 + tgrade (Tow (Suc m)) (Tow m))"
      by (rule pathgB.pb_snoc[OF r tstep]) simp
    then have step: "pathgB tedge tgrade (\<lambda>t. twidth t \<le> Suc m) (Tow (Suc m)) (Tow m)
            (delta (Suc m))" by simp
    from pathgB_trans[OF step wk]
    have "pathgB tedge tgrade (\<lambda>t. twidth t \<le> Suc m) (Tow (Suc m)) (Tow j)
            (delta (Suc m) + (CC m - CC j))" .
    moreover have "delta (Suc m) + (CC m - CC j) = CC (Suc m) - CC j"
      using CC_mono[OF jm] by (simp add: CC_Suc)
    ultimately show ?thesis by simp
  qed
qed

lemma tH4:
  assumes mn: "m \<le> n" and ws: "twidth s \<le> m"
    and p: "pathg tedge tgrade (Tow n) s g"
  shows "\<exists>g'. pathgB tedge tgrade (\<lambda>t. twidth t \<le> m) (Tow m) s g'
              \<and> (CC n - CC m) + g' \<le> g"
  using tpath_shape[OF p]
proof (elim disjE exE conjE)
  fix j assume j: "j \<le> n" and s: "s = Tow j" and gv: "g = CC n - CC j"
  from ws s have jm: "j \<le> m" by simp
  from tower_conf[OF jm] s
  have pb: "pathgB tedge tgrade (\<lambda>t. twidth t \<le> m) (Tow m) s (CC m - CC j)" by simp
  have "(CC n - CC m) + (CC m - CC j) = CC n - CC j"
    using CC_mono[OF mn] CC_mono[OF jm] CC_mono[OF order_trans[OF jm mn]] by simp
  with pb gv show ?thesis by auto
next
  fix j assume j: "j \<le> n" and s: "s = Off j" and gv: "g = (CC n - CC j) + gate j"
  from ws s have jm: "j \<le> m" by simp
  have e: "tedge (Tow j) (Off j)" by (auto simp: tedge_def)
  have b: "twidth (Off j) \<le> m" using jm by simp
  from pathgB.pb_snoc[OF tower_conf[OF jm] e b]
  have pb: "pathgB tedge tgrade (\<lambda>t. twidth t \<le> m) (Tow m) (Off j)
              ((CC m - CC j) + tgrade (Tow j) (Off j))" .
  then have pb2: "pathgB tedge tgrade (\<lambda>t. twidth t \<le> m) (Tow m) (Off j)
              ((CC m - CC j) + gate j)" by simp
  have "(CC n - CC m) + ((CC m - CC j) + gate j) = (CC n - CC j) + gate j"
    using CC_mono[OF mn] CC_mono[OF jm] CC_mono[OF order_trans[OF jm mn]] by simp
  with pb2 gv s show ?thesis by auto
qed

sublocale Tower: graded_ambient_search twidth "\<lambda>_. tedge" tgrade Tow CC
proof
  fix s :: tstate and m n :: nat
  assume "twidth s \<le> m" "m \<le> n"
  then show "{t. tedge s t \<and> twidth t \<le> m} = {t. tedge s t}" by (rule tedge_H1)
next
  fix m :: nat show "twidth (Tow m) \<le> m" by simp
next
  fix m n :: nat assume "m \<le> n" then show "CC m \<le> CC n" by (rule CC_mono)
next
  fix m n :: nat assume "m \<le> n" then show "pathg tedge tgrade (Tow n) (Tow m) (CC n - CC m)"
    by (rule ttower)
next
  fix m n :: nat and s :: tstate and g :: nat
  assume "m \<le> n" "twidth s \<le> m" "pathg tedge tgrade (Tow n) s g"
  then show "\<exists>g'. pathgB tedge tgrade (\<lambda>t. twidth t \<le> m) (Tow m) s g'
                  \<and> (CC n - CC m) + g' \<le> g" by (rule tH4)
qed

lemma Tower_Reach: "Tower.Reach n l = Tow ` {..n} \<union> Off ` {j. j \<le> n \<and> l > D j}"
proof (rule set_eqI, rule iffI)
  fix s assume "s \<in> Tower.Reach n l"
  then obtain g where p: "pathg tedge tgrade (Tow n) s g" and gb: "g \<le> CC n + l"
    by (auto simp: Tower.Reach_def)
  from tpath_shape[OF p] show "s \<in> Tow ` {..n} \<union> Off ` {j. j \<le> n \<and> l > D j}"
  proof (elim disjE exE conjE)
    fix j assume "j \<le> n" "s = Tow j" then show ?thesis by auto
  next
    fix j assume j: "j \<le> n" and s: "s = Off j" and gv: "g = (CC n - CC j) + gate j"
    from gb gv CC_mono[OF j] have "gate j \<le> CC j + l" by (simp add: gate_def)
    then have "l > D j" by (simp add: gate_def)
    with j s show ?thesis by auto
  qed
next
  fix s assume "s \<in> Tow ` {..n} \<union> Off ` {j. j \<le> n \<and> l > D j}"
  then show "s \<in> Tower.Reach n l"
  proof (elim UnE imageE)
    fix j assume j: "j \<in> {..n}" and s: "s = Tow j"
    then have "j \<le> n" by simp
    from ttower[OF this] s CC_mono[OF \<open>j \<le> n\<close>]
    show ?thesis by (auto simp: Tower.Reach_def)
  next
    fix j assume j: "j \<in> {j. j \<le> n \<and> l > D j}" and s: "s = Off j"
    then have jn: "j \<le> n" and dl: "l > D j" by auto
    have e: "tedge (Tow j) (Off j)" by (auto simp: tedge_def)
    from pathg.pg_snoc[OF ttower[OF jn] e]
    have "pathg tedge tgrade (Tow n) (Off j) ((CC n - CC j) + gate j)" by simp
    moreover have "(CC n - CC j) + gate j \<le> CC n + l"
      using CC_mono[OF jn] dl by (simp add: gate_def)
    ultimately show ?thesis using s by (auto simp: Tower.Reach_def)
  qed
qed

lemma tnmin_le: "tnmin l < v \<Longrightarrow> l \<le> D v"
proof -
  assume v: "tnmin l < v"
  from D_unbounded obtain k where "l \<le> D k" by blast
  then have "l \<le> D (tnmin l)" unfolding tnmin_def by (rule LeastI)
  moreover have "D (tnmin l) \<le> D v" using v D_mono by (simp add: monoD)
  ultimately show "l \<le> D v" by simp
qed

sublocale Gated: gated_ambient_search twidth "\<lambda>_. tedge" tgrade Tow CC tnmin
proof
  fix l v assume v: "tnmin l < v"
  have "Tower.stratum v l = {s \<in> Tower.Reach v l. twidth s = v}"
    by (simp add: Tower.stratum_def)
  also have "\<dots> = {Tow v}"
    using Tower_Reach[of v l] tnmin_le[OF v] by auto
  finally show "Tower.stratum v l = {Tow v}" .
qed

lemma Tower_stratum_finite: "finite (Tower.stratum v l)"
proof (rule finite_subset)
  show "Tower.stratum v l \<subseteq> Tower.Reach v l" by (simp add: Tower.stratum_def)
  show "finite (Tower.Reach v l)" by (simp add: Tower_Reach)
qed

text \<open>Part II's growth law, instantiated: in the gated-tower model the census is
  eventually AFFINE in the ambient with slope exactly one --- the abstract form
  of ambient-reduction.md Theorem E / audit-paper-v2.md Theorem 12.\<close>

corollary Tower_affine:
  assumes "tnmin l \<le> n"
  shows "fdiff (\<lambda>n. Tower.census n l) n = 1"
  by (rule Gated.census_affine[OF Tower_stratum_finite assms])

lemma Tower_census:
  assumes "tnmin l \<le> n"
  shows "card (Tower.Reach n l) = card (Tower.Reach (tnmin l) l) + (n - tnmin l)"
proof (rule Gated.chain_collapse_card[OF assms])
  show "finite (Tower.Reach (tnmin l) l)" by (simp add: Tower_Reach)
qed

end

text \<open>The tower interpretation is inhabited: take \<open>\<delta> k = \<lceil>log\<^sub>2 k\<rceil>\<close>-like data.  Any
  monotone unbounded \<open>D\<close> will do; here is the simplest witness, which shows the
  \<^locale>\<open>tower_data\<close> assumptions are consistent.\<close>

interpretation TowerEx: tower_data "\<lambda>k. 1" "\<lambda>k. k"
  by unfold_locales (auto simp: mono_def)

lemma tower_example_nonvacuous: "TowerEx.tnmin l = l"
  unfolding TowerEx.tnmin_def by (rule Least_equality) auto

end
