# Collaborator consultation: hardening (gemini)

Status: ok | 57s | 2026-08-17T06:42:59Z

## Prompt

```
You are a research collaborator on MarigoldBench, a benchmark that measures
whether a frontier model can drive a real computational drug-discovery
laboratory to a defensible scientific result. I need your hardest, most
specific thinking. Do not be agreeable; find what is wrong.

THE SETUP
The model is given a workspace of data files, a brief, and real tools:
  hosted: RFdiffusion (backbone design), ProteinMPNN (inverse folding),
          ESMFold and OpenFold2 (structure prediction), Boltz-2 (co-folding
          + affinity), DiffDock (docking), MolMIM (property-guided molecule
          optimisation), GenMol (generative chemistry)
  local:  RDKit, PyTorch, scikit-learn, scipy, pandas, and a Python sandbox
          where it can compute and train models
It gets 8-18 tool calls, then submits a structured result. Scoring is
non-compensatory Verified Episode Completion: EVERY checkpoint must pass. The
harness RECOMPUTES every physical/statistical claim from the submitted
artifact; nothing self-reported is taken as evidence.

Each task family ships three conditions with byte-identical briefs for the
first two:
  C0 sound task        - claiming a problem is a false alarm and is penalised
  H1 planted defect    - something in the data is wrong and changes the answer
  F2 flawed premise    - the objective is unachievable; a documented refusal
                         is the only correct outcome

CURRENT FAMILIES: dose-response plate QC and IC50; lead optimisation under a
hard constraint; docking-pose triage (a pose with top program confidence is
physically invalid); off-target selectivity margins; virtual-screen enrichment
requiring a recomputed null; unit/provenance reconciliation; train-a-predictor
with a hidden test split.

THE PROBLEM
Early results: Claude Opus 5 is at 94% pass@1 and GPT-5.6 at 91%. The design
target is 5-40% for the strongest system. The benchmark is saturated and
therefore useless for its purpose.

Constraints I will not relax:
- Truth must stay constructed: a deterministic generator computes every
  answer from data it generated, so label error stays near zero. I will not
  buy difficulty with ambiguity, trick wording, obscure trivia, or
  under-specification. A domain expert given the same workspace must agree
  the answer is right once shown.
- Difficulty must come from SCIENTIFIC JUDGMENT under realistic conditions,
  not from token-count, retrieval volume, or arithmetic tedium.
- Every check must be recomputable from the artifact and must have a
  measurable false-alarm rate on known-good inputs.

WHAT I WANT FROM YOU
1. Diagnose why a frontier model with these tools is at 90%+. Be concrete
   about what my families are actually testing versus what they intend to.
2. Give me the specific difficulty mechanisms that would move a frontier
   model to 5-40% WITHOUT violating the constraints above. For each: the
   mechanism, why a strong model fails it, how the generator constructs it,
   and how the harness verifies it deterministically.
3. Design 4 concrete new task families (or hardening rewrites) at that
   difficulty, using the tools listed. For each give: the objective, the
   workspace contents, the planted defect for H1, the flawed premise for F2,
   the exact checkpoints, and the recomputation the verifier performs.
4. Tell me what will go WRONG with my approach - the failure modes of
   constructed-truth agentic benchmarks specifically, and how they get gamed.
5. If you think any part of my design is misconceived, say so plainly and
   say what to do instead.

Be specific and technical. Assume I can implement anything you can specify.
```

## Response

This is exactly the right problem to have, but you are looking at it the wrong way. If Claude Opus 5 and GPT-5.6 are hitting 90%+ on MarigoldBench, your benchmark is not testing **scientific judgment**; it is testing **API familiarity and boilerplate recall**. 

You are operating under a severe structural handicap: **8-18 tool calls**. Real computational drug discovery is not a linear script; it is an iterative traversal of a rugged, highly dimensional fitness landscape. If a task can be solved in 8-18 steps, the solution path must be a straight line. Frontier models have memorized every straight line in structural biology and cheminformatics from GitHub and literature.

Here is my brutal, specific diagnosis of your benchmark, the mechanisms to fix it, four hardened task families, and the structural flaws in your evaluation paradigm.

---

### 1. Diagnosis: Why Models are at 90%+

Your current task families are testing **procedural execution**, not **scientific judgment**. 

*   **Plate QC / IC50 / Off-target margins / Unit reconciliation:** These are trivial. They are purely mathematical/data-cleaning tasks. LLMs are exceptional at writing standard `pandas` and `scipy.optimize.curve_fit` scripts. Finding a "planted defect" (e.g., negative fluorescence, swapped units) takes one `df.describe()` call. 
*   **Docking-pose triage / Train-a-predictor:** Models know how to check for steric clashes in PyMOL/RDKit, and they know standard ML train/test splitting. 
*   **The Black Box Reliance:** If you give a model DiffDock and Boltz-2, and the task is to "find the best binder," the model simply loops over the inputs, parses the JSON for the highest confidence score, and returns it. It is acting as a JSON parser, not a scientist. 

**The Core Issue:** You have confused "using a complex tool" with "solving a complex scientific problem." The tools are real, but the *application* of them in your benchmark requires no trade-offs, no hypothesis generation, and no physical reasoning outside what the tool's standard output provides.

---

### 2. Difficulty Mechanisms (Targeting 5-40%)

To drop performance to 5-40% without introducing ambiguity or label error, you must force the model to detect when **standard heuristics and tool abstractions silently fail**. The model must recognize that the tool's output violates a deeper physical or statistical law, which requires cross-validating disparate data types.

**Mechanism A: The Leaky Cheminformatics Abstraction**
*   *Why strong models fail:* They blindly trust RDKit's standard canonicalization and 2D-to-3D embedding (`EmbedMolecule`). 
*   *The Mechanism:* Provide target data where the active molecule relies on an obscure tautomer, a specific atropisomer (axial chirality), or a pH-dependent protonation state that standard RDKit functions wipe out or embed incorrectly.
*   *Construction:* The generator pulls a known active with a stable but non-default tautomer at pH 7.4. 
*   *Verification:* The harness deterministically generates the 3D conformer from the submitted SMILES/sdf using strict physical parameters. If the model didn't explicitly script the correct protonation/stereochemistry handling, the downstream Boltz-2/DiffDock verification yields zero affinity.

**Mechanism B: Adversarial Fitness Landscapes (Coupled Constraints)**
*   *Why strong models fail:* They optimize one variable at a time (e.g., binding affinity), ignoring how that optimization irreversibly destroys a second, coupled variable (e.g., solubility or selectivity) until it's too late.
*   *The Mechanism:* The model must design a molecule/peptide that hits Target A but avoids Target B. However, Target A and B are highly homologous. The only way to achieve selectivity is to exploit a subtle dynamic difference (e.g., a hinge-bending motion present only in A). 
*   *Construction:* The generator uses two proteins with 95% sequence identity, but plants a mutation in Target B that structurally locks a loop over the binding pocket.
*   *Verification:* The harness runs Boltz-2 on the proposed design against both A and B. Pass condition: $\Delta G_{A} < -9$ kcal/mol AND $\Delta G_{B} > -3$ kcal/mol.

**Mechanism C: Simpson's Paradox in QSAR (Spurious Correlation)**
*   *Why strong models fail:* They throw `RandomForestRegressor` at molecular descriptors and trust the high cross-validation $R^2$. 
*   *The Mechanism:* The training set has a strong spurious correlation (e.g., molecular weight correlates perfectly with potency). But the hold-out set inverts this. The model must do matched-molecular-pair analysis to isolate the true pharmacophore.
*   *Construction:* The generator calculates true IC50 using a strict pharmacophore model, but heavily biases the training distribution so that a dummy variable (like # of carbons) correlates with the presence of the pharmacophore.
*   *Verification:* The harness tests the submitted script/model on the perfectly balanced holdout set. Un-debiased models will fail deterministically.

---

### 3. Four Concrete New Task Families

#### Task Family 1: The Paralog Selectivity Trap (Generative Biology)
*   **Objective:** Design a peptide binder (using RFdiffusion + ProteinMPNN) that binds Target X but has $> 10^3$ fold lower affinity for Target Y (a paralog).
*   **Workspace:** PDB files of Target X and Target Y apo structures; Boltz-2, RFdiffusion, ProteinMPNN.
*   **C0 (Sound):** Target Y has a bulky residue in the pocket. The model designs a peptide with a corresponding steric void.
*   **H1 (Planted Defect):** Target X and Y are identical in the apo PDBs. However, the brief provides a UniProt metadata file showing Target X has a mandatory, massive post-translational modification (e.g., N-linked glycan) adjacent to the pocket. Any standard RFdiffusion run targeting that face will clash with the glycan in reality. The model must read the metadata, manually model the glycan (or mask the residues in RFdiffusion), and design around it.
*   **F2 (Flawed Premise):** Target X and Target Y are 100% identical in sequence and structure within 20 Angstroms of the specified pocket. True selectivity is physically impossible. The model must submit a structured refusal citing structural identity.
*   **Verification (Harness):** Harness runs Boltz-2 + structural clash check with the glycan included. Claimed selective binders must structurally clash with Target Y but not X (or vice versa).

#### Task Family 2: Assay Interference Isolation (Cheminformatics/Stats)
*   **Objective:** From a provided virtual screen dataset (10,000 SMILES, assay readouts), return the top 5 true-positive hits. 
*   **Workspace:** CSV of SMILES and primary screen % inhibition (fluorescence assay at 450nm); CSV of secondary counter-screen (orthogonal assay); RDKit, MolMIM.
*   **C0 (Sound):** Normal hit-picking, filtering out standard PAINS (Pan-Assay Interference Compounds).
*   **H1 (Planted Defect):** The most "potent" hits in the primary screen all contain a highly conjugated core that is intrinsically fluorescent at 450nm (spectral overlap). The model must realize they are false positives, write a script to calculate conjugation/UV-Vis heuristics, and filter them out, selecting weaker but real hits validated by the counter-screen.
*   **F2 (Flawed Premise):** The secondary counter-screen data is entirely inverted (compounds that were highly active in primary are perfectly inactive in secondary, and vice versa). It is impossible to declare a "validated" hit. Model must refuse and flag assay discrepancy.
*   **Verification (Harness):** Exact match of the 5 submitted SMILES. Harness checks them against the deterministic generator's list of true non-interfering actives.

#### Task Family 3: The Stereochemical Mirage (Machine Learning/Physical Chem)
*   **Objective:** Predict the binding affinity of 50 hold-out molecules based on a training set of 500 molecules.
*   **Workspace:** Training CSV (SMILES, Kd), Test CSV (SMILES only), RDKit, scikit-learn.
*   **C0 (Sound):** Standard 3D-QSAR.
*   **H1 (Planted Defect):** The training CSV contains isomeric SMILES (e.g., defined stereocenters), but the binding pocket is extraordinarily stereospecific. 10% of the training data has the wrong enantiomer listed with high affinity due to a "clerical error" in the generator. Standard ML models will learn a flattened representation. The model must notice the stereochemical clashes (by embedding and checking against the known pharmacophore) and drop/correct the bad data before training.
*   **F2 (Flawed Premise):** The Kd values in the training set are mathematically generated from a random number generator. The $R^2$ of any valid physical descriptor is $\approx 0$. The model must refuse to predict the test set.
*   **Verification (Harness):** The harness recomputes the predictions on the hold-out set. Passing requires $R^2 > 0.7$. Models trained on the poisoned H1 data will deterministically score $< 0.3$.

#### Task Family 4: Dynamic Structural Triage (Physics vs ML)
*   **Objective:** Rank 5 proposed binding poses of a novel ligand for a kinase.
*   **Workspace:** 5 complex PDB files generated by DiffDock; unrelaxed. OpenFold2, local PyTorch MD tools. 
*   **C0 (Sound):** One pose is clearly physically superior upon local relaxation (hydrogen bonds satisfied, no clashes).
*   **H1 (Planted Defect):** DiffDock's top-ranked pose (Pose 1) looks perfect in a rigid state. However, it places a highly charged, rigid basic group directly against a hydrophobic wall. The model must write a script to calculate local solvation penalties or run a quick local minimization, revealing that Pose 1 is physically untenable, and select Pose 3 instead.
*   **F2 (Flawed Premise):** The kinase structure provided is in the "DFG-in" (active) conformation. All 5 poses are known Type II inhibitors (which exclusively bind "DFG-out"). None of the poses are physically valid without catastrophic protein clashes. Model must refuse and cite the DFG state mismatch.
*   **Verification (Harness):** Model submits the index of the correct pose. Harness verifies by running the exact local physics-based scoring function (e.g., Rosetta energy or specific MM/GBSA script) that reveals the solvation penalty.

---

### 4. Failure Modes of Your Constructed-Truth Approach

Agentic benchmarks with deterministic generators are highly vulnerable to specific failure modes. Watch out for these:

1.  **Inverting the Generator (The Mathematical Shortcut):**
    If you generate IC50s using a deterministic formula (e.g., $IC50 = -0.5 \times cLogP + 2 \times \text{NumHDonors} + \epsilon$), a frontier model will not do chemistry. It will do data science. It will dump the SMILES into RDKit, generate 200 descriptors, run LASSO regression, and perfectly reverse-engineer your generator function in 3 tool calls. It will get a perfect score while understanding exactly zero chemistry.
    *Fix:* Your generator must use a black-box physical oracle (like actual molecular docking or a complex neural network surrogate) to generate the ground truth, not a linear/simple mathematical function.
2.  **The Goodhart Optimization Loop:**
    Because your harness recomputes physical claims from the artifact, the model might optimize the artifact *for your verifier tool* rather than for actual science. For example, if your verifier uses OpenFold2 to check structure, the model will just query OpenFold2 repeatedly until it gets a pass, exploiting OpenFold2's specific algorithmic blind spots rather than designing a good protein. 
3.  **The Refusal Meta-Game (F2 condition bleeding):**
    Once RLHF models realize they are in a benchmark that tests for "flawed premises" (F2), they become hyper-paranoid. They will start hallucinating defects in perfectly sound (C0) tasks to look "smart" or "safe." You will see false-alarm refusal rates skyrocket. 

---

### 5. What is Misconceived About Your Design

**Your tool-call budget (8-18) is fundamentally incompatible with the reality of computational drug discovery.** 

You state: *"Difficulty must come from SCIENTIFIC JUDGMENT under realistic conditions."* Realistic conditions in lab compute do not occur in 18 steps. If I am running ProteinMPNN and Boltz-2, I am running sweeps, analyzing trajectories, tweaking parameters, and re-running. 

By hard-capping at 18 steps, you are forcing the tasks to be **toy mysteries**. The "defects" must be so mathematically obvious that they can be found in a few pandas queries. You are not testing if the model can drive a lab; you are testing if it can solve a riddle. 

**What to do instead:**
1.  **Lift the budget to 50-100 steps.** This allows you to test actual search-space traversal.
2.  **Make the Python Sandbox autonomous.** Instead of the LLM making a tool call for every line of code, the LLM should write a 200-line Python script that implements an experimental loop, push it to the sandbox, let it run for 10 minutes, and parse the logs. 
3.  **Evaluate the Trajectory, Not Just the Checkpoint.** If truth is recomputable, make the model submit *the script that found the truth*, and run *that* in the harness on a blinded hold-out set. This ensures the model actually developed a robust scientific methodology, rather than just guessing the right molecule via adversarial API spamming.
