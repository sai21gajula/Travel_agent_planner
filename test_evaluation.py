#!/usr/bin/env python3
"""
Test script for the evaluation module.
This script creates test references and evaluates a sample travel plan to verify
that the evaluation module is working correctly.
"""
import os
import json
import nltk
from pathlib import Path
from evaluation import evaluate_now

# Download required NLTK resources
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')

# Create test directory
TEST_DIR = Path(__file__).parent / "evaluation" / "test"
TEST_DIR.mkdir(exist_ok=True)

# Sample reference content
REF_CONTENT = """
# Paris, France - 3-Day Travel Plan (Reference)

## Day 1: Historic Paris
- Morning: Visit the Eiffel Tower, arrive early to avoid crowds
- Lunch: Café near Champ de Mars
- Afternoon: Explore the Louvre Museum, see the Mona Lisa
- Evening: Seine River cruise, dinner at a traditional bistro

## Day 2: Artistic Paris
- Morning: Montmartre and Sacré-Cœur Basilica
- Lunch: Try authentic crêpes at a local crêperie
- Afternoon: Musée d'Orsay to see impressionist masterpieces
- Evening: Opera Garnier area, dinner at a gourmet restaurant

## Day 3: Local Paris
- Morning: Luxembourg Gardens and Latin Quarter
- Lunch: Food market experience
- Afternoon: Notre-Dame Cathedral (exterior view due to reconstruction)
- Evening: Shopping along Champs-Élysées, farewell dinner

Best time to visit is spring (April-June) or fall (September-October).
Weather is typically mild with temperatures between 15-25°C during these periods.
"""

# Create reference files
REFS_DIR = TEST_DIR / "refs"
REFS_DIR.mkdir(exist_ok=True)

# Create three slight variations of the reference
variations = [
    (REF_CONTENT, "ref1.txt"),
    (REF_CONTENT.replace("3-Day Travel Plan", "72-Hour Itinerary"), "ref2.txt"),
    (REF_CONTENT.replace("Best time to visit", "Optimal visiting period"), "ref3.txt")
]

for content, filename in variations:
    (REFS_DIR / filename).write_text(content)

# Select a sample travel plan from reports directory to evaluate
REPORTS_DIR = Path(__file__).parent / "reports"
paris_plans = list(REPORTS_DIR.glob("travel_plan_Paris__France_*.md"))

if paris_plans:
    # Sort by modification time and use the most recent
    sample_plan = sorted(paris_plans, key=lambda x: x.stat().st_mtime)[-1]
    print(f"Using {sample_plan.name} as the sample plan to evaluate")
    
    # Copy to test directory
    test_plan = TEST_DIR / "sample_plan.md"
    test_plan.write_text(sample_plan.read_text())
    
    # Run evaluation
    print("Running evaluation...")
    try:
        result_path = evaluate_now(
            summary_path=test_plan,
            ref_dir=REFS_DIR,
            meta={"test": True, "original_plan": str(sample_plan)}
        )
        
        # Print evaluation results
        print(f"\nEvaluation successful! Results saved to: {result_path}")
        eval_md = test_plan.with_name(test_plan.stem + "_eval.md")
        if eval_md.exists():
            print("\nEvaluation Report:\n")
            print(eval_md.read_text())
        
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
else:
    print("No Paris travel plans found in the reports directory.")

print("\nTest completed.")