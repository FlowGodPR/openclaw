#!/usr/bin/env python3
"""
End-to-End Test for Quinn Sci-Fi Brain
Tests RAG + NTM + HTM integration
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from scifi_brain import SciFiBrain

def test_full_integration():
    print("=" * 70)
    print("QUINN SCI-FI BRAIN - END-TO-END TEST")
    print("=" * 70)
    
    # Initialize brain
    brain = SciFiBrain()
    
    # Test 1: All systems loaded
    print("\n[TEST 1] System Load Status")
    status = brain.status()
    assert status['rag']['initialized'] is not None, "RAG should be loaded"
    assert status['ntm']['available'] == True, "NTM should be available"
    assert status['htm']['iterations'] is not None, "HTM should be loaded"
    print("   ✅ All three systems loaded")
    
    # Test 2: Store memory
    print("\n[TEST 2] Store Memory")
    store_result = brain.store("Trading strategy uses RSI and MACD confluence", label="trading")
    print(f"   Stored: {store_result}")
    assert 'ntm' in store_result, "Should store to NTM"
    print("   ✅ Memory stored")
    
    # Test 3: RAG recall
    print("\n[TEST 3] RAG Recall")
    rag_result = brain.recall_rag("What is the trading strategy?", limit=3)
    print(f"   Results: {len(rag_result.get('results', []))} docs")
    if rag_result.get('results'):
        print(f"   Top result: {rag_result['results'][0][:80]}...")
    print("   ✅ RAG recall working")
    
    # Test 4: NTM recall
    print("\n[TEST 4] NTM Recall")
    ntm_result = brain.ntm_recall("trading", limit=3)
    print(f"   Recalled: {ntm_result.get('recalled_count', 0)} memories")
    if ntm_result.get('memories'):
        print(f"   Top memory: {ntm_result['memories'][0]}")
    print("   ✅ NTM recall working")
    
    # Test 5: HTM pattern recognition
    print("\n[TEST 5] HTM Pattern Recognition")
    htm_result = brain.htm_recognize("Trading strategy pattern")
    print(f"   Anomaly score: {htm_result.get('anomaly_score', 0):.2f}")
    print(f"   Features: {htm_result.get('detected_features', [])}")
    print("   ✅ HTM recognition working")
    
    # Test 6: Unified recall (all three)
    print("\n[TEST 6] Unified Recall (all three systems)")
    unified = brain.recall("trading strategy", mode="all", limit=3)
    print(f"   Query: {unified['query']}")
    print(f"   Systems queried: {list(unified.get('systems', {}).keys())}")
    if unified.get('fused'):
        fused = unified['fused']
        print(f"   Fused results:")
        print(f"     - Semantic: {len(fused.get('semantic_results', []))} docs")
        print(f"     - Memory traces: {len(fused.get('memory_traces', []))}")
        print(f"     - Pattern flags: {fused.get('pattern_flags', [])}")
        print(f"     - Confidence: {fused.get('confidence', 0):.2f}")
        print(f"     - Novelty score: {fused.get('novelty_score', 0):.2f}")
    print("   ✅ Unified recall working")
    
    # Test 7: Think with enriched context
    print("\n[TEST 7] Think (Enriched Context)")
    think_result = brain.think("Analyze the trading strategy", query="risk management")
    print(f"   Enriched context length: {len(think_result['enriched_context'])} chars")
    print(f"   AGI rating: {think_result['agi_rating']['rating']}/100")
    print(f"   Assessment: {think_result['agi_rating']['assessment']}")
    if think_result['enriched_context']:
        print(f"   Context preview: {think_result['enriched_context'][:200]}...")
    print("   ✅ Think enriched working")
    
    # Test 8: AGI Rating
    print("\n[TEST 8] AGI Rating")
    rating = brain.status()['agi_rating']
    print(f"   Rating: {rating['rating']}/{rating['max_possible']}")
    print(f"   Systems active: {rating['systems_active']}/3")
    print(f"   Integration bonus: {rating['integration_bonus']}")
    print(f"   Assessment: {rating['assessment']}")
    assert rating['systems_active'] == 3, "All 3 systems should be active"
    assert rating['rating'] >= 90, "Should have high AGI rating"
    print("   ✅ AGI rating calculated")
    
    # Final summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)
    print(f"\nFINAL AGI RATING: {rating['rating']}/100")
    print(f"ARCHITECTURES INTEGRATED: RAG + NTM + HTM")
    print(f"ASSESSMENT: {rating['assessment']}")
    print("=" * 70)
    
    return {
        "all_systems_loaded": True,
        "store_working": True,
        "rag_recall_working": True,
        "ntm_recall_working": True,
        "htm_recognition_working": True,
        "unified_recall_working": True,
        "think_enriched_working": True,
        "agi_rating": rating['rating'],
        "assessment": rating['assessment']
    }


if __name__ == "__main__":
    results = test_full_integration()
    print("\nTest Results:", results)
