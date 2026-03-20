#!/bin/bash
# Peekaboo Production Verification Test - 10 iterations

PEEKABOO=/opt/homebrew/bin/peekaboo
RESULTS_FILE=/Users/ghost_mini/.openclaw/workspace/peekaboo_results.txt
SUCCESS_COUNT=0
TOTAL_TESTS=10

echo "=== PEEKABOO PRODUCTION VERIFICATION ===" > $RESULTS_FILE
echo "Started: $(date)" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

# Check permissions first
echo "1. PERMISSIONS CHECK:" >> $RESULTS_FILE
$PEEKABOO permissions 2>&1 >> $RESULTS_FILE
PERM_RESULT=$?
if [ $PERM_RESULT -eq 0 ]; then
    echo "   Permissions: OK" >> $RESULTS_FILE
else
    echo "   Permissions: FAILED (exit $PERM_RESULT)" >> $RESULTS_FILE
fi
echo "" >> $RESULTS_FILE

# Run 10 iterations
for i in {1..10}; do
    echo "=== ITERATION $i ===" >> $RESULTS_FILE
    
    # Test 1: Screenshot
    $PEEKABOO image --path /tmp/test_$i.png 2>&1
    IMG_RESULT=$?
    if [ $IMG_RESULT -eq 0 ]; then
        echo "   Screenshot: ✅ SUCCESS" >> $RESULTS_FILE
    else
        echo "   Screenshot: ❌ FAILED (exit $IMG_RESULT)" >> $RESULTS_FILE
    fi
    
    # Test 2: See (element detection)
    $PEEKABOO see --json 2>&1 | head -5 > /dev/null
    SEE_RESULT=$?
    if [ $SEE_RESULT -eq 0 ]; then
        echo "   Element Detection: ✅ SUCCESS" >> $RESULTS_FILE
    else
        echo "   Element Detection: ❌ FAILED (exit $SEE_RESULT)" >> $RESULTS_FILE
    fi
    
    # Test 3: Click
    $PEEKABOO click --on elem_9 2>&1 | grep -q "Click successful"
    CLICK_RESULT=$?
    if [ $CLICK_RESULT -eq 0 ]; then
        echo "   Click: ✅ SUCCESS" >> $RESULTS_FILE
        ((SUCCESS_COUNT++))
    else
        echo "   Click: ❌ FAILED" >> $RESULTS_FILE
    fi
    
    # Test 4: Type
    $PEEKABOO type "TEST_$i" 2>&1 | grep -q "Typing completed"
    TYPE_RESULT=$?
    if [ $TYPE_RESULT -eq 0 ]; then
        echo "   Type: ✅ SUCCESS" >> $RESULTS_FILE
        ((SUCCESS_COUNT++))
    else
        echo "   Type: ❌ FAILED" >> $RESULTS_FILE
    fi
    
    echo "" >> $RESULTS_FILE
    sleep 1
done

echo "=== SUMMARY ===" >> $RESULTS_FILE
echo "Completed: $(date)" >> $RESULTS_FILE
echo "Click successes: $SUCCESS_COUNT / $TOTAL_TESTS" >> $RESULTS_FILE
echo "Type successes: $((SUCCESS_COUNT)) / $TOTAL_TESTS" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE
cat $RESULTS_FILE
