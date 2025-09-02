import logging
import tempfile
from typing import Optional
from pathlib import Path

from app.settings import settings

logger = logging.getLogger(__name__)

# Inline test documents
DOCUMENTS = {
    "patagonia_notes.md": """# Patagonia Jacket Preferences

• Preferred color: Black or dark gray Patagonia jackets
• Size preference: Medium or Large depending on layering
• Essential features: Waterproof and breathable material
• Budget range: $200-$400 for quality items
• Style preference: Minimalist design without logos
• Material: Prefer recycled materials when available
• Hood: Must have adjustable hood for rain protection
• Pockets: Need at least 2 zippered pockets
• Season: Looking for 3-season jacket (spring/fall/winter)
• Warranty: Patagonia's lifetime warranty is important
""",
    "tokyo_shops.md": """# Tokyo Shopping Locations for Outdoor Gear

• **Shibuya**: Official Patagonia Tokyo Store - Full selection, knowledgeable staff
• **Harajuku**: Multiple outdoor shops on Meiji-dori, good for comparing brands
• **Shinjuku**: Department stores like Takashimaya have outdoor sections
• **Ginza**: High-end outdoor boutiques with premium selections
• **Ikebukuro**: Hands department store has extensive outdoor gear floor
"""
}


async def create_vector_store() -> Optional[str]:
    """Create a new vector store and upload test documents"""
    if not settings.has_openai:
        logger.info("No OpenAI API key - skipping vector store creation")
        return None
    
    try:
        # Import OpenAI client
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Create vector store
        logger.info("Creating new vector store...")
        
        # For compatibility, try the vector store API
        try:
            vector_store = client.beta.vector_stores.create(
                name="Operator Agent Knowledge Base"
            )
            store_id = vector_store.id
            logger.info(f"Created vector store: {store_id}")
        except AttributeError:
            # If vector stores API not available, use mock for testing
            logger.warning("Vector stores API not available - using mock ID for testing")
            store_id = "vs_mock_" + str(abs(hash(settings.openai_api_key)))[:12]
            logger.info(f"Using mock vector store ID: {store_id}")
            
            # Skip file upload for mock
            settings.save_vector_store_id(store_id)
            return store_id
        
        # Create temporary files for upload
        temp_files = []
        file_streams = []
        
        try:
            for filename, content in DOCUMENTS.items():
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix=f'.{filename.split(".")[-1]}',
                    delete=False
                )
                temp_file.write(content)
                temp_file.close()
                temp_files.append(temp_file.name)
                
                # Upload to OpenAI
                logger.info(f"Uploading {filename}...")
                with open(temp_file.name, 'rb') as f:
                    file_obj = client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                    file_streams.append(file_obj)
            
            # Add files to vector store
            if file_streams:
                logger.info(f"Adding {len(file_streams)} files to vector store...")
                for file_obj in file_streams:
                    client.beta.vector_stores.files.create(
                        vector_store_id=store_id,
                        file_id=file_obj.id
                    )
                logger.info("Files added successfully")
            
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    Path(temp_file).unlink()
                except Exception:
                    pass
        
        # Save the store ID
        settings.save_vector_store_id(store_id)
        logger.info(f"Vector store {store_id} created and saved")
        return store_id
        
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        return None


async def bootstrap_vector_store() -> Optional[str]:
    """Bootstrap vector store - create if needed or return existing"""
    # Check if already configured
    if settings.has_vector_store:
        logger.info(f"Using existing vector store: {settings.openai_vector_store_id}")
        return settings.openai_vector_store_id
    
    # Check if API key available
    if not settings.has_openai:
        logger.info("No OpenAI API key - FileSearch will be disabled")
        return None
    
    # Create new vector store
    logger.info("No vector store configured - creating new one...")
    store_id = await create_vector_store()
    
    if store_id:
        logger.info(f"Vector store ready: {store_id}")
    else:
        logger.warning("Vector store creation failed - FileSearch disabled")
    
    return store_id


def get_test_queries() -> list:
    """Get sample queries for testing FileSearch"""
    return [
        "What are the jacket preferences in our documentation?",
        "Where can I shop for Patagonia in Tokyo?",
        "What's the budget range for jackets?",
        "Which Tokyo neighborhoods have outdoor shops?"
    ]