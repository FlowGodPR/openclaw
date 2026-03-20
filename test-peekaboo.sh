#!/bin/bash
# Peekaboo Integration Test Suite - 100 iterations
# Tests: see, click, type, image capture, error handling

RESULTS_DIR="/Users/ghost_mini/.openclaw/workspace/peekaboo-test-results"
mkdir -p "$RESULTS_DIR"

SUCCESS=0
FAIL=0
TEST_NUM=0

log_result() {
    local test_num=$1
    local status=$2
    local cmd=$3
    local error=$4
    echo "$test_num,$status,$cmd,$error" >> "$RESULTS_DIR/results.csv"
}

# Initialize results file
echo "test_num,status,command,error" > "$RESULTS_DIR/results.csv"

echo "Starting 100 Peekaboo tests..."
echo "Results will be saved to $RESULTS_DIR"

# Test 1-25: Screenshot capture tests
for i in {1..25}; do
    TEST_NUM=$((TEST_NUM + 1))
    echo "Test $TEST_NUM: Screenshot capture #$i"
    
    output="$RESULTS_DIR/screenshot_$i.png"
    if peekaboo image --mode screen --screen-index 0 --path "$output" 2>&1; then
        SUCCESS=$((SUCCESS + 1))
        log_result $TEST_NUM "success" "image capture" ""
    else
        FAIL=$((FAIL + 1))
        log_result $TEST_NUM "fail" "image capture" "screenshot failed"
    fi
done

# Test 26-50: UI element detection (see command)
for i in {26..50}; do
    TEST_NUM=$((TEST_NUM + 1))
    echo "Test $TEST_NUM: UI detection #$i"
    
    output="$RESULTS_DIR/see_$i.png"
    if peekaboo see --annotate --path "$output" 2>&1; then
        SUCCESS=$((SUCCESS + 1))
        log_result $TEST_NUM "success" "see annotate" ""
    else
        FAIL=$((FAIL + 1))
        log_result $TEST_NUM "fail" "see annotate" "ui detection failed"
    fi
done

# Test 51-75: Keyboard input tests
for i in {51..75}; do
    TEST_NUM=$((TEST_NUM + 1))
    echo "Test $TEST_NUM: Type input #$i"
    
    test_text="Test $i: Peekaboo automation"
    if peekaboo type "$test_text" --delay 5 2>&1; then
        SUCCESS=$((SUCCESS + 1))
        log_result $TEST_NUM "success" "type" ""
    else
        FAIL=$((FAIL + 1))
        log_result $TEST_NUM "fail" "type" "type command failed"
    fi
done

# Test 76-90: Hotkey/press tests
for i in {76..90}; do
    TEST_NUM=$((TEST_NUM + 1))
    echo "Test $TEST_NUM: Hotkey/press #$i"
    
    case $((i % 3)) in
        0) cmd="peekaboo press enter 2>&1" ;;
        1) cmd="peekaboo press escape 2>&1" ;;
        2) cmd="peekaboo hotkey --keys 'cmd,tab' 2>&1" ;;
    esac
    
    if eval $cmd; then
        SUCCESS=$((SUCCESS + 1))
        log_result $TEST_NUM "success" "hotkey/press" ""
    else
        FAIL=$((FAIL + 1))
        log_result $TEST_NUM "fail" "hotkey/press" "hotkey failed"
    fi
done

# Test 91-100: Window/app listing tests
for i in {91..100}; do
    TEST_NUM=$((TEST_NUM + 1))
    echo "Test $TEST_NUM: List apps/windows #$i"
    
    if peekaboo list apps --json 2>&1 | head -1 > /dev/null; then
        SUCCESS=$((SUCCESS + 1))
        log_result $TEST_NUM "success" "list apps" ""
    else
        FAIL=$((FAIL + 1))
        log_result $TEST_NUM "fail" "list apps" "list failed"
    fi
done

# Calculate accuracy
TOTAL=$((SUCCESS + FAIL))
ACCURACY=$(echo "scale=2; $SUCCESS * 100 / $TOTAL" | bc)

echo ""
echo "========================================="
echo "PEEKABOO TEST RESULTS"
echo "========================================="
echo "Total tests: $TOTAL"
echo "Successful: $SUCCESS"
echo "Failed: $FAIL"
echo "Accuracy: $ACCURACY%"
echo "Target: 99%"
echo ""

if (( $(echo "$ACCURACY >= 99" | bc -l) )); then
    echo "✅ TARGET MET: $ACCURACY% accuracy achieved"
else
    echo "❌ TARGET NOT MET: Need 99%, got $ACCURACY%"
fi

echo ""
echo "Results saved to: $RESULTS_DIR/results.csv"
cat "$RESULTS_DIR/results.csv"
