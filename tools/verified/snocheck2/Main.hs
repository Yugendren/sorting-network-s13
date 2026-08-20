module Main where

import           System.Environment             ( getArgs )
import           System.Exit                    ( exitWith
                                                  , exitFailure
                                                  , exitSuccess
                                                  , ExitCode(..)
                                                  )
import           System.IO                      ( hPutStrLn, stderr )
import           Control.Exception              ( SomeException
                                                  , try
                                                  , evaluate
                                                  , displayException
                                                  )
import           Data.List                       ( intercalate )
import qualified Data.ByteString               as B

import           Decode2
import           Translate2
import qualified Verified.PrefixChecker        as VP

main :: IO ()
main = do
  args <- getArgs
  case args of
    ["-v", path] -> runV path
    ["-p", path] -> runP path
    _             -> do
      putStrLn "usage: snocheck2 -v PROOF   (v1/v2 full-problem check, via check_proof_get_bound)"
      putStrLn "       snocheck2 -p PROOF   (v2p prefix-rooted check, via check_prefix_proof_get_bound)"
      exitFailure

-- | The two SHA-256 integrity checks required by
-- docs/certificate-format-v2.md (trailer payload_sha256, sec.3.5; v2p
-- section_sha256, sec.9.3) are skipped: this GHC package db (checked via
-- `ghc-pkg list`) has neither cryptohash-sha256 nor SHA, and shelling out
-- was explicitly disallowed. Every other integrity check is enforced --
-- see Decode2's module header for the exact list.
warnSkippedShaChecks :: IO ()
warnSkippedShaChecks = hPutStrLn stderr
  "warning: no SHA-256 library in this GHC package db -- skipping trailer payload_sha256 (sec.3.5) and v2p section_sha256 (sec.9.3) checks; all other integrity checks (magic, format_version/flags, header_hash/FNV1a64, length/offset/contiguity, end_magic, prefix section structure and permutation checks) are enforced"

rejectExit1 :: String -> IO a
rejectExit1 msg = do
  hPutStrLn stderr ("REJECT: " ++ msg)
  exitFailure

-- | Run an IO action that produces a String, forcing it fully (so that any
-- exception raised anywhere during decode/translate/check -- including deep
-- inside the lazily-evaluated verified checker's traversal of the proof --
-- is caught here rather than escaping past this frame) and returning
-- Left on failure.
runFully :: IO String -> IO (Either SomeException String)
runFully act = try $ do
  s <- act
  _ <- evaluate (length s)
  return s

runV :: FilePath -> IO ()
runV path = do
  proofData <- B.readFile path
  containerResult <- try (evaluate (detectContainer proofData)) :: IO (Either SomeException Container)
  case containerResult of
    Left e -> rejectExit1 (displayException e)
    Right V2P -> do
      hPutStrLn stderr
        "REJECT: prefix-rooted certificate (v2p): use -p, not -v -- a prefix claim must never be printed as a full-problem bound"
      exitWith (ExitFailure 2)
    Right _ -> do
      warnSkippedShaChecks
      r <- runFully $ do
        let steps       = proofSteps2 proofData
            vcSteps      = translateProofSteps steps
            resultMaybe :: Maybe (Integer, Integer)
            resultMaybe = do
              (width, bnd) <- VP.check_proof_get_bound vcSteps
              return (VP.integer_of_int width, VP.integer_of_int bnd)
        return (show resultMaybe)
      case r of
        Left e  -> rejectExit1 (displayException e)
        Right s -> putStrLn s

runP :: FilePath -> IO ()
runP path = do
  proofData <- B.readFile path
  containerResult <- try (evaluate (detectContainer proofData)) :: IO (Either SomeException Container)
  case containerResult of
    Left e -> rejectExit1 (displayException e)
    Right c | c /= V2P -> do
      hPutStrLn stderr "REJECT: not a prefix-rooted (v2p) certificate -- use -v for v1/v2 files"
      exitWith (ExitFailure 2)
    Right _ -> do
      warnSkippedShaChecks
      r <- runFully $ do
        let pr    = prefixRoot proofData
            steps = proofSteps2 proofData
            vcSteps = translateProofSteps steps
            n     = prChannels pr
            claimed = toInteger (prClaimedBound pr)
            prefixStr = formatPrefix (prPrefix pr)
            -- THE SWAP BELOW IS CRITICAL AND DELIBERATE. The v2p prefix
            -- section stores each comparator as (a,b) meaning "channel a
            -- receives the pairwise MAXIMUM, channel b the pairwise
            -- MINIMUM" (docs/certificate-format-v2.md sec.9.3). Isabelle's
            -- apply_cmp (i,j) sends i to the MINIMUM and j to the MAXIMUM
            -- (see apply_cmp_list in Verified/PrefixChecker.hs). So every
            -- stored (a,b) must be passed to the verified checker as (b,a).
            pairs :: [(VP.Nat, VP.Nat)]
            pairs =
              [ (VP.nat_of_integer (toInteger b), VP.nat_of_integer (toInteger a))
              | (a, b) <- prPrefix pr
              ]
            witness = VP.ProofWitness
              (VP.Int_of_integer (prWitnessStep pr))
              (prInvert pr)
              (map (VP.Int_of_integer . toInteger) (prPerm pr))
            resultMaybe :: Maybe VP.Nat
            resultMaybe = VP.check_prefix_proof_get_bound
              vcSteps
              (VP.nat_of_integer (toInteger n))
              pairs
              (Just witness)
            -- Tag the outcome in the forced string itself so the outer
            -- IO code (after runFully has caught any exception from the
            -- traversal above) only has to dispatch on plain text, never
            -- re-run any of the checking logic.
            outcome = case resultMaybe of
              Nothing -> "NONE"
              Just kNat ->
                let k = VP.integer_of_nat kNat
                    okLine =
                      "OK verified prefix n=" ++ show n
                        ++ " L=" ++ show (length (prPrefix pr))
                        ++ " prefix=" ++ prefixStr
                        ++ " bound=" ++ show k
                        ++ " claimed=" ++ show claimed
                in  if k >= claimed
                      then "OK\n" ++ okLine
                      else "BELOW\n" ++ show k ++ "\n" ++ show claimed
        return outcome
      case r of
        Left e  -> rejectExit1 (displayException e)
        Right s -> case lines s of
          ("NONE" : _) -> do
            hPutStrLn stderr "REJECT: verified checker rejected the certificate"
            exitFailure
          ("OK" : okLine : _) -> do
            putStrLn okLine
            exitSuccess
          ("BELOW" : kStr : claimedStr : _) -> do
            hPutStrLn stderr
              ("REJECT: verified bound " ++ kStr ++ " is below the claimed bound " ++ claimedStr)
            exitFailure
          _ -> rejectExit1 ("internal error: unexpected outcome rendering: " ++ s)

formatPrefix :: [(Int, Int)] -> String
formatPrefix [] = "<empty>"
formatPrefix ps = intercalate "," [ show a ++ "-" ++ show b | (a, b) <- ps ]
