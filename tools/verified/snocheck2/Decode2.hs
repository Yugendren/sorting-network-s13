{-# LANGUAGE BangPatterns #-}
-- | Decode2: reads the v1 (legacy), v2 (wide) and v2p (prefix-rooted)
-- certificate containers described in docs/certificate-format-v2.md
-- sections 2, 3 and 9. This is UNVERIFIED glue: it performs the cheap
-- structural/integrity checks the spec marks as MUST, then hands step
-- payloads to Verified.PrefixChecker (via Translate2) for the checks that
-- actually establish the proof's correctness.
--
-- Mirrors tools/cert_v2.py's parsing (that script is the tested reference
-- implementation this module is built against) and, for the v1 container,
-- checker/snocheck/src/Decode.hs (the frozen reader).
--
-- SHA-256 NOTE: no SHA-256 library is present in the GHC package db this
-- binary is built against (checked: only `parallel` in the stack snapshot
-- db, and base/bytestring/containers/etc in the global db -- no
-- cryptohash-sha256, no SHA). Per the build instructions, the two SHA-256
-- checks required by the spec (trailer `payload_sha256`, v2p section
-- `section_sha256`) are therefore SKIPPED here; every other integrity check
-- in sections 2/3/9 (magic, format_version/flags, header_hash via FNV1a64,
-- length/offset/contiguity checks, end_magic, prefix section structure and
-- permutation checks) is fully enforced. Main.hs prints a one-line warning
-- to stderr identifying exactly what is skipped.
module Decode2
  ( Container(..)
  , PrefixRoot(..)
  , detectContainer
  , proofSteps2
  , prefixRoot
  ) where

import           Data.Bits
import           Data.List                      ( sort )
import           Data.Word
import           Data.ByteString                ( ByteString )
import qualified Data.ByteString               as B
import qualified Data.ByteString.Char8         as BC

import           VectSet                        ( VectSet )
import qualified VectSet                       as VS
import           ProofStep

-- --------------------------------------------------------------------------
-- container tag and prefix-root record (public API)
-- --------------------------------------------------------------------------

data Container = V1 | V2 | V2P deriving (Show, Eq)

-- | The prefix root of a v2p certificate, in the STORED engine convention:
-- 'prPrefix' pairs are (a,b) meaning "a receives the pairwise maximum, b the
-- pairwise minimum" (sec.9.3). Callers that feed this into
-- 'Verified.PrefixChecker.check_prefix_proof_get_bound' MUST swap each pair
-- to (b,a) -- see the comment at the call site in Main.hs.
data PrefixRoot = PrefixRoot
  { prChannels      :: !Int
  , prPrefix        :: ![(Int, Int)]
  , prClaimedBound  :: !Int
  , prInvert        :: !Bool
  , prPerm          :: ![Int]
  , prWitnessStep   :: !Integer
  } deriving (Show)

-- --------------------------------------------------------------------------
-- primitive readers
-- --------------------------------------------------------------------------

magicV2, endMagicV2, sectionMagicV2P :: ByteString
magicV2 = BC.pack "SNOCERT2"
endMagicV2 = BC.pack "SNOCEND2"
sectionMagicV2P = BC.pack "SNPX"

-- | Read `len` little-endian bytes starting at absolute offset `off` as a
-- (non-negative, machine-word-sized) Int. Used for offsets/lengths/counts,
-- all of which fit comfortably in a 64-bit signed Int for any file this
-- checker will ever see.
readLEInt :: Int -> ByteString -> Int -> Int
readLEInt len bs off = sum
  [ fromIntegral (B.index bs (off + i)) `shiftL` (8 * i) | i <- [0 .. len - 1] ]

u16At, u32At, u64At :: ByteString -> Int -> Int
u16At = readLEInt 2
u32At = readLEInt 4
u64At = readLEInt 8

-- | Read a full 64-bit little-endian value as an honest Word64 (used only
-- where the field is a hash/bit-pattern rather than a size, so the sign bit
-- must not be reinterpreted).
readLEWord64 :: ByteString -> Int -> Word64
readLEWord64 bs off = foldl step 0 [0 .. 7]
  where step acc i = acc .|. (fromIntegral (B.index bs (off + i)) `shiftL` (8 * i))

fnvOffsetBasis, fnvPrime :: Word64
fnvOffsetBasis = 0xcbf29ce484222325
fnvPrime = 0x00000100000001b3

fnv1a64 :: ByteString -> Word64
fnv1a64 = B.foldl' step fnvOffsetBasis
  where step h b = (h `xor` fromIntegral b) * fnvPrime

packedLen :: Int -> Int
packedLen c = bit (0 `max` (c - 3))

-- --------------------------------------------------------------------------
-- Either-based validation plumbing (unwrapped to `error` at the public API
-- boundary; Main.hs catches the resulting exceptions and prints "REJECT: ").
-- --------------------------------------------------------------------------

type Result a = Either String a

check :: String -> Bool -> Result ()
check msg cond = if cond then Right () else Left msg

-- --------------------------------------------------------------------------
-- step payload decode, shared by v1/v2/v2p (only the witness id width
-- differs). Mirrors checker/snocheck/src/Decode.hs's decodeProofStep /
-- decodeWitnesses.
-- --------------------------------------------------------------------------

decodeProofStep :: Int -> ByteString -> ProofStep
decodeProofStep idSize stepData = ProofStep { vectSet   = vs
                                             , bound     = bnd
                                             , witnesses = ws
                                             }
 where
  channels          = fromIntegral (B.index stepData 0)
  bnd               = fromIntegral (B.index stepData 1)
  encodedSetLength  = packedLen channels
  encodedSetBytes   = B.take encodedSetLength (B.drop 2 stepData)
  vs                = VS.fromBytes channels encodedSetBytes
  witnessData       = B.drop (encodedSetLength + 2) stepData
  (witnessType, witnessChannels) = case B.index witnessData 0 of
    0 -> (Huffman False, channels - 1)
    1 -> (Huffman True, channels - 1)
    2 -> (Successors, channels)
    _ -> errorWithoutStackTrace "invalid witness kind byte"
  ws = witnessType . decodeWitnesses idSize witnessChannels $ B.drop 1 witnessData

decodeWitnesses :: Int -> Int -> ByteString -> [Maybe Witness]
decodeWitnesses idSize channels bs = case B.uncons bs of
  Nothing        -> []
  Just (0, tail') -> decodeWitness False tail'
  Just (1, tail') -> decodeWitness True tail'
  Just (2, tail') -> (Nothing :) $! decodeWitnesses idSize channels tail'
  Just (_, _)     -> errorWithoutStackTrace "invalid witness tag byte"
 where
  decodeWitness inv bs' =
    let (permBytes, tail') = B.splitAt channels bs'
    in  ((  Just
         $! (Witness { invert = inv
                     , perm   = map fromIntegral . B.unpack $ permBytes
                     , stepId = readLEInt idSize tail' 0
                     }
            )
         ) :
        )
          $! decodeWitnesses idSize channels (B.drop idSize tail')

-- --------------------------------------------------------------------------
-- v1 container (sec.2). Direct mirror of Decode.hs; the frozen reader
-- performs no integrity checks beyond ByteString bounds, and this doesn't
-- either -- any malformed v1 file surfaces as a runtime exception that
-- Main.hs's broad exception handler turns into a REJECT.
-- --------------------------------------------------------------------------

parseV1 :: ByteString -> (Int, Int -> ByteString)
parseV1 bs = (stepCount, stepData)
 where
  stepCount = u32At bs 0
  stepData step =
    let entryOff = 4 + 12 * step
        off      = u64At bs entryOff
        len_     = u32At bs (entryOff + 8)
    in  B.take len_ (B.drop off bs)

-- --------------------------------------------------------------------------
-- v2p prefix-root section (sec.9.3), checks P1 (structure) of sec.9.4.
-- section_sha256 (P2) is intentionally NOT checked here -- see module note.
-- --------------------------------------------------------------------------

data PrefixSection = PrefixSection
  { psChannels        :: !Int
  , psPrefixLen        :: !Int
  , psClaimedBound     :: !Int
  , psRootInvert       :: !Bool
  , psRootPerm         :: ![Int]
  , psRootWitnessStep  :: !Integer
  , psPrefix           :: ![(Int, Int)]
  , psSectionBytes     :: !Int  -- prefix_bytes = 64 + 2*L + n + packed_len(n)
  }

parsePrefixSection :: ByteString -> Result PrefixSection
parsePrefixSection bs = do
  let nTotal = B.length bs
      base   = 64
  check "file too short for prefix section header" (nTotal >= base + 32)
  check "bad prefix section magic" (B.take 4 (B.drop base bs) == sectionMagicV2P)
  let sectionVersion = u32At bs (base + 4)
  check "unsupported prefix section_version" (sectionVersion == 1)
  let channels = u16At bs (base + 8)
  check "prefix section channels out of range" (channels >= 1 && channels <= 255)
  let prefixLen         = u16At bs (base + 10)
      claimedBound       = u16At bs (base + 12)
      rootInvertByte     = B.index bs (base + 14)
  check "root_invert must be 0 or 1" (rootInvertByte == 0 || rootInvertByte == 1)
  let rootInvert  = rootInvertByte == 1
      rootPermLen = fromIntegral (B.index bs (base + 15)) :: Int
  check "root_perm_len does not match channels" (rootPermLen == channels)
  let rootWitnessStep    = toInteger (readLEWord64 bs (base + 16))
      rootPackedLenField = u32At bs (base + 24)
      expectedPackedLen  = packedLen channels
  check "root_packed_len does not match packed_len(channels)"
        (rootPackedLenField == expectedPackedLen)
  let reserved = u32At bs (base + 28)
  check "prefix section reserved field must be zero" (reserved == 0)
  let prefixOff   = base + 32
      permOff     = prefixOff + 2 * prefixLen
      packedOff   = permOff + channels
      shaOff      = packedOff + expectedPackedLen
      prefixBytes = (shaOff + 32) - base
  check "prefix section extends past end of file" (shaOff + 32 <= nTotal)
  let prefixList =
        [ (a, b)
        | k <- [0 .. prefixLen - 1]
        , let a = fromIntegral (B.index bs (prefixOff + 2 * k)) :: Int
        , let b = fromIntegral (B.index bs (prefixOff + 2 * k + 1)) :: Int
        ]
  mapM_
    (\(k, (a, b)) ->
      check
        ("prefix comparator " ++ show (k :: Int) ++ ": channel out of range or a == b")
        (a < channels && b < channels && a /= b)
    )
    (zip [0 ..] prefixList)
  let rootPerm = [ fromIntegral (B.index bs (permOff + i)) :: Int | i <- [0 .. channels - 1] ]
  check "root_perm is not a permutation" (sort rootPerm == [0 .. channels - 1])
  -- section_sha256 (bytes[64..shaOff]) intentionally not verified: no
  -- SHA-256 library available. See module-header note.
  return PrefixSection
    { psChannels       = channels
    , psPrefixLen      = prefixLen
    , psClaimedBound   = claimedBound
    , psRootInvert     = rootInvert
    , psRootPerm       = rootPerm
    , psRootWitnessStep = rootWitnessStep
    , psPrefix         = prefixList
    , psSectionBytes   = prefixBytes
    }

-- --------------------------------------------------------------------------
-- v2 / v2p container (sec.3, sec.9.2). Both share this parser; v2p differs
-- only in table_offset (shifted past the prefix section) and flags.
-- --------------------------------------------------------------------------

data V2Parsed = V2Parsed
  { v2Container      :: !Container
  , v2StepCount      :: !Int
  , v2GetPayload     :: Int -> ByteString
  , v2PrefixSection  :: !(Maybe PrefixSection)
  }

-- | Contiguity/bounds validation of the step table (sec.3.3 MUSTs), shared
-- by v2 and v2p (only the table's start offset differs).
validateTable :: ByteString -> Int -> Int -> Int -> Int -> Result ()
validateTable bs tableOffset payloadOffset payloadBytes stepCount = loop 0 payloadOffset
 where
  endOfPayload = payloadOffset + payloadBytes
  loop !i !prevEnd
    | i >= stepCount =
        if prevEnd == endOfPayload
          then Right ()
          else Left "step table does not cover exact payload region"
    | otherwise =
        let entryOff = tableOffset + 16 * i
            off      = u64At bs entryOff
            len_     = u64At bs (entryOff + 8)
        in  if len_ < 4
              then Left ("step table entry " ++ show i ++ ": payload length too short")
              else if not (payloadOffset <= off && off + len_ <= endOfPayload)
                then Left ("step table entry " ++ show i ++ ": out of payload bounds")
                else if off /= prevEnd
                  then Left ("step table entry " ++ show i ++ ": not contiguous")
                  else loop (i + 1) (off + len_)

parseV2Container :: ByteString -> Result V2Parsed
parseV2Container bs = do
  let n = B.length bs
  check "file too short for v2 header" (n >= 64)
  check "bad v2 magic" (B.take 8 bs == magicV2)
  let formatVersion = u32At bs 8
  (container, expectedFlags) <- case formatVersion of
    2 -> Right (V2, 0 :: Int)
    3 -> Right (V2P, 1 :: Int)
    _ -> Left "unsupported format_version"
  let flags = u32At bs 12
  check ("flags must be " ++ show expectedFlags ++ " for " ++ show container)
        (flags == expectedFlags)
  let stepCount = u64At bs 16
  check "step_count must be at least 1" (stepCount >= 1)
  (tableOffset, mPrefixSection) <- case container of
    V2P -> do
      ps <- parsePrefixSection bs
      let pb                  = psSectionBytes ps
          computedTableOffset = 64 + pb
          headerTableOffset   = u64At bs 24
      check "table_offset inconsistent with prefix_bytes" (headerTableOffset == computedTableOffset)
      return (computedTableOffset, Just ps)
    _ -> do
      let t = u64At bs 24
      check "table_offset must be 64" (t == 64)
      return (t, Nothing)
  let payloadOffset = u64At bs 32
  check "payload_offset inconsistent with step_count"
        (payloadOffset == tableOffset + 16 * stepCount)
  let payloadBytes  = u64At bs 40
      rootChannels  = u16At bs 48
      rootBound     = u16At bs 50
      reserved      = u32At bs 52
  check "reserved header field must be zero" (reserved == 0)
  let headerHash = readLEWord64 bs 56
  check "header hash mismatch" (headerHash == fnv1a64 (B.take 56 bs))
  let expectedTotal = tableOffset + 16 * stepCount + payloadBytes + 40
  check "unexpected file length" (n == expectedTotal)
  validateTable bs tableOffset payloadOffset payloadBytes stepCount
  let trailerOff = payloadOffset + payloadBytes
  check "end magic mismatch" (B.take 8 (B.drop (trailerOff + 32) bs) == endMagicV2)
  -- payload_sha256 (trailer bytes[0..32)) intentionally not verified: no
  -- SHA-256 library available. See module-header note.
  let getPayload i =
        let entryOff = tableOffset + 16 * i
            off      = u64At bs entryOff
            len_     = u64At bs (entryOff + 8)
        in  B.take len_ (B.drop off bs)
  -- root_channels / root_bound are a mirror of the decoded last step
  -- (sec.3.2); a reader MUST verify and reject on mismatch.
  let lastParsed = decodeProofStep 8 (getPayload (stepCount - 1))
  check "root fields do not match decoded last step"
        (VS.channels (vectSet lastParsed) == rootChannels && bound lastParsed == rootBound)
  return V2Parsed
    { v2Container     = container
    , v2StepCount     = stepCount
    , v2GetPayload    = getPayload
    , v2PrefixSection = mPrefixSection
    }

-- --------------------------------------------------------------------------
-- public API
-- --------------------------------------------------------------------------

-- | Dispatch on the 8-byte magic and, if present, format_version (sec.4,
-- sec.9.2): "SNOCERT2" + format_version 2 is v2, "SNOCERT2" + format_version
-- 3 is v2p, anything else is v1.
detectContainer :: ByteString -> Container
detectContainer bs
  | B.length bs < 8 || B.take 8 bs /= magicV2 = V1
  | otherwise = either errorWithoutStackTrace id $ do
      check "file too short for v2 header" (B.length bs >= 12)
      case u32At bs 8 of
        2 -> Right V2
        3 -> Right V2P
        _ -> Left "unsupported format_version"

-- | (step_count, step lookup) for whichever container the bytes are in.
-- Works for v1, v2 and v2p (v2p is included for completeness/symmetry with
-- the container's own step table; callers wanting the prefix claim must
-- also call 'prefixRoot').
proofSteps2 :: ByteString -> (Int, Int -> ProofStep)
proofSteps2 bs = case detectContainer bs of
  V1 ->
    let (stepCount, getPayload) = parseV1 bs
    in  (stepCount, decodeProofStep 4 . getPayload)
  _ ->
    let v2p = either errorWithoutStackTrace id (parseV2Container bs)
    in  (v2StepCount v2p, decodeProofStep 8 . v2GetPayload v2p)

-- | The prefix root of a v2p file (sec.9.3/9.4 P1). Errors (via 'error') on
-- any other container.
prefixRoot :: ByteString -> PrefixRoot
prefixRoot bs = either errorWithoutStackTrace id $ do
  v2p <- parseV2Container bs
  check "not a prefix-rooted (v2p) certificate" (v2Container v2p == V2P)
  case v2PrefixSection v2p of
    Nothing -> Left "not a prefix-rooted (v2p) certificate"
    Just ps -> Right PrefixRoot
      { prChannels     = psChannels ps
      , prPrefix       = psPrefix ps
      , prClaimedBound = psClaimedBound ps
      , prInvert       = psRootInvert ps
      , prPerm         = psRootPerm ps
      , prWitnessStep  = psRootWitnessStep ps
      }
