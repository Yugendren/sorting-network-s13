// Verifier B independently parses candidates and checks bit-parallel truth tables.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"math/bits"
	"os"
	"sort"
	"strconv"
	"strings"
	"unicode/utf8"
)

var truthLabels = map[string]bool{
	"PUBLISHED": true, "ARTIFACT_VERIFIED": true, "LOCALLY_REPRODUCED": true,
	"MEASURED": true, "ASSUMED": true, "UNKNOWN": true,
}

type comparator struct {
	lower int
	upper int
	layer *int
}

type candidate struct {
	channels       int
	declaredCount  int
	layerCount     *int
	source         string
	truthLabel     string
	comparators    []comparator
	checksum       string
	artifactSHA256 string
}

type candidateError struct {
	code    string
	message string
}

func (err candidateError) Error() string { return err.message }

func fail(code, message string) error { return candidateError{code: code, message: message} }

func decimal(text, field string, positive bool) (int, error) {
	if text == "" {
		return 0, fail("MALFORMED_HEADER", field+" is not decimal")
	}
	for _, char := range text {
		if char < '0' || char > '9' {
			return 0, fail("MALFORMED_HEADER", field+" is not decimal")
		}
	}
	value, err := strconv.Atoi(text)
	if err != nil || (positive && value == 0) {
		return 0, fail("MALFORMED_HEADER", field+" has an invalid value")
	}
	return value, nil
}

func header(line, name string) (string, error) {
	prefix := name + " "
	if !strings.HasPrefix(line, prefix) || len(line) == len(prefix) {
		return "", fail("MALFORMED_HEADER", "missing or empty "+name+" header")
	}
	return line[len(prefix):], nil
}

func parseCandidate(path string, expectedChannels int) (candidate, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return candidate{}, fail("READ_ERROR", err.Error())
	}
	artifactHash := fmt.Sprintf("%x", sha256.Sum256(data))
	if len(data) == 0 || data[len(data)-1] != '\n' {
		return candidate{}, fail("MISSING_FINAL_NEWLINE", "artifact must end in one newline")
	}
	if !utf8.Valid(data) {
		return candidate{}, fail("INVALID_UTF8", "artifact is not valid UTF-8")
	}
	if strings.ContainsRune(string(data), '\r') {
		return candidate{}, fail("NON_CANONICAL_NEWLINE", "carriage returns are prohibited")
	}
	lines := strings.Split(string(data[:len(data)-1]), "\n")
	if len(lines) < 9 {
		return candidate{}, fail("MALFORMED_STRUCTURE", "missing required lines")
	}
	for _, line := range lines {
		if line == "" {
			return candidate{}, fail("MALFORMED_STRUCTURE", "blank lines are prohibited")
		}
	}
	if lines[0] != "sorting-network-v1" {
		return candidate{}, fail("WRONG_SCHEMA", "wrong schema line")
	}

	channelText, err := header(lines[1], "channels")
	if err != nil {
		return candidate{}, err
	}
	channels, err := decimal(channelText, "channels", true)
	if err != nil {
		return candidate{}, err
	}
	countText, err := header(lines[2], "declared_count")
	if err != nil {
		return candidate{}, err
	}
	declaredCount, err := decimal(countText, "declared_count", false)
	if err != nil {
		return candidate{}, err
	}
	layerText, err := header(lines[3], "layer_count")
	if err != nil {
		return candidate{}, err
	}
	var layerCount *int
	if layerText != "-" {
		value, parseErr := decimal(layerText, "layer_count", false)
		if parseErr != nil {
			return candidate{}, parseErr
		}
		layerCount = &value
	}
	source, err := header(lines[4], "source")
	if err != nil {
		return candidate{}, err
	}
	truthLabel, err := header(lines[5], "truth_label")
	if err != nil {
		return candidate{}, err
	}
	if !truthLabels[truthLabel] {
		return candidate{}, fail("BAD_TRUTH_LABEL", "unrecognized truth label")
	}
	if lines[6] != "comparators_begin" {
		return candidate{}, fail("MALFORMED_STRUCTURE", "missing comparators_begin")
	}
	if lines[len(lines)-2] != "comparators_end" {
		return candidate{}, fail("TRAILING_OR_MISSING_DATA", "comparators_end must precede checksum")
	}
	checksumParts := strings.Split(lines[len(lines)-1], " ")
	if len(checksumParts) != 2 || checksumParts[0] != "sha256" || len(checksumParts[1]) != 64 {
		return candidate{}, fail("MALFORMED_CHECKSUM", "checksum line is malformed")
	}
	checksumBytes, decodeErr := hex.DecodeString(checksumParts[1])
	if decodeErr != nil || len(checksumBytes) != 32 || strings.ToLower(checksumParts[1]) != checksumParts[1] {
		return candidate{}, fail("MALFORMED_CHECKSUM", "checksum must be lowercase hexadecimal")
	}
	signedPrefix := strings.Join(lines[:len(lines)-1], "\n") + "\n"
	actualChecksum := fmt.Sprintf("%x", sha256.Sum256([]byte(signedPrefix)))
	if actualChecksum != checksumParts[1] {
		return candidate{}, fail("CHECKSUM_MISMATCH", "candidate checksum does not match")
	}

	comparators := make([]comparator, 0, declaredCount)
	seenLayered, seenUnlayered := false, false
	priorLayer := -1
	usedByLayer := make(map[int]map[int]bool)
	for index, line := range lines[7 : len(lines)-2] {
		parts := strings.Split(line, " ")
		if len(parts) != 2 && len(parts) != 3 {
			return candidate{}, fail("MALFORMED_COMPARATOR", fmt.Sprintf("bad comparator at line %d", index+8))
		}
		lower, parseErr := decimal(parts[0], "lower", false)
		if parseErr != nil {
			return candidate{}, fail("MALFORMED_COMPARATOR", parseErr.Error())
		}
		upper, parseErr := decimal(parts[1], "upper", false)
		if parseErr != nil {
			return candidate{}, fail("MALFORMED_COMPARATOR", parseErr.Error())
		}
		if lower < 0 || lower >= upper || upper >= channels {
			return candidate{}, fail("INVALID_CHANNEL_PAIR", fmt.Sprintf("invalid comparator at line %d", index+8))
		}
		var layer *int
		if len(parts) == 3 {
			seenLayered = true
			value, layerErr := decimal(parts[2], "layer", false)
			if layerErr != nil {
				return candidate{}, fail("MALFORMED_COMPARATOR", layerErr.Error())
			}
			if layerCount == nil || value >= *layerCount || value < priorLayer {
				return candidate{}, fail("INVALID_LAYER", fmt.Sprintf("invalid layer at line %d", index+8))
			}
			priorLayer = value
			if usedByLayer[value] == nil {
				usedByLayer[value] = make(map[int]bool)
			}
			if usedByLayer[value][lower] || usedByLayer[value][upper] {
				return candidate{}, fail("LAYER_CONFLICT", fmt.Sprintf("channel reused in layer %d", value))
			}
			usedByLayer[value][lower], usedByLayer[value][upper] = true, true
			layer = &value
		} else {
			seenUnlayered = true
		}
		comparators = append(comparators, comparator{lower: lower, upper: upper, layer: layer})
	}
	if seenLayered && seenUnlayered {
		return candidate{}, fail("MIXED_LAYER_ANNOTATIONS", "layers must be present on all or no comparators")
	}
	if seenLayered != (layerCount != nil) {
		return candidate{}, fail("LAYER_HEADER_MISMATCH", "layer_count disagrees with comparator records")
	}
	if len(comparators) != declaredCount {
		return candidate{}, fail("COUNT_MISMATCH", "declared comparator count does not match records")
	}
	if expectedChannels >= 0 && channels != expectedChannels {
		return candidate{}, fail("WRONG_CHANNEL_COUNT", "candidate has the wrong number of channels")
	}
	return candidate{channels: channels, declaredCount: declaredCount, layerCount: layerCount,
		source: source, truthLabel: truthLabel, comparators: comparators,
		checksum: checksumParts[1], artifactSHA256: artifactHash}, nil
}

func duplicatePairs(value candidate) []string {
	counts := make(map[string]int)
	for _, comparator := range value.comparators {
		key := fmt.Sprintf("%d %d", comparator.lower, comparator.upper)
		counts[key]++
	}
	result := make([]string, 0)
	for key, count := range counts {
		if count > 1 {
			result = append(result, fmt.Sprintf("%s x%d", key, count))
		}
	}
	sort.Strings(result)
	return result
}

func verify(value candidate) (map[string]any, bool) {
	patterns := 1 << value.channels
	words := (patterns + 63) / 64
	wires := make([][]uint64, value.channels)
	for channel := 0; channel < value.channels; channel++ {
		wires[channel] = make([]uint64, words)
		for pattern := 0; pattern < patterns; pattern++ {
			if ((pattern >> channel) & 1) == 1 {
				wires[channel][pattern/64] |= uint64(1) << (pattern % 64)
			}
		}
	}
	for _, comparator := range value.comparators {
		lowerWire, upperWire := wires[comparator.lower], wires[comparator.upper]
		for word := 0; word < words; word++ {
			lower, upper := lowerWire[word], upperWire[word]
			lowerWire[word] = lower & upper
			upperWire[word] = lower | upper
		}
	}
	bad := make([]uint64, words)
	for channel := 0; channel+1 < value.channels; channel++ {
		for word := 0; word < words; word++ {
			bad[word] |= wires[channel][word] &^ wires[channel+1][word]
		}
	}
	failingCount, first := 0, -1
	for word, mask := range bad {
		failingCount += bits.OnesCount64(mask)
		if first < 0 && mask != 0 {
			first = word*64 + bits.TrailingZeros64(mask)
		}
	}
	base := map[string]any{
		"artifact_sha256":       value.artifactSHA256,
		"candidate_checksum":    value.checksum,
		"channels":              value.channels,
		"comparators":           value.declaredCount,
		"duplicate_comparators": duplicatePairs(value),
		"implementation":        "verifier-b-go-bitparallel-v1",
	}
	if first < 0 {
		base["counterexample"] = nil
		base["failing_input_count"] = 0
		base["verdict"] = "ACCEPT"
		return base, true
	}
	inputBits := make([]byte, value.channels)
	outputBits := make([]byte, value.channels)
	for channel := 0; channel < value.channels; channel++ {
		inputBits[channel] = byte('0' + ((first >> channel) & 1))
		outputBits[channel] = '0'
		if (wires[channel][first/64] & (uint64(1) << (first % 64))) != 0 {
			outputBits[channel] = '1'
		}
	}
	base["counterexample"] = map[string]any{
		"input_bits": string(inputBits), "input_integer": first, "output_bits": string(outputBits),
	}
	base["failing_input_count"] = failingCount
	base["verdict"] = "INVALID"
	return base, false
}

func emit(report map[string]any) {
	encoded, _ := json.Marshal(report)
	fmt.Println(string(encoded))
}

func main() {
	expectedChannels := flag.Int("expected-channels", -1, "required channel count")
	flag.Parse()
	if flag.NArg() != 1 {
		emit(map[string]any{"artifact_sha256": nil, "error": "one candidate path is required",
			"error_code": "ARGUMENT_ERROR", "implementation": "verifier-b-go-bitparallel-v1", "verdict": "MALFORMED"})
		os.Exit(2)
	}
	path := flag.Arg(0)
	value, err := parseCandidate(path, *expectedChannels)
	if err != nil {
		var artifact any = nil
		if data, readErr := os.ReadFile(path); readErr == nil {
			artifact = fmt.Sprintf("%x", sha256.Sum256(data))
		}
		candidateErr, ok := err.(candidateError)
		code := "PARSE_ERROR"
		if ok {
			code = candidateErr.code
		}
		emit(map[string]any{"artifact_sha256": artifact, "error": err.Error(), "error_code": code,
			"implementation": "verifier-b-go-bitparallel-v1", "verdict": "MALFORMED"})
		os.Exit(2)
	}
	report, accepted := verify(value)
	emit(report)
	if !accepted {
		os.Exit(1)
	}
}
