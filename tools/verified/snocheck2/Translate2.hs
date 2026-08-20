{-# LANGUAGE Safe #-}
-- | Translate2: mirrors checker/snocheck/src/Translate.hs, but targets
-- Verified.PrefixChecker (the prefix-capable extracted checker) instead of
-- the frozen Verified.Checker.
module Translate2
  ( translateProofSteps
  )
where

import qualified Verified.PrefixChecker        as VP
import           ProofStep
import           VectSet                        ( VectSet )
import qualified VectSet                       as VS

translateProofSteps :: (Int, Int -> ProofStep) -> VP.Proof_cert
translateProofSteps (stepCount, steps) =
  VP.ProofCert (VP.Int_of_integer $ toInteger stepCount) (translateStepFn steps)

translateStepFn :: (Int -> ProofStep) -> VP.Int -> VP.Proof_step
translateStepFn steps (VP.Int_of_integer stepId) =
  translateStep (steps $ fromInteger stepId)

translateStep :: ProofStep -> VP.Proof_step
translateStep step = VP.ProofStep width vectList stepBound stepWitnesses
 where
  width         = VP.Int_of_integer . toInteger $ VS.channels (vectSet step)
  vectList      = VS.asBoolVectList (vectSet step)
  stepBound     = VP.Int_of_integer . toInteger $ bound step
  stepWitnesses = translateWitnesses (witnesses step)

translateWitnesses :: Witnesses -> VP.Proof_step_witnesses
translateWitnesses (Huffman pol ws) =
  VP.HuffmanWitnesses pol (translateWitnessList ws)
translateWitnesses (Successors ws) =
  VP.SuccessorWitnesses (translateWitnessList ws)

translateWitnessList :: [Maybe Witness] -> [Maybe VP.Proof_witness]
translateWitnessList = map (fmap translateWitness)

translateWitness :: Witness -> VP.Proof_witness
translateWitness witness = VP.ProofWitness
  (VP.Int_of_integer . toInteger $ stepId witness)
  (invert witness)
  (map (VP.Int_of_integer . toInteger) $ perm witness)
