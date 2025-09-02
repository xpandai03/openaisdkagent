import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.settings import settings
from app.startup.vectorstore_bootstrap import bootstrap_vector_store, get_test_queries


async def test_vector_store_creation():
    """Test vector store creation and persistence"""
    print("Testing vector store creation...")
    
    if not settings.has_openai:
        print("⚠️  No OpenAI API key - skipping vector store tests")
        return False
    
    # Check if already exists
    if settings.has_vector_store:
        print(f"✓ Vector store already exists: {settings.openai_vector_store_id}")
        return True
    
    # Try to create
    store_id = await bootstrap_vector_store()
    if store_id:
        print(f"✓ Vector store created: {store_id}")
        return True
    else:
        print("✗ Failed to create vector store")
        return False


async def test_filesearch_queries():
    """Test FileSearch with sample queries"""
    print("\nTesting FileSearch queries...")
    
    if not settings.has_openai or not settings.has_vector_store:
        print("⚠️  FileSearch not available - skipping query tests")
        return
    
    from app.agents import run_agent
    
    test_queries = get_test_queries()
    
    for query in test_queries[:2]:  # Test first 2 queries
        print(f"\nQuery: {query}")
        result = await run_agent(query)
        
        if result["mode"] == "error":
            print(f"  ✗ Error: {result['final_text'][:100]}")
        else:
            print(f"  ✓ Result: {result['final_text'][:100]}...")
            if result["used_file_search"]:
                print("  ✓ FileSearch was used")
            else:
                print("  ⚠️  FileSearch not detected in tool calls")


def test_persistence():
    """Test that vector store ID persists"""
    print("\nTesting persistence...")
    
    state_file = Path(".state/operator_agent.json")
    if state_file.exists():
        print(f"✓ State file exists: {state_file}")
        
        import json
        with open(state_file) as f:
            state = json.load(f)
            if "vector_store_id" in state:
                print(f"✓ Vector store ID persisted: {state['vector_store_id']}")
                return True
    
    print("⚠️  No persisted state found")
    return False


async def main():
    """Run all FileSearch tests"""
    print("=" * 50)
    print("FileSearch Test Suite")
    print("=" * 50)
    
    # Test creation
    created = await test_vector_store_creation()
    
    # Test queries if created
    if created:
        await test_filesearch_queries()
    
    # Test persistence
    test_persistence()
    
    print("\n" + "=" * 50)
    print("Tests complete!")


if __name__ == "__main__":
    asyncio.run(main())